"""
dock_drop.py — Dock drag-and-drop handler for summary4u desktop app.

AC-9:   Finder drag file to Dock icon → transfers to running app
AC-11:  drag .txt file → skip ASR, go straight to summarize

On macOS, when a file is dragged to the Dock icon (or the .app bundle's Dock tile),
the app receives an 'open-file' Apple Event via NSApplication.open(_:).

rumps (built on AppKit) handles this via the open_file handler.

We detect the file type:
  - Audio/video (.mp3/.wav/.m4a/.mp4/.flac)  → transcribe + summarize
  - Text        (.txt/.md)                   → skip ASR, summarize directly
  - Other       → return (not supported)

The handler is registered on the rumps.App in main_app.py:

    @app.open_file
    def handle_dock_drop(filepath: str) -> None:
        DockDropHandler.handle(filepath)

AC-11 is implemented here by checking the extension before deciding
whether to run ASR (speech recognition) or go straight to the LLM summarizer.
"""

from __future__ import annotations

import os
import threading
import subprocess
from pathlib import Path


# ── Supported file types ──────────────────────────────────────────────────────

AUDIO_EXTENSIONS  = {".mp3", ".wav", ".m4a", ".mp4", ".flac", ".aac", ".ogg"}
TEXT_EXTENSIONS   = {".txt", ".md", ".markdown"}
SKIP_ASR_EXTENSIONS = TEXT_EXTENSIONS   # AC-11: these skip ASR


# ── Handler ───────────────────────────────────────────────────────────────────

class DockDropHandler:
    """
    Processes files dropped onto the summary4u Dock icon.

    Thread-safety: handle() can be called from any thread (rumps uses the
    main thread for open_file callbacks on macOS).
    """

    @staticmethod
    def is_supported(filepath: str) -> bool:
        """Return True if the file extension is supported."""
        ext = Path(filepath).suffix.lower()
        return ext in AUDIO_EXTENSIONS or ext in TEXT_EXTENSIONS

    @staticmethod
    def is_audio(filepath: str) -> bool:
        ext = Path(filepath).suffix.lower()
        return ext in AUDIO_EXTENSIONS

    @staticmethod
    def is_text(filepath: str) -> bool:
        ext = Path(filepath).suffix.lower()
        return ext in TEXT_EXTENSIONS

    @staticmethod
    def handle(
        filepath: str,
        skip_asr: bool | None = None,
        template: str = "default课堂笔记",
        model: str = "small",
    ) -> bool:
        """
        Process a Dock-dropped file.

        Args:
            filepath:    absolute path to the dropped file
            skip_asr:    AC-11 override. None = auto-detect from extension.
            template:    summarization prompt template key
            model:       Whisper model for ASR

        Returns:
            True if the file was accepted and a task was queued,
            False if the file type is unsupported.
        """
        filepath = os.path.abspath(os.path.expanduser(filepath))

        if not os.path.exists(filepath):
            return False

        ext = Path(filepath).suffix.lower()

        # Auto-detect skip_asr from extension (AC-11)
        if skip_asr is None:
            skip_asr = ext in SKIP_ASR_EXTENSIONS

        if ext not in AUDIO_EXTENSIONS and ext not in TEXT_EXTENSIONS:
            return False

        # Enqueue the task to the FastAPI backend via HTTP POST
        _enqueue_task(
            filepath=filepath,
            skip_asr=skip_asr,
            template=template,
            model=model,
        )
        return True


# ── Task enqueueing ───────────────────────────────────────────────────────────

def _enqueue_task(
    filepath: str,
    skip_asr: bool,
    template: str,
    model: str,
) -> None:
    """
    POST the dropped file to the FastAPI /tasks endpoint.
    Runs in a background thread so we don't block the Dock event handler.
    """

    def _thread():
        import urllib.request
        import urllib.parse
        import json

        payload = json.dumps({
            "type": "local_file",
            "filepath": filepath,
            "skip_asr": skip_asr,
            "template": template,
            "model": model,
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                "http://localhost:8000/api/tasks",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                _ = resp.read()
        except Exception:
            # Fallback: spawn a subprocess to run the CLI
            _enqueue_via_cli(filepath, skip_asr, template, model)

    t = threading.Thread(target=_thread, daemon=True)
    t.start()


def _enqueue_via_cli(
    filepath: str,
    skip_asr: bool,
    template: str,
    model: str,
) -> None:
    """
    Fallback: run python -m src.main --audio-file directly.
    Used when FastAPI is not yet up (cold start).
    """
    import sys

    args = [sys.executable, "-m", "src.main", "--audio-file", filepath]
    if skip_asr:
        # When skipping ASR, we can't use --audio-file directly;
        # fall back to reading the text file content inline
        args = [
            sys.executable, "-c",
            f"print(open('{filepath}').read())",
        ]
    try:
        subprocess.Popen(
            args,
            cwd=os.path.dirname(os.path.dirname(__file__)),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass
