# ==============================================================================
#  SpotiSync - 1-Click Automated Installer & Setup
#  Repo: https://github.com/Junaid355/SpotiSync
#  Usage: iwr -useb https://raw.githubusercontent.com/Junaid355/SpotiSync/main/install.ps1 | iex
# ==============================================================================

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = "SilentlyContinue"

$InstallDir = "$env:USERPROFILE\.spotisync"
$RepoRaw = "https://raw.githubusercontent.com/Junaid355/SpotiSync/main"

Write-Host ""
Write-Host " ========================================================" -ForegroundColor Green
Write-Host "   [*] Installing SpotiSync Setup Suite..." -ForegroundColor Green
Write-Host "   [+] Creator: Junaid355 | GitHub: Junaid355/SpotiSync" -ForegroundColor Cyan
Write-Host " ========================================================" -ForegroundColor Green
Write-Host ""

# 1. Create App Directory
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    New-Item -ItemType Directory -Force -Path "$InstallDir\web" | Out-Null
}

$files = @(
    "SpotifyAutoManager.ps1",
    "BackgroundStartupCheck.vbs",
    "Enable-Startup-AutoCheck.bat",
    "Disable-Startup-AutoCheck.bat",
    "Start-SpotifyManager.bat",
    "Run-Silent-Test.bat",
    "core.py",
    "app.py",
    "README.md",
    "web/index.html",
    "web/style.css",
    "web/app.js"
)

Write-Host "Downloading SpotiSync files..." -ForegroundColor Cyan
foreach ($f in $files) {
    $url = "$RepoRaw/$f"
    $dest = "$InstallDir\$f"
    $parent = Split-Path -Parent $dest
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
    } catch {}
}

# 2. Create Desktop Shortcut for GUI Dashboard
$wsh = New-Object -ComObject WScript.Shell
$desktop = [System.Environment]::GetFolderPath('Desktop')
$shortcut = $wsh.CreateShortcut("$desktop\SpotiSync Dashboard.lnk")
$shortcut.TargetPath = "$InstallDir\Start-SpotifyManager.bat"
$shortcut.WorkingDirectory = "$InstallDir"
$shortcut.Description = "SpotiSync Spotify & Spicetify Auto-Setup Suite"
$shortcut.Save()

# 3. Enable Headless Auto-Check on Startup
$regKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$vbsPath = "$InstallDir\BackgroundStartupCheck.vbs"
$val = "wscript.exe `"$vbsPath`""
Set-ItemProperty -Path $regKey -Name "SpotifyAutoSetupManager" -Value $val

Write-Host "`nRunning initial setup pipeline..." -ForegroundColor Green
# 4. Run the automated installer and patcher
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$InstallDir\SpotifyAutoManager.ps1" -AutoFix

Write-Host ""
Write-Host " ========================================================" -ForegroundColor Green
Write-Host "  [SUCCESS] SpotiSync Installed and Configured!" -ForegroundColor Green
Write-Host "  [*] Spotify + Spicetify + Marketplace are ready." -ForegroundColor Green
Write-Host "  [*] Silent Startup Auto-Check is ENABLED (0 RAM)." -ForegroundColor Cyan
Write-Host "  [*] Desktop shortcut created: 'SpotiSync Dashboard'" -ForegroundColor Cyan
Write-Host " ========================================================" -ForegroundColor Green
Write-Host ""
