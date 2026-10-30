# KytyPS5-nhl27-enhanced (release candidate 2) - DRAFT, review before sharing

> Draft notes prepared with AI help. The fork's "AI Use" rule says text you post must come from you, so
> rewrite or confirm these notes in your own words before you publish them.

A build of duy64/KytyPS5-nhl (release a917829, branch `opt/nhl27-fixes`) for NHL 27 (PPSA34063) with
steadier frame pacing and a faster PGO build. Source code (GPL-2.0): `KytyPS5-nhl27-enhanced-rc2-src.zip`,
shipped next to this build (git branch `nhl27-enhanced`). Commits after a917829:

- `dc04d4a9` videoOut: the game's own flip rate at a 60 Hz vblank is now the default (menus and cut-scenes
  at 30 fps, gameplay at 60 fps). Before, everything ran uncapped against a 240 Hz vblank (play about 54-80 fps, menus 40-75 fps, uneven pacing).
  `KYTY_FORCE_FLIP_RATE=0` with `KYTY_MENU_VBLANK_HZ=240` / `KYTY_PLAY_VBLANK_HZ=240` brings back the old
  behaviour.
- `1f8fb5ef` swapchain: frame-pacing log lines (`NHL27FRAMETIME` every 5 s with 1% / 0.1% lows,
  `NHL27HITCH` for each frame over 50 ms).
- `b8867192` PGO profile recorded with the clang-cl 19.1.5 that ships with VS 2022 Build Tools
  (`tools/pgo/nhl27-clang19.profdata`), built with `-DKYTY_ARCH_AVX2=ON`. Build line: `tools/pgo/README.md`.
- `3616c580` videoOut: at the 30 Hz flip rate, a frame that misses its vblank now shows on the next vblank
  (50 ms) instead of the next even one (66 ms). In a 15-minute match the 62-72 ms hitches in 30 Hz scenes fell
  from 222 to 23 (most became 50 ms); gameplay unchanged. `KYTY_LATE_FLIP=0` restores the old behaviour.
- `cfgGlobal.json`: `KYTY_PERF_STATS` set to `0` (its timers cost time and print to the console constantly).

## Measured (Ryzen 7 9800X3D, RTX 5080, scripted 15-minute CPU vs CPU Play Now match)

| | a917829 defaults (1 run) | pacing fix (2 runs) | pacing fix + PGO/AVX2 (3 runs) |
|---|---|---|---|
| Gameplay fps (median / p10) | 67 / 54 (uncapped) | 60 / 59-60 | 60 / 60 |
| Gameplay mean 1% low (fps) | - | 44.9-46.9 | 48.7-49.8 |
| Gameplay 5 s windows with no missed frame | - | 58-71% | 75-87% |
| Gameplay frames over 50 ms (15 min) | - | 28-31 | 9-23 |
| Menus / 30 Hz scenes fps (median / p10) | 40 / - (uncapped) | 30 / 29 | 30 / 28 |
| Emulator GPU-thread time per draw+dispatch | - | 3.21 us | 2.88 us (-10%) |

The 30 Hz cut-scene numbers swing a lot between identical runs (the match content differs), so they are not
compared here; see Known issues.

## Requirements

- A CPU with AVX2 (Intel Haswell / AMD Zen or newer).
- Everything else as in duy64's release (Vulkan GPU, the game dump, `cfgGlobal.json` switches).

## Known issues

- Heavy 30 Hz cut-scenes (arena intro, some replays) can still drop to 20-25 fps for a few seconds
  (about 600 frames over 34 ms in a 15-minute match; the misses are now mostly 50 ms rather than 66 ms).
  The cause is guest memory faults on GPU-written pages, not GPU speed; that path is unchanged.
- A fresh folder compiles shaders during the first arena load. On the test PC that took about 30 s of 2-29 fps,
  but its GPU driver shader cache was already warm, so expect longer on a new PC. After that load the first
  match ran like later ones. Later boots pre-warm the shaders (`KYTY_SHADER_PREGEN`, on by default).
- Purple glowing eyes (seen once, earlier build): not reproduced in about 140 captured frames of menus,
  intros, close-ups and gameplay. Please report the scene if you see it.
- The upstream known bugs (jersey cloth, some skin tones, facial hair, bright pixels, logos) are unchanged.

## Credits

duy64 (KytyPS5-nhl), pengui07, pargi, the KytyPS5 authors (GPL-2.0, see `licenses/`).
AnyPS5 (boykopovar) was used as a reference only. No code was copied from it.

## AI involvement

The changes, measurements and these notes were produced with an AI coding assistant (Claude) driving the
build, scripted test runs and log analysis. Human testing: (fill in what you played and checked).
