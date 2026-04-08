"""
Dose Calculator Module

Provides dose estimation for radiology examinations based on patient
characteristics and examination parameters.
"""

from typing import Optional


class DoseCalculator:
    """
    Calculate estimated radiation dose based on patient data and examination type.

    This is a simplified model for demonstration purposes.
    Actual clinical dose calculations require calibrated equipment and
    examination-specific protocols.
    """

    # Typical dose conversion factors (mSv per unit)
    # Based on typical adult CT dose estimates
    DOSE_FACTORS = {
        "CT_HEAD": 2.0,  # mSv
        "CT_CHEST": 7.0,  # mSv
        "CT_ABDOMEN": 10.0,  # mSv
        "CT_PELVIS": 8.0,  # mSv
        "XRAY_CHEST": 0.1,  # mSv
        "XRAY_SPINE": 1.5,  # mSv
        "XRAY_ABDOMEN": 0.7,  # mSv
        "MAMMOGRAPHY": 0.4,  # mSv
        "DEFAULT": 5.0,  # mSv
    }

    # Weight adjustment factors
    # Dose increases approximately linearly with patient size
    WEIGHT_FACTORS = {
        "pediatric_under_10": 0.3,
        "pediatric_under_18": 0.6,
        "normal_adult": 1.0,
        "overweight": 1.2,
        "obese": 1.5,
    }

    @staticmethod
    def calculate_age_bucket(age: int) -> str:
        """
        Categorize patient age into bucket.

        Args:
            age: Patient age in years.

        Returns:
            Age category string.
        """
        if age < 10:
            return "pediatric_under_10"
        elif age < 18:
            return "pediatric_under_18"
        else:
            return "normal_adult"

    @staticmethod
    def calculate_weight_factor(weight_kg: float) -> float:
        """
        Calculate weight adjustment factor.

        Args:
            weight_kg: Patient weight in kilograms.

        Returns:
            Weight adjustment multiplier.
        """
        if weight_kg < 20:
            return 0.3
        elif weight_kg < 40:
            return 0.5
        elif weight_kg < 60:
            return 0.8
        elif weight_kg < 80:
            return 1.0
        elif weight_kg < 100:
            return 1.2
        else:
            return 1.5

    @classmethod
    def estimate_dose(
        cls,
        age: int,
        gender: str,
        weight_kg: float,
        exam_type: str = "DEFAULT",
        protocol: str = "standard",
    ) -> dict:
        """
        Estimate radiation dose for an examination.

        Args:
            age: Patient age in years.
            gender: Patient gender (M/F/Other).
            weight_kg: Patient weight in kilograms.
            exam_type: Type of examination (e.g., CT_HEAD, XRAY_CHEST).
            protocol: Protocol modifier (standard, low_dose, high_resolution).

        Returns:
            Dictionary containing dose estimate and relevant factors.
        """
        # Get base dose factor
        base_dose = cls.DOSE_FACTORS.get(exam_type, cls.DOSE_FACTORS["DEFAULT"])

        # Apply age factor
        age_bucket = cls.calculate_age_bucket(age)
        age_factor = cls.WEIGHT_FACTORS.get(age_bucket, 1.0)

        # Apply weight factor
        weight_factor = cls.calculate_weight_factor(weight_kg)

        # Gender adjustment (minor differences in typical dose)
        gender_factor = 1.0
        if gender.upper() == "F":
            gender_factor = 0.95  # Slightly lower for female patients

        # Protocol adjustment
        protocol_factors = {
            "low_dose": 0.5,
            "standard": 1.0,
            "high_resolution": 1.3,
            "screening": 0.7,
        }
        protocol_factor = protocol_factors.get(protocol, 1.0)

        # Calculate final dose
        estimated_dose = (
            base_dose * age_factor * weight_factor * gender_factor * protocol_factor
        )

        return {
            "estimated_dose_mSv": round(estimated_dose, 2),
            "base_dose": base_dose,
            "age_factor": round(age_factor, 2),
            "weight_factor": round(weight_factor, 2),
            "gender_factor": round(gender_factor, 2),
            "protocol_factor": round(protocol_factor, 2),
            "exam_type": exam_type,
            "weight_kg": weight_kg,
            "age": age,
            "gender": gender,
        }

    @classmethod
    def get_dose_comparison(cls, dose_mSv: float) -> dict:
        """
        Compare estimated dose to natural background radiation.

        Args:
            dose_mSv: Estimated dose in millisieverts.

        Returns:
            Dictionary with comparison data.
        """
        annual_background = 2.4  # mSv per year (average)

        return {
            "dose_mSv": dose_mSv,
            "equivalent_days_of_background": round(
                dose_mSv / annual_background * 365, 1
            ),
            "equivalent_chest_xrays": round(dose_mSv / 0.1, 1),
            "air_travel_hours": round(
                dose_mSv / 0.005 * 60, 0
            ),  # ~0.005 mSv per hour at altitude
        }

    @classmethod
    def format_dose_result(cls, result: dict) -> str:
        """
        Format dose result as human-readable string.

        Args:
            result: Dose calculation result dictionary.

        Returns:
            Formatted string with dose information.
        """
        dose = result["estimated_dose_mSv"]
        comparison = cls.get_dose_comparison(dose)

        return (
            f"Estimated Dose: {dose} mSv\n"
            f"Equivalent to {comparison['equivalent_days_of_background']} days of natural background\n"
            f"Equivalent to ~{comparison['equivalent_chest_xrays']} chest X-rays"
        )
