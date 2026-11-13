#ifndef EMULATOR_SRC_COMMON_SPINWAIT_H_
#define EMULATOR_SRC_COMMON_SPINWAIT_H_

// Bounded spinning for the page-tracking spin locks.
// A waiter pauses for a while, then gives up its time slice, so a lock holder that lost its CPU can run again
// instead of every waiter burning a core until the scheduler returns to it. Uncontended locking is unchanged.
// KYTY_SPIN_YIELD=0 at startup restores the old pause-only loops.

#include <atomic>
#include <cstdint>
#include <cstdlib>
#include <thread>

#if defined(_MSC_VER)
#include <intrin.h>
#elif defined(__x86_64__)
#include <xmmintrin.h>
#endif

namespace Kyty::SpinWait {

inline constexpr uint32_t SpinsBeforeYield = 2048;

inline bool YieldEnabled() noexcept {
	static const bool enabled = [] {
		const char* value = std::getenv("KYTY_SPIN_YIELD");
		return value == nullptr || value[0] != '0';
	}();
	return enabled;
}

inline void Pause() noexcept {
#if defined(__x86_64__) || defined(_M_X64)
	_mm_pause();
#elif defined(_M_ARM64)
	__yield();
#elif defined(__aarch64__)
	asm volatile("yield");
#endif
}

// One step of a wait loop. `spins` counts the steps of the current wait.
inline void Step(uint32_t& spins) noexcept {
	if (++spins < SpinsBeforeYield || !YieldEnabled()) {
		Pause();
		return;
	}
	spins = 0;
	std::this_thread::yield();
}

} // namespace Kyty::SpinWait

#endif /* EMULATOR_SRC_COMMON_SPINWAIT_H_ */
