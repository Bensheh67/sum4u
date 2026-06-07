#!/usr/bin/env bash
# Verification script for M1: Desktop App skeleton
# Run from project root: bash scripts/run_desktop.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "=== M1 Verification: Desktop App Skeleton ==="
echo ""

# Check desktop/ directory exists
echo "[1/6] desktop/ directory..."
ls desktop/ || { echo "FAIL: desktop/ not found"; exit 1; }
echo "    OK"

# Check required files
echo "[2/6] Required files..."
for f in desktop/main_app.py desktop/menu_bar.py desktop/requirements.txt desktop/preview.html; do
  if [ ! -f "$f" ]; then
    echo "    MISSING: $f"
    exit 1
  fi
  echo "    ✓ $f"
done

# Check Python syntax
echo "[3/6] Python syntax..."
python3 -m py_compile desktop/menu_bar.py && echo "    ✓ menu_bar.py OK"
python3 -m py_compile desktop/main_app.py && echo "    ✓ main_app.py OK"

# Install desktop dependencies
echo "[4/6] Installing desktop dependencies..."
pip install -q -r desktop/requirements.txt 2>&1 | tail -3

# Check imports work (without actually running the App)
echo "[5/6] Import check..."
python3 -c "
import sys, os
sys.path.insert(0, 'desktop')
from menu_bar import ensure_icons, MenuBarController, _TEMPLATES
print('    ✓ menu_bar imports OK')
assert set(_TEMPLATES.keys()) == {'idle','running','done','error'}, 'missing states'
print('    ✓ all 4 states defined')
"

# Generate icons
echo "[6/6] Icon generation..."
python3 -c "
import sys, os
sys.path.insert(0,'desktop')
from menu_bar import ensure_icons, get_icon_path
ensure_icons()
for s in ['idle','running','done','error']:
    p = get_icon_path(s)
    assert os.path.exists(p), f'missing: {p}'
    print(f'    ✓ {s}.svg')
"

echo ""
echo "=== All M1 checks passed ==="
echo ""
echo "To run the app:"
echo "  python3 desktop/main_app.py"
echo ""
echo "AC checklist:"
echo "  AC-1  (double-click entry → icon in 1s)    → run and observe menu bar"
echo "  AC-2  (main window no auto-popup)          → verify no window on launch"
echo "  AC-3  (icon persists after main window close) → close window, check icon"
echo "  AC-23 (localhost:8000 reachable)           → click '启动浏览器' menu item"