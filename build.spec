# -*- mode: python ; coding: utf-8 -*-
# =============================================================================
#  build.spec  —  PyInstaller spec file
#  YOLO · OCR  Detection Suite
#
#  Use this spec for reproducible, advanced builds instead of relying on the
#  auto-generated one produced by build.bat / build.sh.
#
#  Usage:
#      pyinstaller build.spec
#      pyinstaller build.spec --noconfirm   # skip overwrite prompts
#
#  To toggle console window:
#      Change  console=False  →  console=True  in the EXE() call below.
# =============================================================================

import os
import sys
from pathlib import Path

# ── project root (same directory as this spec file) ───────────────────────────
ROOT = Path(SPECPATH)          # PyInstaller sets SPECPATH to spec file's dir

# ── helper: resolve a package's install location ─────────────────────────────
def pkg_path(name: str) -> str:
    import importlib.util
    spec = importlib.util.find_spec(name)
    if spec is None:
        raise RuntimeError(f"Package '{name}' not found in the current environment.")
    origin = spec.origin or ""
    # for namespace packages origin may be None; fall back to submodule_search_locations
    if not origin and spec.submodule_search_locations:
        return str(list(spec.submodule_search_locations)[0])
    return str(Path(origin).parent)


# =============================================================================
#  1. ANALYSIS
# =============================================================================

a = Analysis(
    # ── entry point ───────────────────────────────────────────────────────────
    scripts=[str(ROOT / "main.py")],

    # ── extra Python paths (so `import ui.xxx` works) ─────────────────────────
    pathex=[str(ROOT)],

    # ── binary libraries (OpenCV, PyQt6 plugins, etc. are auto-collected) ─────
    binaries=[],

    # ── data files ────────────────────────────────────────────────────────────
    #    Format:  (source_glob_or_dir, destination_in_bundle)
    datas=[
        # our own packages
        (str(ROOT / "ui"),   "ui"),
        (str(ROOT / "core"), "core"),

        # ultralytics ships YAML configs and other data files
        (pkg_path("ultralytics"), "ultralytics"),

        # easyocr ships detection/recognition model configs
        (pkg_path("easyocr"),    "easyocr"),

        # pydicom ships its DICOM data dictionaries
        (pkg_path("pydicom"),    "pydicom"),
    ],

    # ── hidden imports ────────────────────────────────────────────────────────
    #    Modules that PyInstaller's static analyser misses because they are
    #    loaded dynamically (importlib, __import__, lazy loaders, etc.).
    hiddenimports=[
        # ── our own packages ──────────────────────────────────────────────────
        "ui",
        "ui.theme",
        "ui.widgets",
        "ui.panel_left",
        "ui.panel_center",
        "ui.panel_right",
        "ui.panel_log",
        "ui.main_window",
        "core",
        "core.file_utils",
        "core.model_loader",
        "core.inference",

        # ── PyQt6 ─────────────────────────────────────────────────────────────
        "PyQt6",
        "PyQt6.QtWidgets",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtSvg",
        "PyQt6.sip",

        # ── ultralytics / YOLO ────────────────────────────────────────────────
        "ultralytics",
        "ultralytics.models",
        "ultralytics.models.yolo",
        "ultralytics.models.yolo.detect",
        "ultralytics.nn",
        "ultralytics.nn.tasks",
        "ultralytics.nn.modules",
        "ultralytics.utils",
        "ultralytics.utils.checks",
        "ultralytics.utils.ops",
        "ultralytics.data",
        "ultralytics.data.augment",
        "ultralytics.data.utils",
        "ultralytics.cfg",
        "ultralytics.trackers",

        # ── easyocr ───────────────────────────────────────────────────────────
        "easyocr",
        "easyocr.easyocr",
        "easyocr.utils",
        "easyocr.config",
        "easyocr.detection",
        "easyocr.recognition",
        "easyocr.model.vgg_model",
        "easyocr.model.modules",

        # ── pydicom ───────────────────────────────────────────────────────────
        "pydicom",
        "pydicom.encoders",
        "pydicom.encoders.native",
        "pydicom.pixel_data_handlers",
        "pydicom.pixel_data_handlers.numpy_handler",
        "pydicom.pixel_data_handlers.util",
        "pydicom.overlays",
        "pydicom.sequence",

        # ── opencv ────────────────────────────────────────────────────────────
        "cv2",

        # ── Pillow ────────────────────────────────────────────────────────────
        "PIL",
        "PIL.Image",
        "PIL.ImageOps",
        "PIL.ImageFilter",
        "PIL.JpegImagePlugin",
        "PIL.PngImagePlugin",
        "PIL.BmpImagePlugin",
        "PIL.TiffImagePlugin",

        # ── NumPy ─────────────────────────────────────────────────────────────
        "numpy",
        "numpy.core._multiarray_umath",
        "numpy.core._multiarray_tests",
        "numpy.random",

        # ── PyTorch ───────────────────────────────────────────────────────────
        "torch",
        "torch.nn",
        "torch.nn.functional",
        "torch.utils",
        "torch.utils.data",
        "torch.cuda",
        "torchvision",
        "torchvision.transforms",
        "torchvision.transforms.functional",
        "torchvision.models",

        # ── scipy / sklearn (pulled by easyocr) ───────────────────────────────
        "scipy",
        "scipy.special",
        "scipy.special._ufuncs_cxx",
        "scipy.linalg",
        "scipy.sparse",
        "scipy.sparse._compressed",
        "sklearn",
        "sklearn.utils",
        "sklearn.utils._cython_blas",
        "sklearn.neighbors",
        "sklearn.neighbors._partition_nodes",

        # ── standard library extras sometimes missed ──────────────────────────
        "pathlib",
        "zipfile",
        "tempfile",
        "glob",
        "datetime",
    ],

    # ── hook directories (add project-local hooks if needed) ──────────────────
    hookspath=[],

    # ── runtime hook: run before user code in the frozen exe ─────────────────
    runtime_hooks=[],

    # ── intentionally excluded modules ───────────────────────────────────────
    excludes=[
        "tkinter",
        "matplotlib",
        "IPython",
        "jupyter",
        "notebook",
        "streamlit",
        "pytest",
        "setuptools",
        "distutils",
        "docutils",
    ],

    # ── misc Analysis options ─────────────────────────────────────────────────
    noarchive=False,   # True = keep .pyc files on disk (slower startup)
    optimize=0,        # 0 = no optimisation; 2 = strip docstrings
)


# =============================================================================
#  2. PYZ  (Python bytecode archive)
# =============================================================================

pyz = PYZ(a.pure, a.zipped_data, cipher=None)


# =============================================================================
#  3. EXE  (the launcher stub)
# =============================================================================

exe = EXE(
    pyz,
    a.scripts,
    [],                     # no extra binaries embedded in the launcher stub

    exclude_binaries=True,  # binaries go into the COLLECT step (--onedir)

    name="YoloOCR",

    # ── appearance ────────────────────────────────────────────────────────────
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,            # True strips debug symbols — saves space, loses tracebacks
    upx=False,              # UPX compression — can trigger AV false positives; keep off
    console=False,          # False = no black console window (release build)
                            # Set to True for a debug build that shows Python tracebacks

    # ── Windows-specific metadata ─────────────────────────────────────────────
    #   icon="assets/icon.ico",   # uncomment and point to your .ico file
    version_file=None,            # point to a win_version_info.txt if needed
)


# =============================================================================
#  4. COLLECT  (--onedir bundle: gather everything into dist/YoloOCR/)
# =============================================================================

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,

    strip=False,
    upx=False,
    upx_exclude=[
        # UPX can corrupt some DLLs — list known-bad ones here if UPX is enabled
        "vcruntime140.dll",
        "python3*.dll",
        "Qt6Core.dll",
        "Qt6Widgets.dll",
        "Qt6Gui.dll",
    ],
    name="YoloOCR",
)

# =============================================================================
#  Notes for maintainers
# =============================================================================
#
#  ① Adding a new UI or core module
#      • Add `"ui.new_module"` / `"core.new_module"` to hiddenimports above.
#        PyInstaller may pick it up automatically via Analysis, but listing it
#        explicitly avoids silent misses.
#
#  ② Adding a new static asset (e.g. icons/, models/)
#      • Add an entry to the `datas` list:
#            ("assets/icons", "assets/icons"),
#
#  ③ Windows app icon
#      • Create a 256×256 .ico file, save it to assets/icon.ico, then
#        uncomment the `icon=` line in the EXE() call above.
#
#  ④ Switching to --onefile
#      • Remove the COLLECT() call entirely.
#      • Change the EXE() call: pass  a.binaries, a.zipfiles, a.datas
#        directly after `a.scripts` and set  exclude_binaries=False.
#      • Note: --onefile is significantly slower to start for large ML apps
#        because every launch extracts the bundle to a temp directory.
#
#  ⑤ Console window
#      • console=False  →  clean windowed app (release)
#      • console=True   →  terminal shows Python stdout/stderr (debug)
#
# =============================================================================
