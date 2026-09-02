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
    $which = Get-Command "spotify" -ErrorAction SilentlyContinue
    if ($which) { return $which.Source }
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
    $which = Get-Command "spicetify" -ErrorAction SilentlyContinue
    if ($which) { return $which.Source }
    return $null
}

function Test-MarketplaceInstalled {
    $spicetifyPath = Get-SpicetifyPath
    if (-not $spicetifyPath) { return $false }
    $marketDir = "$env:LOCALAPPDATA\spicetify\CustomApps\marketplace"
    if (Test-Path $marketDir) { return $true }
    try {
        $apps = & $spicetifyPath config custom_apps 2>$null
        if ($apps -match "marketplace") { return $true }
    } catch {}
    return $false
}

function Show-Diagnostics {
    Write-Host " [System Diagnostics]" -ForegroundColor Yellow
    Write-Host " --------------------------------------------------------" -ForegroundColor DarkGray
    
    # 1. Spotify
    $spotPath = Get-SpotifyPath
    if ($spotPath) {
        Write-Host "  Spotify Desktop  : " -NoNewline
        Write-Host "INSTALLED" -ForegroundColor Green -NoNewline
        Write-Host " ($spotPath)" -ForegroundColor DarkGray
    } else {
        Write-Host "  Spotify Desktop  : " -NoNewline
        Write-Host "MISSING" -ForegroundColor Red
    }

    # Process
    $proc = Get-Process -Name Spotify -ErrorAction SilentlyContinue
    Write-Host "  Spotify Status   : " -NoNewline
    if ($proc) {
        Write-Host "RUNNING ($($proc.Count) processes)" -ForegroundColor Green
    } else {
        Write-Host "STOPPED" -ForegroundColor DarkYellow
    }

    # 2. Spicetify
    $spicePath = Get-SpicetifyPath
    if ($spicePath) {
        $ver = (& $spicePath -v 2>$null)
        Write-Host "  Spicetify CLI    : " -NoNewline
        Write-Host "INSTALLED ($ver)" -ForegroundColor Green
    } else {
        Write-Host "  Spicetify CLI    : " -NoNewline
        Write-Host "MISSING" -ForegroundColor Red
    }

    # 3. Marketplace
    $market = Test-MarketplaceInstalled
    Write-Host "  Marketplace Hub  : " -NoNewline
    if ($market) {
        Write-Host "READY" -ForegroundColor Green
    } else {
        Write-Host "NOT INSTALLED" -ForegroundColor Red
    }

    # 4. Startup Check
    $regKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
    $startupEntry = (Get-ItemProperty -Path $regKey -Name "SpotifyAutoSetupManager" -ErrorAction SilentlyContinue)
    Write-Host "  Auto-Check Boot  : " -NoNewline
    if ($startupEntry) {
        Write-Host "ENABLED (100% Silent Background & Auto-Close)" -ForegroundColor Green
    } else {
        Write-Host "DISABLED" -ForegroundColor DarkGray
    }

    Write-Host " --------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host ""
}

function Update-SpotiSyncFiles {
    # Silently updates script from GitHub
    $repoRaw = "https://raw.githubusercontent.com/Junaid355/SpotiSync/main"
    $scriptDir = $PSScriptRoot
    if (-not $scriptDir) { $scriptDir = "$env:USERPROFILE\.spotisync" }
    
    $files = @("SpotifyAutoManager.ps1", "core.py", "app.py", "BackgroundStartupCheck.vbs")
    foreach ($f in $files) {
        try {
            $dest = "$scriptDir\$f"
            Invoke-WebRequest -Uri "$repoRaw/$f" -OutFile "$dest.new" -UseBasicParsing -TimeoutSec 5 2>$null
            if (Test-Path "$dest.new") {
                Move-Item -Path "$dest.new" -Destination $dest -Force 2>$null
            }
        } catch {}
    }
}

function Install-SpotifyClient {
    $url = "https://download.scdn.co/SpotifySetup.exe"
    $dest = "$env:TEMP\SpotifySetup.exe"
    
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
        $proc = Start-Process -FilePath $dest -ArgumentList "/silent" -PassThru
        
        $maxWait = 60
        $elapsed = 0
        while ($elapsed -lt $maxWait) {
            Start-Sleep -Seconds 2
            $elapsed += 2
            $spotPath = Get-SpotifyPath
            if ($spotPath) { return $true }
        }
    } catch {}
    return (Get-SpotifyPath) -ne $null
}

function Install-SpicetifyCLI {
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        iwr -useb https://raw.githubusercontent.com/spicetify/cli/main/install.ps1 | iex
        return (Get-SpicetifyPath) -ne $null
    } catch {
        return $false
    }
}

function Install-SpicetifyMarketplace {
    try {
        iwr -useb https://raw.githubusercontent.com/spicetify/marketplace/main/resources/install.ps1 | iex
        $spicePath = Get-SpicetifyPath
        if ($spicePath) {
            & $spicePath config custom_apps marketplace 2>$null
        }
        return $true
    } catch {
        return $false
    }
}

function Apply-SpicetifyPatches {
    $spicePath = Get-SpicetifyPath
    if (-not $spicePath) { return $false }

    # Stop Spotify before patching
    Stop-Process -Name Spotify -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1

    & $spicePath backup apply 2>$null
    if ($LASTEXITCODE -ne 0) {
        & $spicePath restore backup apply 2>$null
    }
    return $true
}

function Start-SpotifyPatched {
    $spotPath = Get-SpotifyPath
    if ($spotPath) {
        Start-Process $spotPath
    }
}

function Start-AutoFixPipeline {
    # Step 1: Spotify
    $spotPath = Get-SpotifyPath
    if (-not $spotPath) {
        Install-SpotifyClient
    }

    # Step 2: Spicetify CLI
    $spicePath = Get-SpicetifyPath
    if (-not $spicePath) {
        Install-SpicetifyCLI
    } else {
        # Check for Spicetify updates
        & $spicePath upgrade 2>$null
    }

    # Step 3: Marketplace
    if (-not (Test-MarketplaceInstalled)) {
        Install-SpicetifyMarketplace
    }

    # Step 4: Apply & Launch
    Apply-SpicetifyPatches
    Start-SpotifyPatched
}

function Run-SilentStartupCheck {
    <#
    100% HEADLESS BACKGROUND EXECUTION (NO UI SHOWN):
    1. Checks GitHub for self-update silently.
    2. If Spotify is NOT downloaded: silently downloads and installs everything in the background.
    3. If Spicetify / Marketplace are missing or Spotify updated: installs and applies patches silently.
    4. If Spotify is already installed and ready: verifies everything and starts Spotify if not running.
    5. Auto-closes immediately. Leaves 0 MB of residual RAM in the background.
    #>
    Update-SpotiSyncFiles

    $spotPath = Get-SpotifyPath
    $spicePath = Get-SpicetifyPath

    if (-not $spotPath) {
        Install-SpotifyClient
        Install-SpicetifyCLI
        Install-SpicetifyMarketplace
        Apply-SpicetifyPatches
        Start-SpotifyPatched
    } elseif (-not $spicePath -or -not (Test-MarketplaceInstalled)) {
        Install-SpicetifyCLI
        Install-SpicetifyMarketplace
        Apply-SpicetifyPatches
        Start-SpotifyPatched
    } else {
        $proc = Get-Process -Name Spotify -ErrorAction SilentlyContinue
        if (-not $proc) {
            Start-SpotifyPatched
        }
    }

    # Free memory and exit immediately
    [System.GC]::Collect()
    exit 0
}

function Toggle-Startup {
    $regKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
    $scriptDir = $PSScriptRoot
    if (-not $scriptDir) { $scriptDir = "$env:USERPROFILE\.spotisync" }
    $vbsPath = "$scriptDir\BackgroundStartupCheck.vbs"
    $val = "wscript.exe `"$vbsPath`""

    $exists = (Get-ItemProperty -Path $regKey -Name "SpotifyAutoSetupManager" -ErrorAction SilentlyContinue)
    if ($exists) {
        Remove-ItemProperty -Path $regKey -Name "SpotifyAutoSetupManager" -ErrorAction SilentlyContinue
        Write-Host "Silent Auto-check on Windows Startup disabled." -ForegroundColor Yellow
    } else {
        Set-ItemProperty -Path $regKey -Name "SpotifyAutoSetupManager" -Value $val
        Write-Host "Silent Auto-check on Windows Startup ENABLED." -ForegroundColor Green
        Write-Host "It will run 100% invisible with NO UI on boot, auto-download if missing, and auto-close (0 RAM)." -ForegroundColor Cyan
    }
}

# CLI Parameter handling
if ($StartupSilent) {
    Run-SilentStartupCheck
    exit 0
}

if ($Update) {
    Write-Host "Checking for SpotiSync updates from GitHub..." -ForegroundColor Cyan
    Update-SpotiSyncFiles
    Write-Host "Updated!" -ForegroundColor Green
    exit 0
}

if ($AutoFix) {
    Write-Host "Running Auto-Setup..." -ForegroundColor Cyan
    Start-AutoFixPipeline
    Write-Host "Done!" -ForegroundColor Green
    exit 0
}

if ($CheckOnly) {
    Write-BrandHeader
    Show-Diagnostics
    exit 0
}

if ($Launch) {
    Start-SpotifyPatched
    exit 0
}

if ($Apply) {
    Apply-SpicetifyPatches
    exit 0
}

if ($Marketplace) {
    Install-SpicetifyMarketplace
    exit 0
}

if ($Startup) {
    Toggle-Startup
    exit 0
}

# Interactive Menu
do {
    Write-BrandHeader
    Show-Diagnostics

    Write-Host "  [1] Complete 1-Click Auto Setup (Download + Spicetify + Patch + Launch)" -ForegroundColor Green
    Write-Host "  [2] Launch Spotify" -ForegroundColor Cyan
    Write-Host "  [3] Apply / Re-apply Spicetify Patches" -ForegroundColor White
    Write-Host "  [4] Install / Update Spicetify Marketplace" -ForegroundColor White
    Write-Host "  [5] Stop Spotify Processes" -ForegroundColor Yellow
    Write-Host "  [6] Toggle Silent Auto-Check on Startup (No UI, Auto-closes, 0 RAM)" -ForegroundColor Magenta
    Write-Host "  [7] Refresh Diagnostics" -ForegroundColor White
    Write-Host "  [8] Update SpotiSync from GitHub" -ForegroundColor Cyan
    Write-Host "  [0] Exit" -ForegroundColor DarkGray
    Write-Host ""
    $choice = Read-Host " Select an option [0-8]"

    switch ($choice) {
        "1" { Start-AutoFixPipeline; Read-Host "`nPress Enter to return..." }
        "2" { Start-SpotifyPatched; Start-Sleep -Seconds 2 }
        "3" { Apply-SpicetifyPatches; Read-Host "`nPress Enter to return..." }
        "4" { Install-SpicetifyMarketplace; Read-Host "`nPress Enter to return..." }
        "5" { Stop-Process -Name Spotify -Force -ErrorAction SilentlyContinue; Write-Host "Spotify stopped." -ForegroundColor Green; Start-Sleep -Seconds 1 }
        "6" { Toggle-Startup; Start-Sleep -Seconds 2 }
        "7" { }
        "8" { Update-SpotiSyncFiles; Write-Host "Updated from GitHub." -ForegroundColor Green; Start-Sleep -Seconds 2 }
        "0" { exit }
        default { Write-Host "Invalid option" -ForegroundColor Red; Start-Sleep -Seconds 1 }
    }
} while ($choice -ne "0")
