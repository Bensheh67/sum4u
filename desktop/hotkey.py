"""
hotkey.py — pynput global hotkey listener.

Monitors Cmd+Shift+S (default) system-wide and fires a callback.
The callback is registered by main_app at startup.

Usage:
    from desktop.hotkey import HotkeyManager
    hkm = HotkeyManager()
    hkm.register(lambda: print("triggered!"))
    hkm.start_daemon()   # non-blocking background listener

AC-5:  Chrome foreground + ⌘⇧S → trigger
AC-7:  preferences change hotkey → new combo takes effect immediately
"""

from __future__ import annotations

import threading
import atexit
from typing import Callable

try:
    from pynput import keyboard
except ImportError:
    raise ImportError("pynput not installed. Run: pip install -r desktop/requirements.txt")


# ── Key combo helpers ─────────────────────────────────────────────────────────

def parse_combo(desc: str) -> frozenset:
    """
    Parse a human-readable combo string like 'cmd+shift+s' into a pynput key set.
    Used for AC-7: prefs can store 'cmd+shift+s' and we re-parse at runtime.
    """
    KEYS = {
        "cmd": keyboard.Key.cmd,
        "shift": keyboard.Key.shift,
        "alt": keyboard.Key.alt,
        "ctrl": keyboard.Key.ctrl,
    }
    parts = desc.lower().replace(" ", "").split("+")
    keys: set = set()
    for p in parts:
        if p in KEYS:
            keys.add(KEYS[p])
        elif len(p) == 1:
            keys.add(keyboard.KeyCode.from_char(p))
    return frozenset(keys)


def combo_to_str(combo: frozenset) -> str:
    """Human-readable string for a combo frozenset."""
    labels = []
    for k in combo:
        if k == keyboard.Key.cmd:
            labels.append("cmd")
        elif k == keyboard.Key.shift:
            labels.append("shift")
        elif k == keyboard.Key.alt:
            labels.append("alt")
        elif k == keyboard.Key.ctrl:
            labels.append("ctrl")
        elif isinstance(k, keyboard.KeyCode):
            labels.append(k.char.lower())
    return "+".join(labels)


# ── Default ───────────────────────────────────────────────────────────────────

DEFAULT_COMBO = parse_combo("cmd+shift+s")


# ── Hotkey state tracker ──────────────────────────────────────────────────────

class _KeyState:
    """Tracks currently pressed keys across all keyboards."""
    _pressed: set = set()
    _lock = threading.Lock()

    @classmethod
    def press(cls, key):
        with cls._lock:
            cls._pressed.add(key)

    @classmethod
    def release(cls, key):
        with cls._lock:
            cls._pressed.discard(key)

    @classmethod
    def current(cls) -> frozenset:
        with cls._lock:
            return frozenset(cls._pressed)

    @classmethod
    def matches(cls, combo: frozenset) -> bool:
        """Return True if all keys in combo are currently pressed."""
        return combo.issubset(cls._pressed)

    @classmethod
    def clear(cls):
        with cls._lock:
            cls._pressed.clear()


# ── Manager ───────────────────────────────────────────────────────────────────

class HotkeyManager:
    """
    Global hotkey watcher.

    Start non-blocking with .start_daemon(), then register a callback
    with .register(fn).  The callback is fired on the listener thread.

    AC-7: call .update_combo(new_combo) to switch hotkey at runtime —
    the listener restarts automatically with the new combo.
    """

    def __init__(
        self,
        combo: frozenset = DEFAULT_COMBO,
        on_trigger: Callable[[], None] | None = None,
    ):
        self._combo = combo
        self._on_trigger = on_trigger
        self._listener: keyboard.Listener | None = None
        self._listener_lock = threading.Lock()
        self._started = False

    # ── public API ───────────────────────────────────────────────────────────

    def register(self, callback: Callable[[], None]) -> None:
        """Set the callback invoked when the hotkey is pressed."""
        self._on_trigger = callback

    def update_combo(self, combo: frozenset) -> None:
        """Replace the watched combo (AC-7: takes effect immediately)."""
        self._combo = combo
        self._started = False   # prevent _run from re-using a stale listener
        self._restart()

    def start_daemon(self) -> None:
        """Start the listener in a background thread (non-blocking)."""
        if self._started:
            return
        with self._listener_lock:
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release,
                suppress=False,
            )
            self._listener.start()
            self._started = True

    def stop(self) -> None:
        """Stop the listener."""
        with self._listener_lock:
            if self._listener is not None:
                self._listener.stop()
                self._listener = None
        self._started = False

    # ── internals ───────────────────────────────────────────────────────────

    def _run(self) -> None:
        # Listener is started by start_daemon(); _run() is called by the
        # listener's own internal thread and blocks until stopped.
        with self._listener_lock:
            if self._listener is not None:
                self._listener.join()

    def _restart(self) -> None:
        self.stop()          # stop + clear before re-creating
        _KeyState.clear()
        self.start_daemon()

    def _on_press(self, key) -> None:
        _KeyState.press(key)
        if _KeyState.matches(self._combo):
            cb = self._on_trigger
            if cb is not None:
                cb()

    def _on_release(self, key) -> None:
        _KeyState.release(key)
