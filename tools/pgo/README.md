# NHL 27 gameplay profile for PGO

`nhl27.profdata` is an LLVM IR profile of the emulator playing an NHL 27 (PPSA34063) match:
about 5 minutes of Play Now gameplay, recorded after the boot and menus (counters reset once the
match started), with the NHL 27 recommended `KYTY_*` switches.

Building with it (clang-cl only; the profile matches clang 22.1.8, the version that recorded it):

```
cmake -S . -B _Build/windows -DKYTY_PGO=use
```

`KYTY_PGO_PROFILE` defaults to this file. Another clang version ignores the profile with a
warning (`KYTY_PGO_PROFILE_COMPILER` names the expected version). Functions changed since the
profile was recorded simply get no profile data, so it degrades gradually; record a new one
after larger changes.

Measured on an RX 9070 XT + Ryzen 7 5800X3D: 18.6 vs 16.1 fps in gameplay (+15%, three boots
of each build, same switches).

## Recording a new profile

1. Configure a separate build directory with `-DKYTY_PGO=generate` and build `kyty_emulator`.
   The instrumented emulator writes `LLVM_PROFILE_FILE` every 30 seconds.
2. Run the game with `LLVM_PROFILE_FILE=<path>\nhl27.profraw`, get into a match, then create an
   empty file named `pgo.reset` in the emulator's working directory: the emulator zeroes its
   counters (prints `NHL27PGO: counters reset`), so the profile describes gameplay only.
3. Play for a few minutes and close the emulator.
4. `llvm-profdata merge -o tools/pgo/nhl27.profdata nhl27.profraw` (same LLVM version as the
   compiler), then rebuild with `-DKYTY_PGO=use`.
   Reconfigure (`cmake -S . -B <build dir> -DKYTY_PGO=use`) before building: the profile's hash
   is a configure-time define, and without it nothing is rebuilt with the new profile.

Do not enable `KYTY_PERF_STATS` while recording: its timers run millions of times per second
and would make their own code look hot.

## clang 19 profile (nhl27-enhanced)

`nhl27-clang19.profdata` is the same kind of profile recorded with the clang-cl 19.1.5 that ships with Visual
Studio 2022 Build Tools, so a PGO build needs no separate LLVM install. Recorded on a Ryzen 7 9800X3D +
RTX 5080 with `-DKYTY_ARCH_AVX2=ON`: boot excluded via `pgo.reset`, then menus, versus screen, arena intro
(30 Hz scenes) and about 4 minutes of a CPU vs CPU Play Now match, `KYTY_PERF_STATS=0`.

```
cmake -S . -B _Build/pgo -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON ^
  -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DKYTY_ARCH_AVX2=ON ^
  -DKYTY_PGO=use -DKYTY_PGO_PROFILE=%CD%/tools/pgo/nhl27-clang19.profdata -DKYTY_PGO_PROFILE_COMPILER=19.1.5
```

Measured against the same source without PGO/AVX2 (same machine, scripted 15-minute match): GPU-thread time
per draw or dispatch 2.88 vs 3.21-3.29 us in gameplay frames (-10%), 3.14 vs 3.35-3.51 us in the 30 Hz
crowd scenes (-6%); gameplay 1% low 48.7 vs 44.9 fps. The build needs an AVX2 CPU (Intel Haswell / AMD Zen
or newer).
