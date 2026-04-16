"""
Exposure Parser Module

Provides functions to parse OCR text from EasyOCR and DICOM metadata
to extract radiation exposure parameters and calculate mAs.
"""

import re
from typing import Optional, Tuple

from pydicom import Dataset
from pydicom.errors import InvalidDicomError


def parse_ocr_text(ocr_text: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Parse OCR text to extract mA and kVp values using Regular Expressions.

    Handles varying spaces between numbers and units, such as:
    - "6.13 mA 76.86kV"
    - "6.13mA 76.86 kV"
    - "6.13mA 76.86kV"
    - "6.13 mA  76.86 kV"

    Args:
        ocr_text: String output from EasyOCR (e.g., "6.13 mA 76.86kV").

    Returns:
        Tuple of (mA, kVp) as floats. Returns (None, None) if parsing fails.

    Examples:
        >>> parse_ocr_text("6.13 mA 76.86kV")
        (6.13, 76.86)
        >>> parse_ocr_text("100mA 120kV")
        (100.0, 120.0)
    """
    if not ocr_text or not isinstance(ocr_text, str):
        return None, None

    # Pattern to match mA (with optional spaces)
    # Matches: "mA", "ma", "mA", "MA" - with optional spaces before and after
    # The number can be integer or float
    ma_pattern = r"(\d+\.?\d*)\s*(?:mA|ma|MA|mA)"

    # Pattern to match kV/kVp (with optional spaces)
    # Matches: "kV", "kVp", "kv", "KVP" - with optional spaces
    # The number can be integer or float
    kvp_pattern = r"(\d+\.?\d*)\s*(?:kV|kVp|kv|KV|kvp|KVP)"

    # Search for mA value
    ma_match = re.search(ma_pattern, ocr_text, re.IGNORECASE)
    mA = float(ma_match.group(1)) if ma_match else None

    # Search for kVp value
    kvp_match = re.search(kvp_pattern, ocr_text, re.IGNORECASE)
    kVp = float(kvp_match.group(1)) if kvp_match else None

    return mA, kVp


def parse_dicom_exposure(dicom_path: str) -> Optional[int]:
    """
    Read a DICOM file and extract the Exposure Time from tag (0018, 1150).

    The Exposure Time tag contains the exposure time in milliseconds.

    Args:
        dicom_path: Path to the DICOM file.

    Returns:
        Exposure time in milliseconds, or None if not available.

    Raises:
        FileNotFoundError: If the DICOM file does not exist.
        InvalidDicomError: If the file is not a valid DICOM file.
    """
    try:
        import pydicom

        dcm = pydicom.dcmread(dicom_path)

        # Tag (0018, 1150) - Exposure Time
        if hasattr(dcm, "ExposureTime") and dcm.ExposureTime is not None:
            return int(dcm.ExposureTime)

        return None

    except FileNotFoundError:
        raise FileNotFoundError(f"DICOM file not found: {dicom_path}")
    except InvalidDicomError as e:
        raise InvalidDicomError(f"Invalid DICOM file: {dicom_path} - {str(e)}")


def parse_dicom_exposure_from_dataset(dicom_dataset: Dataset) -> Optional[int]:
    """
    Extract the Exposure Time from a pydicom Dataset object.

    Args:
        dicom_dataset: A pydicom Dataset object.

    Returns:
        Exposure time in milliseconds, or None if not available.
    """
    if not isinstance(dicom_dataset, Dataset):
        return None

    # Tag (0018, 1150) - Exposure Time
    if (
        hasattr(dicom_dataset, "ExposureTime")
        and dicom_dataset.ExposureTime is not None
    ):
        return int(dicom_dataset.ExposureTime)

    return None


def calculate_mas(mA: float, exposure_time_ms: int) -> Optional[float]:
    """
    Calculate total mAs (milliampere-seconds).

    The formula is: mAs = mA × (exposure_time_ms / 1000)

    Args:
        mA: Tube current in milliamperes.
        exposure_time_ms: Exposure time in milliseconds.

    Returns:
        Total mAs as a float, or None if inputs are invalid.
    """
    if mA is None or exposure_time_ms is None:
        return None

    if mA <= 0 or exposure_time_ms <= 0:
        return None

    exposure_time_s = exposure_time_ms / 1000.0
    return mA * exposure_time_s


def format_exposure_output(
    kVp: Optional[float] = None,
    mA: Optional[float] = None,
    exposure_time_ms: Optional[int] = None,
    mAs: Optional[float] = None,
) -> dict:
    """
    Format the exposure parameters into a dictionary for UI display.

    Args:
        kVp: Tube voltage in kilovolts.
        mA: Tube current in milliamperes.
        exposure_time_ms: Exposure time in milliseconds.
        mAs: Calculated milliampere-seconds.

    Returns:
        Dictionary containing all exposure parameters with formatted values.
    """
    # Convert exposure time to seconds for display
    exposure_time_s = None
    if exposure_time_ms is not None:
        exposure_time_s = exposure_time_ms / 1000.0

    return {
        "kVp": round(kVp, 2) if kVp is not None else None,
        "mA": round(mA, 2) if mA is not None else None,
        "exposure_time_ms": exposure_time_ms,
        "exposure_time_s": round(exposure_time_s, 3)
        if exposure_time_s is not None
        else None,
        "mAs": round(mAs, 2) if mAs is not None else None,
    }


def parse_exposure_from_ocr_and_dicom(ocr_text: str, dicom_path: str) -> dict:
    """
    Complete function to parse OCR text and DICOM metadata,
    then calculate and return all exposure parameters.

    Args:
        ocr_text: String output from EasyOCR (e.g., "6.13 mA 76.86kV").
        dicom_path: Path to the DICOM file.

    Returns:
        Dictionary containing kVp, mA, exposure_time_s, and calculated mAs.
        Returns dictionary with None values if parsing fails.

    Raises:
        FileNotFoundError: If the DICOM file does not exist.
        InvalidDicomError: If the file is not a valid DICOM file.
    """
    # Step 1: Parse OCR text to get mA and kVp
    mA, kVp = parse_ocr_text(ocr_text)

    # Step 2: Parse DICOM metadata to get Exposure Time
    exposure_time_ms = parse_dicom_exposure(dicom_path)

    # Step 3: Calculate mAs
    mAs = calculate_mas(mA, exposure_time_ms) if mA and exposure_time_ms else None

    # Step 4: Format and return the output
    return format_exposure_output(
        kVp=kVp, mA=mA, exposure_time_ms=exposure_time_ms, mAs=mAs
    )


def parse_exposure_from_ocr_and_dataset(ocr_text: str, dicom_dataset: Dataset) -> dict:
    """
    Complete function to parse OCR text and DICOM dataset,
    then calculate and return all exposure parameters.

    Args:
        ocr_text: String output from EasyOCR (e.g., "6.13 mA 76.86kV").
        dicom_dataset: A pydicom Dataset object.

    Returns:
        Dictionary containing kVp, mA, exposure_time_s, and calculated mAs.
        Returns dictionary with None values if parsing fails.
    """
    # Step 1: Parse OCR text to get mA and kVp
    mA, kVp = parse_ocr_text(ocr_text)

    # Step 2: Parse DICOM dataset to get Exposure Time
    exposure_time_ms = parse_dicom_exposure_from_dataset(dicom_dataset)

    # Step 3: Calculate mAs
    mAs = calculate_mas(mA, exposure_time_ms) if mA and exposure_time_ms else None

    # Step 4: Format and return the output
    return format_exposure_output(
        kVp=kVp, mA=mA, exposure_time_ms=exposure_time_ms, mAs=mAs
    )


# Example usage and testing
if __name__ == "__main__":
    # Test OCR parsing with various formats
    test_ocr_texts = [
        "6.13 mA 76.86kV",
        "6.13mA 76.86 kV",
        "100mA 120kV",
        "50 mA 80 kVp",
        "200mA 140kVp",
    ]

    print("=== Testing OCR Text Parsing ===")
    for text in test_ocr_texts:
        mA, kVp = parse_ocr_text(text)
        print(f"Input: '{text}' -> mA: {mA}, kVp: {kVp}")

    print("\n=== Testing mAs Calculation ===")
    # Test mAs calculation with example values
    test_cases = [
        (6.13, 14080),  # From your example: 6.13 mA, 14080 ms
        (100, 1000),  # 100 mA, 1 second
        (200, 500),  # 200 mA, 0.5 seconds
    ]
    for mA, exp_ms in test_cases:
        mas = calculate_mas(mA, exp_ms)
        exp_s = exp_ms / 1000
        print(f"mA: {mA}, Exposure: {exp_ms}ms ({exp_s}s) -> mAs: {mas}")

    print("\n=== Testing Output Formatting ===")
    sample_result = format_exposure_output(
        kVp=76.86, mA=6.13, exposure_time_ms=14080, mAs=86.3104
    )
    print(f"Sample output: {sample_result}")
