# KytyPS5-nhl27-enhanced (release candidate 1) - DRAFT, review before sharing

> Draft notes prepared with AI help. The fork's "AI Use" rule says text you post must come from you, so
> rewrite or confirm these notes in your own words before you publish them.

A build of duy64/KytyPS5-nhl (release a917829, branch `opt/nhl27-fixes`) for NHL 27 (PPSA34063) with
steadier frame pacing and a faster PGO build. Source: branch `nhl27-enhanced`, commits after a917829:

- `dc04d4a9` videoOut: the game's own flip rate at a 60 Hz vblank is now the default (menus and cut-scenes
  at 30 fps, gameplay at 60 fps). Before, everything ran uncapped (50-120 fps swings, visible stutter).
  `KYTY_FORCE_FLIP_RATE=0` with `KYTY_MENU_VBLANK_HZ=240` / `KYTY_PLAY_VBLANK_HZ=240` brings back the old
  behaviour.
- `1f8fb5ef` swapchain: frame-pacing log lines (`NHL27FRAMETIME` every 5 s with 1% / 0.1% lows,
  `NHL27HITCH` for each frame over 50 ms).
- `b8867192` PGO profile recorded with the clang-cl 19.1.5 that ships with VS 2022 Build Tools
  (`tools/pgo/nhl27-clang19.profdata`), built with `-DKYTY_ARCH_AVX2=ON`. Build line: `tools/pgo/README.md`.
- `cfgGlobal.json`: `KYTY_PERF_STATS` set to `0` (its timers cost time and print ~25 lines/s).

## Measured (Ryzen 7 9800X3D, RTX 5080, scripted 15-minute CPU vs CPU Play Now match)

| | a917829 defaults | pacing fix | pacing fix + PGO/AVX2 |
|---|---|---|---|
| Gameplay fps (median / p10) | 67 / 54 (uncapped) | 60 / 59 | 60 / 60 |
| Gameplay 5 s windows with no missed frame | - | 57-58% | 79-87% |
| Gameplay frames over 50 ms (15 min) | - | 31-52 | 20-23 |
| Menus / 30 Hz scenes fps (median / p10) | 40 / - (uncapped) | 30 / 29 | 30 / 28-29 |
| Emulator GPU-thread time per draw | - | 3.21-3.29 us | 2.88 us (-10%) |

## Requirements

- A CPU with AVX2 (Intel Haswell / AMD Zen or newer).
- Everything else as in duy64's release (Vulkan GPU, the game dump, `cfgGlobal.json` switches).

## Known issues

- Heavy 30 Hz cut-scenes (arena intro, some replays) can still drop to 15-25 fps for a few seconds.
  The cause is guest memory faults on GPU-written pages, not GPU speed; that path is unchanged.
- A fresh folder compiles shaders during the first arena load (about 30 s of 2-29 fps); after that the first
  match ran like warm runs (play 75% clean windows, 9 frames over 50 ms in 15 min). Later boots pre-warm
  the shaders (`KYTY_SHADER_PREGEN`, on by default).
- Purple glowing eyes (seen once, earlier build): not reproduced in about 140 captured frames of menus,
  intros, close-ups and gameplay. Please report the scene if you see it.
- The upstream known bugs (jersey cloth, some skin tones, facial hair, bright pixels, logos) are unchanged.

## Credits

duy64 (KytyPS5-nhl), pengui07, pargi, the KytyPS5 authors (GPL-2.0, see `licenses/`).
AnyPS5 (boykopovar) was used as a reference only. No code was copied from it.

## AI involvement

The changes, measurements and these notes were produced with an AI coding assistant (Claude) driving the
build, scripted test runs and log analysis. Human testing: (fill in what you played and checked).
