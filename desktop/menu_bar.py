"""
Menu bar icon controller — 4-state SVG-based icon swap.
States: idle / running / done / error
"""
import os
import rumps

# Absolute path to this file's directory (desktop/)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_ICON_DIR = os.path.join(_BASE_DIR, "icons")


def _svg_path(name: str) -> str:
    return os.path.join(_ICON_DIR, f"{name}.svg")


# ── SVG templates ────────────────────────────────────────────────────────────

_SVG_IDLE = """<svg xmlns="http://www.w3.org/2000/svg" width="44" height="22" viewBox="0 0 22 22">
  <rect width="22" height="22" rx="4" fill="none"/>
  <circle cx="11" cy="11" r="6" stroke="{color}" stroke-width="2" fill="none"/>
  <circle cx="11" cy="11" r="2" fill="{color}"/>
</svg>"""

_SVG_RUNNING = """<svg xmlns="http://www.w3.org/2000/svg" width="44" height="22" viewBox="0 0 22 22">
  <rect width="22" height="22" rx="4" fill="none"/>
  <circle cx="11" cy="11" r="6" stroke="{color}" stroke-width="2" fill="none"/>
  <circle cx="11" cy="11" r="3" fill="{color}">
    <animate attributeName="opacity" values="0.3;1;0.3" dur="1.5s" repeatCount="indefinite"/>
  </circle>
</svg>"""

_SVG_DONE = """<svg xmlns="http://www.w3.org/2000/svg" width="44" height="22" viewBox="0 0 22 22">
  <rect width="22" height="22" rx="4" fill="none"/>
  <circle cx="11" cy="11" r="6" stroke="{color}" stroke-width="2" fill="none"/>
  <circle cx="11" cy="11" r="3" fill="{color}"/>
</svg>"""

_SVG_ERROR = """<svg xmlns="http://www.w3.org/2000/svg" width="44" height="22" viewBox="0 0 22 22">
  <rect width="22" height="22" rx="4" fill="none"/>
  <circle cx="11" cy="11" r="6" stroke="{color}" stroke-width="2" fill="none"/>
  <text x="11" y="15" text-anchor="middle" font-size="10" font-weight="bold" fill="{color}">!</text>
</svg>"""

_TEMPLATES = {
    "idle":    (_SVG_IDLE,    "#8E8E93"),   # macOS secondary label color
    "running": (_SVG_RUNNING, "#0D9488"),   # teal
    "done":    (_SVG_DONE,    "#10B981"),   # green
    "error":   (_SVG_ERROR,   "#EF4444"),   # red
}


def _render_svg(template: str, color: str) -> str:
    return template.format(color=color)


def _write_icon(name: str, svg: str) -> str:
    path = os.path.join(_ICON_DIR, f"{name}.svg")
    os.makedirs(_ICON_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path


# ── Icon generation ──────────────────────────────────────────────────────────

def ensure_icons():
    """Generate all 4 SVG icon files. Safe to call on every startup."""
    for state, (template, color) in _TEMPLATES.items():
        svg = _render_svg(template, color)
        _write_icon(state, svg)


def get_icon_path(state: str) -> str:
    """Return absolute path to the SVG for given state."""
    return _svg_path(state)


# ── Controller class ─────────────────────────────────────────────────────────

class MenuBarController:
    """
    Manages the rumps.StatusItem icon and 4-state transitions.

    States: idle | running | done | error
    Transitions:
      idle → running  (task starts)
      running → done  (all tasks complete)
      running → error (task fails)
      done → idle     (5s timer, auto-reset)
      error → idle    (user clicks, or 30s timer)
    """

    def __init__(self, app: rumps.App):
        self._app = app
        self._state = "idle"
        self._done_timer: rumps.Timer | None = None
        self._error_timer: rumps.Timer | None = None

    def set_state(self, state: str):
        """Update icon to state (idle/running/done/error)."""
        if state not in _TEMPLATES:
            raise ValueError(f"Unknown state: {state}")

        self._state = state
        template, color_hex = _TEMPLATES[state]
        svg = _render_svg(template, color_hex)

        # Write temp .svg → macOS reads it as a template image via NSImage
        tmp = os.path.join(_ICON_DIR, f"current.svg")
        os.makedirs(_ICON_DIR, exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(svg)

        # rumps wants a file path string; we use the temp path
        self._app.icon = tmp

        # Cancel any pending auto-reset timers
        self._cancel_timers()

        # Auto-reset for done / error states
        if state == "done":
            self._done_timer = rumps.Timer(self._reset_to_idle, 5)
            self._done_timer.start()
        elif state == "error":
            self._error_timer = rumps.Timer(self._reset_to_idle, 30)
            self._error_timer.start()

    def _reset_to_idle(self, _):
        self.set_state("idle")

    def _cancel_timers(self):
        for t in (self._done_timer, self._error_timer):
            if t is not None:
                t.stop()
        self._done_timer = None
        self._error_timer = None

    @property
    def current_state(self) -> str:
        return self._state

    # Convenience shortcuts
    def task_started(self):
        self.set_state("running")

    def all_tasks_done(self):
        self.set_state("done")

    def task_failed(self):
        self.set_state("error")

    def user_acknowledge(self):
        """User clicked the menu bar icon — clear error immediately."""
        self._cancel_timers()
        self.set_state("idle")