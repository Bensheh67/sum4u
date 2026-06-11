#!/usr/bin/env python3
"""
summary4u Desktop App — M3 implementation.

Architecture:
  rumps      → menu bar icon + popover menu
  pywebview  → main window (HTML/WebUI)
  uvicorn    → subprocess that serves FastAPI on port 8000

Acceptance criteria (M3):
  AC-8   菜单栏点击 → 弹出 popover (480×280px，毛玻璃背景)
  AC-9   popover 输入 URL + Enter → 关闭 popover + 提交任务
  AC-10  popover 支持模板选择 (default/structured/bullet/course/short_video)
  AC-12  popover 支持 Cmd+Enter 快捷提交
  AC-15  主窗口历史列表显示最近 5 条 (超出显示「查看全部」)
  AC-16  历史列表点击 → 在 Finder 中定位文件
  ── Also carries forward M1/M2 AC-1,2,3,23
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
_ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DESKTOP   = os.path.dirname(os.path.abspath(__file__))
_TEMPLATES = os.path.join(_ROOT, "templates")
_STATIC    = os.path.join(_ROOT, "static")
_SERVER_PORT = 8000
_SERVER_URL  = f"http://localhost:{_SERVER_PORT}"

# New M3 templates
_DESKTOP_MAIN    = os.path.join(_TEMPLATES, "desktop_main.html")
_DESKTOP_POPOVER = os.path.join(_TEMPLATES, "desktop_popover.html")


# ── icon generation (menu_bar.py) ────────────────────────────────────────────
def _ensure_icons():
    sys.path.insert(0, _DESKTOP)
    from menu_bar import ensure_icons
    ensure_icons()


# ── M2 modules: hotkey, notification, preferences, dock-drop ────────────────
_hotkey_manager = None


def _setup_m2():
    """Initialize M2 components. Called once at startup."""
    global _hotkey_manager

    # Preferences (singleton, loads prefs.json on first access)
    from desktop import preferences as prefs_mod
    prefs_mod.Preferences()  # force init

    # HotkeyManager singleton
    from desktop import hotkey as hotkey_mod
    _hotkey_manager = hotkey_mod.HotkeyManager()
    _hotkey_manager.start_daemon()

    # Register hotkey reload callback so preferences_window can update it live
    from desktop import preferences_window as pw_mod
    pw_mod.on_hotkey_reload(lambda combo: _hotkey_manager.update_combo(combo))

    # Notifier: clicking notification opens main window
    from desktop import notifier as notifier_mod
    notifier_mod.set_on_click_callback(_show_main_window_from_notify)


def _show_main_window_from_notify():
    """Callback: called when user clicks a system notification."""
    if not is_main_window_open():
        thread = threading.Thread(target=open_main_window, daemon=True)
        thread.start()
    elif _main_window is not None:
        _main_window.show()


# ── uvicorn subprocess management ────────────────────────────────────────────

_uvicorn_proc: subprocess.Popen | None = None


def start_uvicorn():
    """Start FastAPI via uvicorn in a background subprocess (port 8000)."""
    global _uvicorn_proc
    if _uvicorn_proc is not None and _uvicorn_proc.poll() is None:
        return  # already running

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
_popover_window: webview.Window | None = None


class DesktopAPI:
    """JavaScript API exposed to the desktop_main.html renderer."""

    @staticmethod
    def open_in_finder(path: str):
        """Open Finder and select the file at `path` (AC-16)."""
        if path and os.path.exists(path):
            subprocess.Popen(["open", "-R", path])

    @staticmethod
    def open_summaries_folder():
        """Open the summaries directory in Finder."""
        summaries_dir = os.path.join(_ROOT, "summaries")
        os.makedirs(summaries_dir, exist_ok=True)
        subprocess.Popen(["open", summaries_dir])

    @staticmethod
    def open_preferences():
        """Open the preferences/settings window."""
        from desktop import preferences_window as pw_mod
        # Preferences window is shown via rumps menu item already;
        # this is a JS-accessible fallback.
        pass

    @staticmethod
    def get_static_url(path: str) -> str:
        """Return absolute URL for a static asset."""
        return f"{_SERVER_URL}/static/{path}"


def open_main_window():
    """Show the main window. Called when user clicks '打开主窗口' in menu."""
    global _main_window

    # Use the new desktop_main.html template
    main_html = _DESKTOP_MAIN if os.path.exists(_DESKTOP_MAIN) else os.path.join(_DESKTOP, "preview.html")

    # If already open, bring to front
    if _main_window is not None:
        _main_window.show()
        return

    # Create main window
    window = webview.create_window(
        "summary4u",
        f"file://{main_html}",
        width=1024,
        height=720,
        min_size=(800, 600),
        resizable=True,
        js_api=DesktopAPI(),
    )
    _main_window = window

    start_uvicorn()
    webview.start()
    # When we reach here, the window was closed by the user
    _main_window = None


def is_main_window_open() -> bool:
    return _main_window is not None


def open_popover():
    """Show the quick-input popover window (AC-8).

    Uses a frameless pywebview window positioned near the menu bar.
    Closing the popover returns control immediately.
    """
    global _popover_window

    if not os.path.exists(_DESKTOP_POPOVER):
        return  # graceful degradation: popover not ready

    # Position: center horizontally, 80px from top of screen
    try:
        from AppKit import NSScreen, NSApplication
        screen = NSScreen.mainScreen().frame
        scr_w = screen.size.width
        scr_h = screen.size.height
        popover_w, popover_h = 480, 280
        x = (scr_w - popover_w) / 2
        y = scr_h - 80 - popover_h
    except Exception:
        x, y, popover_w, popover_h = 100, 100, 480, 280

    window = webview.create_window(
        "",
        f"file://{_DESKTOP_POPOVER}",
        width=popover_w,
        height=popover_h,
        x=int(x),
        y=int(y),
        frameless=True,
        resizable=False,
        debug=False,
        js_api=DesktopAPI(),
    )
    _popover_window = window

    # Run popover in a separate non-blocking thread
    thread = threading.Thread(target=lambda: webview.start(debug=False), daemon=True)
    thread.start()


def close_popover():
    """Close the popover window (called from desktop_popover.js via popoverAPI)."""
    global _popover_window
    if _popover_window is not None:
        try:
            _popover_window.destroy()
        except Exception:
            pass
        _popover_window = None


class PopoverAPI:
    """API exposed to desktop_popover.html JavaScript."""

    @staticmethod
    def close():
        """JS calls this to signal the popover should close."""
        close_popover()

    @staticmethod
    def read_clipboard() -> str:
        """Return current clipboard text for auto-paste on focus (AC-12)."""
        try:
            import subprocess
            result = subprocess.run(
                ["osascript", "-e", "get the clipboard"],
                capture_output=True, text=True, timeout=2
            )
            return result.stdout.strip()
        except Exception:
            return ""


# ── App class ────────────────────────────────────────────────────────────────

class Summary4uApp(rumps.App):
    """rumps wrapper — menu bar app with popover and stateful icon."""

    def __init__(self):
        super().__init__("summary4u")

        self._state = "idle"

        _ensure_icons()
        from menu_bar import MenuBarController
        self._controller = MenuBarController(self)

        self._build_menu()

        start_uvicorn()
        _setup_m2()

        self._controller.set_state("idle")
        signal.signal(signal.SIGINT, signal.SIG_DFL)

    def _build_menu(self):
        """Build the popover menu shown when clicking the menu bar icon.
        
        rumps 0.4.0: menu is a list, submenus are MenuItem with .add() children,
        and separators are rumps.separator().
        """
        # Recent tasks submenu (placeholder — populated dynamically in M3)
        recent = rumps.MenuItem("最近任务")
        recent.add(rumps.MenuItem("（暂无）"))
        for _k, _mi in recent.items():
            if _mi.title == "（暂无）":
                _mi.state = 0
                break

        self.menu = [
            rumps.MenuItem("打开主窗口"),     # → AC-2
            rumps.separator,
            rumps.MenuItem("快速输入"),       # → AC-8
            rumps.separator,
            recent,
            rumps.separator,
            rumps.MenuItem("启动浏览器"),     # → AC-23
            rumps.MenuItem("停止服务"),
            rumps.separator,
            rumps.MenuItem("偏好设置..."),    # → opens preferences
            rumps.separator,
            rumps.MenuItem("退出"),
        ]

    # ── rumps click handlers ────────────────────────────────────────────────

    @rumps.clicked("打开主窗口")
    def open_main(self, _):
        thread = threading.Thread(target=open_main_window, daemon=True)
        thread.start()

    @rumps.clicked("快速输入")
    def open_popover(self, _):
        """AC-8: Show the quick-input popover window."""
        open_popover()

    @rumps.clicked("启动浏览器")
    def open_browser(self, _):
        webbrowser.open(_SERVER_URL)

    @rumps.clicked("停止服务")
    def stop_server(self, _):
        stop_uvicorn()
        rumps.notification("summary4u", "服务已停止", "后台已关闭")

    @rumps.clicked("偏好设置...")
    def open_preferences(self, _):
        from desktop import preferences_window as pw_mod
        pw_mod.open_preferences()

    @rumps.clicked("退出")
    def quit_app(self, _):
        stop_uvicorn()
        rumps.quit()

    # ── state API ────────────────────────────────────────────────────────────

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