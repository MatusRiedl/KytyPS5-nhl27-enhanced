// Decision fixture for the texture-cache partial-overlap tail (KYTY_OVERLAP_MERGE_COPY). No GPU and
// no TextureCache instance: it tests the pure PlanOverlapCopy and OverlapSafeToDelete.
// Ported from duy64/KytyPS5-nhl opt/nhl27-tailfix (18642a72), without its Stage B region checks.
//
// Addresses, sizes and formats come from a real depth log. Extents are made up (1024x1024, one level,
// one layer, linear): PlanOverlapCopy does not read them.
//
// Each case is a shape that has reached the tail. PlanOverlapCopy does not repeat the earlier
// ResolveOverlap branches (equal address with equal block extent, mip and view).

#include "graphics/host_gpu/renderer/cache/textureCache.h"
#include "graphics/host_gpu/renderer/image/imageInfo.h"

#include <cstdint>
#include <cstdio>
#include <cstdlib>

namespace {

using namespace Libs::Graphics;

void Check(bool value, const char* text) {
	if (!value) {
		std::fprintf(stderr, "TextureCacheOverlapTests: failed: %s\n", text);
		std::abort();
	}
}

ImageInfo MakeInfo(uint64_t address, uint64_t size, vk::Format format, uint32_t bytes_per_block) {
	ImageInfo info;
	info.data.address    = address;
	info.data.size       = size;
	info.pixel_format    = format;
	info.bytes_per_block = bytes_per_block;
	info.extent          = {1024, 1024, 1};
	info.resources       = {1, 1};
	info.pitch           = 1024;
	info.type            = Prospero::ImageType::kColor2D;
	info.samples         = 1;
	info.tile_mode       = Prospero::TileMode::kLinear;
	return info;
}

// Requested depth against a color image at another base: tail, and not eligible for an offset copy.
void TestOffsetDepth() {
	const auto requested = MakeInfo(0x11c00c0000ull, 0xf00000ull, vk::Format::eD32SfloatS8Uint, 8);
	const auto cached    = MakeInfo(0x11c0f00000ull, 0x1fe0000ull, vk::Format::eR8G8B8A8Unorm, 4);
	const auto plan      = PlanOverlapCopy(requested, cached, true, false, true);
	Check(plan.branch == OverlapPlanBranch::TailFallThrough, "offset depth: tail");
	Check(!plan.fix_eligible, "offset depth: not fix-eligible");
}

// Same base, different format and size, both non-depth with 4-byte blocks: merged copy.
void TestSameBase() {
	const auto requested = MakeInfo(0x11c00c0000ull, 0xf00000ull, vk::Format::eR32Sfloat, 4);
	const auto cached =
	    MakeInfo(0x11c00c0000ull, 0x1c0000ull, vk::Format::eA2B10G10R10UnormPack32, 4);
	const auto plan = PlanOverlapCopy(requested, cached, true, false, true);
	Check(plan.branch == OverlapPlanBranch::MergedCopy, "same base: merged copy");
	Check(!plan.fix_eligible, "same base: no offset fix needed");
}

// The same formats at an offset base inside the requested range: tail, eligible for an offset copy.
void TestOffsetAlias() {
	const auto requested = MakeInfo(0x11c00c0000ull, 0xf00000ull, vk::Format::eR32Sfloat, 4);
	const auto cached =
	    MakeInfo(0x11c0f00000ull, 0x1c0000ull, vk::Format::eA2B10G10R10UnormPack32, 4);
	const auto plan = PlanOverlapCopy(requested, cached, true, false, true);
	Check(plan.branch == OverlapPlanBranch::TailFallThrough, "offset alias: tail");
	Check(plan.fix_eligible, "offset alias: fix-eligible");
}

void TestFormatEqualOffsetAlias() {
	const auto requested = MakeInfo(0x11c00c0000ull, 0xf00000ull, vk::Format::eR8G8B8A8Unorm, 4);
	const auto cached    = MakeInfo(0x11c0f00000ull, 0x1c0000ull, vk::Format::eR8G8B8A8Unorm, 4);
	const auto plan      = PlanOverlapCopy(requested, cached, true, false, true);
	Check(plan.branch == OverlapPlanBranch::TailFallThrough, "format-equal offset: tail");
	Check(plan.fix_eligible, "format-equal offset: fix-eligible");
}

// Each case breaks one guard of the same-base shape, so none may copy.
void TestGuardRejections() {
	const auto requested = MakeInfo(0x11c00c0000ull, 0xf00000ull, vk::Format::eR32Sfloat, 4);
	const auto cached =
	    MakeInfo(0x11c00c0000ull, 0x1c0000ull, vk::Format::eA2B10G10R10UnormPack32, 4);
	const auto rejected = [](const OverlapPlan& plan, const char* text) {
		Check(plan.branch == OverlapPlanBranch::TailFallThrough && !plan.fix_eligible, text);
	};
	{
		const auto depth = MakeInfo(0x11c00c0000ull, 0xf00000ull, vk::Format::eD32Sfloat, 4);
		rejected(PlanOverlapCopy(depth, cached, true, false, true), "guard: depth");
	}
	{
		auto other    = cached;
		other.samples = 2;
		rejected(PlanOverlapCopy(requested, other, true, false, true), "guard: samples");
	}
	{
		auto other   = requested;
		other.bgra16 = true;
		rejected(PlanOverlapCopy(other, cached, true, false, true), "guard: color transform");
	}
	{
		auto other = cached;
		other.type = Prospero::ImageType::kColor3D;
		rejected(PlanOverlapCopy(requested, other, true, false, true), "guard: type");
	}
	{
		const auto narrow = MakeInfo(0x11c00c0000ull, 0xf00000ull, vk::Format::eR8G8B8A8Unorm, 4);
		const auto wide =
		    MakeInfo(0x11c00c0000ull, 0x1c0000ull, vk::Format::eR32G32B32A32Sfloat, 16);
		rejected(PlanOverlapCopy(narrow, wide, true, false, true), "guard: block size");
	}
	rejected(PlanOverlapCopy(requested, cached, true, true, true), "guard: speculative");
	rejected(PlanOverlapCopy(requested, cached, false, false, true), "guard: no merged image");
	rejected(PlanOverlapCopy(requested, cached, true, false, false), "guard: not safe to delete");
}

// NumFramesBeforeRemoval is 32: the age must be strictly greater, and heap refs must be zero.
void TestSafeToDelete() {
	Check(OverlapSafeToDelete(1000, 967, 0), "safe: age 33");
	Check(!OverlapSafeToDelete(1000, 968, 0), "safe: age 32 is not enough");
	Check(!OverlapSafeToDelete(1000, 100, 1), "safe: heap refs");
	Check(!OverlapSafeToDelete(100, 100, 0), "safe: age 0");
	// A last access after the current tick clamps to age 0.
	Check(!OverlapSafeToDelete(100, 200, 0), "safe: clock behind");
}

} // namespace

int main() {
	TestOffsetDepth();
	TestSameBase();
	TestOffsetAlias();
	TestFormatEqualOffsetAlias();
	TestGuardRejections();
	TestSafeToDelete();
	std::puts("TextureCacheOverlapTests: all cases passed");
	return 0;
}
