"""
DICOM Handler Module
Handles loading and processing DICOM files for the radiology reader application.
"""

import tempfile
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import pydicom


class DicomHandler:
    """Handles DICOM file loading and metadata extraction."""

    @staticmethod
    def load_dicom(path: str) -> Optional[np.ndarray]:
        """
        Load a DICOM file and return it as a BGR numpy array.

        Args:
            path: Path to the DICOM file.

        Returns:
            BGR numpy array of the image, or None if loading fails.
        """
        if not Path(path).exists():
            return None

        try:
            ds = pydicom.dcmread(path)
            arr: np.ndarray = ds.pixel_array

            # Normalize to uint8 if needed
            if arr.dtype != np.uint8:
                arr_min = float(arr.min())
                arr_max = float(arr.max())
                denom = arr_max - arr_min + 1e-9
                arr = ((arr - arr_min) / denom * 255.0).astype(np.uint8)

            # Convert grayscale to BGR
            if arr.ndim == 2:
                arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
            elif arr.ndim == 3 and arr.shape[2] == 1:
                arr = cv2.cvtColor(arr[:, :, 0], cv2.COLOR_GRAY2BGR)

            return arr

        except Exception:
            return None

    @staticmethod
    def load_image(path: str) -> Optional[np.ndarray]:
        """
        Load any image file as BGR numpy array.
        Tries multiple methods to handle various file formats.

        Args:
            path: Path to the image file.

        Returns:
            BGR numpy array or None if loading fails.
        """
        if not Path(path).exists():
            return None

        # Try standard image formats first
        img = cv2.imread(path)
        if img is not None:
            return img

        # Try DICOM format
        dicom = DicomHandler.load_dicom(path)
        if dicom is not None:
            return dicom

        # Try reading raw bytes and decoding
        try:
            with open(path, "rb") as f:
                data = f.read()
            # Try to decode as image using cv2 with different flags
            img = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img is not None:
                return img
            img = cv2.imdecode(
                np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_UNCHANGED
            )
            if img is not None:
                # Convert to BGR if grayscale
                if img.ndim == 2:
                    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                elif img.ndim == 3 and img.shape[2] == 4:
                    return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                return img
        except Exception:
            pass

        return None

    @staticmethod
    def extract_metadata(path: str) -> dict:
        """
        Extract patient and study metadata from a DICOM file.
        Returns empty metadata for non-DICOM files.

        Args:
            path: Path to the file.

        Returns:
            Dictionary containing extracted metadata.
        """
        metadata = {
            "patient_id": "",
            "patient_name": "",
            "patient_birth_date": "",
            "patient_sex": "",
            "study_date": "",
            "study_description": "",
            "modality": "",
            "institution": "",
            "rows": 0,
            "columns": 0,
        }

        try:
            ds = pydicom.dcmread(path)

            # Patient Information
            if hasattr(ds, "PatientID"):
                metadata["patient_id"] = str(ds.PatientID)
            if hasattr(ds, "PatientName"):
                name = ds.PatientName
                if hasattr(name, "family_name"):
                    metadata["patient_name"] = (
                        f"{name.given_name} {name.family_name}".strip()
                    )
                else:
                    metadata["patient_name"] = str(name)
            if hasattr(ds, "PatientBirthDate"):
                metadata["patient_birth_date"] = str(ds.PatientBirthDate)
            if hasattr(ds, "PatientSex"):
                metadata["patient_sex"] = str(ds.PatientSex)

            # Study Information
            if hasattr(ds, "StudyDate"):
                metadata["study_date"] = str(ds.StudyDate)
            if hasattr(ds, "StudyDescription"):
                metadata["study_description"] = str(ds.StudyDescription)
            if hasattr(ds, "Modality"):
                metadata["modality"] = str(ds.Modality)
            if hasattr(ds, "InstitutionName"):
                metadata["institution"] = str(ds.InstitutionName)

            # Image Dimensions
            if hasattr(ds, "Rows"):
                metadata["rows"] = int(ds.Rows)
            if hasattr(ds, "Columns"):
                metadata["columns"] = int(ds.Columns)

        except Exception:
            pass

        return metadata

    @staticmethod
    def get_patient_info(path: str) -> dict:
        """
        Get simplified patient info from DICOM.
        Returns empty values for non-DICOM files.

        Args:
            path: Path to the file.

        Returns:
            Dictionary with patient_id, name, age, gender, exam_date.
        """
        metadata = DicomHandler.extract_metadata(path)

        # Calculate age from birth date and study date if available
        age = ""
        if metadata["patient_birth_date"] and metadata["study_date"]:
            try:
                birth_year = int(metadata["patient_birth_date"][:4])
                study_year = int(metadata["study_date"][:4])
                age = str(study_year - birth_year)
            except (ValueError, IndexError):
                pass

        return {
            "patient_id": metadata["patient_id"],
            "name": metadata["patient_name"],
            "age": age,
            "gender": metadata["patient_sex"],
            "exam_date": metadata["study_date"],
        }

    @staticmethod
    def dicom_to_temp_png(path: str) -> Optional[str]:
        """
        Convert DICOM to temporary PNG file.

        Args:
            path: Path to the DICOM file.

        Returns:
            Path to the temporary PNG file, or None if conversion fails.
        """
        bgr = DicomHandler.load_dicom(path)
        if bgr is None:
            return None

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp.close()
        cv2.imwrite(tmp.name, bgr)
        return tmp.name

    @staticmethod
    def is_supported(path: str) -> bool:
        """
        Check if a file can be loaded as an image.
        Returns True for any file - we'll attempt to load it.
        """
        if not Path(path).exists():
            return False
        return True
