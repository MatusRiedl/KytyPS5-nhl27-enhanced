# Faceoff

Launcher for the KytyPS5-nhl27-enhanced build of NHL 27. Put `Faceoff.exe` next to `kyty_emulator.exe`.

- Play tab: game folder, Play button, resolution / display / render scale / trophy popups (written to `cfgGlobal.json`),
  shader cache state and saves.
- Multiplayer tab: under construction.

It starts the emulator exactly like `play-nhl27.ps1` (same environment, arguments and `play_log.txt`).

Run from source: `set FACEOFF_HOME=<build folder>` then `.venv\Scripts\python -m faceoff`.
Build: `powershell -ExecutionPolicy Bypass -File packaging\build.ps1` -> `dist\Faceoff.exe`.
Check: `FACEOFF_SMOKE=<folder>` writes what the page shows and two window pictures, then closes.

Font: Titillium Web (SIL OFL, `faceoff/web/fonts/OFL.txt`). No NHL, EA or team artwork is included; the background art
is read at run time from the player's own game dump.
