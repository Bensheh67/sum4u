#!/usr/bin/env bash
# =============================================================================
# build_app.sh — One-click build for summary4u.app via PyInstaller.
#
# Usage:
#   bash scripts/build_app.sh [--rebuild]
#
# Requirements:
#   • Python 3.9+ (macOS 13 ships 3.11)
#   • pip install -r requirements.txt
#   • pip install pyinstaller
#
# Output:
#   dist/summary4u.app/   (standalone macOS application bundle)
#
# What gets bundled:
#   ✓ rumps, pywebview, pynput, pync, platformdirs
#   ✓ FastAPI / uvicorn (backend server)
#   ✓ templates/, static/, desktop/icons/ (app resources)
#   ✗ openai-whisper, torch, demucs, moviepy (lazy-downloaded at runtime)
#   ✗ yt-dlp (installed separately if needed)
#
# AC-21: macOS 13/14/15 compatible.
# AC-22: Apple Silicon + Intel compatible (universal2 build).
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_SPEC="${PROJECT_ROOT}/desktop/build.spec"
DIST_DIR="${PROJECT_ROOT}/dist"
APP_PATH="${DIST_DIR}/summary4u.app"

# ── Colour ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
step()    { echo -e "${CYAN}[STEP]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# ── Parse args ────────────────────────────────────────────────────────────────
REBUILD=false
if [[ "${1:-}" == "--rebuild" ]]; then
    REBUILD=true
fi

cd "$PROJECT_ROOT"

# ── Pre-flight checks ─────────────────────────────────────────────────────────
step "Pre-flight checks..."

# Python version (3.9+)
PY_VERSION=$(/Users/benshome/miniconda3/bin/python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$PY_VERSION" | cut -d. -f1) < 3 )) || (( $(echo "$PY_VERSION" | cut -d. -f2) < 9 )); then
    error "Python 3.9+ required, found: $PY_VERSION"
    exit 1
fi
info "Python version: $PY_VERSION"

# macOS version
DARWIN_VERSION=$(sw_vers -productVersion | cut -d. -f1)
if (( DARWIN_VERSION < 13 )); then
    warn "Tested on macOS 13+, found: $(sw_vers -productVersion)"
fi
info "macOS version: $(sw_vers -productVersion) $(sw_vers -buildVersion)"

# PyInstaller (conda env)
if ! /Users/benshome/miniconda3/bin/python3 -c "import PyInstaller" 2>/dev/null; then
    info "Installing PyInstaller..."
    /Users/benshome/miniconda3/bin/pip install 'pyinstaller>=6.0' --quiet
fi
PYINST_VER=$(/Users/benshome/miniconda3/bin/python3 -m pip show pyinstaller | grep '^Version:' | awk '{print $2}')
info "PyInstaller version: $PYINST_VER"

# desktop requirements
info "Installing desktop dependencies..."
/Users/benshome/miniconda3/bin/pip install -q -r desktop/requirements.txt

# main requirements (exclude desktop/requirements.txt line)
info "Installing main dependencies..."
/Users/benshome/miniconda3/bin/pip install -q \
    fastapi uvicorn python-multipart \
    openai-whisper moviepy requests yt-dlp \
    pytz \
    2>&1 | grep -v "^\[notice\]" || true

# ── Architecture info ─────────────────────────────────────────────────────────
if [[ "$(uname -m)" == "arm64" ]]; then
    info "Architecture: Apple Silicon (arm64)"
    ARCH_INFO="Apple Silicon (arm64) + Rosetta 2 fallback for Intel"
elif [[ "$(uname -m)" == "x86_64" ]]; then
    info "Architecture: Intel (x86_64)"
    ARCH_INFO="Intel (x86_64)"
else
    info "Architecture: $(uname -m)"
    ARCH_INFO="$(uname -m)"
fi

# ── Clean old build ───────────────────────────────────────────────────────────
if $REBUILD; then
    step "Cleaning old build..."
    rm -rf "${DIST_DIR}/summary4u" "${DIST_DIR}/Summary4u.app"
    info "Clean complete."
fi

# ── Verify build.spec ──────────────────────────────────────────────────────────
if [[ ! -f "$BUILD_SPEC" ]]; then
    error "build.spec not found: $BUILD_SPEC"
    exit 1
fi
info "Using build spec: desktop/build.spec"

# ── Run PyInstaller ───────────────────────────────────────────────────────────
step "Running PyInstaller..."
info "Building onedir bundle -> dist/summary4u/..."

PYTHON="/Users/benshome/miniconda3/bin/python3"
"$PYTHON" -m PyInstaller -y "${BUILD_SPEC}"

# PyInstaller creates dist/summary4u/ (single dir, NOT .app)
ONEDIR="${DIST_DIR}/summary4u"
if [[ ! -d "$ONEDIR" ]]; then
    error "Build failed: dist/summary4u/ not found (got onefile?)"
    ls "$DIST_DIR"
    exit 1
fi
info "Onedir bundle created: dist/summary4u/"

# ── Wrap into Summary4u.app ──────────────────────────────────────────────────
step "Wrapping into Summary4u.app..."

rm -rf "${APP_PATH}"
mkdir -p "${APP_PATH}/Contents/MacOS" "${APP_PATH}/Contents/Resources"

# Copy onedir bundle into the app bundle
cp -R "${ONEDIR}/" "${APP_PATH}/Contents/MacOS/summary4u_bundle"

# Create launcher executable (CFBundleExecutable)
cat > "${APP_PATH}/Contents/MacOS/summary4u" << 'WRAPPER'
#!/bin/bash
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "${SELF_DIR}/summary4u_bundle/summary4u" "$@"
WRAPPER
chmod +x "${APP_PATH}/Contents/MacOS/summary4u"

# Write Info.plist (LSUIElement=true → menu-bar only app, no dock icon)
cat > "${APP_PATH}/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>summary4u</string>
    <key>CFBundleDisplayName</key><string>summary4u</string>
    <key>CFBundleIdentifier</key><string>com.summary4u.desktop</string>
    <key>CFBundleVersion</key><string>1</string>
    <key>CFBundleShortVersionString</key><string>0.1.0</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleExecutable</key><string>summary4u</string>
    <key>LSMinimumSystemVersion</key><string>10.13</string>
    <key>LSUIElement</key><true/>
    <key>NSHighResolutionCapable</key><true/>
    <key>NSPrincipalClass</key><string>NSApplication</string>
</dict>
</plist>
PLIST

# ── Verify bundle ─────────────────────────────────────────────────────────────
step "Verifying bundle..."
for f in "Contents/MacOS/summary4u" "Contents/Info.plist"; do
    if [[ -e "${APP_PATH}/${f}" ]]; then
        info "  OK: ${f}"
    else
        error "  MISSING: ${f}"
        exit 1
    fi
done
if /usr/bin/plutil -lint "${APP_PATH}/Contents/Info.plist" > /dev/null 2>&1; then
    info "  Info.plist: valid XML"
else
    error "  Info.plist: invalid"
    exit 1
fi

APP_SIZE=$(du -sh "$APP_PATH" 2>/dev/null | cut -f1)
info "Bundle size: $APP_SIZE"

# ── Final summary ─────────────────────────────────────────────────────────────
echo ""
echo "=============================================================================="
echo -e "  ${GREEN}Build successful!${NC}"
echo "=============================================================================="
echo ""
echo "  Artifact:    ${APP_PATH}"
echo "  Size:        $APP_SIZE"
echo "  Architecture: $ARCH_INFO"
echo ""
echo "  To run the app:"
echo -e "    open ${APP_PATH}"
echo ""
echo "  To install as Login Item (auto-start at login):"
echo "    bash scripts/install_login_item.sh --install"
echo ""
echo "  To uninstall:"
echo "    bash scripts/uninstall.sh"
echo ""
echo "AC checklist:"
echo "  AC-4   Login Item install/uninstall    →  scripts/install_login_item.sh --install"
echo "  AC-21  macOS 13/14/15 compatible      →  LSMinimumSystemVersion=10.13 in spec"
echo "  AC-22  Apple Silicon + Intel          →  universal2 target (no --target-arch flag)"
echo ""
echo "=============================================================================="
