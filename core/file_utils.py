import os
import glob
import tempfile

import cv2
import numpy as np
import pydicom
from pathlib import Path

SUPPORTED_EXTENSIONS: frozenset = frozenset({
    ".jpg", ".jpeg", ".png", ".bmp",
    ".tiff", ".tif", ".dcm",
})

def collect_files_from_paths(paths: list[str]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []

    for raw in paths:
        p = Path(raw).resolve()
        if p.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        result.append({
            "name": p.name,
            "type": "path",
            "path": key,
        })

    return result


def collect_files_from_folder(folder: str) -> list[dict]:
    found: list[str] = []

    for ext in SUPPORTED_EXTENSIONS:
        found.extend(glob.glob(os.path.join(folder, f"*{ext}")))
        found.extend(glob.glob(os.path.join(folder, f"*{ext.upper()}")))

    seen: set[str] = set()
    unique: list[str] = []
    for raw in found:
        key = str(Path(raw).resolve())
        if key not in seen:
            seen.add(key)
            unique.append(key)

    unique.sort(key=lambda p: Path(p).name.lower())

    return [
        {"name": Path(p).name, "type": "path", "path": p}
        for p in unique
    ]

def load_dicom_as_bgr(path: str) -> np.ndarray:
    ds = pydicom.dcmread(path)
    arr: np.ndarray = ds.pixel_array

    if arr.dtype != np.uint8:
        arr_min = float(arr.min())
        arr_max = float(arr.max())
        denom = arr_max - arr_min + 1e-9
        arr = ((arr - arr_min) / denom * 255.0).astype(np.uint8)

    if arr.ndim == 2:
        arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
    elif arr.ndim == 3 and arr.shape[2] == 1:
        arr = cv2.cvtColor(arr[:, :, 0], cv2.COLOR_GRAY2BGR)

    return arr


def load_image_as_bgr(path: str) -> np.ndarray | None:
    ext = Path(path).suffix.lower()

    try:
        if ext == ".dcm":
            return load_dicom_as_bgr(path)

        img = cv2.imread(path)
        return img

    except Exception:
        return None


def dicom_to_temp_png(path: str) -> str:
    bgr = load_dicom_as_bgr(path)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp.close()
    cv2.imwrite(tmp.name, bgr)
    return tmp.name
