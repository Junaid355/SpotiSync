"""
Spotify & Spicetify Auto-Detector & Setup Suite - Desktop Application
"""

import os
import sys
import json
import threading
import argparse
import webview
from core import SystemDetector, SpotifyManager

current_dir = os.path.dirname(os.path.abspath(__file__))
web_dir = os.path.join(current_dir, "web")
index_html = os.path.join(web_dir, "index.html")

_window = None
_manager = None


def emit_log(message: str, level: str = "info"):
    """Sends a log message into the web view console."""
    print(f"[{level.upper()}] {message}")
    global _window
    if _window:
        safe_msg = json.dumps(str(message))
        safe_lvl = json.dumps(str(level))
        try:
            _window.evaluate_js(f"if (window.receiveBackendLog) window.receiveBackendLog({safe_msg}, {safe_lvl});")
        except Exception as e:
            pass


def emit_status():
    """Pushes latest diagnostics directly to UI."""
    global _window
    if _window:
        status = SystemDetector.get_full_status()
        safe_status = json.dumps(status)
        try:
            _window.evaluate_js(f"if (window.receiveBackendStatus) window.receiveBackendStatus({safe_status});")
        except Exception:
            pass


class JsApi:
    """Minimal, clean class for PyWebView JS bridge with zero circular references."""

    def get_status(self):
        return SystemDetector.get_full_status()

    def auto_setup_all(self):
        def worker():
            try:
                _manager.auto_setup_all()
            except Exception as e:
                emit_log(f"Auto-setup error: {e}", "error")
            finally:
                emit_status()
                if _window:
                    _window.evaluate_js("if (window.onActionCompleted) window.onActionCompleted();")

        threading.Thread(target=worker, daemon=True).start()
        return "started"

    def launch_spotify(self):
        def worker():
            _manager.launch_spotify()
            emit_status()

        threading.Thread(target=worker, daemon=True).start()
        return "started"

    def apply_spicetify(self):
        def worker():
            try:
                _manager.apply_spicetify()
            except Exception as e:
                emit_log(f"Apply error: {e}", "error")
            finally:
                emit_status()
                if _window:
                    _window.evaluate_js("if (window.onActionCompleted) window.onActionCompleted();")

        threading.Thread(target=worker, daemon=True).start()
        return "started"

    def install_marketplace(self):
        def worker():
            try:
                _manager.install_marketplace()
            except Exception as e:
                emit_log(f"Marketplace install error: {e}", "error")
            finally:
                emit_status()
                if _window:
                    _window.evaluate_js("if (window.onActionCompleted) window.onActionCompleted();")

        threading.Thread(target=worker, daemon=True).start()
        return "started"

    def kill_spotify(self):
        def worker():
            _manager.kill_spotify()
            emit_status()
            if _window:
                _window.evaluate_js("if (window.onActionCompleted) window.onActionCompleted();")

        threading.Thread(target=worker, daemon=True).start()
        return "started"

    def set_startup_enabled(self, enabled: bool):
        res = _manager.set_startup_enabled(bool(enabled))
        emit_status()
        return res


def run_auto_startup_mode():
    """Silent background check executed when PC boots or triggered via --auto."""
    print("Executing Spotify Auto-Check on Startup...")
    mgr = SpotifyManager()
    
    # 1. Check if Spotify is installed
    if not SystemDetector.is_spotify_installed():
        print("Spotify is missing. Initiating auto-setup pipeline...")
        mgr.auto_setup_all()
        return

    # 2. Check Spicetify
    if not SystemDetector.is_spicetify_installed():
        print("Spicetify is missing. Installing...")
        mgr.install_spicetify_cli()
        mgr.install_marketplace()
        mgr.apply_spicetify()

    # 3. Check if Spotify is already running; if not, launch patched Spotify
    if not SystemDetector.is_spotify_running():
        print("Launching Patched Spotify...")
        mgr.launch_spotify()
    else:
        print("Spotify is already active.")


def main():
    global _window, _manager
    parser = argparse.ArgumentParser(description="Spotify & Spicetify Auto-Setup Suite")
    parser.add_argument("--auto", action="store_true", help="Run in silent auto-check startup mode")
    parser.add_argument("--check", action="store_true", help="Print system status and exit")
    args = parser.parse_args()

    if args.auto:
        run_auto_startup_mode()
        return

    if args.check:
        print(json.dumps(SystemDetector.get_full_status(), indent=2))
        return

    _manager = SpotifyManager(log_callback=emit_log)
    api = JsApi()
    
    _window = webview.create_window(
        title="SpotiSync - Spotify & Spicetify Auto-Setup Suite",
        url=f"file:///{index_html.replace(os.sep, '/')}",
        js_api=api,
        width=1020,
        height=720,
        min_size=(900, 620),
        text_select=True,
    )
    webview.start(debug=False)


if __name__ == "__main__":
    main()
