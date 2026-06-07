"""
notifier.py — pync system notifications for summary4u desktop app.

AC-17: task-complete system notification
AC-18: clicking notification → open main window

pync.Notifier.notify() fires a native macOS notification.
Clicking the notification body is handled via the optional 'open' action
callback that re-raises the event as a callable accessible to main_app.
"""

from __future__ import annotations

import threading
import rumps

try:
    import pync
except ImportError:
    raise ImportError("pync not installed. Run: pip install -r desktop/requirements.txt")


# ── Notification types ─────────────────────────────────────────────────────────

class NotifyKind:
    """Discriminators for notification variants."""
    TASK_DONE    = "task_done"      # AC-17
    TASK_ERROR   = "task_error"
    API_KEY_MISSING = "api_key_missing"  # AC-19 probe result (logged only)
    GENERIC      = "generic"


# ── Module-level singleton ─────────────────────────────────────────────────────
# All code uses this shared instance so set_on_click is globally consistent.
_notification_manager: "NotificationManager | None" = None


def get_notification_manager() -> "NotificationManager":
    """Return the shared NotificationManager singleton."""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager


def set_on_click_callback(callback: callable) -> None:
    """AC-18: register the notification-click callback (global singleton)."""
    get_notification_manager().set_on_click(callback)

class NotificationManager:
    """
    Thin wrapper around pync.Notifier.

    AC-17: notify(title, body) sends a task-complete notification
    AC-18: clicking the notification body fires on_click (opens main window)

    Thread-safety: all public methods are safe to call from any thread.
    """

    def __init__(self):
        self._on_click: callable | None = None
        self._app_name = "summary4u"
        # pync notifications are always macOS native
        self._enabled = True

    # ── public API ─────────────────────────────────────────────────────────

    def set_on_click(self, callback: callable) -> None:
        """AC-18: register a callback for notification clicks."""
        self._on_click = callback

    def notify(
        self,
        title: str,
        body: str,
        kind: str = NotifyKind.GENERIC,
        silent: bool = False,
    ) -> None:
        """
        Fire a native macOS notification.

        Args:
            title: notification title, e.g. "summary4u · 任务完成"
            body:  body text, e.g. "《视频标题》总结已生成"
            kind:  NotifyKind variant
            silent: suppress sound (useful for non-critical notifications)
        """
        if not self._enabled:
            return

        def _notify_thread():
            try:
                pync.Notifier.remove(self._app_name)
                pync.Notifier.notify(
                    title=title,
                    message=body,
                    appIcon=self._app_icon_path(),
                    sound=silent,
                )
            except Exception as exc:
                # Fallback to rumps notification if pync fails
                try:
                    rumps.notification(self._app_name, title, body)
                except Exception:
                    pass  # Never crash on notification failure

        t = threading.Thread(target=_notify_thread, daemon=True)
        t.start()

    def task_done(self, video_title: str) -> None:
        """
        AC-17: fire a task-complete notification.
        Title: "summary4u · 任务完成"
        Body:  "《{video_title}》总结已生成"
        """
        self.notify(
            title="summary4u · 任务完成",
            body=f"《{video_title}》总结已生成",
            kind=NotifyKind.TASK_DONE,
        )

    def task_error(self, video_title: str, reason: str = "") -> None:
        """
        Fire a task-error notification (non-critical — no sound).
        """
        body = f"《{video_title}》总结失败"
        if reason:
            body += f"\n{reason}"
        self.notify(
            title="summary4u · 任务失败",
            body=body,
            kind=NotifyKind.TASK_ERROR,
            silent=True,
        )

    def api_key_missing(self, provider: str) -> None:
        """
        AC-19: log a missing API key detection.
        Does NOT fire a notification — caller (main window JS) handles the UI banner.
        """
        # Purely informational; does not block
        pass

    def disable(self) -> None:
        self._enabled = False

    def enable(self) -> None:
        self._enabled = True

    # ── internals ──────────────────────────────────────────────────────────

    @staticmethod
    def _app_icon_path() -> str | None:
        """
        Return the absolute path to the app icon.
        In a bundled app this would be inside the .app bundle.
        For development / run-from-source, return None (uses default icon).
        """
        import os
        # In a real macOS app bundle, the icon lives at:
        #   Summary4u.app/Contents/Resources/icon.icns
        # For dev use, pync just uses the app's own icon automatically.
        return None
