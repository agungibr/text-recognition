#!/usr/bin/env bash
# =============================================================================
#  build.sh  —  Linux / macOS PyInstaller build script
#  YOLO · OCR  Detection Suite
#
#  Usage:
#      chmod +x build.sh
#      ./build.sh              # release build (no console window)
#      ./build.sh --console    # keep terminal window (useful for debugging)
#
#  Output:
#      dist/YoloOCR/           (--onedir bundle)
#      dist/YoloOCR/YoloOCR    (executable)
#
#  Requirements:
#      pip install pyinstaller
#      All runtime deps in requirements.txt must be installed.
# =============================================================================

set -euo pipefail

# ── resolve script directory so the script works from any CWD ────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── colours for pretty output ─────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
RESET='\033[0m'

log()  { echo -e "${CYAN}${BOLD}[build]${RESET}  $*"; }
ok()   { echo -e "${GREEN}${BOLD}[  ok ]${RESET}  $*"; }
warn() { echo -e "${YELLOW}${BOLD}[ warn]${RESET}  $*"; }
die()  { echo -e "${RED}${BOLD}[error]${RESET}  $*" >&2; exit 1; }

# ── parse arguments ───────────────────────────────────────────────────────────
CONSOLE_FLAG="--noconsole"
for arg in "$@"; do
    case "$arg" in
        --console) CONSOLE_FLAG=""; warn "Console window ENABLED (debug mode)" ;;
        --help|-h)
            echo "Usage: $0 [--console]"
            echo "  --console   Keep terminal window (debug mode)"
            exit 0
            ;;
        *) die "Unknown argument: $arg" ;;
    esac
done

APP_NAME="YoloOCR"
ENTRY="main.py"
DIST_DIR="dist"
BUILD_DIR="build"
SPEC_FILE="${APP_NAME}.spec"

# ── sanity checks ─────────────────────────────────────────────────────────────
log "Checking environment …"

command -v python3 &>/dev/null || die "python3 not found in PATH"
command -v pyinstaller &>/dev/null || die "pyinstaller not found — run: pip install pyinstaller"

[[ -f "$ENTRY" ]] || die "Entry point '$ENTRY' not found (run from project root)"
[[ -d "ui"   ]] || die "'ui/' directory not found"
[[ -d "core" ]] || die "'core/' directory not found"

PYTHON="python3"
PYTHON_VER=$($PYTHON --version 2>&1)
ok "Python:      $PYTHON_VER"
ok "PyInstaller: $(pyinstaller --version 2>&1)"

# ── clean previous build artefacts ───────────────────────────────────────────
log "Cleaning previous build …"
rm -rf "$BUILD_DIR" "$DIST_DIR" "$SPEC_FILE"
ok "Clean done."

# ── detect platform ───────────────────────────────────────────────────────────
PLATFORM="$(uname -s)"
case "$PLATFORM" in
    Linux*)  OS_LABEL="Linux" ;;
    Darwin*) OS_LABEL="macOS" ;;
    *)       OS_LABEL="$PLATFORM"; warn "Untested platform: $PLATFORM" ;;
esac
log "Platform:  $OS_LABEL"

# ── locate easyocr model cache (add as data if present) ──────────────────────
EASYOCR_DATA_ARGS=()
EASYOCR_CACHE="${HOME}/.EasyOCR/model"
if [[ -d "$EASYOCR_CACHE" ]]; then
    EASYOCR_DATA_ARGS=("--add-data" "${EASYOCR_CACHE}:.EasyOCR/model")
    ok "EasyOCR model cache found — will be bundled."
else
    warn "EasyOCR model cache not found at ${EASYOCR_CACHE}."
    warn "Models will be downloaded on first run (requires internet)."
fi

# ── build ─────────────────────────────────────────────────────────────────────
log "Running PyInstaller …"
echo

pyinstaller \
    --name "$APP_NAME" \
    --onedir \
    ${CONSOLE_FLAG:+$CONSOLE_FLAG} \
    \
    --paths "$SCRIPT_DIR" \
    \
    --hidden-import "ui" \
    --hidden-import "ui.theme" \
    --hidden-import "ui.widgets" \
    --hidden-import "ui.panel_left" \
    --hidden-import "ui.panel_center" \
    --hidden-import "ui.panel_right" \
    --hidden-import "ui.panel_log" \
    --hidden-import "ui.main_window" \
    --hidden-import "core" \
    --hidden-import "core.file_utils" \
    --hidden-import "core.model_loader" \
    --hidden-import "core.inference" \
    \
    --hidden-import "ultralytics" \
    --hidden-import "ultralytics.models" \
    --hidden-import "ultralytics.models.yolo" \
    --hidden-import "ultralytics.nn.tasks" \
    --hidden-import "ultralytics.utils" \
    --hidden-import "ultralytics.data" \
    \
    --hidden-import "easyocr" \
    --hidden-import "easyocr.easyocr" \
    --hidden-import "easyocr.utils" \
    --hidden-import "easyocr.config" \
    \
    --hidden-import "cv2" \
    --hidden-import "PIL" \
    --hidden-import "PIL.Image" \
    --hidden-import "numpy" \
    --hidden-import "pydicom" \
    --hidden-import "pydicom.pixel_data_handlers" \
    --hidden-import "pydicom.pixel_data_handlers.numpy_handler" \
    \
    --hidden-import "torch" \
    --hidden-import "torchvision" \
    --hidden-import "torchvision.transforms" \
    \
    --hidden-import "PyQt6" \
    --hidden-import "PyQt6.QtWidgets" \
    --hidden-import "PyQt6.QtCore" \
    --hidden-import "PyQt6.QtGui" \
    \
    --collect-all "ultralytics" \
    --collect-all "easyocr" \
    --collect-all "pydicom" \
    \
    --exclude-module "tkinter" \
    --exclude-module "matplotlib" \
    --exclude-module "IPython" \
    --exclude-module "notebook" \
    --exclude-module "streamlit" \
    \
    "${EASYOCR_DATA_ARGS[@]}" \
    \
    --distpath  "$DIST_DIR" \
    --workpath  "$BUILD_DIR" \
    --noconfirm \
    "$ENTRY"

echo

# ── post-build checks ─────────────────────────────────────────────────────────
EXE_PATH="${DIST_DIR}/${APP_NAME}/${APP_NAME}"

if [[ ! -f "$EXE_PATH" ]]; then
    die "Expected executable not found at: $EXE_PATH"
fi

chmod +x "$EXE_PATH"

ok "Build succeeded!"
echo
echo -e "  ${BOLD}Executable:${RESET}  ${GREEN}${EXE_PATH}${RESET}"
echo -e "  ${BOLD}Bundle dir:${RESET}  ${DIST_DIR}/${APP_NAME}/"
echo
log "To run the app:"
echo -e "  ${BOLD}./${EXE_PATH}${RESET}"
echo

# ── optional: create a compressed archive ─────────────────────────────────────
if command -v tar &>/dev/null; then
    ARCHIVE="${APP_NAME}-${OS_LABEL}.tar.gz"
    log "Creating archive: ${ARCHIVE} …"
    tar -czf "$ARCHIVE" -C "$DIST_DIR" "$APP_NAME"
    ok "Archive created: ${ARCHIVE}"
    echo
fi
