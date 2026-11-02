# KytyPS5-nhl


A private working fork of [KytyPS5](https://github.com/KytyPS5/KytyPS5) focused on getting **EA Sports NHL 27** (PPSA34063, v01.003.001) running well. NHL 26 is untested on this fork. The working branch is `cold`.


> [!IMPORTANT]
> Not affiliated with Sony Interactive Entertainment, PlayStation or Electronic Arts. No game files or
> system software are distributed. Use only game files you have obtained legally.


## Build lines
- `-main`: clean playable build for daily play
- `-texcopy`: test build with the partial-overlap copy fix (v3); crash fix real, ice-glitch rate about the same as main
- `-launchupd`: launcher fix for updating the build you are running
- `-tailfix`: parked Nov 1 — tail-safe kill-switch diagnostic for the one-time black-crowd event (Be A Pro team-select crash on that line unresolved)
- `-ringbuf`: in flight — ring-buffer frame recorder (press F2 after a glitch to dump the ring)
- `-depthcol`: in flight — depth-as-color copy test for the ice glitch
Retired Nov 1: the tester diagnostic lines (-crumb, -modlist, -texdiag, -texfix, -texmerge, -readback, -rebind) — their releases were deleted and no tester builds are made from this fork anymore; -indirect was cancelled and never released.


*Development on this fork is AI-assisted; all changes are reviewed and tested in-game by the maintainer before release.*


## Status (2026-11-01)


| | NHL 27 |
|---|---|
| Boots to menus | Yes |
| Franchise / Play Now menus | Yes |
| Loads into a match | Yes |
| Player / scene lighting | **Fixed** (front-face encoding) |
| Commentary audio | Working (Opus multistream fix); some lines still garbled |
| Save / profile | Working |


## Known bugs


- **Jersey cloth glitches**
- **Some skin tones look wrong in cut-scenes**
- **Occasional crashes**
- **Blurry facial hair**
- **Bright pixels**
- **Scrambled team logos**
- **Volume normalization issues**
- Texture glitch: garbled / pixel-matrix ice and players, usually right after goals; HUD unaffected; main baseline 6-12 glitches per game; under investigation (depth-as-color test and ring-buffer recorder in flight)
- GPU device-loss crash: tester 1 (RTX 4080) now plays clean on RC3 (3 Be A Pro games with sims, no crash) — that is an RC3 result, not a fix in this fork; no tester builds are made from this fork anymore


## Notable fixes in this fork


- **Lighting (both games):** the pixel-shader front-face input now follows `SPI_BARYC_CNTL.FRONT_FACE_ALL_BITS`
  (integer 1/0 instead of float ±1). The lighting's `== 0` test never passed before, so direct light was
  never applied (players and floor were dark). Found by Cryan.
- **Commentary audio:** AJM Opus (codec 24) with a 2-byte LE length prefix. 2-channel instances are two uncoupled
  mono streams (self-delimited stream 0 + stream 1) whose TOC configs can differ.
- **Shader recompiler:**
  - partial-wave reductions (float-compare exec-bounded);
  - DPP/permlane inactive-lane preservation;
  - workgroup buffer sync;
  - bounded `S_SETPC` jump tables;
  - loop cap for runaway lighting loops (38 ms → 1.7 ms per draw);
  - memoized exponential recursion in resource materialization.
