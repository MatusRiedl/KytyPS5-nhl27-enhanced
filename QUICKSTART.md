# Quick start

## 1. Install

1. Download `Faceoff-v0.10.0.zip` from the [release page](../../releases/latest).
2. Extract it anywhere you can write to, with at least 2 GB free. Not inside `Program Files`.
3. Start `Faceoff.exe`. If Windows SmartScreen warns, choose **More info**, then **Run anyway**. If Faceoff asks for
   Microsoft's WebView2 Runtime, install it and start Faceoff again.

**Coming from RC3, RC4 or RC5:** extract the zip into your old folder and let it overwrite. Faceoff moves the old
build into `builds/` on the first start, and your saves, shader cache and game folder stay. To keep saves from another
Kyty install, copy `_SaveData`, `_DownloadData` and `_Trophies` into the Faceoff folder.

## 2. Point it at the game

Press **Browse** on the Play tab and pick your NHL 27 folder, the one that holds `eboot.bin` (PPSA34063, game version
01.003.001). Faceoff shows the title and version with a check mark when it's right.

## 3. Pick a build and settings

- **Emulator build:** v0.10.0 is the default. Older builds download when you pick them.
- **Resolution:** 1440p is the default. 4K at 100% render scale needs a lot of video memory.
- **Render scale:** lower is faster. 67% is the default.
- **Display:** windowed or fullscreen.

## 4. Play

Plug in a controller first, then press **Play NHL 27**. The first arena load stutters for 30 s or longer while
shaders compile; after that the shader cache is warm. Close the game window when you're done.

Keyboard: J = Cross, L = Circle, I = Triangle, K = Square, arrow keys = D-pad, WASD = left stick, Enter = Options,
Q / E = L1 / R1.

## If something goes wrong

- **The game won't start and a window names `MSVCP140.dll` or `VCRUNTIME140.dll`:** install the latest Microsoft
  Visual C++ Redistributable (x64).
- **Nothing happens on a CPU without AVX2:** the build needs AVX2 (Intel Haswell / AMD Zen or newer).
- **`could not reserve 13824 MB for guest direct memory`:** you started again too soon after closing. Wait a few
  seconds.
- **A crash:** Faceoff shows the play log. Press **Copy log**, or **Logs** to open its folder, and send it with your
  GPU and driver version on [Discord](https://gg.puckpeak.com). For a silent exit also send the Windows Event Viewer
  entry (Windows Logs > Application, `kyty_emulator.exe`).
