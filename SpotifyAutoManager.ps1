param(
    [switch]$AutoFix,
    [switch]$CheckOnly,
    [switch]$Launch,
    [switch]$Apply,
    [switch]$Marketplace,
    [switch]$Startup,
    [switch]$StartupSilent,
    [switch]$Update
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Host.UI.RawUI.WindowTitle = "SpotiSync - Spotify & Spicetify Auto-Detector"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ScriptDir) { $ScriptDir = "$env:USERPROFILE\.spotisync" }

function Write-BrandHeader {
    Clear-Host
    Write-Host ""
    Write-Host " ========================================================" -ForegroundColor Green
    Write-Host "   [*] SpotiSync - Spotify & Spicetify Auto Setup Suite" -ForegroundColor Green
    Write-Host "   [+] Auto-Detection | 1-Click Installer | Marketplace" -ForegroundColor Cyan
    Write-Host "   [+] GitHub: https://github.com/Junaid355/SpotiSync" -ForegroundColor DarkGray
    Write-Host " ========================================================" -ForegroundColor Green
    Write-Host ""
}

function Get-SpotifyPath {
    $paths = @(
        "$env:APPDATA\Spotify\Spotify.exe",
        "$env:LOCALAPPDATA\Spotify\Spotify.exe",
        "$env:ProgramFiles\Spotify\Spotify.exe",
        "${env:ProgramFiles(x86)}\Spotify\Spotify.exe"
    )
    foreach ($p in $paths) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

function Get-SpicetifyPath {
    $paths = @(
        "$env:LOCALAPPDATA\spicetify\spicetify.exe",
        "$env:APPDATA\spicetify\spicetify.exe"
    )
    foreach ($p in $paths) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

function Test-MarketplaceInstalled {
    $marketDir = "$env:LOCALAPPDATA\spicetify\CustomApps\marketplace"
    $marketDir2 = "$env:APPDATA\spicetify\CustomApps\marketplace"
    if ((Test-Path $marketDir) -or (Test-Path $marketDir2)) { return $true }
    return $false
}

function Test-SpotifyPatched {
    # 1. Check index.html inside active xpui folder (Roaming & Local)
    $indexPaths = @(
        "$env:APPDATA\Spotify\Apps\xpui\index.html",
        "$env:LOCALAPPDATA\Spotify\Apps\xpui\index.html"
    )
    foreach ($indexPath in $indexPaths) {
        if (Test-Path $indexPath) {
            $content = Get-Content -Path $indexPath -Raw -ErrorAction SilentlyContinue
            if ($content -and $content -match "spicetify") {
                return $true
            }
        }
    }
    # 2. Check backup directories
    $backupPaths = @(
        "$env:APPDATA\spicetify\Backup",
        "$env:LOCALAPPDATA\spicetify\Backup"
    )
    foreach ($bp in $backupPaths) {
        if (Test-Path $bp) {
            $files = Get-ChildItem -Path $bp -ErrorAction SilentlyContinue
            if ($files -and $files.Count -gt 0) {
                return $true
            }
        }
    }
    return $false
}

function Apply-SpicetifyPatches {
    $spicePath = Get-SpicetifyPath
    if (-not $spicePath) { return $false }

    $wasRunning = $false
    $proc = Get-Process -Name Spotify -ErrorAction SilentlyContinue
    if ($proc) {
        $wasRunning = $true
        Stop-Process -Name Spotify -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }

    # Step 1: Ensure Spicetify CLI is up to date
    & $spicePath update 2>$null

    # Step 2: Attempt standard apply
    & $spicePath apply 2>$null
    if ($LASTEXITCODE -ne 0 -or -not (Test-SpotifyPatched)) {
        # Fallback 1: restore, then backup apply
        & $spicePath restore 2>$null
        & $spicePath backup apply 2>$null
    }

    if ($LASTEXITCODE -ne 0 -or -not (Test-SpotifyPatched)) {
        # Fallback 2: clear stale backup and create fresh backup apply (for Spotify version updates)
        & $spicePath clear 2>$null
        & $spicePath backup apply 2>$null
    }

    if ($wasRunning) {
        $spotPath = Get-SpotifyPath
        if ($spotPath) { Start-Process $spotPath }
    }

    return (Test-SpotifyPatched)
}

function Run-SilentStartupCheck {
    $spotPath = Get-SpotifyPath
    if (-not $spotPath) { exit 0 }

    # If Spotify was unpatched by an update, re-patch immediately
    if (-not (Test-SpotifyPatched)) {
        Apply-SpicetifyPatches
    }

    [System.GC]::Collect()
    exit 0
}

if ($StartupSilent) {
    Run-SilentStartupCheck
    exit 0
}

if ($CheckOnly) {
    Write-BrandHeader
    Write-Host " [System Diagnostics]" -ForegroundColor Yellow
    Write-Host " --------------------------------------------------------" -ForegroundColor DarkGray
    $spotPath = Get-SpotifyPath
    Write-Host "  Spotify Desktop  : " -NoNewline
    if ($spotPath) { Write-Host "INSTALLED ($spotPath)" -ForegroundColor Green } else { Write-Host "MISSING" -ForegroundColor Red }

    $proc = Get-Process -Name Spotify -ErrorAction SilentlyContinue
    Write-Host "  Spotify Status   : " -NoNewline
    if ($proc) { Write-Host "RUNNING ($($proc.Count) processes)" -ForegroundColor Green } else { Write-Host "STOPPED" -ForegroundColor DarkYellow }

    $isPatched = Test-SpotifyPatched
    Write-Host "  Spicetify Patch  : " -NoNewline
    if ($isPatched) { Write-Host "PATCHED & ACTIVE" -ForegroundColor Green } else { Write-Host "OUTDATED / UNPATCHED" -ForegroundColor Red }

    $market = Test-MarketplaceInstalled
    Write-Host "  Marketplace Hub  : " -NoNewline
    if ($market) { Write-Host "READY" -ForegroundColor Green } else { Write-Host "NOT INSTALLED" -ForegroundColor Red }

    $regKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
    $startupEntry = (Get-ItemProperty -Path $regKey -Name "SpotifyAutoSetupManager" -ErrorAction SilentlyContinue)
    Write-Host "  Auto-Check Boot  : " -NoNewline
    if ($startupEntry) { Write-Host "ENABLED (100% Silent Background & Auto-Close)" -ForegroundColor Green } else { Write-Host "DISABLED" -ForegroundColor DarkGray }
    Write-Host " --------------------------------------------------------" -ForegroundColor DarkGray
    exit 0
}

if ($AutoFix -or $Apply) {
    Write-BrandHeader
    Write-Host " [*] Applying Spicetify patch..." -ForegroundColor Cyan
    Apply-SpicetifyPatches
    Write-Host " [OK] Complete!" -ForegroundColor Green
    Start-Sleep -Seconds 2
    exit 0
}

Write-BrandHeader
$isPatched = Test-SpotifyPatched
Write-Host " Spotify Status: " -NoNewline
if ($isPatched) { Write-Host "Active & Patched [OK]" -ForegroundColor Green } else { Write-Host "Needs Patch [!]" -ForegroundColor Red }
Write-Host ""
Write-Host " [1] Re-Patch / AutoFix Spotify" -ForegroundColor Cyan
Write-Host " [2] Toggle Windows Startup Check" -ForegroundColor Yellow
Write-Host " [3] Launch Spotify" -ForegroundColor Green
Write-Host " [4] Exit" -ForegroundColor DarkGray
Write-Host ""
$choice = Read-Host " Enter choice (1-4)"
switch ($choice) {
    "1" { Apply-SpicetifyPatches }
    "2" {
        $regKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
        $vbsPath = Join-Path $ScriptDir "BackgroundStartupCheck.vbs"
        $val = "wscript.exe `"$vbsPath`""
        $exists = (Get-ItemProperty -Path $regKey -Name "SpotifyAutoSetupManager" -ErrorAction SilentlyContinue)
        if ($exists) {
            Remove-ItemProperty -Path $regKey -Name "SpotifyAutoSetupManager" -ErrorAction SilentlyContinue
            Write-Host "Startup check disabled." -ForegroundColor Yellow
        } else {
            Set-ItemProperty -Path $regKey -Name "SpotifyAutoSetupManager" -Value $val
            Write-Host "Startup check enabled!" -ForegroundColor Green
        }
        Start-Sleep -Seconds 2
    }
    "3" {
        $spotPath = Get-SpotifyPath
        if ($spotPath) { Start-Process $spotPath }
    }
    default { exit 0 }
}
