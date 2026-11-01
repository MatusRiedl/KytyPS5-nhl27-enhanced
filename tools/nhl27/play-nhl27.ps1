# Starts NHL 27 with the settings from cfgGlobal.json (and cfgPPSA34063.json if present), the way the
# launcher does. Saves the game folder in game_path.txt. Log: play_log.txt, the run before it: play_log_previous.txt.
param([string]$GamePath = "")

$ErrorActionPreference = "Stop"
$here  = $PSScriptRoot
$exe   = Join-Path $here "kyty_emulator.exe"
$saved = Join-Path $here "game_path.txt"
$log   = Join-Path $here "play_log.txt"

function Test-GameFolder([string]$path) {
	return $path -and (Test-Path -LiteralPath (Join-Path $path "eboot.bin"))
}

if (-not $GamePath -and (Test-Path -LiteralPath $saved)) {
	$GamePath = (Get-Content -LiteralPath $saved -TotalCount 1).Trim()
}
if ($GamePath -and (Split-Path -Leaf $GamePath) -eq "eboot.bin") {
	$GamePath = Split-Path -Parent $GamePath
}
if (-not (Test-GameFolder $GamePath)) {
	Add-Type -AssemblyName System.Windows.Forms
	$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
	$dialog.Description = "Select your NHL 27 game folder (the one that holds eboot.bin)"
	if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
		exit 1
	}
	$GamePath = $dialog.SelectedPath
}
if (-not (Test-GameFolder $GamePath)) {
	Write-Host "No eboot.bin in $GamePath. Pick the folder that holds eboot.bin."
	exit 1
}
Set-Content -LiteralPath $saved -Value $GamePath -Encoding UTF8

$screens = @{
	R1280X720  = @(1280, 720)
	R1920X1080 = @(1920, 1080)
	R2560X1440 = @(2560, 1440)
	R3840X2160 = @(3840, 2160)
}
$arguments = @("--game", "`"$GamePath`"")
foreach ($name in "cfgGlobal.json", "cfgPPSA34063.json") {
	$file = Join-Path $here $name
	if (-not (Test-Path -LiteralPath $file)) {
		continue
	}
	$emu = (Get-Content -LiteralPath $file -Raw | ConvertFrom-Json).emu
	foreach ($setting in $emu.env.PSObject.Properties) {
		[Environment]::SetEnvironmentVariable($setting.Name, [string]$setting.Value, "Process")
	}
	if ($screens.ContainsKey([string]$emu.screen_resolution)) {
		$size = $screens[[string]$emu.screen_resolution]
		$arguments += @("--screen-width", $size[0], "--screen-height", $size[1])
	}
	if ($emu.fullscreen_enabled) {
		$arguments += "--fullscreen"
	}
	if ($emu.extra_args) {
		$arguments += $emu.extra_args
	}
}

if (Test-Path -LiteralPath $log) {
	Move-Item -LiteralPath $log -Destination (Join-Path $here "play_log_previous.txt") -Force
}
Write-Host "Starting NHL 27 from $GamePath"
Write-Host "Keep this window open while you play. The log goes to play_log.txt."
$process = Start-Process -FilePath $exe -ArgumentList ($arguments -join " ") -WorkingDirectory $here `
	-RedirectStandardOutput $log -RedirectStandardError (Join-Path $here "play_log_errors.txt") `
	-NoNewWindow -PassThru
$process.WaitForExit()
if ($process.ExitCode -ne 0) {
	Write-Host "The game stopped with code $($process.ExitCode). If it crashed, keep play_log.txt for the bug report."
	exit 1
}
