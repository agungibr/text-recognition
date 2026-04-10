# Text Detection Suite

A local desktop application for running **YOLO object detection + EasyOCR text recognition** on images and DICOM radiological files. Built with PyQt6.

---

## Running from Source

### 1 — Install dependencies

```bash
pip install -r requirements.txt
```

### 2 — Run

```bash
python main.py
```

---

## Building a Standalone Executable

### Windows

```bat
:: Release build (no console window)
build.bat

:: Debug build (keeps terminal for error output)
build.bat --console
```

Output: `dist\YoloOCR\YoloOCR.exe`

### Linux / macOS

```bash
chmod +x build.sh
./build.sh          # release
./build.sh --console  # debug
```

Output: `dist/YoloOCR/YoloOCR`

### Advanced — build.spec

```bash
pip install pyinstaller
pyinstaller build.spec --noconfirm
```

---

## Using the Built Executable

1. Open the output folder (`dist\YoloOCR\`)
2. Run `YoloOCR.exe` (Windows) or `YoloOCR` (Linux/macOS)
3. Place `best.pt` in a `models/` folder next to the executable, or use **Browse** to select it
4. Click **Load Model** → **Load OCR** → add files → **Run Detection**

> **Note:** The output folder is large (1–2 GB+) because it bundles the full ML stack. Distribute the entire `dist\YoloOCR\` folder — the executable will not work if moved alone.

