#ifndef EMULATOR_SRC_GRAPHICS_HOST_GPU_RENDERER_CACHE_READBACKWINDOW_H_
#define EMULATOR_SRC_GRAPHICS_HOST_GPU_RENDERER_CACHE_READBACKWINDOW_H_

#include <algorithm>
#include <cstdint>

namespace Libs::Graphics {

// KYTY_READBACK_WINDOW_KIB (from upstream 1d5c8787): a read of GPU-written bytes widens to the aligned window
// of its buffer, so one download takes the scattered GPU-written islands next to it. `window` is a power of
// two. The result always covers [vaddr, vaddr + size) and stays inside the buffer; a read that touches no
// GPU-written byte, or does not lie inside the buffer, is left as it is.
inline void WidenReadback(uint64_t buffer_start, uint64_t buffer_size, uint64_t window, bool gpu_written,
                          uint64_t& vaddr, uint64_t& size) {
	const uint64_t buffer_end = buffer_start + buffer_size;
	if (!gpu_written || window == 0 || size == 0 || vaddr < buffer_start || vaddr + size > buffer_end) {
		return;
	}
	const uint64_t begin = std::max(vaddr & ~(window - 1), buffer_start);
	const uint64_t end   = std::min(std::max(begin + window, vaddr + size), buffer_end);
	if (begin <= vaddr && vaddr + size <= end) {
		size  = end - begin;
		vaddr = begin;
	}
}

} // namespace Libs::Graphics

#endif /* EMULATOR_SRC_GRAPHICS_HOST_GPU_RENDERER_CACHE_READBACKWINDOW_H_ */
