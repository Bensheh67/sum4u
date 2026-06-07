# -*- mode: python ; coding: utf-8 -*-
# =============================================================================
# build.spec — PyInstaller spec for summary4u.app
#
# Usage:  pyinstaller desktop/build.spec
# Output: dist/summary4u/   (standalone onedir bundle; build_app.sh wraps it
#          into summary4u.app after build)
#
# PyInstaller >= 6 required.  Tested with 6.20.0.
#
# AC-21: macOS 13/14/15 compatible.
# AC-22: Apple Silicon + Intel compatible.
# =============================================================================

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

_ROOT    = Path("/Users/benshome/Desktop/summary4u")
_DESKTOP = _ROOT / "desktop"

# ── Data files ────────────────────────────────────────────────────────────────
def _data_files():
    collected = []
    for src_dir, dst_prefix in [
        (_ROOT / "templates", "Resources"),
        (_ROOT / "static",   "Resources/static"),
    ]:
        if src_dir.exists():
            for f in src_dir.rglob("*"):
                if f.is_file():
                    collected.append((str(f), dst_prefix))
    icons = _DESKTOP / "icons"
    if icons.exists():
        for f in icons.rglob("*"):
            if f.is_file():
                collected.append((str(f), "Resources/icons"))
    return collected

# ── Hidden imports ────────────────────────────────────────────────────────────
_hidden = [
    "rumps", "pync", "pync.Notifier", "pync.TerminalNotifier", "pync.listeners",
    "pywebview", "pywebview.window", "pywebview.js",
    "pynput", "pynput.keyboard", "pynput.keyboard._darwin",
    "platformdirs",
    "uvicorn", "uvicorn.loops", "uvicorn.loops.auto",
    "uvicorn.protocols", "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto", "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto", "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "fastapi", "starlette", "starlette.routing",
    "starlette.middleware", "starlette.middleware.cors",
    "python_multipart",
    "desktop.preferences_window",
    "pynput._util.darwin",
    # pync vendor (terminal-notifier binary bundled in pync package)
    "pync.vendor",
    "dateutil",
    "dateutil.parser",
]

# ── Build (onedir → dist/summary4u/) ──────────────────────────────────────────
a = Analysis(
    [str(_DESKTOP / "main_app.py")],
    pathex=[],
    binaries=[],
    datas=_data_files() + collect_data_files('pync'),
    hiddenimports=_hidden,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="summary4u",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="summary4u",
)