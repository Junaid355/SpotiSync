"""
Spotify & Spicetify Auto-Detector & Setup Suite - Core Engine
Handles system diagnostics, downloads, PowerShell automation, and registry management.
"""

import os
import sys
import json
import time
import shutil
import urllib.request
import subprocess
import winreg
from typing import Dict, Any, Callable, Optional

# Standard Paths
APPDATA = os.environ.get("APPDATA", "")
LOCALAPPDATA = os.environ.get("LOCALAPPDATA", "")
USERPROFILE = os.environ.get("USERPROFILE", "")

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


class SystemDetector:
    """Performs real-time diagnostics on Spotify and Spicetify installations."""

    @staticmethod
    def get_spotify_path() -> Optional[str]:
        for path in SPOTIFY_EXE_PATHS:
            if os.path.exists(path):
                return path
        # Check in PATH
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
        # Check config custom_apps
        try:
            result = subprocess.run([spicetify_path, "config", "custom_apps"], capture_output=True, text=True, timeout=5)
            if "marketplace" in result.stdout:
                return True
        except Exception:
            pass

        # Also check file directory
        custom_apps_dir = os.path.join(LOCALAPPDATA, "spicetify", "CustomApps", "marketplace")
        if os.path.exists(custom_apps_dir) and os.path.isdir(custom_apps_dir):
            return True

        return False

    @staticmethod
    def is_spicetify_applied() -> bool:
        """Checks if Spicetify has backed up and applied modifications."""
        backup_dir = os.path.join(LOCALAPPDATA, "spicetify", "Backup")
        if os.path.exists(backup_dir) and os.path.isdir(backup_dir):
            files = os.listdir(backup_dir)
            return len(files) > 0
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
            },
            "spicetify": {
                "installed": spicetify_path is not None,
                "path": spicetify_path,
                "version": spicetify_ver,
                "marketplace_installed": cls.is_marketplace_installed(),
                "applied": cls.is_spicetify_applied(),
            },
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

            if process.returncode == 0:
                return True
            else:
                self._log(f"Process ended with code {process.returncode}", "warning")
                return False
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
            proc = subprocess.Popen([installer_path], creationflags=0)
            
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

    def apply_spicetify(self, force_backup: bool = True) -> bool:
        """Applies Spicetify modifications/patches."""
        spicetify_path = SystemDetector.get_spicetify_path()
        if not spicetify_path:
            self._log("Spicetify executable not found! Cannot apply patch.", "error")
            return False

        self.kill_spotify()

        cmd = f"& '{spicetify_path}' backup apply" if force_backup else f"& '{spicetify_path}' apply"
        self._log(f"Applying Spicetify patches ({'backup apply' if force_backup else 'apply'})...", "info")
        
        success = self.run_powershell_cmd(cmd)
        if not success:
            self._log("Attempting 'spicetify restore backup apply' fallback...", "warning")
            fallback_cmd = f"& '{spicetify_path}' restore backup apply"
            success = self.run_powershell_cmd(fallback_cmd)

        if success:
            self._log("Spicetify applied successfully! Spotify is now customized.", "success")
        return success

    def launch_spotify(self) -> bool:
        """Launches Spotify application."""
        spotify_path = SystemDetector.get_spotify_path()
        if not spotify_path:
            self._log("Spotify executable not found! Cannot launch.", "error")
            return False

        self._log(f"Launching Spotify from {spotify_path}...", "info")
        try:
            subprocess.Popen([spotify_path], close_fds=True)
            self._log("Spotify launched!", "success")
            return True
        except Exception as e:
            self._log(f"Failed to launch Spotify: {e}", "error")
            return False

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
