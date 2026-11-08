# Build dist\Faceoff.exe (one file, no console). Put it in the KytyPS5-nhl27-enhanced folder next to kyty_emulator.exe.
#   powershell -ExecutionPolicy Bypass -File packaging\build.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (Get-Process -Name Faceoff -ErrorAction SilentlyContinue) { throw "Close Faceoff first." }

$py = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $py)) { python -m venv .venv }
& $py -m pip install --quiet "pywebview==6.2.1" pyinstaller pillow pytest
if ($LASTEXITCODE -ne 0) { throw "could not install the build tools" }

& $py -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "tests failed" }

& $py packaging\make_icon.py
if ($LASTEXITCODE -ne 0) { throw "could not draw the icon" }

$web = Join-Path $root 'faceoff\web'
& $py -m PyInstaller --noconfirm --clean --onefile --noconsole --name Faceoff `
    --icon (Join-Path $root 'packaging\faceoff.ico') `
    --add-data "$web;faceoff\web" `
    --distpath dist --workpath build --specpath build `
    packaging\launcher.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

$exe = Join-Path $root 'dist\Faceoff.exe'
(Get-FileHash $exe -Algorithm SHA256).Hash.ToLower() + "  Faceoff.exe" | Set-Content (Join-Path $root 'dist\SHA256SUMS.txt') -Encoding ascii
Write-Host "Built $exe"
