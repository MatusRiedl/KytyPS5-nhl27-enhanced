// Stress test for Kyty::SpinWait, used by the page-tracking spin locks (TrackingSpinLock, SpinGuard).
// The lock below has the same shape as TrackingSpinLock (test-and-set, then wait on reads), without the
// emulator's assert dependency. Threads outnumber cores several times over, so lock holders are preempted.
// Checks: no deadlock (a watchdog), mutual exclusion (an owner check and an unguarded counter), and
// that the yield path is actually taken when KYTY_SPIN_YIELD=1.
// Usage: spin_wait_tests [--no-yield]

#include "common/spinWait.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <thread>
#include <vector>

namespace {

std::atomic<uint64_t> g_yield_steps {0};

class TestLock {
public:
	void lock() noexcept {
		while (m_lock.test_and_set(std::memory_order_acquire)) {
			uint32_t spins = 0;
			while (m_lock.test(std::memory_order_relaxed)) {
				Kyty::SpinWait::Step(spins);
				if (spins == 0) {
					g_yield_steps.fetch_add(1, std::memory_order_relaxed);
				}
			}
		}
	}
	void unlock() noexcept { m_lock.clear(std::memory_order_release); }

private:
	std::atomic_flag m_lock = ATOMIC_FLAG_INIT;
};

int Fail(const char* what) {
	std::printf("SpinWaitTests: FAIL %s\n", what);
	return 1;
}

} // namespace

int main(int argc, char** argv) {
	const bool yield = !(argc > 1 && std::strcmp(argv[1], "--no-yield") == 0);
#if defined(_WIN32)
	_putenv_s("KYTY_SPIN_YIELD", yield ? "1" : "0");
#else
	setenv("KYTY_SPIN_YIELD", yield ? "1" : "0", 1);
#endif
	if (Kyty::SpinWait::YieldEnabled() != yield) {
		return Fail("YieldEnabled does not follow KYTY_SPIN_YIELD");
	}

	const unsigned cores = std::max(1u, std::thread::hardware_concurrency());
	// Oversubscribed 4x with the yield. Pause-only loops get one thread per core: oversubscribed, they did not
	// finish in 5 minutes on a 16-thread CPU (48 of 64 threads), the starvation the yield is meant to end.
	const unsigned threads = yield ? cores * 4 : cores;
	const auto     started = std::chrono::steady_clock::now();
	const int      iters   = 20000;

	TestLock              lock;
	std::atomic<int>      inside {0};
	std::atomic<bool>     overlap {false};
	uint64_t              counter = 0; // guarded by lock only
	std::atomic<unsigned> finished {0};

	std::vector<std::thread> pool;
	pool.reserve(threads);
	for (unsigned t = 0; t < threads; t++) {
		pool.emplace_back([&] {
			for (int i = 0; i < iters; i++) {
				lock.lock();
				if (inside.fetch_add(1, std::memory_order_relaxed) != 0) {
					overlap.store(true, std::memory_order_relaxed);
				}
				counter++;
				// Hold the lock a little, sometimes long enough to be preempted inside it.
				if ((i & 255) == 0) {
					std::this_thread::sleep_for(std::chrono::microseconds(50));
				}
				inside.fetch_sub(1, std::memory_order_relaxed);
				lock.unlock();
			}
			finished.fetch_add(1, std::memory_order_relaxed);
		});
	}

	const auto deadline = std::chrono::steady_clock::now() + std::chrono::minutes(5);
	while (finished.load() < threads) {
		if (std::chrono::steady_clock::now() > deadline) {
			std::printf("SpinWaitTests: FAIL deadlock or livelock, %u of %u threads finished\n", finished.load(),
			            threads);
			std::fflush(stdout);
			std::_Exit(1);
		}
		std::this_thread::sleep_for(std::chrono::milliseconds(20));
	}
	for (auto& th : pool) {
		th.join();
	}

	if (overlap.load()) {
		return Fail("two threads inside the lock");
	}
	if (counter != static_cast<uint64_t>(threads) * iters) {
		return Fail("lost updates under the lock");
	}
	if (yield && g_yield_steps.load() == 0) {
		return Fail("yield path never taken under contention");
	}
	if (!yield && g_yield_steps.load() != 0) {
		return Fail("yield path taken with KYTY_SPIN_YIELD=0");
	}
	const auto ms =
	    std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - started).count();
	std::printf("SpinWaitTests: all cases passed (%s, %u threads, %llu yields, %lld ms)\n", yield ? "yield" : "no-yield",
	            threads, static_cast<unsigned long long>(g_yield_steps.load()), static_cast<long long>(ms));
	return 0;
}
