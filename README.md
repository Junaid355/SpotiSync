# 🎵 SpotiSync — Automated Spotify & Spicetify Setup Suite

[![GitHub Stars](https://img.shields.io/github/stars/Junaid355/SpotiSync?style=for-the-badge&color=1DB954)](https://github.com/Junaid355/SpotiSync)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-blue?style=for-the-badge)](https://github.com/Junaid355/SpotiSync)
[![Zero RAM](https://img.shields.io/badge/Residual%20RAM-0%20MB-green?style=for-the-badge)](https://github.com/Junaid355/SpotiSync)

An ultra-lightweight, automated Windows application and background utility that manages your Spotify and Spicetify setup.

If Spotify or Spicetify is missing, unpatched, or updated, SpotiSync **automatically downloads official standalone Spotify, installs Spicetify CLI + Marketplace, applies custom patches, and launches your patched player**.

---

## ⚡ 1-Click Install (Powershell)

Open PowerShell and paste this single command:

```powershell
iwr -useb https://raw.githubusercontent.com/Junaid355/SpotiSync/main/install.ps1 | iex
```

> **What this command does:**
> 1. Auto-downloads and configures SpotiSync in your user profile.
> 2. Automatically downloads & installs Spotify Win32 standalone if missing.
> 3. Installs Spicetify CLI & Marketplace.
> 4. Applies customization patches and launches your Spotify player.
> 5. Enables the silent zero-RAM startup check on boot.
> 6. Creates a `SpotiSync Dashboard` shortcut on your Desktop.

---

## 🌟 Key Features

- 🤫 **100% Silent Background Startup (0 MB Residual RAM)**:
  - On PC boot, runs silently in the background with **NO UI or terminal popups**.
  - Checks in `<100ms`, launches Spotify, and terminates immediately to consume **0 MB of RAM**.
- 🔄 **Auto-Repair & Auto-Update**:
  - Automatically detects when Spotify updates and re-applies Spicetify patches silently (`spicetify restore backup apply`).
  - Auto-updates Spicetify CLI and SpotiSync directly from GitHub.
- 📦 **1-Click Missing Components Installer**:
  - Automatically fetches official standalone Spotify from Spotify CDN (`SpotifySetup.exe`).
  - Automatically installs Spicetify CLI and the Marketplace extension hub.
- 🖥️ **Optional Modern Dark Dashboard**:
  - Open `SpotiSync Dashboard` whenever you want a visual UI with live diagnostic badges, action buttons, and live terminal logs.

---

## 🚀 Usage & Commands

### 1. Manual GUI Dashboard
Double-click `Start-SpotifyManager.bat` or run:
```powershell
python app.py
```

### 2. Standalone PowerShell Utility
- **Interactive Menu**:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\SpotifyAutoManager.ps1
  ```
- **1-Click Auto Setup**:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\SpotifyAutoManager.ps1 -AutoFix
  ```
- **Silent Background Run (No UI, Auto-close)**:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\SpotifyAutoManager.ps1 -StartupSilent
  ```
- **Check Diagnostics**:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\SpotifyAutoManager.ps1 -CheckOnly
  ```

---

## 🛠️ Quick Files & Toggles

| Shortcut | Action |
| :--- | :--- |
| `Run-Silent-Test.bat` | Tests the invisible background check (No UI, auto-closes). |
| `Enable-Startup-AutoCheck.bat` | Enables silent startup auto-check on Windows boot. |
| `Disable-Startup-AutoCheck.bat` | Disables startup auto-check. |
| `Start-SpotifyManager.bat` | Opens the interactive visual UI dashboard. |

---

## 👤 Author & Credits

- Created by **[Junaid355](https://github.com/Junaid355)**
- Powered by [Spicetify CLI](https://github.com/spicetify/cli) & [Spicetify Marketplace](https://github.com/spicetify/marketplace)
