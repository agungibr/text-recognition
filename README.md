# YOLO · OCR — Detection Suite

A local-first desktop application for running **YOLO object detection + EasyOCR text recognition** on images and DICOM radiological files. Built with PyQt6 — no browser, no server, no data leaves your machine.

---

## Table of Contents

1. [Features](#features)
2. [Screenshots / Layout](#screenshots--layout)
3. [Project Structure](#project-structure)
4. [Requirements](#requirements)
5. [Installation](#installation)
6. [Running the App](#running-the-app)
7. [Where to Put `best.pt`](#where-to-put-bestpt)
8. [How to Use](#how-to-use)
9. [Supported File Formats](#supported-file-formats)
10. [Output Format](#output-format)
11. [Building a Standalone Executable](#building-a-standalone-executable)
12. [Customisation Guide](#customisation-guide)
13. [Module Reference](#module-reference)
14. [Troubleshooting](#troubleshooting)

---

## Features

| Feature | Detail |
|---|---|
| **YOLO inference** | Any Ultralytics `.pt` / `.pth` model (YOLOv8, YOLOv9, YOLOv11, …) |
| **EasyOCR** | Reads text from every detected bounding box |
| **DICOM support** | Loads `.dcm` radiological files natively via pydicom |
| **Batch processing** | Queue multiple files or an entire folder in one run |
| **Live preview** | Click any queued file to preview it before running |
| **Colour-coded table** | Confidence ≥ 0.7 green · ≥ 0.4 yellow · < 0.4 red |
| **Crop thumbnails** | Scrollable strip of every detected region |
| **ZIP export** | One click exports all `.txt` logs + crop images |
| **GPU / CPU toggle** | Use CUDA if available, fall back to CPU silently |
| **Multi-language OCR** | id · en · ms · ja · ko (or any EasyOCR-supported pair) |
| **Fully offline** | Zero network calls after first model download |
| **Packagable** | PyInstaller scripts included for Windows `.exe` and Linux binary |

---

## Screenshots / Layout

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  YOLO · OCR   ░░░░░░░░░░░░░░░░░░░░░░░░  [1/4] image.jpg      ● Model  ● OCR   │  ← topbar
├────────────────┬─────────────────────────────┬───────────────────────────────────┤
│  YOLO · OCR   │  FILE QUEUE                 │  DETECTIONS           4 objects  │
│  Detection     │  ┌─────────────────────┐   │  ┌──────────┐  ┌──────────────┐ │
│  Suite v1.0    │  │ scan_001.jpg    [4] │   │  │  Total   │  │  Avg Conf   │ │
│                │  │ scan_002.dcm  ──── │   │  │    4     │  │    0.81     │ │
│  ── Model ──  │  │ scan_003.png        │   │  └──────────┘  └──────────────┘ │
│  [best.pt   ] │  └─────────────────────┘   │                                  │
│  ● Ready       │                             │  ID  TEXT         CONF   SIZE   │
│  [Load Model] │  PREVIEW                    │  00  HEPATIC       0.92  48×31  │
│                │  ┌─────────────────────┐   │  01  T2            0.87  22×18  │
│  ── OCR ────  │  │                     │   │  02  LEFT          0.54  60×20  │
│  Lang [id+en] │  │   [image preview]   │   │  03  123.4         0.31  35×14  │
│  ☑ Use GPU    │  │                     │   │                                  │
│  ● Ready       │  └─────────────────────┘   │  CROPS                          │
│  [Load OCR]   │                             │  ┌────┐ ┌────┐ ┌────┐ ┌────┐  │
│                │                             │  │crop│ │crop│ │crop│ │crop│  │
│  ── Detection ─│                             │  └────┘ └────┘ └────┘ └────┘  │
│  Conf  0.25   │                             │                                  │
│  ████░░░░░░   │                             │                                  │
│  ☑ Save crops │                             │                                  │
│                │                             │                                  │
│  ── Input ───  │                             │                                  │
│  [+Files][+Dir]│                             │                                  │
│  [Clear]       │                             │                                  │
│  4 files queued│                             │                                  │
│                │                             │                                  │
│  ────────────  │                             │                                  │
│  [▶ Run      ] │                             │                                  │
│  [↓ Export   ] │                             │                                  │
├────────────────┴─────────────────────────────┴───────────────────────────────────┤
│  LOG                                                                   [Clear] │
│    14:03:01  Processing  →  scan_001.jpg                                       │
│    14:03:02    ✔  obj_00  conf=0.92  "HEPATIC"                                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Three-panel layout:**

- **Left (280 px)** — configuration: model, OCR, confidence, file queue, run/export
- **Center** — file queue list + live image preview (split vertically)
- **Right** — detection metrics, colour-coded table, crop thumbnails
- **Bottom** — timestamped log strip

---

## Project Structure

```
desktop/
│
├── main.py                  # Entry point — run this
├── requirements.txt         # All runtime dependencies (pip)
├── build.bat                # Windows PyInstaller build script
├── build.sh                 # Linux / macOS PyInstaller build script
├── build.spec               # Advanced PyInstaller spec (reproducible builds)
│
├── models/                  # ← DROP your best.pt HERE (auto-detected)
│   └── best.pt
│
├── core/                    # Pure Python — zero Qt, fully unit-testable
│   ├── __init__.py
│   ├── file_utils.py        # File discovery + DICOM / image loading helpers
│   ├── model_loader.py      # ModelLoader QThread  (YOLO + EasyOCR)
│   └── inference.py         # InferenceWorker QThread  (detection pipeline)
│
├── ui/                      # All PyQt6 code
│   ├── __init__.py
│   ├── theme.py             # COLORS palette + global STYLESHEET
│   ├── widgets.py           # Badge · MetricCard · Divider · ImageViewer · …
│   ├── panel_left.py        # LeftPanel  (config sidebar)
│   ├── panel_center.py      # CenterPanel (file queue + preview)
│   ├── panel_right.py       # RightPanel  (results table + crops)
│   ├── panel_log.py         # LogPanel    (timestamped log)
│   └── main_window.py       # MainWindow  (assembles all panels)
│
└── before/
    └── app.py               # Original monolithic Streamlit → PyQt6 port (reference)
```

> **Design principle:** `core/` modules never import from `ui/`.
> `ui/` modules import from `core/` but never the reverse.
> This keeps business logic independently testable.

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.10 or newer |
| PyQt6 | 6.5+ |
| ultralytics | 8.0+ |
| easyocr | 1.7+ |
| opencv-python | 4.8+ |
| numpy | 1.24+ |
| Pillow | 10.0+ |
| pydicom | 2.4+ |

GPU acceleration requires a CUDA-compatible GPU with PyTorch CUDA builds installed.
The app falls back to CPU silently if CUDA is unavailable.

---

## Installation

### 1 — Clone / download

```bash
git clone <your-repo-url>
cd desktop
```

### 2 — Create a virtual environment (strongly recommended)

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

> **GPU users:** Install the CUDA build of PyTorch *before* running the above command.
> Visit https://pytorch.org/get-started/locally/ and pick your CUDA version, then run
> the generated `pip install torch torchvision ...` command first.

### 4 — (Optional) Place your model

Copy `best.pt` into the `models/` folder:

```
desktop/models/best.pt
```

The app will auto-detect it and pre-fill the model path on startup.

---

## Running the App

```bash
python main.py
```

That's it. No config files, no environment variables required.

---

## Where to Put `best.pt`

You have three options — pick whichever suits your workflow:

### Option A — `models/` folder (recommended)

```
desktop/models/best.pt
```

The app checks this path on startup and **pre-fills the model path field automatically**.
Nothing else needed — just launch and click **Load Model**.

### Option B — Anywhere, use Browse

Leave the `models/` folder empty and click the **Browse** button in the Model section
to pick any `.pt` or `.pth` file from anywhere on your machine.

### Option C — Absolute path in the text field

Type or paste a full path directly into the model path input:

```
C:\Users\you\weights\best.pt
/home/you/weights/best.pt
```

> **Note:** The `models/` folder is tracked by git (via `.gitkeep`) but `*.pt` files
> are intentionally excluded because weight files can be hundreds of megabytes.
> Add this to your `.gitignore` if needed:
> ```
> models/*.pt
> models/*.pth
> ```

---

## How to Use

### Step 1 — Load the YOLO model

1. The **Model** section is at the top of the left panel.
2. If you placed `best.pt` in `models/`, the path is already filled in.
   Otherwise click **Browse** and select your `.pt` file.
3. Click **Load Model**.
4. Wait for the badge to turn **● Ready** (loading happens in the background).

### Step 2 — Load the OCR engine

1. In the **OCR Engine** section, choose your language pair from the dropdown:
   - `id + en` — Indonesian + English (default)
   - `en only` — English only
   - `id only` — Indonesian only
   - `id + en + ms` — Indonesian + English + Malay
   - `ja + en` — Japanese + English
   - `ko + en` — Korean + English
2. Tick **Use GPU** if you have a CUDA GPU (untick to force CPU).
3. Click **Load OCR**.
4. First run downloads the EasyOCR models (~100 MB) to `~/.EasyOCR/`.
   Subsequent runs load from cache instantly.
5. Wait for the badge to turn **● Ready**.

### Step 3 — Add files

In the **Input Files** section:

| Button | Action |
|---|---|
| **+ Files** | Opens a file picker — select one or more images / DICOM files |
| **+ Folder** | Scans an entire folder (non-recursive) for supported images |
| **Clear** | Removes all files from the queue |

- DICOM files (`.dcm`) appear **highlighted in amber** in the queue list.
- Duplicate paths are automatically skipped.
- The file count label updates in real time.

### Step 4 — Configure detection

In the **Detection** section:

- **Confidence slider** — drag to set the minimum confidence threshold (0.00 – 1.00).
  Default is `0.25`. Only detections above this value are reported.
- **Save cropped detections** — when checked, each bounding-box region is saved
  as a `.jpg` crop in the output directory and shown as a thumbnail in the right panel.

### Step 5 — Run

Click **▶ Run Detection**.

- The thin progress bar in the top bar fills as files are processed.
- Each file's status appears in the **Log** panel at the bottom.
- As each file finishes, its queue entry turns **green** with a detection count badge `[N]`.

### Step 6 — Review results

Click any file in the queue to see its results in the **right panel**:

- **Total** — number of detected objects.
- **Avg Conf** — mean confidence across all detections.
- **Table** — one row per detection:
  - `ID` — sequential index
  - `TEXT` — OCR text extracted from the bounding box
  - `CONF` — confidence score (green ≥ 0.7 · yellow ≥ 0.4 · red < 0.4)
  - `SIZE` — bounding box dimensions in pixels (`W×H`)
- **Crops strip** — scrollable horizontal row of thumbnail previews for each crop.

### Step 7 — Export

Click **↓ Export Results (ZIP)**.

Choose a save location. The ZIP archive contains one folder per image:

```
detection_20240815_143022.zip
└── scan_001/
│   ├── scan_001.txt      ← detection log (one line per object)
│   ├── scan_001_crop00.jpg
│   ├── scan_001_crop01.jpg
│   └── …
└── scan_002/
    ├── scan_002.txt
    └── …
```

---

## Supported File Formats

| Extension | Type | Notes |
|---|---|---|
| `.jpg` / `.jpeg` | JPEG image | Standard, lossy |
| `.png` | PNG image | Lossless, transparency supported |
| `.bmp` | Bitmap | Uncompressed |
| `.tiff` / `.tif` | TIFF image | Multi-page not supported (first frame only) |
| `.dcm` | DICOM | Radiological images — pixel array auto-normalised to uint8 |

---

## Output Format

Each processed image produces a plain-text log file alongside its crop images:

```
OBJ_000 | text='HEPATIC' | conf=0.921 | center=(124.5,88.3) | size=48.0x31.0
OBJ_001 | text='T2'      | conf=0.872 | center=(210.1,45.7) | size=22.0x18.0
OBJ_002 | text='LEFT'    | conf=0.541 | center=(88.0,200.4) | size=60.0x20.0
OBJ_003 | text='123.4'   | conf=0.314 | center=(300.2,155.9)| size=35.0x14.0
```

Fields:
- `text` — OCR result (may be empty `''` if no text was recognised)
- `conf` — YOLO confidence score in range `[0, 1]`
- `center` — bounding box centre coordinates `(x, y)` in pixels
- `size` — bounding box `width × height` in pixels

---

## Building a Standalone Executable

No Python installation needed on the target machine after building.

### Windows → `.exe`

```bat
cd desktop

:: Release build (no console window)
build.bat

:: Debug build (keeps a terminal for reading error messages)
build.bat --console
```

Output: `dist\YoloOCR\YoloOCR.exe`

### Linux / macOS → binary

```bash
cd desktop
chmod +x build.sh

# Release build
./build.sh

# Debug build
./build.sh --console
```

Output: `dist/YoloOCR/YoloOCR`

A `.tar.gz` archive is also created automatically if `tar` is available.

### Advanced — `build.spec`

For reproducible CI/CD builds or when you need fine-grained control:

```bash
pip install pyinstaller
pyinstaller build.spec --noconfirm
```

The spec file is fully documented with inline comments covering:
- Adding new modules or static assets
- Bundling EasyOCR model cache offline
- Switching to `--onefile` mode
- Adding a Windows app icon
- Toggling the console window

> **Bundle size note:** The output directory will be large (1–2 GB+ with CUDA PyTorch)
> because the full ML stack is included. Use `--onedir` (the default) rather than
> `--onefile` — `--onefile` extracts to a temp folder on every launch, making startup
> very slow for ML-heavy apps.

---

## Customisation Guide

### Changing the colour theme

All colours live in one place — `ui/theme.py`:

```python
# ui/theme.py
COLORS = {
    "bg":       "#0F1117",   # main background
    "accent":   "#4B8BF4",   # primary blue — buttons, highlights, progress
    "success":  "#2ECC71",   # green — loaded / processed / high confidence
    "warning":  "#F39C12",   # amber — DICOM files, medium confidence
    "error":    "#E74C3C",   # red — errors, low confidence
    # … and more
}
```

Change any hex value and the entire UI updates — no other files to touch.

### Adding an OCR language

In `ui/panel_left.py`, add an entry to `_LANG_MAP`:

```python
_LANG_MAP: dict[str, list[str]] = {
    "id + en":      ["id", "en"],
    "fr + en":      ["fr", "en"],   # ← add new pair here
    # …
}
```

Then add the matching display string to `self.lang_combo.addItems(...)` — or simply
add it to `_LANG_MAP` and it populates the combo automatically (the combo is built
from `_LANG_MAP.keys()`).

All language codes supported by EasyOCR are valid.
See https://www.jaided.ai/easyocr/ for the full list.

### Changing the default confidence threshold

In `ui/panel_left.py`, inside `_add_detection_group`:

```python
self.conf_slider.setValue(25)   # 25 = 0.25  ← change this (0–100)
```

### Setting a different default model path

In `ui/panel_left.py`, inside `_add_model_group`:

```python
_default_model = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models", "best.pt",   # ← change folder/filename here
)
```

### Adding a new panel or feature

1. Create `ui/panel_new.py` following the same pattern as the existing panels.
2. Import and instantiate it in `ui/main_window.py`.
3. Wire its signals in `_connect_signals()`.
4. Add `"ui.panel_new"` to `hiddenimports` in both `build.bat`, `build.sh`,
   and `build.spec` so PyInstaller bundles it.

---

## Module Reference

### `main.py`

Entry point. Inserts the project root onto `sys.path` (so `import ui.xxx` and
`import core.xxx` work whether invoked via `python main.py` or a PyInstaller bundle),
then calls `ui.main_window.launch()`.

---

### `core/file_utils.py`

Pure-Python helpers. No Qt dependency.

| Symbol | Description |
|---|---|
| `SUPPORTED_EXTENSIONS` | `frozenset` of lowercase extensions the app accepts |
| `collect_files_from_paths(paths)` | Converts a list of path strings into file-dicts, deduplicating by resolved path |
| `collect_files_from_folder(folder)` | Non-recursive folder scan; returns file-dicts sorted by name |
| `load_dicom_as_bgr(path)` | Reads a `.dcm` file → normalised BGR `uint8` NumPy array |
| `load_image_as_bgr(path)` | Dispatcher — DICOM or standard image → BGR array |
| `dicom_to_temp_png(path)` | Converts DICOM → temporary `.png` file (caller must delete) |

**File-dict schema** (used throughout the app):

```python
{
    "name": str,    # display filename (basename)
    "type": "path", # always "path" for disk files
    "path": str,    # absolute resolved path
}
```

---

### `core/model_loader.py`

`ModelLoader(QThread)` — loads YOLO or EasyOCR in a background thread so the UI
never freezes during the (potentially multi-minute) first load.

```python
loader = ModelLoader("yolo", model_path="models/best.pt")
loader = ModelLoader("ocr",  languages=["id", "en"], use_gpu=True)

loader.done.connect(lambda obj, kind: ...)   # (model_or_reader, "yolo"|"ocr")
loader.error.connect(lambda msg: ...)
loader.start()
```

EasyOCR GPU init failures are caught internally and retried on CPU automatically.

---

### `core/inference.py`

`InferenceWorker(QThread)` — iterates the file queue, runs YOLO + EasyOCR on each
image, writes per-image `.txt` logs, optionally saves crops, then emits all results.

```python
worker = InferenceWorker(
    model=yolo_model,
    reader=ocr_reader,
    files=file_dicts,
    conf=0.25,
    save_crops=True,
)
worker.progress.connect(lambda pct, label: ...)
worker.result.connect(lambda results, output_dir: ...)
worker.log.connect(lambda msg: ...)
worker.error.connect(lambda msg: ...)
worker.start()
```

---

### `ui/theme.py`

Single source of truth for all visual tokens.

- `COLORS` — dict of hex strings (background, surface levels, accent, status colours, text)
- `STYLESHEET` — one large Qt CSS string built from `COLORS` using f-strings

---

### `ui/widgets.py`

Reusable stateless widgets shared across all panels.

| Class | Description |
|---|---|
| `Badge` | Coloured pill label with four named states: `idle · busy · ok · error` |
| `SectionLabel` | Small all-caps muted section header |
| `ValueLabel` | Monospace primary-colour value display |
| `MetricCard` | Bordered card with a small label above a large numeric value |
| `Divider` | 1-px horizontal `QFrame` rule |
| `ImageViewer` | Aspect-ratio-preserving image label — accepts file paths or NumPy arrays |

---

### `ui/panel_left.py`

`LeftPanel(QWidget)` — fixed 280 px sidebar.

Emits seven signals (all connected in `MainWindow._connect_signals`):
`loadModelClicked · loadOCRClicked · addFilesClicked · addFolderClicked ·
clearFilesClicked · runClicked · exportClicked`

Exposes read-only properties consumed by `MainWindow`:
`model_path · conf · save_crops · use_gpu · languages`

Public slots: `setFileCount(n) · setRunnable(bool) · setExportable(bool)`

---

### `ui/panel_center.py`

`CenterPanel(QWidget)` — vertically split file queue + image preview.

- `setFiles(files)` — repopulates the queue list
- `markProcessed(filename, result)` — turns a queue item green with a `[N]` badge
- `clearResults()` — resets the cached result map
- Emits `fileSelected(dict)` when the user clicks a queue item

DICOM preview is rendered by converting the pixel array via `load_dicom_as_bgr`.

---

### `ui/panel_right.py`

`RightPanel(QWidget)` — results view with a `QStackedWidget`:

- **Index 0** — empty placeholder shown before first run
- **Index 1** — live results: metric cards + colour-coded table + crop strip

- `showResult(result)` — populates all widgets from a result dict
- `clear()` — switches back to the placeholder

---

### `ui/panel_log.py`

`LogPanel(QWidget)` — fixed-height (130 px) timestamped log.

- `append(msg)` — adds a line with `HH:MM:SS` prefix, colour-coded by content
- `clear()` — wipes the list

Colour rules: `✕ / Error / error` → red · `✔ / Done` → green · `→ / Processing` → blue

---

### `ui/main_window.py`

`MainWindow(QMainWindow)` — the top-level window.

Owns all application state: `_model · _reader · _files · _results · _output_dir`

Key responsibilities:
- Builds the topbar, horizontal body splitter, and log strip
- Wires all panel signals to action methods
- Starts `ModelLoader` threads for YOLO and OCR
- Starts `InferenceWorker` thread on Run
- Handles file add / folder scan / clear / export
- Routes file-selection events from `CenterPanel` to `RightPanel`

Also exports `launch()` — called by `main.py` to create `QApplication` and show the window.

---

## Troubleshooting

### App window doesn't appear / crashes on launch

- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Try running from the project root: `cd desktop && python main.py`
- Check that you are using **Python 3.10 or newer**: `python --version`

### "Model not found" error when clicking Load Model

- Check that the path in the model field points to an existing `.pt` file.
- If using the `models/` folder, confirm the file is named exactly `best.pt`.
- Use the **Browse** button to navigate to the file directly.

### EasyOCR takes a long time on first Load OCR

This is normal. EasyOCR downloads detection and recognition model weights
(~100 MB total) to `~/.EasyOCR/model/` on the first run.
Subsequent loads use the local cache and are near-instant.

### GPU not being used (slow inference)

1. Confirm PyTorch was installed with CUDA support:
   ```python
   import torch; print(torch.cuda.is_available())
   ```
   If `False`, reinstall PyTorch from https://pytorch.org/get-started/locally/
2. Tick **Use GPU** in the OCR Engine section before clicking Load OCR.
3. YOLO uses GPU automatically when a CUDA-enabled PyTorch is present.

### DICOM file shows "Cannot render DICOM"

- Confirm `pydicom` is installed: `pip install pydicom`
- Some DICOM files use compressed transfer syntaxes (JPEG 2000, RLE).
  Install the optional handler: `pip install pylibjpeg pylibjpeg-libjpeg`
- Multi-frame DICOM (cine/video) is not supported — only single-frame files.

### PyInstaller build fails

- Install PyInstaller first: `pip install pyinstaller`
- Run the build from the `desktop/` directory (where `main.py` lives).
- If a hidden import is missing at runtime, add it to the `hiddenimports` list
  in `build.spec` and rebuild.
- For very large models, Windows Defender may slow down or block extraction.
  Add the `dist/` folder to your antivirus exclusions during development.

### Export ZIP is missing crop images

Make sure **Save cropped detections** is checked in the Detection section
*before* clicking Run. Crops are not saved retroactively.

---

## License

Add your license here.

---

## Acknowledgements

- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) — object detection engine
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) — text recognition
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) — GUI framework
- [pydicom](https://github.com/pydicom/pydicom) — DICOM file support
- [OpenCV](https://opencv.org/) — image processing
