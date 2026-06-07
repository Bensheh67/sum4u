"""
preferences.py — read/write user preferences for summary4u desktop app.

Persists to:
  ~/Library/Application Support/summary4u/prefs.json

AC-7:  hotkey change → HotkeyManager.update_combo() called
AC-20: Whisper model change → saved here, readable by FastAPI backend

The Preferences singleton is shared between:
  - main_app (hotkey registration, app-level settings)
  - preferences_window (UI reads/writes)
  - FastAPI backend (whisper model at task dispatch time)
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Optional

try:
    import platformdirs
except ImportError:
    import sys
    sys.exit("platformdirs not installed. Run: pip install -r desktop/requirements.txt")


# ── App data directory ─────────────────────────────────────────────────────────

APP_NAME     = "summary4u"
APP_AUTHOR   = "summary4u"


def _app_dir() -> Path:
    return Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR))


# ── Default preferences ────────────────────────────────────────────────────────

DEFAULTS: dict[str, Any] = {
    # Hotkey (human-readable string, parsed by hotkey.parse_combo)
    "hotkey": "cmd+shift+s",

    # Appearance
    "theme": "system",   # "system" | "light" | "dark"

    # Model & performance
    "default_whisper_model":  "small",
    "default_template":      "default课堂笔记",
    "max_concurrent_tasks":  3,

    # Output
    "output_folder":         "summaries",
    "save_transcriptions":    True,

    # Notifications
    "notify_on_done":         True,
    "notify_on_error":        False,
}


# ── Singleton ──────────────────────────────────────────────────────────────────

class Preferences:
    """
    Thread-safe singleton.  Reads and writes ~/Library/Application Support/summary4u/prefs.json.

    AC-7:  callers call .set("hotkey", "cmd+shift+opt+s")
           then HotkeyManager.update_combo() with the parsed combo.

    AC-20: callers call .set("default_whisper_model", "medium")
           → saved to disk → FastAPI reads at task dispatch time.
    """

    _instance: Optional["Preferences"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "Preferences":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self) -> None:
        self._path = _app_dir() / "prefs.json"
        self._data: dict[str, Any] = {}
        self._data_lock = threading.RLock()
        self._load()

    # ── I/O ────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        with self._data_lock:
            if self._path.exists():
                try:
                    with open(self._path, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                    # Deep-merge with defaults so new keys are always present
                    self._data = self._deep_merge(dict(DEFAULTS), raw)
                except Exception:
                    self._data = dict(DEFAULTS)
            else:
                self._data = dict(DEFAULTS)
                self._save_unchecked()

    def _save_unchecked(self) -> None:
        """Save without acquiring the lock (caller must hold it)."""
        try:
            os.makedirs(self._path.parent, exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass  # Never fail on preferences write

    def _save(self) -> None:
        with self._data_lock:
            self._save_unchecked()

    @staticmethod
    def _deep_merge(base: dict, overrides: dict) -> dict:
        result = base.copy()
        for k, v in overrides.items():
            if isinstance(v, dict) and k in result and isinstance(result[k], dict):
                result[k] = Preferences._deep_merge(result[k], v)
            else:
                result[k] = v
        return result

    # ── public API ────────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        """Read a preference value."""
        with self._data_lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Write a preference value and persist to disk."""
        with self._data_lock:
            self._data[key] = value
            self._save_unchecked()

    def get_all(self) -> dict[str, Any]:
        """Return a copy of all preferences (read-only-ish)."""
        with self._data_lock:
            return dict(self._data)

    def reset(self) -> None:
        """Reset all preferences to defaults."""
        with self._data_lock:
            self._data = dict(DEFAULTS)
            self._save_unchecked()


# ── Convenience accessors ─────────────────────────────────────────────────────

def get_preferences() -> Preferences:
    return Preferences()


def get_hotkey_combo() -> str:
    """Return the stored hotkey string, e.g. 'cmd+shift+s'."""
    return Preferences().get("hotkey", DEFAULTS["hotkey"])


def set_hotkey_combo(combo_str: str) -> None:
    Preferences().set("hotkey", combo_str)


def get_default_whisper_model() -> str:
    """AC-20: return stored Whisper model."""
    return Preferences().get("default_whisper_model", DEFAULTS["default_whisper_model"])
