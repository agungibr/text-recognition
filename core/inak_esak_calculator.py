import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
#  Default calibration constants
# ---------------------------------------------------------------------------
DEFAULT_COEFF_A: float = 0.0004
DEFAULT_COEFF_B: float = 2.5917
DEFAULT_BSF: float = 1.35

# Reference/QC limits
MAX_KVP_ERROR_PERCENT: float = 10.0
MEASUREMENT_UNCERTAINTY_PERCENT: float = 0.5
CONFIDENCE_LEVEL: float = 95.0
COVERAGE_FACTOR_K: float = 2.0
EXPANDED_UNCERTAINTY: float = COVERAGE_FACTOR_K * MEASUREMENT_UNCERTAINTY_PERCENT  # 1.0%


@dataclass
class CalibrationPoint:
    """A single kVp – mGy calibration measurement."""
    kvp: float
    mgy: float


@dataclass
class RegressionResult:
    """Result of power-regression fitting."""
    a: float
    b: float
    r_squared: float
    points_used: int


@dataclass
class INAKESAKResult:
    """Complete calculation result for y, INAK, ESAK."""
    kvp: float
    ma: float
    exposure_time_s: float
    mas: float
    y_mgy: float
    inak_mgy: float
    esak_mgy: float
    bsf: float
    coeff_a: float
    coeff_b: float
    source_kvp: str = ""       # "DICOM" or "Manual"
    source_ma: str = ""
    source_time: str = ""


class INAKESAKCalculator:
    """
    Calculator for y (dose output), INAK, and ESAK.

    Supports two workflows:
        1. Power regression from calibration data → derive a, b → compute y
        2. Direct equation with known coefficients → compute y directly
    """

    def __init__(
        self,
        coeff_a: float = DEFAULT_COEFF_A,
        coeff_b: float = DEFAULT_COEFF_B,
        bsf: float = DEFAULT_BSF,
    ):
        self.coeff_a = coeff_a
        self.coeff_b = coeff_b
        self.bsf = bsf

    # ------------------------------------------------------------------
    #  Power regression from calibration data
    # ------------------------------------------------------------------
    @staticmethod
    def fit_power_regression(
        data: List[CalibrationPoint],
    ) -> RegressionResult:
        """
        Fit y = a × x^b using log-linearised least-squares.

        Steps (matching prompt):
            1. Compute X = ln(kVp), Y = ln(mGy) for every point
            2. Linear regression Y = A + b·X
            3. a = e^A
        """
        n = len(data)
        if n < 2:
            raise ValueError("At least 2 calibration points are required.")

        # Step 3 — ln(x) and ln(y)
        xs = [math.log(p.kvp) for p in data]
        ys = [math.log(p.mgy) for p in data]

        sum_x = sum(xs)
        sum_y = sum(ys)
        sum_xy = sum(x * y for x, y in zip(xs, ys))
        sum_x2 = sum(x * x for x in xs)

        # Step 4 — slope b
        denom = n * sum_x2 - sum_x ** 2
        if abs(denom) < 1e-15:
            raise ValueError("Degenerate calibration data (identical kVp values).")
        b = (n * sum_xy - sum_x * sum_y) / denom

        # Step 5 — intercept A
        a_log = (sum_y - b * sum_x) / n

        # Step 6 — a = e^A
        a = math.exp(a_log)

        # R² calculation
        y_mean = sum_y / n
        ss_tot = sum((y - y_mean) ** 2 for y in ys)
        ss_res = sum((y - (a_log + b * x)) ** 2 for x, y in zip(xs, ys))
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-15 else 1.0

        return RegressionResult(a=a, b=b, r_squared=r_squared, points_used=n)

    def update_coefficients_from_calibration(
        self, data: List[CalibrationPoint]
    ) -> RegressionResult:
        """Run regression and update internal coefficients."""
        result = self.fit_power_regression(data)
        self.coeff_a = result.a
        self.coeff_b = result.b
        return result

    # ------------------------------------------------------------------
    #  Core calculations
    # ------------------------------------------------------------------
    def calculate_y(self, kvp: float) -> float:
        """
        Calculate dose output y (mGy).

        y = a × kVp^b
        """
        if kvp <= 0:
            raise ValueError(f"kVp must be positive, got {kvp}")
        return self.coeff_a * (kvp ** self.coeff_b)

    def calculate_inak(self, kvp: float, mas: float) -> float:
        """
        Calculate Incident Air Kerma (mGy).

        INAK = y × (mAs / 1000)
        """
        y = self.calculate_y(kvp)
        return y * (mas / 1000.0)

    def calculate_esak(self, inak: float, bsf: Optional[float] = None) -> float:
        """
        Calculate Entrance Surface Air Kerma (mGy).

        ESAK = INAK × BSF
        """
        factor = bsf if bsf is not None else self.bsf
        return inak * factor

    def calculate_all(
        self,
        kvp: float,
        ma: float,
        exposure_time_s: float,
        bsf: Optional[float] = None,
        source_kvp: str = "",
        source_ma: str = "",
        source_time: str = "",
    ) -> INAKESAKResult:
        """
        Run the complete calculation pipeline: mAs → y → INAK → ESAK.
        """
        mas = ma * exposure_time_s
        y = self.calculate_y(kvp)
        inak = self.calculate_inak(kvp, mas)
        esak = self.calculate_esak(inak, bsf)

        return INAKESAKResult(
            kvp=kvp,
            ma=ma,
            exposure_time_s=exposure_time_s,
            mas=mas,
            y_mgy=y,
            inak_mgy=inak,
            esak_mgy=esak,
            bsf=bsf if bsf is not None else self.bsf,
            coeff_a=self.coeff_a,
            coeff_b=self.coeff_b,
            source_kvp=source_kvp,
            source_ma=source_ma,
            source_time=source_time,
        )

    # ------------------------------------------------------------------
    #  DICOM extraction helpers
    # ------------------------------------------------------------------
    @staticmethod
    def extract_exposure_params(ds: Any) -> Dict[str, Optional[float]]:
        """
        Extract kVp, mA, and exposure time from a pydicom Dataset.

        Returns dict with keys: kvp, ma, exposure_time_s, mas
        Values are None when the tag is missing.

        DICOM tags used:
            (0018,0060) → KVP
            (0018,1151) → XRayTubeCurrent (mA)
            (0018,1150) → ExposureTime (ms → converted to seconds)
            (0018,1152) → Exposure (mAs, fallback)
        """
        params: Dict[str, Optional[float]] = {
            "kvp": None,
            "ma": None,
            "exposure_time_s": None,
            "mas": None,
        }

        def _safe_float(attr_name: str) -> Optional[float]:
            try:
                val = getattr(ds, attr_name, None)
                if val is None:
                    return None
                # Handle MultiValue
                if hasattr(val, '__iter__') and not isinstance(val, str):
                    val = val[0] if len(val) > 0 else None
                return float(val) if val is not None else None
            except (TypeError, ValueError, IndexError):
                return None

        # kVp — tag (0018,0060)
        params["kvp"] = _safe_float("KVP")

        # mA — tag (0018,1151)
        params["ma"] = _safe_float("XRayTubeCurrent")

        # Exposure Time — tag (0018,1150), value in ms → convert to s
        exp_ms = _safe_float("ExposureTime")
        if exp_ms is not None:
            params["exposure_time_s"] = exp_ms / 1000.0

        # Direct mAs — tag (0018,1152), fallback
        params["mas"] = _safe_float("Exposure")

        return params

    @staticmethod
    def extract_exposure_params_from_path(dicom_path: str) -> Dict[str, Optional[float]]:
        """Extract exposure parameters from a DICOM file path."""
        try:
            import pydicom
            ds = pydicom.dcmread(dicom_path, force=True)
            return INAKESAKCalculator.extract_exposure_params(ds)
        except Exception:
            return {"kvp": None, "ma": None, "exposure_time_s": None, "mas": None}


# ---------------------------------------------------------------------------
#  Module-level convenience
# ---------------------------------------------------------------------------
_default_calculator = INAKESAKCalculator()


def quick_calculate(kvp: float, ma: float, exposure_time_s: float) -> INAKESAKResult:
    """One-shot convenience with default coefficients."""
    return _default_calculator.calculate_all(kvp, ma, exposure_time_s)
