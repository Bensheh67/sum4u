#!/usr/bin/env python3
"""
summary4u Desktop App — M1 skeleton entry point.

Architecture:
  rumps      → menu bar icon + popover menu
  pywebview  → main window (HTML/WebUI)
  uvicorn    → subprocess that serves FastAPI on port 8000

Acceptance criteria (M1):
  AC-1  双击/运行入口 → 1秒内菜单栏图标出现
  AC-2  主窗口不自动弹出
  AC-3  关闭主窗口后菜单栏图标仍存在
  AC-23 App 运行时 localhost:8000 仍可访问(共享 FastAPI 后端)
"""

import os
import sys
import subprocess
import webbrowser
import threading
import time
import signal

# ── dependency guard ────────────────────────────────────────────────────────
try:
    import rumps
except ImportError:
    print("ERROR: rumps not installed. Run: pip install -r desktop/requirements.txt")
    sys.exit(1)

try:
    import webview
except ImportError:
    print("ERROR: pywebview not installed. Run: pip install -r desktop/requirements.txt")
    sys.exit(1)

# ── project paths ────────────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DESKTOP = os.path.dirname(os.path.abspath(__file__))
_PREVIEW_HTML = os.path.join(_DESKTOP, "preview.html")
_MAIN_HTML = os.path.join(_ROOT, "index.html")   # existing WebUI entry
_SERVER_PORT = 8000
_SERVER_URL = f"http://localhost:{_SERVER_PORT}"


# ── icon generation (menu_bar.py) ───────────────────────────────────────────
def _ensure_icons():
    sys.path.insert(0, _DESKTOP)
    from menu_bar import ensure_icons
    ensure_icons()


# ── uvicorn subprocess management ────────────────────────────────────────────

_uvicorn_proc: subprocess.Popen | None = None


def start_uvicorn():
    """Start FastAPI via uvicorn in a background subprocess (port 8000)."""
    global _uvicorn_proc
    if _uvicorn_proc is not None and _uvicorn_proc.poll() is None:
        return  # already running

    # Start from project root so FastAPI can find src/
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn",
         "src.main:app",
         "--host", "127.0.0.1",
         "--port", str(_SERVER_PORT),
         "--root-path", ""],
        cwd=_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _uvicorn_proc = proc
    # Give uvicorn a moment to bind
    time.sleep(1.5)


def stop_uvicorn():
    global _uvicorn_proc
    if _uvicorn_proc is None:
        return
    proc, _uvicorn_proc = _uvicorn_proc, None
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


# ── main window management ───────────────────────────────────────────────────

_main_window: webview.Window | None = None


def open_main_window():
    """Show the main window. Called when user clicks '打开主窗口' in menu."""
    global _main_window

    # Determine which HTML to show
    if os.path.exists(_MAIN_HTML):
        url_or_file = _MAIN_HTML
    else:
        url_or_file = _PREVIEW_HTML

    # If already open, just bring to front
    if _main_window is not None:
        _main_window.hide()   # pywebview has no "bring to front" directly; show again
        _main_window.show()
        return

    # Create a new pywebview window
    window = webview.create_window(
        "summary4u",
        url_or_file if os.path.exists(_MAIN_HTML) else f"file://{_PREVIEW_HTML}",
        width=1024,
        height=720,
        min_size=(800, 600),
        resizable=True,
        js_api=None,
    )
    _main_window = window

    # Start uvicorn if not yet running (AC-23)
    start_uvicorn()

    # pywebview event loop runs on this thread; returns when window is closed
    webview.start()
    # When we reach here, the window was closed by the user
    _main_window = None


def is_main_window_open() -> bool:
    return _main_window is not None


# ── App class ────────────────────────────────────────────────────────────────

class Summary4uApp(rumps.App):
    """rumps wrapper — menu bar app with popover and stateful icon."""

    def __init__(self):
        # App name (displayed in menu bar)
        super().__init__("summary4u")

        # State: "idle" | "running" | "done" | "error"
        self._state = "idle"

        # Build menu bar icon
        _ensure_icons()
        from menu_bar import MenuBarController
        self._controller = MenuBarController(self)

        # Build the popover menu
        self.menu = self._build_menu()

        # Start uvicorn in background so AC-23 works
        start_uvicorn()

        # Initial state: idle
        self._controller.set_state("idle")

        # Register signal handler so Ctrl+C still exits cleanly
        signal.signal(signal.SIGINT, signal.SIG_DFL)

    def _build_menu(self) -> rumps.Menu:
        """Build the popover menu shown when clicking the menu bar icon."""
        menu = rumps.Menu()

        menu.add("打开主窗口")          # → AC-2: window does not auto-pop
        menu.add(rumps.MenuItem(""))     # separator

        # Recent tasks submenu (placeholder — real data in M2)
        recent = rumps.Menu("最近任务")
        recent.add("（暂无）")
        recent.enabled = False
        menu.add(recent)

        menu.add(rumps.MenuItem(""))
        menu.add("启动浏览器")          # → AC-23: verify localhost:8000
        menu.add("停止服务")            # stop uvicorn
        menu.add(rumps.MenuItem(""))
        menu.add("退出")                # → AC-3: icon stays after main window close

        return menu

    # ── rumps click handler ────────────────────────────────────────────────
    @rumps.clicked("打开主窗口")
    def open_main(self, _):
        """Open main window in a separate thread (non-blocking)."""
        thread = threading.Thread(target=open_main_window, daemon=True)
        thread.start()

    @rumps.clicked("启动浏览器")
    def open_browser(self, _):
        """Open localhost:8000 in default browser — verifies AC-23."""
        webbrowser.open(_SERVER_URL)

    @rumps.clicked("停止服务")
    def stop_server(self, _):
        stop_uvicorn()
        rumps.notification("summary4u", "服务已停止", "后台已关闭")

    @rumps.clicked("退出")
    def quit_app(self, _):
        stop_uvicorn()
        rumps.quit()

    # ── state API (called by other components) ─────────────────────────────
    def set_state(self, state: str):
        self._state = state
        self._controller.set_state(state)

    @property
    def state(self) -> str:
        return self._state


# ── entry point ──────────────────────────────────────────────────────────────

def main():
    app = Summary4uApp()
    app.run()


if __name__ == "__main__":
    main()