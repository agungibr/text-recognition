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
        return np.clip(arr_f, low, high)

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
    def _overlay_style(image: np.ndarray) -> dict:
        """Compute dynamic overlay text style based on image resolution."""
        h, w = image.shape[:2]
        base = float(max(1, min(h, w)))
        font_scale = max(0.42, min(0.95, base / 1200.0))
        thickness = 1 if font_scale < 0.7 else 2
        line_gap = max(6, int(10 * font_scale))
        pad_x = max(7, int(12 * font_scale))
        pad_y = max(6, int(10 * font_scale))
        margin = max(10, int(16 * font_scale))
        return {
            "font": cv2.FONT_HERSHEY_SIMPLEX,
            "font_scale": font_scale,
            "thickness": thickness,
            "line_gap": line_gap,
            "pad_x": pad_x,
            "pad_y": pad_y,
            "margin": margin,
        }

    @staticmethod
    def _block_size(
        image: np.ndarray,
        lines: list[str],
        font_scale: Optional[float] = None,
        thickness: Optional[int] = None,
    ) -> tuple[int, int]:
        """Calculate text block width/height for layout placement."""
        style = DicomHandler._overlay_style(image)
        font = style["font"]
        fs = font_scale if font_scale is not None else style["font_scale"]
        th = thickness if thickness is not None else style["thickness"]
        line_gap = style["line_gap"]
        pad_x = style["pad_x"]
        pad_y = style["pad_y"]

        filtered = [line for line in lines if line]
        if not filtered:
            return 0, 0

        widths = []
        heights = []
        for line in filtered:
            (tw, th_line), _ = cv2.getTextSize(line, font, fs, th)
            widths.append(tw)
            heights.append(th_line)

        max_w = max(widths)
        max_h = max(heights)
        line_step = max_h + line_gap
        block_w = max_w + (2 * pad_x)
        block_h = (2 * pad_y) + (line_step * len(filtered)) - line_gap
        return int(block_w), int(block_h)

    @staticmethod
    def draw_text_block(
        image: np.ndarray,
        lines: list[str],
        x: int,
        y: int,
        align_right: bool = False,
        font_scale: Optional[float] = None,
        thickness: Optional[int] = None,
    ) -> np.ndarray:
        """
        Draw a grouped multi-line text block with solid black background.
        """
        if image is None or image.size == 0:
            return image

        filtered = [line for line in lines if line]
        if not filtered:
            return image

        style = DicomHandler._overlay_style(image)
        font = style["font"]
        fs = font_scale if font_scale is not None else style["font_scale"]
        th = thickness if thickness is not None else style["thickness"]
        line_gap = style["line_gap"]
        pad_x = style["pad_x"]
        pad_y = style["pad_y"]
        margin = style["margin"]

        h, w = image.shape[:2]
        block_w, block_h = DicomHandler._block_size(image, filtered, fs, th)
        if block_w <= 0 or block_h <= 0:
            return image

        x1 = x - block_w if align_right else x
        x1 = max(margin, min(x1, w - block_w - margin))
        y1 = max(margin, min(y, h - block_h - margin))
        x2 = x1 + block_w
        y2 = y1 + block_h

        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 0), -1)

        line_sizes = [cv2.getTextSize(line, font, fs, th)[0] for line in filtered]
        max_text_h = max(sz[1] for sz in line_sizes)
        line_step = max_text_h + line_gap
        text_y = y1 + pad_y + max_text_h
        text_x = x1 + pad_x

        for line in filtered:
            cv2.putText(
                image,
                line,
                (text_x, text_y),
                font,
                fs,
                (255, 255, 255),
                th,
                cv2.LINE_AA,
            )
            text_y += line_step

        return image

    @staticmethod
    def extract_metadata_from_dataset(ds: Any) -> dict:
        """Extract patient and study metadata from a loaded pydicom dataset."""
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
        """Extract patient and study metadata from a DICOM file path."""
        empty = {
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
            ds = pydicom.dcmread(path, force=True)
            return DicomHandler.extract_metadata_from_dataset(ds)
        except Exception:
            return empty

    @staticmethod
    def render_metadata_overlay(image: np.ndarray, metadata: dict) -> np.ndarray:
        """Render MicroDicom-style metadata blocks directly onto image pixels."""
        if image is None or image.size == 0:
            return image

        overlay = image.copy()
        style = DicomHandler._overlay_style(overlay)
        margin = style["margin"]
        fs = style["font_scale"]
        th = style["thickness"]
        h, w = overlay.shape[:2]

        top_left_lines = [
            f"Name: {metadata.get('patient_name', '')}" if metadata.get("patient_name") else "",
            f"Patient ID: {metadata.get('patient_id', '')}" if metadata.get("patient_id") else "",
            (
                f"Birth Date: {metadata.get('patient_birth_date_formatted', '')}"
                if metadata.get("patient_birth_date_formatted")
                else ""
            ),
            (
                f"Gender: {metadata.get('patient_sex_formatted', '') or metadata.get('patient_sex', '')}"
                if (metadata.get("patient_sex_formatted") or metadata.get("patient_sex"))
                else ""
            ),
            (
                f"Study Date: {metadata.get('study_date_formatted', '')}"
                if metadata.get("study_date_formatted")
                else ""
            ),
        ]
        top_left_lines = [line for line in top_left_lines if line]

        top_right_lines = [
            f"Institution: {metadata.get('institution', '')}" if metadata.get("institution") else "",
            f"Modality: {metadata.get('modality', '')}" if metadata.get("modality") else "",
            (
                f"Ref Physician: {metadata.get('referring_physician', '')}"
                if metadata.get("referring_physician")
                else ""
            ),
            (
                f"Accession: {metadata.get('accession_number', '')}"
                if metadata.get("accession_number")
                else ""
            ),
        ]
        top_right_lines = [line for line in top_right_lines if line]

        bottom_left_lines = []
        if metadata.get("study_description"):
            bottom_left_lines.append(f"Study: {metadata.get('study_description', '')}")
        if metadata.get("series_description"):
            bottom_left_lines.append(f"Series: {metadata.get('series_description', '')}")
        if metadata.get("patient_age"):
            bottom_left_lines.append(f"Age: {metadata.get('patient_age', '')}")

        bottom_right_lines = [f"Size: {w} x {h}"]
        if metadata.get("rows") and metadata.get("columns"):
            bottom_right_lines.append(
                f"Matrix: {metadata.get('columns')} x {metadata.get('rows')}"
            )

        if top_left_lines:
            DicomHandler.draw_text_block(
                overlay,
                top_left_lines,
                x=margin,
                y=margin,
                align_right=False,
                font_scale=fs,
                thickness=th,
            )

        if top_right_lines:
            DicomHandler.draw_text_block(
                overlay,
                top_right_lines,
                x=w - margin,
                y=margin,
                align_right=True,
                font_scale=fs,
                thickness=th,
            )

        if bottom_left_lines:
            _, block_h = DicomHandler._block_size(overlay, bottom_left_lines, fs, th)
            DicomHandler.draw_text_block(
                overlay,
                bottom_left_lines,
                x=margin,
                y=max(margin, h - margin - block_h),
                align_right=False,
                font_scale=fs,
                thickness=th,
            )

        if bottom_right_lines:
            _, block_h = DicomHandler._block_size(overlay, bottom_right_lines, fs, th)
            DicomHandler.draw_text_block(
                overlay,
                bottom_right_lines,
                x=w - margin,
                y=max(margin, h - margin - block_h),
                align_right=True,
                font_scale=fs,
                thickness=th,
            )

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
        except Exception as e:
            print(f"Error loading DICOM {path}: {e}")
            import traceback
            traceback.print_exc()
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
    def get_overlay_text(path: str) -> dict:
        """Extract overlay metadata organized for 4-corner display like MicroDICOM.
        
        Returns dict with keys: 'top_left', 'top_right', 'bottom_left', 'bottom_right'
        Each containing a list of text lines to display in that corner.
        """
        if not Path(path).exists():
            return {'top_left': [], 'top_right': [], 'bottom_left': [], 'bottom_right': []}
        
        try:
            ds = pydicom.dcmread(path, force=True)
            
            # Extract metadata with safe access
            name = DicomHandler._safe_get_attr(ds, "PatientName", "").strip() or "Unknown"
            patient_id = DicomHandler._safe_get_attr(ds, "PatientID", "").strip() or ""
            birth_date = DicomHandler._format_dicom_date(DicomHandler._safe_get_attr(ds, "PatientBirthDate", ""))
            gender = DicomHandler._format_gender(DicomHandler._safe_get_attr(ds, "PatientSex", ""))
            study_desc = DicomHandler._safe_get_attr(ds, "StudyDescription", "").strip() or ""
            
            institution = DicomHandler._safe_get_attr(ds, "InstitutionName", "").strip() or ""
            manufacturer = DicomHandler._safe_get_attr(ds, "Manufacturer", "").strip() or ""
            manufacturer_model = DicomHandler._safe_get_attr(ds, "ManufacturerModelName", "").strip() or ""
            referring_physician = DicomHandler._safe_get_attr(ds, "ReferringPhysicianName", "").strip() or ""
            
            study_date = DicomHandler._format_dicom_date(DicomHandler._safe_get_attr(ds, "StudyDate", ""))
            study_time = DicomHandler._safe_get_attr(ds, "StudyTime", "").strip() or ""
            
            # Format study time HHmmss.ffffff -> HH:mm:ss
            if study_time and len(study_time) >= 6:
                study_time = f"{study_time[0:2]}:{study_time[2:4]}:{study_time[4:6]}"
            
            # Get transfer syntax and other info
            transfer_syntax = "Unknown"
            try:
                ts = ds.file_meta.TransferSyntaxUID
                if "LittleEndian" in str(ts):
                    transfer_syntax = "LittleEndianImplicit"
                elif "BigEndian" in str(ts):
                    transfer_syntax = "BigEndianImplicit"
                else:
                    transfer_syntax = str(ts).split(".")[-1][:20]
            except:
                pass
            
            # Get exposure parameters
            exposure_time = DicomHandler._safe_get_attr(ds, "ExposureTime", "").strip() or ""
            xray_current = DicomHandler._safe_get_attr(ds, "XRayTubeCurrent", "").strip() or ""
            kvp = DicomHandler._safe_get_attr(ds, "KVP", "").strip() or ""
            
            # Pixel spacing
            pixel_spacing = "PX"
            try:
                ps = ds.PixelSpacing
                if ps:
                    pixel_spacing = f"PX: {ps[0]}"
            except:
                pass
            
            overlay_dict = {
                'top_left': [
                    name,
                    patient_id,
                    f"{birth_date} {gender}".strip(),
                    study_desc
                ],
                'top_right': [
                    institution,
                    manufacturer_model,
                    referring_physician,
                    f"{study_date} {study_time}".strip()
                ],
                'bottom_left': [
                    "ST: 0.00 mm",
                    pixel_spacing,
                    transfer_syntax,
                    "Images: 1/1"
                ],
                'bottom_right': []  # Will be filled with dynamic data (zoom, WL, WW)
            }
            
            # Add exposure parameters if available
            if xray_current or kvp:
                voltage_str = ""
                if xray_current:
                    voltage_str += f"{xray_current} mA"
                if kvp:
                    if voltage_str:
                        voltage_str += f" {kvp} kV"
                    else:
                        voltage_str = f"{kvp} kV"
                overlay_dict['bottom_right'].append(voltage_str)
            
            return overlay_dict
        except Exception as e:
            return {'top_left': [], 'top_right': [], 'bottom_left': [], 'bottom_right': []}

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
        return Path(path).exists()
