// WidenReadback (KYTY_READBACK_WINDOW_KIB): the widened read covers the original, stays inside its buffer,
// and is left alone when no GPU-written byte is read.

#include "graphics/host_gpu/renderer/cache/readbackWindow.h"

#include <cstdint>
#include <cstdio>

namespace {

int g_failures = 0;

void Expect(const char* what, uint64_t buffer_start, uint64_t buffer_size, uint64_t window, bool gpu_written,
            uint64_t vaddr, uint64_t size, uint64_t want_vaddr, uint64_t want_size) {
	uint64_t v = vaddr;
	uint64_t s = size;
	Libs::Graphics::WidenReadback(buffer_start, buffer_size, window, gpu_written, v, s);
	if (v != want_vaddr || s != want_size) {
		std::printf("ReadbackWindowTests: FAIL %s: got [0x%llx,+0x%llx) want [0x%llx,+0x%llx)\n", what,
		            static_cast<unsigned long long>(v), static_cast<unsigned long long>(s),
		            static_cast<unsigned long long>(want_vaddr), static_cast<unsigned long long>(want_size));
		g_failures++;
	}
}

} // namespace

int main() {
	constexpr uint64_t KiB = 1024;
	constexpr uint64_t W   = 512 * KiB;
	constexpr uint64_t B   = 0x10000000; // window-aligned buffer start

	Expect("clean read untouched", B, 4 * W, W, false, B + 0x1234, 16, B + 0x1234, 16);
	Expect("off untouched", B, 4 * W, 0, true, B + 0x1234, 16, B + 0x1234, 16);
	Expect("aligned window", B, 4 * W, W, true, B + W + 0x1234, 16, B + W, W);
	// The window starts at the read's aligned start and stretches to cover the read's end.
	Expect("read spanning windows", B, 4 * W, W, true, B + W - 8, 16, B, W + 8);
	Expect("larger than window", B, 4 * W, W, true, B + 0x100, 2 * W, B, 2 * W + 0x100);
	// Buffer starts mid-window: the window starts at the buffer and keeps its full length (upstream's rule).
	Expect("clip start", B + 0x3000, 2 * W, W, true, B + 0x3000 + 0x40, 16, B + 0x3000, W);
	// Buffer ends mid-window.
	Expect("clip end", B, W + 0x2000, W, true, B + W + 0x100, 16, B + W, 0x2000);
	// A read past the buffer is not widened.
	Expect("outside buffer", B, W, W, true, B + W - 8, 16, B + W - 8, 16);

	if (g_failures != 0) {
		return 1;
	}
	std::printf("ReadbackWindowTests: all cases passed\n");
	return 0;
}
