"""
DICOM Handler Module
Handles loading and processing DICOM files for the radiology reader application.
Uses pydicom metadata and renders viewer-style overlays into image data.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
import pydicom


class DicomHandler:
    """Handles DICOM loading, metadata extraction, and overlay rendering."""

    @staticmethod
    def _safe_get_attr(ds: Any, attr_name: str, default: str = "") -> str:
        """Safely get a DICOM attribute value."""
        try:
            if hasattr(ds, attr_name):
                value = getattr(ds, attr_name)
                if value is not None:
                    return str(value).strip()
        except Exception:
            pass
        return default

    @staticmethod
    def _format_dicom_date(date_str: str) -> str:
        """Convert DICOM date format (YYYYMMDD) to YYYY-MM-DD."""
        if not date_str or len(date_str) < 8:
            return ""
        try:
            dt = datetime.strptime(date_str[:8], "%Y%m%d")
            return dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return date_str

    @staticmethod
    def _calculate_age(birth_date: str, study_date: str) -> str:
        """Calculate age from birth and study date."""
        if not birth_date or not study_date:
            return ""
        try:
            birth = datetime.strptime(birth_date[:8], "%Y%m%d")
            study = datetime.strptime(study_date[:8], "%Y%m%d")
            age_years = study.year - birth.year
            if (study.month, study.day) < (birth.month, birth.day):
                age_years -= 1
            if age_years >= 0:
                return str(age_years)
        except (ValueError, TypeError, IndexError):
            pass
        return ""

    @staticmethod
    def _format_patient_name(ds: Any) -> str:
        """Extract and format patient name from DICOM dataset."""
        try:
            if not hasattr(ds, "PatientName"):
                return ""
            name = ds.PatientName
            if name is None:
                return ""
            if hasattr(name, "family_name") and hasattr(name, "given_name"):
                given = str(name.given_name).strip() if name.given_name else ""
                family = str(name.family_name).strip() if name.family_name else ""
                if given and family:
                    return f"{given} {family}"
                return given or family
            return str(name).replace("^", " ").strip()
        except Exception:
            return ""

    @staticmethod
    def _format_gender(sex: str) -> str:
        """Convert DICOM sex code to readable format."""
        sex_map = {"M": "Male", "F": "Female", "O": "Other"}
        return sex_map.get(sex.upper(), sex) if sex else ""

    @staticmethod
    def _safe_scalar(value: Any) -> Optional[float]:
        """Extract first scalar value from a DICOM element."""
        try:
            if isinstance(value, pydicom.multival.MultiValue):
                if not value:
                    return None
                value = value[0]
            if isinstance(value, (list, tuple)):
                if not value:
                    return None
                value = value[0]
            return float(value)
        except Exception:
            return None

    @staticmethod
    def _select_image_frame(arr: np.ndarray) -> np.ndarray:
        """Select a single frame if a multi-frame image is provided."""
        if arr.ndim == 4:
            return arr[0]
        if arr.ndim == 3 and arr.shape[-1] not in (1, 3, 4):
            return arr[0]
        return arr

    @staticmethod
    def _apply_windowing(arr: np.ndarray, ds: Any) -> np.ndarray:
        """Apply DICOM window center/width if available."""
        if not hasattr(ds, "WindowCenter") or not hasattr(ds, "WindowWidth"):
            return arr

        wc = DicomHandler._safe_scalar(getattr(ds, "WindowCenter", None))
        ww = DicomHandler._safe_scalar(getattr(ds, "WindowWidth", None))
        if wc is None or ww is None or ww <= 1e-6:
            return arr

        arr_f = arr.astype(np.float32)
        low = wc - (ww / 2.0)
        high = wc + (ww / 2.0)
        arr_f = np.clip(arr_f, low, high)
        return arr_f

    @staticmethod
    def _normalize_to_uint8(arr: np.ndarray) -> np.ndarray:
        """Normalize any numeric image array to uint8 [0..255]."""
        arr_f = arr.astype(np.float32)
        arr_min = float(arr_f.min())
        arr_max = float(arr_f.max())
        if arr_max - arr_min < 1e-9:
            return np.zeros_like(arr_f, dtype=np.uint8)
        arr_f = ((arr_f - arr_min) / (arr_max - arr_min)) * 255.0
        return arr_f.astype(np.uint8)

    @staticmethod
    def _to_bgr(arr: np.ndarray) -> np.ndarray:
        """Convert grayscale/RGB/BGRA array to BGR for OpenCV processing."""
        if arr.ndim == 2:
            return cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
        if arr.ndim == 3 and arr.shape[2] == 1:
            return cv2.cvtColor(arr[:, :, 0], cv2.COLOR_GRAY2BGR)
        if arr.ndim == 3 and arr.shape[2] == 4:
            return cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
        if arr.ndim == 3 and arr.shape[2] == 3:
            return arr
        return cv2.cvtColor(arr.astype(np.uint8), cv2.COLOR_GRAY2BGR)

    @staticmethod
    def extract_metadata_from_dataset(ds: Any) -> dict:
        """
        Extract patient and study metadata from a loaded pydicom dataset.
        """
        metadata = {
            "patient_id": "",
            "patient_name": "",
            "patient_birth_date": "",
            "patient_birth_date_formatted": "",
            "patient_sex": "",
            "patient_sex_formatted": "",
            "patient_age": "",
            "study_date": "",
            "study_date_formatted": "",
            "study_description": "",
            "series_description": "",
            "modality": "",
            "institution": "",
            "referring_physician": "",
            "accession_number": "",
            "rows": 0,
            "columns": 0,
        }

        try:
            metadata["patient_id"] = DicomHandler._safe_get_attr(ds, "PatientID")
            metadata["patient_name"] = DicomHandler._format_patient_name(ds)

            birth_date = DicomHandler._safe_get_attr(ds, "PatientBirthDate")
            metadata["patient_birth_date"] = birth_date
            metadata["patient_birth_date_formatted"] = DicomHandler._format_dicom_date(
                birth_date
            )

            sex = DicomHandler._safe_get_attr(ds, "PatientSex")
            metadata["patient_sex"] = sex
            metadata["patient_sex_formatted"] = DicomHandler._format_gender(sex)

            study_date = DicomHandler._safe_get_attr(ds, "StudyDate")
            metadata["study_date"] = study_date
            metadata["study_date_formatted"] = DicomHandler._format_dicom_date(study_date)

            metadata["patient_age"] = DicomHandler._calculate_age(birth_date, study_date)
            if not metadata["patient_age"]:
                dicom_age = DicomHandler._safe_get_attr(ds, "PatientAge")
                if dicom_age:
                    try:
                        age_num = "".join(c for c in dicom_age if c.isdigit())
                        if age_num:
                            metadata["patient_age"] = str(int(age_num))
                    except ValueError:
                        pass

            metadata["study_description"] = DicomHandler._safe_get_attr(
                ds, "StudyDescription"
            )
            metadata["series_description"] = DicomHandler._safe_get_attr(
                ds, "SeriesDescription"
            )
            metadata["modality"] = DicomHandler._safe_get_attr(ds, "Modality")
            metadata["institution"] = DicomHandler._safe_get_attr(ds, "InstitutionName")
            metadata["referring_physician"] = DicomHandler._safe_get_attr(
                ds, "ReferringPhysicianName"
            )
            metadata["accession_number"] = DicomHandler._safe_get_attr(
                ds, "AccessionNumber"
            )

            rows_val = getattr(ds, "Rows", 0)
            cols_val = getattr(ds, "Columns", 0)
            metadata["rows"] = int(rows_val) if rows_val else 0
            metadata["columns"] = int(cols_val) if cols_val else 0
        except Exception:
            pass

        return metadata

    @staticmethod
    def extract_metadata(path: str) -> dict:
        """
        Extract patient and study metadata from a DICOM file path.
        """
        try:
            ds = pydicom.dcmread(path, force=True)
            return DicomHandler.extract_metadata_from_dataset(ds)
        except Exception:
            return {
                "patient_id": "",
                "patient_name": "",
                "patient_birth_date": "",
                "patient_birth_date_formatted": "",
                "patient_sex": "",
                "patient_sex_formatted": "",
                "patient_age": "",
                "study_date": "",
                "study_date_formatted": "",
                "study_description": "",
                "series_description": "",
                "modality": "",
                "institution": "",
                "referring_physician": "",
                "accession_number": "",
                "rows": 0,
                "columns": 0,
            }

    @staticmethod
    def _draw_overlay_line(
        image: np.ndarray,
        text: str,
        x_anchor: int,
        y_baseline: int,
        font: int,
        font_scale: float,
        thickness: int,
        align_right: bool = False,
    ) -> None:
        """Draw one text line with a dark background and subtle shadow."""
        if not text:
            return

        h, w = image.shape[:2]
        margin = 8
        bg_pad_x = 5
        bg_pad_y = 4

        (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        x = x_anchor - text_w if align_right else x_anchor
        x = max(margin, min(x, w - text_w - margin))

        y = max(text_h + margin, min(y_baseline, h - margin))
        x1 = max(0, x - bg_pad_x)
        y1 = max(0, y - text_h - bg_pad_y)
        x2 = min(w - 1, x + text_w + bg_pad_x)
        y2 = min(h - 1, y + baseline + bg_pad_y)

        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 0), -1)
        cv2.putText(
            image,
            text,
            (x + 1, y + 1),
            font,
            font_scale,
            (0, 0, 0),
            thickness + 1,
            cv2.LINE_AA,
        )
        cv2.putText(
            image,
            text,
            (x, y),
            font,
            font_scale,
            (245, 245, 245),
            thickness,
            cv2.LINE_AA,
        )

    @staticmethod
    def render_metadata_overlay(image: np.ndarray, metadata: dict) -> np.ndarray:
        """
        Render MicroDicom-style metadata text directly onto image pixels.
        """
        if image is None or image.size == 0:
            return image

        overlay = image.copy()
        h, w = overlay.shape[:2]

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = float(max(0.38, min(0.58, min(w, h) / 1100.0)))
        thickness = 1
        line_height = cv2.getTextSize("Ag", font, font_scale, thickness)[0][1] + 8
        margin = 12

        top_left_lines = [
            f"Name: {metadata.get('patient_name', '')}" if metadata.get("patient_name") else "",
            f"Patient ID: {metadata.get('patient_id', '')}" if metadata.get("patient_id") else "",
            f"DOB: {metadata.get('patient_birth_date_formatted', '')}" if metadata.get("patient_birth_date_formatted") else "",
            f"Sex: {metadata.get('patient_sex_formatted', '') or metadata.get('patient_sex', '')}" if (metadata.get("patient_sex_formatted") or metadata.get("patient_sex")) else "",
            f"Study Date: {metadata.get('study_date_formatted', '')}" if metadata.get("study_date_formatted") else "",
        ]
        top_left_lines = [line for line in top_left_lines if line]

        top_right_lines = [
            f"Institution: {metadata.get('institution', '')}" if metadata.get("institution") else "",
            f"Modality: {metadata.get('modality', '')}" if metadata.get("modality") else "",
            f"Ref. Physician: {metadata.get('referring_physician', '')}" if metadata.get("referring_physician") else "",
            f"Accession: {metadata.get('accession_number', '')}" if metadata.get("accession_number") else "",
        ]
        top_right_lines = [line for line in top_right_lines if line]

        bottom_left_lines = [
            f"Study: {metadata.get('study_description', '')}" if metadata.get("study_description") else "",
            f"Series: {metadata.get('series_description', '')}" if metadata.get("series_description") else "",
            f"Age: {metadata.get('patient_age', '')}" if metadata.get("patient_age") else "",
        ]
        bottom_left_lines = [line for line in bottom_left_lines if line]

        bottom_right_lines = [f"Size: {w} x {h}"]
        if metadata.get("rows") and metadata.get("columns"):
            bottom_right_lines.append(
                f"DICOM Matrix: {metadata.get('columns')} x {metadata.get('rows')}"
            )

        y = margin + line_height
        for line in top_left_lines:
            DicomHandler._draw_overlay_line(
                overlay, line, margin, y, font, font_scale, thickness, align_right=False
            )
            y += line_height

        y = margin + line_height
        for line in top_right_lines:
            DicomHandler._draw_overlay_line(
                overlay,
                line,
                w - margin,
                y,
                font,
                font_scale,
                thickness,
                align_right=True,
            )
            y += line_height

        if bottom_left_lines:
            y = h - margin - (line_height * (len(bottom_left_lines) - 1))
            for line in bottom_left_lines:
                DicomHandler._draw_overlay_line(
                    overlay,
                    line,
                    margin,
                    y,
                    font,
                    font_scale,
                    thickness,
                    align_right=False,
                )
                y += line_height

        y = h - margin - (line_height * (len(bottom_right_lines) - 1))
        for line in bottom_right_lines:
            DicomHandler._draw_overlay_line(
                overlay,
                line,
                w - margin,
                y,
                font,
                font_scale,
                thickness,
                align_right=True,
            )
            y += line_height

        return overlay

    @staticmethod
    def load_dicom(path: str, include_overlay: bool = True) -> Optional[np.ndarray]:
        """
        Load a DICOM file and return BGR numpy array.
        If include_overlay=True, metadata text is rendered on the image itself.
        """
        if not Path(path).exists():
            return None

        try:
            ds = pydicom.dcmread(path, force=True)
            arr = np.asarray(ds.pixel_array)
            arr = DicomHandler._select_image_frame(arr)
            arr = DicomHandler._apply_windowing(arr, ds)
            arr = DicomHandler._normalize_to_uint8(arr)

            photometric = str(getattr(ds, "PhotometricInterpretation", "")).upper()
            if photometric == "MONOCHROME1":
                arr = 255 - arr

            image_bgr = DicomHandler._to_bgr(arr)
            if include_overlay:
                metadata = DicomHandler.extract_metadata_from_dataset(ds)
                image_bgr = DicomHandler.render_metadata_overlay(image_bgr, metadata)
            return image_bgr
        except Exception:
            return None

    @staticmethod
    def load_image(path: str, include_overlay: bool = True) -> Optional[np.ndarray]:
        """
        Load any image file as BGR numpy array.
        For DICOM files, include_overlay controls metadata text rendering.
        """
        if not Path(path).exists():
            return None

        lower_path = path.lower()
        if lower_path.endswith((".dcm", ".dicom")) or DicomHandler._is_dicom_file(path):
            dicom = DicomHandler.load_dicom(path, include_overlay=include_overlay)
            if dicom is not None:
                return dicom

        img = cv2.imread(path)
        if img is not None:
            return img

        dicom = DicomHandler.load_dicom(path, include_overlay=include_overlay)
        if dicom is not None:
            return dicom

        try:
            with open(path, "rb") as f:
                data = f.read()
            img = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img is not None:
                return img
            img = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
            if img is not None:
                if img.ndim == 2:
                    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                if img.ndim == 3 and img.shape[2] == 4:
                    return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                return img
        except Exception:
            pass

        return None

    @staticmethod
    def _is_dicom_file(path: str) -> bool:
        """Check if a file is a DICOM file by reading its header."""
        try:
            with open(path, "rb") as f:
                f.seek(128)
                magic = f.read(4)
                return magic == b"DICM"
        except Exception:
            return False

    @staticmethod
    def get_patient_info(path: str) -> dict:
        """Get simplified patient info from DICOM metadata."""
        metadata = DicomHandler.extract_metadata(path)
        return {
            "patient_id": metadata["patient_id"],
            "name": metadata["patient_name"],
            "age": metadata["patient_age"],
            "gender": metadata["patient_sex_formatted"] or metadata["patient_sex"],
            "exam_date": metadata["study_date_formatted"] or metadata["study_date"],
            "study_description": metadata["study_description"],
            "modality": metadata["modality"],
            "institution": metadata["institution"],
        }

    @staticmethod
    def dicom_to_temp_png(path: str, include_overlay: bool = True) -> Optional[str]:
        """Convert DICOM to temporary PNG, optionally with rendered metadata overlay."""
        bgr = DicomHandler.load_dicom(path, include_overlay=include_overlay)
        if bgr is None:
            return None

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp.close()
        cv2.imwrite(tmp.name, bgr)
        return tmp.name

    @staticmethod
    def is_supported(path: str) -> bool:
        """Check if a file can be loaded as an image."""
        if not Path(path).exists():
            return False
        return True
