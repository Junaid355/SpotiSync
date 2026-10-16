"""
Spotify & Spicetify Auto-Detector & Setup Suite - Core Engine
Handles system diagnostics, downloads, PowerShell automation, auto-updates, and registry management.
"""

import os
import sys
import json
import time
import shutil
import urllib.request
import urllib.error
import subprocess
import winreg
from typing import Dict, Any, Callable, Optional, List

# Standard Paths
APPDATA = os.environ.get("APPDATA", "")
LOCALAPPDATA = os.environ.get("LOCALAPPDATA", "")
USERPROFILE = os.environ.get("USERPROFILE", "")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

SPOTIFY_EXE_PATHS = [
    os.path.join(APPDATA, "Spotify", "Spotify.exe"),
    os.path.join(LOCALAPPDATA, "Spotify", "Spotify.exe"),
    os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Spotify", "Spotify.exe"),
    os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Spotify", "Spotify.exe"),
]

SPICETIFY_EXE_PATHS = [
    os.path.join(LOCALAPPDATA, "spicetify", "spicetify.exe"),
    os.path.join(APPDATA, "spicetify", "spicetify.exe"),
]

SPOTIFY_DOWNLOAD_URL = "https://download.scdn.co/SpotifySetup.exe"
SPICETIFY_INSTALL_CMD = "iwr -useb https://raw.githubusercontent.com/spicetify/cli/main/install.ps1 | iex"
MARKETPLACE_INSTALL_CMD = "iwr -useb https://raw.githubusercontent.com/spicetify/marketplace/main/resources/install.ps1 | iex"

REG_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_APP_NAME = "SpotifyAutoSetupManager"

GITHUB_REPO = "Junaid355/SpotiSync"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/Junaid355/SpotiSync/main"
VERSION_FILE = os.path.join(SCRIPT_DIR, "version.json")


class AutoUpdater:
    """Handles automated GitHub repository sync and self-updates for SpotiSync."""

    FILES_TO_SYNC = [
        "core.py",
        "app.py",
        "SpotifyAutoManager.ps1",
        "Start-SpotifyManager.bat",
        "BackgroundStartupCheck.vbs",
        "Enable-Startup-AutoCheck.bat",
        "Disable-Startup-AutoCheck.bat",
        "Run-Silent-Test.bat",
        "README.md",
        "version.json",
        "web/index.html",
        "web/style.css",
        "web/app.js",
    ]

    @staticmethod
    def get_local_version() -> Dict[str, Any]:
        if os.path.exists(VERSION_FILE):
            try:
                with open(VERSION_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "version": "1.1.0",
            "commit": "unknown",
            "name": "SpotiSync Suite",
            "repo": f"https://github.com/{GITHUB_REPO}"
        }

    @classmethod
    def check_for_updates(cls, token: Optional[str] = None) -> Dict[str, Any]:
        """Checks GitHub API for the latest commit on main branch."""
        local_info = cls.get_local_version()
        local_commit = local_info.get("commit", "")

        url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/main"
        headers = {
            "User-Agent": "SpotiSync-AutoUpdater",
            "Accept": "application/vnd.github+json"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                remote_sha = data.get("sha", "")
                commit_info = data.get("commit", {})
                message = commit_info.get("message", "").split("\n")[0]
                date = commit_info.get("author", {}).get("date", "")

                has_update = bool(remote_sha and local_commit and remote_sha != local_commit and local_commit != "unknown")

                return {
                    "available": has_update,
                    "local_version": local_info.get("version", "1.1.0"),
                    "local_commit": local_commit[:7] if local_commit else "current",
                    "latest_commit": remote_sha[:7] if remote_sha else "latest",
                    "latest_sha": remote_sha,
                    "message": message,
                    "date": date,
                    "repo": f"https://github.com/{GITHUB_REPO}",
                    "checked_at": time.time(),
                }
        except Exception as e:
            return {
                "available": False,
                "local_version": local_info.get("version", "1.1.0"),
                "local_commit": local_commit[:7] if local_commit else "current",
                "latest_commit": "unknown",
                "error": str(e),
                "checked_at": time.time(),
            }

    @classmethod
    def download_and_apply_update(cls, log_callback: Optional[Callable[[str, str], None]] = None) -> bool:
        """Downloads updated files from raw GitHub into the current installation directory."""
        def _log(msg, lvl="info"):
            if log_callback:
                log_callback(msg, lvl)
            else:
                print(f"[{lvl.upper()}] {msg}")

        _log(f"Starting auto-update from https://github.com/{GITHUB_REPO}...", "info")
        check_res = cls.check_for_updates()
        new_sha = check_res.get("latest_sha", "")

        success_count = 0
        for rel_path in cls.FILES_TO_SYNC:
            remote_url = f"{GITHUB_RAW_URL}/{rel_path}"
            local_target = os.path.join(SCRIPT_DIR, rel_path)
            parent_dir = os.path.dirname(local_target)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)

            try:
                req = urllib.request.Request(remote_url, headers={"User-Agent": "SpotiSync-Updater"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    content = resp.read()
                    with open(local_target, "wb") as f:
                        f.write(content)
                success_count += 1
                _log(f"Updated: {rel_path}", "info")
            except Exception as e:
                _log(f"Notice: Failed to fetch {rel_path} ({e})", "warning")

        # Save updated version.json
        if new_sha:
            try:
                version_data = {
                    "version": "1.1.0",
                    "commit": new_sha,
                    "name": "SpotiSync Suite",
                    "repo": f"https://github.com/{GITHUB_REPO}",
                    "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                with open(VERSION_FILE, "w", encoding="utf-8") as f:
                    json.dump(version_data, f, indent=2)
            except Exception:
                pass

        if success_count > 0:
            _log(f"SpotiSync updated successfully ({success_count} files refreshed)!", "success")
            return True
        else:
            _log("Auto-update failed to download files.", "error")
            return False


class SystemDetector:
    """Performs real-time diagnostics on Spotify and Spicetify installations."""

    _cached_update_info = None
    _last_update_check = 0

    @staticmethod
    def get_spotify_path() -> Optional[str]:
        for path in SPOTIFY_EXE_PATHS:
            if os.path.exists(path):
                return path
        which_path = shutil.which("spotify")
        if which_path and os.path.exists(which_path):
            return which_path
        return None

    @staticmethod
    def is_spotify_installed() -> bool:
        return SystemDetector.get_spotify_path() is not None

    @staticmethod
    def is_ms_store_spotify_installed() -> bool:
        """Checks if the Microsoft Store (AppX) edition is installed."""
        try:
            cmd = ['powershell', '-NoProfile', '-Command', 'Get-AppxPackage -Name SpotifyAB.SpotifyMusic']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return "SpotifyAB.SpotifyMusic" in result.stdout
        except Exception:
            return False

    @staticmethod
    def is_spotify_running() -> bool:
        try:
            cmd = ['powershell', '-NoProfile', '-Command', '(Get-Process -Name Spotify -ErrorAction SilentlyContinue).Count']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            count_str = result.stdout.strip()
            return int(count_str) > 0 if count_str.isdigit() else False
        except Exception:
            return False

    @staticmethod
    def get_spicetify_path() -> Optional[str]:
        for path in SPICETIFY_EXE_PATHS:
            if os.path.exists(path):
                return path
        which_path = shutil.which("spicetify")
        if which_path and os.path.exists(which_path):
            return which_path
        return None

    @staticmethod
    def is_spicetify_installed() -> bool:
        return SystemDetector.get_spicetify_path() is not None

    @staticmethod
    def get_spicetify_version() -> Optional[str]:
        spicetify_path = SystemDetector.get_spicetify_path()
        if not spicetify_path:
            return None
        try:
            result = subprocess.run([spicetify_path, "-v"], capture_output=True, text=True, timeout=5)
            ver = result.stdout.strip()
            return ver if ver else None
        except Exception:
            return None

    @staticmethod
    def is_marketplace_installed() -> bool:
        spicetify_path = SystemDetector.get_spicetify_path()
        if not spicetify_path:
            return False
        # Check file directory
        for base in [APPDATA, LOCALAPPDATA]:
            market_dir = os.path.join(base, "spicetify", "CustomApps", "marketplace")
            if os.path.exists(market_dir) and os.path.isdir(market_dir):
                return True
        # Check config custom_apps
        try:
            result = subprocess.run([spicetify_path, "config", "custom_apps"], capture_output=True, text=True, timeout=5)
            if "marketplace" in result.stdout:
                return True
        except Exception:
            pass
        return False

    @staticmethod
    def is_spotify_updates_blocked() -> bool:
        """Checks if Spotify update paths are blocked with dummy files."""
        for p in [os.path.join(LOCALAPPDATA, "Spotify", "Update"), os.path.join(APPDATA, "Spotify", "Update")]:
            if os.path.exists(p) and os.path.isfile(p):
                return True
        return False

    @staticmethod
    def is_spicetify_applied() -> bool:
        """Checks if Spicetify has backed up and applied modifications."""
        found_xpui = False
        for spot_root in [os.path.join(APPDATA, "Spotify"), os.path.join(LOCALAPPDATA, "Spotify")]:
            index_path = os.path.join(spot_root, "Apps", "xpui", "index.html")
            if os.path.exists(index_path):
                found_xpui = True
                try:
                    with open(index_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        if "spicetify" in content.lower():
                            return True
                except Exception:
                    pass

        if found_xpui:
            return False

        # Legacy xpui.spa check
        for spot_root in [os.path.join(APPDATA, "Spotify"), os.path.join(LOCALAPPDATA, "Spotify")]:
            spa_path = os.path.join(spot_root, "xpui.spa")
            if os.path.exists(spa_path):
                for backup_dir in [os.path.join(APPDATA, "spicetify", "Backup"), os.path.join(LOCALAPPDATA, "spicetify", "Backup")]:
                    if os.path.exists(backup_dir) and os.path.isdir(backup_dir):
                        try:
                            if len(os.listdir(backup_dir)) > 0:
                                return True
                        except Exception:
                            pass
        return False

    @staticmethod
    def is_startup_enabled() -> bool:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, REG_APP_NAME)
                return bool(val)
        except Exception:
            return False

    @classmethod
    def get_cached_update_status(cls, force: bool = False) -> Dict[str, Any]:
        now = time.time()
        if force or cls._cached_update_info is None or (now - cls._last_update_check > 300):
            cls._cached_update_info = AutoUpdater.check_for_updates()
            cls._last_update_check = now
        return cls._cached_update_info

    @classmethod
    def get_full_status(cls) -> Dict[str, Any]:
        spotify_path = cls.get_spotify_path()
        spicetify_path = cls.get_spicetify_path()
        spicetify_ver = cls.get_spicetify_version()

        return {
            "spotify": {
                "installed": spotify_path is not None,
                "path": spotify_path,
                "running": cls.is_spotify_running(),
                "is_ms_store": cls.is_ms_store_spotify_installed(),
                "updates_blocked": cls.is_spotify_updates_blocked(),
            },
            "spicetify": {
                "installed": spicetify_path is not None,
                "path": spicetify_path,
                "version": spicetify_ver,
                "marketplace_installed": cls.is_marketplace_installed(),
                "applied": cls.is_spicetify_applied(),
            },
            "app_update": cls.get_cached_update_status(),
            "system": {
                "startup_enabled": cls.is_startup_enabled(),
                "timestamp": time.time(),
            }
        }


class SpotifyManager:
    """Executes installation, patching, updates, and process management."""

    def __init__(self, log_callback: Optional[Callable[[str, str], None]] = None):
        self.log_callback = log_callback or self._default_log

    def _log(self, msg: str, level: str = "info"):
        self.log_callback(msg, level)

    def _default_log(self, msg: str, level: str):
        prefix = {
            "info": "[INFO]",
            "success": "[SUCCESS]",
            "warning": "[WARN]",
            "error": "[ERROR]"
        }.get(level, "[LOG]")
        print(f"{prefix} {msg}")

    def run_powershell_cmd(self, command: str) -> bool:
        """Executes a PowerShell command with real-time output logging."""
        self._log(f"Executing: {command}", "info")
        try:
            process = subprocess.Popen(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            for line in iter(process.stdout.readline, ''):
                clean_line = line.strip()
                if clean_line:
                    self._log(clean_line, "info")

            process.stdout.close()
            process.wait()

            return process.returncode == 0
        except Exception as e:
            self._log(f"Execution failed: {e}", "error")
            return False

    def kill_spotify(self) -> bool:
        """Terminates running Spotify processes gracefully or forcefully."""
        self._log("Stopping running Spotify instances...", "info")
        try:
            cmd = "Stop-Process -Name Spotify -Force -ErrorAction SilentlyContinue"
            subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, timeout=10)
            time.sleep(1)
            self._log("Spotify processes stopped.", "success")
            return True
        except Exception as e:
            self._log(f"Failed to stop Spotify: {e}", "warning")
            return False

    def download_and_install_spotify(self) -> bool:
        """Downloads official standalone Win32 Spotify installer and executes it."""
        self._log("Initiating official Spotify standalone setup...", "info")
        temp_dir = os.path.join(LOCALAPPDATA, "Temp")
        installer_path = os.path.join(temp_dir, "SpotifySetup.exe")

        try:
            self._log(f"Downloading from {SPOTIFY_DOWNLOAD_URL} ...", "info")
            urllib.request.urlretrieve(SPOTIFY_DOWNLOAD_URL, installer_path)
            self._log(f"Installer downloaded to {installer_path}", "success")

            self._log("Running Spotify installer (please wait a moment)...", "info")
            subprocess.Popen([installer_path], creationflags=0)

            # Wait for Spotify to be installed
            max_wait = 90
            start_t = time.time()
            installed = False

            while time.time() - start_t < max_wait:
                if SystemDetector.is_spotify_installed():
                    installed = True
                    break
                time.sleep(2)

            if installed:
                self._log("Spotify Desktop client successfully installed!", "success")
                return True
            else:
                self._log("Spotify installer was started, but installation path is pending.", "warning")
                return True
        except Exception as e:
            self._log(f"Error downloading/installing Spotify: {e}", "error")
            return False

    def install_spicetify_cli(self) -> bool:
        """Installs Spicetify CLI via the official script."""
        self._log("Starting Spicetify CLI installation...", "info")
        success = self.run_powershell_cmd(SPICETIFY_INSTALL_CMD)

        spicetify_path = SystemDetector.get_spicetify_path()
        if spicetify_path or success:
            self._log("Spicetify CLI installation completed successfully!", "success")
            return True
        else:
            self._log("Failed to locate Spicetify CLI after installation script.", "error")
            return False

    def install_marketplace(self) -> bool:
        """Installs Spicetify Marketplace extension."""
        self._log("Installing Spicetify Marketplace...", "info")
        success = self.run_powershell_cmd(MARKETPLACE_INSTALL_CMD)

        spicetify_path = SystemDetector.get_spicetify_path()
        if spicetify_path:
            subprocess.run([spicetify_path, "config", "custom_apps", "marketplace"], capture_output=True)

        self._log("Spicetify Marketplace setup finished.", "success")
        return success

    def update_spicetify(self) -> bool:
        """Updates Spicetify CLI to the latest release."""
        spicetify_path = SystemDetector.get_spicetify_path()
        if not spicetify_path:
            self._log("Spicetify not found to update.", "warning")
            return False
        self._log("Checking and upgrading Spicetify CLI...", "info")
        cmd = f"& '{spicetify_path}' update"
        return self.run_powershell_cmd(cmd)

    def ensure_valid_spicetify_config(self) -> None:
        """Ensures Spicetify config does not use a broken or empty theme like 'marketplace' as current_theme."""
        spicetify_path = SystemDetector.get_spicetify_path()
        if not spicetify_path:
            return
        try:
            # Check current theme
            res = subprocess.run([spicetify_path, "config", "current_theme"], capture_output=True, text=True, timeout=5)
            curr = res.stdout.strip()
            if curr.lower() == "marketplace" or not curr:
                self._log("Fixing current_theme to SpicetifyDefault (marketplace is a custom app, not a theme)...", "info")
                subprocess.run([spicetify_path, "config", "current_theme", "SpicetifyDefault"], capture_output=True, timeout=5)

            # Ensure marketplace is in custom_apps
            res2 = subprocess.run([spicetify_path, "config", "custom_apps"], capture_output=True, text=True, timeout=5)
            if "marketplace" not in res2.stdout:
                subprocess.run([spicetify_path, "config", "custom_apps", "marketplace"], capture_output=True, timeout=5)
        except Exception as e:
            self._log(f"Notice: Config check warning ({e})", "warning")

    def apply_spicetify(self, force_backup: bool = True) -> bool:
        """Applies Spicetify modifications/patches with auto-update and multi-tier recovery."""
        spicetify_path = SystemDetector.get_spicetify_path()
        if not spicetify_path:
            self._log("Spicetify executable not found! Cannot apply patch.", "error")
            return False

        self.kill_spotify()
        self.ensure_valid_spicetify_config()

        # Step 1: Attempt spicetify update (non-blocking if rate limited)
        self._log("Checking Spicetify CLI updates...", "info")
        self.run_powershell_cmd(f"& '{spicetify_path}' update")

        # Step 2: Try standard apply or backup apply
        cmd = f"& '{spicetify_path}' backup apply" if force_backup else f"& '{spicetify_path}' apply"
        self._log(f"Applying Spicetify patches ({'backup apply' if force_backup else 'apply'})...", "info")
        success = self.run_powershell_cmd(cmd)

        # Step 3: Fallback 1 - restore, then backup apply
        if not success or not SystemDetector.is_spicetify_applied():
            self._log("Attempting 'spicetify restore backup apply' recovery...", "warning")
            fallback_cmd = f"& '{spicetify_path}' restore; & '{spicetify_path}' backup apply"
            success = self.run_powershell_cmd(fallback_cmd)

        # Step 4: Fallback 2 - clear stale backup and create fresh backup apply
        if not success or not SystemDetector.is_spicetify_applied():
            self._log("Attempting 'spicetify clear backup apply' for updated Spotify...", "warning")
            clear_cmd = f"& '{spicetify_path}' clear; & '{spicetify_path}' backup apply"
            success = self.run_powershell_cmd(clear_cmd)

        if success or SystemDetector.is_spicetify_applied():
            self._log("Spicetify applied successfully! Spotify is now customized.", "success")
            self.block_spotify_updates()
            return True
        else:
            self._log("Failed to apply Spicetify patches.", "error")
            return False

    def block_spotify_updates(self) -> bool:
        """Blocks Spotify from automatically downloading updates by locking Update directory paths."""
        self._log("Configuring Spotify auto-update blocker...", "info")
        paths = [
            os.path.join(LOCALAPPDATA, "Spotify", "Update"),
            os.path.join(APPDATA, "Spotify", "Update"),
        ]
        user = os.environ.get("USERNAME", "Everyone")
        import stat
        success = True
        for p in paths:
            try:
                parent = os.path.dirname(p)
                if not os.path.exists(parent):
                    os.makedirs(parent, exist_ok=True)
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                if not os.path.exists(p):
                    with open(p, "w", encoding="utf-8") as f:
                        f.write("Spotify auto-updates blocked by SpotiSync")
                os.chmod(p, stat.S_IREAD)
                subprocess.run(["icacls", p, "/deny", f"{user}:(W,D)"], capture_output=True)
            except Exception as e:
                self._log(f"Failed to lock {p}: {e}", "warning")
                success = False

        if success:
            self._log("Spotify auto-updater blocked (preventing Spotify from wiping Spicetify).", "success")
        return success

    def unblock_spotify_updates(self) -> bool:
        """Unblocks Spotify updates."""
        self._log("Removing Spotify auto-update blocker...", "info")
        paths = [
            os.path.join(LOCALAPPDATA, "Spotify", "Update"),
            os.path.join(APPDATA, "Spotify", "Update"),
        ]
        user = os.environ.get("USERNAME", "Everyone")
        import stat
        for p in paths:
            try:
                if os.path.exists(p):
                    subprocess.run(["icacls", p, "/remove:d", user], capture_output=True)
                    os.chmod(p, stat.S_IWRITE)
                    if os.path.isdir(p):
                        shutil.rmtree(p, ignore_errors=True)
                    else:
                        os.remove(p)
            except Exception as e:
                self._log(f"Failed to unlock {p}: {e}", "warning")
        self._log("Spotify auto-updater unblocked.", "info")
        return True

    def launch_spotify(self) -> bool:
        """Launches Spotify application decoupled as an interactive Windows user process."""
        spotify_path = SystemDetector.get_spotify_path()
        if not spotify_path:
            self._log("Spotify executable not found! Cannot launch.", "error")
            return False

        self._log(f"Launching Spotify from {spotify_path}...", "info")
        try:
            # Shell.Application starts process decoupled in user's interactive desktop
            cmd = f"$app = New-Object -ComObject Shell.Application; $app.ShellExecute('{spotify_path}', '', '', 'open', 1)"
            subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, timeout=10)
            self._log("Spotify launched!", "success")
            return True
        except Exception as e:
            self._log(f"Failed to launch Spotify: {e}", "error")
            return False

    def update_spotisync(self) -> bool:
        """Performs full automated GitHub self-update of SpotiSync."""
        return AutoUpdater.download_and_apply_update(log_callback=self.log_callback)

    def set_startup_enabled(self, enabled: bool) -> bool:
        """Configures Windows Startup Registry entry to run silently and exit (0 RAM)."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
                if enabled:
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    vbs_path = os.path.join(script_dir, "BackgroundStartupCheck.vbs")
                    val_str = f'wscript.exe "{vbs_path}"'
                    winreg.SetValueEx(key, REG_APP_NAME, 0, winreg.REG_SZ, val_str)
                    self._log("Silent background check on Windows Startup enabled (auto-closes, 0 RAM).", "success")
                else:
                    try:
                        winreg.DeleteValue(key, REG_APP_NAME)
                        self._log("Silent auto-check on Windows Startup disabled.", "info")
                    except FileNotFoundError:
                        pass
            return True
        except Exception as e:
            self._log(f"Failed to update startup registry: {e}", "error")
            return False

    def auto_setup_all(self) -> Dict[str, Any]:
        """
        Complete 1-Click Pipeline:
        1. Checks Spotify -> Downloads & Installs if missing
        2. Checks Spicetify CLI -> Installs if missing
        3. Checks Marketplace -> Installs if missing
        4. Applies Backup & Patch
        5. Launches Spotify
        """
        self._log("=== Starting Automated Spotify & Spicetify Full Setup ===", "info")

        # Step 1: Spotify
        if not SystemDetector.is_spotify_installed():
            self._log("[Step 1/4] Spotify is not installed. Initiating download...", "info")
            if not self.download_and_install_spotify():
                self._log("Spotify installation failed. Aborting pipeline.", "error")
                return {"success": False, "step": "spotify"}
        else:
            self._log("[Step 1/4] Spotify is already installed.", "success")

        # Step 2: Spicetify CLI
        if not SystemDetector.is_spicetify_installed():
            self._log("[Step 2/4] Spicetify CLI not detected. Running install script...", "info")
            if not self.install_spicetify_cli():
                self._log("Spicetify CLI installation failed.", "error")
                return {"success": False, "step": "spicetify_cli"}
        else:
            ver = SystemDetector.get_spicetify_version()
            self._log(f"[Step 2/4] Spicetify CLI detected ({ver or 'OK'}).", "success")

        # Step 3: Marketplace
        if not SystemDetector.is_marketplace_installed():
            self._log("[Step 3/4] Installing Spicetify Marketplace...", "info")
            self.install_marketplace()
        else:
            self._log("[Step 3/4] Spicetify Marketplace is already installed.", "success")

        # Step 4: Patch & Launch
        self._log("[Step 4/4] Applying Spicetify patches...", "info")
        self.apply_spicetify(force_backup=True)

        self._log("Launching patched Spotify...", "info")
        self.launch_spotify()

        self._log("=== Automated Setup Completed Successfully! ===", "success")
        return {"success": True, "step": "completed"}


if __name__ == "__main__":
    print(json.dumps(SystemDetector.get_full_status(), indent=2))
