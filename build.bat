@echo off
setlocal EnableDelayedExpansion

:: ═══════════════════════════════════════════════════════════════════════════
::  build.bat  —  Windows PyInstaller build script
::  YOLO · OCR  Detection Suite
::
::  Usage:
::      build.bat            (release build, no console window)
::      build.bat --console  (keep console for debugging)
::
::  Output:  dist\YoloOCR\YoloOCR.exe
:: ═══════════════════════════════════════════════════════════════════════════

title YOLO OCR  —  PyInstaller Build

:: ── parse optional flags ────────────────────────────────────────────────────
set "CONSOLE_FLAG=--noconsole"
set "BUILD_LABEL=release (no console)"
for %%A in (%*) do (
    if /I "%%A"=="--console" (
        set "CONSOLE_FLAG=--console"
        set "BUILD_LABEL=debug (with console)"
    )
)

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   YOLO · OCR  —  PyInstaller Build (Windows) ║
echo  ╚══════════════════════════════════════════════╝
echo.
echo   Mode : %BUILD_LABEL%
echo   Dir  : %~dp0
echo.

:: ── verify Python is available ───────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR]  Python not found on PATH.
    echo           Install Python 3.10+ and make sure it is on PATH.
    pause
    exit /b 1
)
for /f "tokens=*" %%V in ('python --version 2^>^&1') do echo   Python : %%V

:: ── verify PyInstaller is installed ─────────────────────────────────────────
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [INFO]  PyInstaller not found — installing…
    python -m pip install pyinstaller --quiet
    if errorlevel 1 (
        echo  [ERROR]  Failed to install PyInstaller.
        pause
        exit /b 1
    )
)
for /f "tokens=*" %%V in ('python -m PyInstaller --version 2^>^&1') do echo   PyInstaller : %%V

:: ── clean previous build artefacts ──────────────────────────────────────────
echo.
echo  [1/4]  Cleaning previous build artefacts…

if exist "build\YoloOCR" (
    echo         Removing build\YoloOCR …
    rmdir /s /q "build\YoloOCR"
)
if exist "dist\YoloOCR" (
    echo         Removing dist\YoloOCR …
    rmdir /s /q "dist\YoloOCR"
)
if exist "YoloOCR.spec" (
    echo         Removing YoloOCR.spec …
    del /q "YoloOCR.spec"
)

:: ── run PyInstaller ──────────────────────────────────────────────────────────
echo.
echo  [2/4]  Running PyInstaller…
echo.

python -m PyInstaller ^
    --name "YoloOCR" ^
    --onedir ^
    %CONSOLE_FLAG% ^
    --clean ^
    --noconfirm ^
    ^
    --paths "." ^
    ^
    --add-data "ui;ui" ^
    --add-data "core;core" ^
    ^
    --hidden-import "ui" ^
    --hidden-import "ui.theme" ^
    --hidden-import "ui.widgets" ^
    --hidden-import "ui.panel_left" ^
    --hidden-import "ui.panel_center" ^
    --hidden-import "ui.panel_right" ^
    --hidden-import "ui.panel_log" ^
    --hidden-import "ui.main_window" ^
    --hidden-import "core" ^
    --hidden-import "core.file_utils" ^
    --hidden-import "core.model_loader" ^
    --hidden-import "core.inference" ^
    ^
    --hidden-import "ultralytics" ^
    --hidden-import "ultralytics.models" ^
    --hidden-import "ultralytics.models.yolo" ^
    --hidden-import "ultralytics.nn.tasks" ^
    --hidden-import "ultralytics.utils" ^
    ^
    --hidden-import "easyocr" ^
    --hidden-import "easyocr.easyocr" ^
    --hidden-import "easyocr.utils" ^
    --hidden-import "easyocr.model.vgg_model" ^
    --hidden-import "easyocr.detection" ^
    --hidden-import "easyocr.recognition" ^
    ^
    --hidden-import "pydicom" ^
    --hidden-import "pydicom.encoders" ^
    --hidden-import "pydicom.encoders.gdcm" ^
    --hidden-import "pydicom.encoders.pylibjpeg" ^
    --hidden-import "pydicom.encoders.native" ^
    ^
    --hidden-import "cv2" ^
    --hidden-import "PIL" ^
    --hidden-import "PIL.Image" ^
    --hidden-import "numpy" ^
    ^
    --hidden-import "PyQt6" ^
    --hidden-import "PyQt6.QtWidgets" ^
    --hidden-import "PyQt6.QtCore" ^
    --hidden-import "PyQt6.QtGui" ^
    ^
    --hidden-import "torch" ^
    --hidden-import "torchvision" ^
    --hidden-import "torchvision.transforms" ^
    ^
    --hidden-import "sklearn" ^
    --hidden-import "sklearn.utils._cython_blas" ^
    --hidden-import "scipy" ^
    --hidden-import "scipy.special" ^
    --hidden-import "scipy.special._ufuncs_cxx" ^
    --hidden-import "scipy.sparse._compressed" ^
    ^
    --collect-all "ultralytics" ^
    --collect-all "easyocr" ^
    --collect-all "pydicom" ^
    --collect-data "torchvision" ^
    ^
    --exclude-module "tkinter" ^
    --exclude-module "matplotlib" ^
    --exclude-module "IPython" ^
    --exclude-module "jupyter" ^
    --exclude-module "notebook" ^
    ^
    main.py

if errorlevel 1 (
    echo.
    echo  [ERROR]  PyInstaller failed — see output above.
    pause
    exit /b 1
)

:: ── copy ancillary files into dist ───────────────────────────────────────────
echo.
echo  [3/4]  Copying ancillary files…

if exist "requirements.txt" (
    copy /y "requirements.txt" "dist\YoloOCR\" >nul
    echo         requirements.txt  →  dist\YoloOCR\
)
if exist "README.md" (
    copy /y "README.md" "dist\YoloOCR\" >nul
    echo         README.md         →  dist\YoloOCR\
)

:: ── report ───────────────────────────────────────────────────────────────────
echo.
echo  [4/4]  Build complete.
echo.
echo   ┌──────────────────────────────────────────────────┐
echo   │  Executable:  dist\YoloOCR\YoloOCR.exe           │
echo   │  Run it:      dist\YoloOCR\YoloOCR.exe           │
echo   └──────────────────────────────────────────────────┘
echo.

:: ── optional: open output folder in Explorer ─────────────────────────────────
if exist "dist\YoloOCR\YoloOCR.exe" (
    echo  Open output folder? [Y/N]
    choice /c YN /n /m "  > "
    if errorlevel 2 goto :done
    explorer "dist\YoloOCR"
)

:done
echo.
endlocal
