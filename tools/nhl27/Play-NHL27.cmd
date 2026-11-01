@echo off
rem Double-click to play. The first start asks for the game folder. To use another one, delete game_path.txt.
powershell -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0play-nhl27.ps1" %*
if errorlevel 1 pause
