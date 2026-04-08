import glob
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pydicom

SUPPORTED_EXTENSIONS: frozenset = frozenset(
    {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tiff",
        ".tif",
        ".dcm",
    }
)


def collect_files_from_paths(paths: list[str]) -> list[dict]:
    """
    Collect supported image files from a list of paths.

    Args:
        paths: List of file paths to process

    Returns:
        List of dictionaries with file information
    """
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
        result.append(
            {
                "name": p.name,
                "type": "path",
                "path": key,
            }
        )

    return result


def collect_files_from_folder(folder: str) -> list[dict]:
    """
    Recursively collect supported image files from a folder.

    Args:
        folder: Directory path to search

    Returns:
        List of dictionaries with file information
    """
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

    return [{"name": Path(p).name, "type": "path", "path": p} for p in unique]


def load_dicom_as_bgr(path: str) -> np.ndarray:
    """
    Load a DICOM file and convert it to BGR numpy array.

    Args:
        path: Path to DICOM file

    Returns:
        BGR image as numpy array (uint8)
    """
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
    """
    Load any supported image format and return as BGR array.

    Args:
        path: Path to image file

    Returns:
        BGR image array or None if loading fails
    """
    ext = Path(path).suffix.lower()

    try:
        if ext == ".dcm":
            return load_dicom_as_bgr(path)

        img = cv2.imread(path)
        return img

    except Exception:
        return None


def dicom_to_temp_png(path: str) -> str:
    """
    Convert DICOM to temporary PNG file for processing.

    Args:
        path: Path to DICOM file

    Returns:
        Path to temporary PNG file (caller should clean up)
    """
    bgr = load_dicom_as_bgr(path)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp.close()
    cv2.imwrite(tmp.name, bgr)
    return tmp.name


def extract_dicom_metadata(path: str) -> dict:
    """
    Extract patient and study metadata from DICOM file.

    Args:
        path: Path to DICOM file

    Returns:
        Dictionary with extracted metadata fields
    """
    try:
        ds = pydicom.dcmread(path)
        return {
            "patient_id": str(getattr(ds, "PatientID", "")),
            "patient_name": str(getattr(ds, "PatientName", "")),
            "patient_birth_date": str(getattr(ds, "PatientBirthDate", "")),
            "patient_sex": str(getattr(ds, "PatientSex", "")),
            "study_date": str(getattr(ds, "StudyDate", "")),
            "study_description": str(getattr(ds, "StudyDescription", "")),
            "modality": str(getattr(ds, "Modality", "")),
            "institution_name": str(getattr(ds, "InstitutionName", "")),
        }
    except Exception:
        return {}


def save_image(image: np.ndarray, path: str) -> bool:
    """
    Save numpy image array to file.

    Args:
        image: BGR image array
        path: Output file path

    Returns:
        True if successful, False otherwise
    """
    try:
        cv2.imwrite(path, image)
        return True
    except Exception:
        return False
