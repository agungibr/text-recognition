"""
Data Matcher Module

Matches extracted text data with patient records from CSV/database.
Used for cross-referencing OCR results with known patient information.
"""

import re
from typing import Optional


class DataMatcher:
    """
    Matches OCR extracted text with patient data records.

    Supports flexible matching for patient ID, name, age, gender, and other fields.
    Helps validate and enrich extracted information with known patient data.
    """

    def __init__(self):
        """Initialize the data matcher."""
        self._patient_data: list[dict] = []

    def load_patient_data(self, data: list[dict]) -> int:
        """
        Load patient data records for matching.

        Args:
            data: List of patient record dictionaries.

        Returns:
            Number of records loaded.
        """
        self._patient_data = data
        return len(data)

    def load_from_csv_records(self, records: list[dict]) -> int:
        """
        Load patient data directly from CSV records.

        Args:
            records: List of dicts from pandas/csv reading.

        Returns:
            Number of records loaded.
        """
        self._patient_data = records
        return len(records)

    def match_patient(
        self, extracted_data: dict, threshold: float = 0.7
    ) -> Optional[dict]:
        """
        Find matching patient record based on extracted data.

        Args:
            extracted_data: Dict with fields like 'patient_id', 'name', 'age', 'gender'.
            threshold: Minimum match score (0.0 to 1.0) for a valid match.

        Returns:
            Best matching patient record or None if no match found.
        """
        if not self._patient_data:
            return None

        best_match = None
        best_score = 0.0

        for record in self._patient_data:
            score = self._calculate_match_score(extracted_data, record)
            if score > best_score:
                best_score = score
                best_match = record

        if best_score >= threshold:
            return best_match

        return None

    def find_all_matches(
        self, extracted_data: dict, threshold: float = 0.5
    ) -> list[tuple[dict, float]]:
        """
        Find all patient records that match extracted data.

        Args:
            extracted_data: Dict with extracted patient information.
            threshold: Minimum match score to include.

        Returns:
            List of (patient_record, score) tuples sorted by score descending.
        """
        if not self._patient_data:
            return []

        matches = []
        for record in self._patient_data:
            score = self._calculate_match_score(extracted_data, record)
            if score >= threshold:
                matches.append((record, score))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def _calculate_match_score(self, extracted: dict, record: dict) -> float:
        """
        Calculate similarity score between extracted data and patient record.

        Args:
            extracted: Extracted data dictionary.
            record: Patient record from database.

        Returns:
            Similarity score between 0.0 and 1.0.
        """
        scores = []
        weights = []

        # Patient ID matching (highest weight)
        if extracted.get("patient_id") and record.get("patient_id"):
            weights.append(0.4)
            if self._normalize_id(extracted["patient_id"]) == self._normalize_id(
                record["patient_id"]
            ):
                scores.append(1.0)
            else:
                scores.append(0.0)

        # Name matching (medium weight)
        if extracted.get("name") and record.get("name"):
            weights.append(0.25)
            name_sim = self._name_similarity(extracted["name"], record.get("name", ""))
            scores.append(name_sim)

        # Gender matching (low weight)
        if extracted.get("gender") and record.get("gender"):
            weights.append(0.15)
            if self._normalize_gender(extracted["gender"]) == self._normalize_gender(
                record["gender"]
            ):
                scores.append(1.0)
            else:
                scores.append(0.0)

        # Age matching (low weight)
        if extracted.get("age") and record.get("age"):
            weights.append(0.2)
            try:
                age_ext = int(re.search(r"\d+", str(extracted["age"])).group())
                age_rec = int(re.search(r"\d+", str(record["age"])).group())
                if age_ext == age_rec:
                    scores.append(1.0)
                elif abs(age_ext - age_rec) <= 2:
                    scores.append(0.8)
                else:
                    scores.append(0.0)
            except (ValueError, AttributeError, TypeError):
                scores.append(0.0)
                weights[-1] = 0.1  # Reduce weight if parsing fails

        # Calculate weighted average
        if not scores or not weights:
            return 0.0

        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        return weighted_sum / total_weight

    @staticmethod
    def _normalize_id(patient_id: str) -> str:
        """Normalize patient ID for comparison."""
        return re.sub(r"[^a-zA-Z0-9]", "", str(patient_id).upper())

    @staticmethod
    def _normalize_gender(gender: str) -> str:
        """Normalize gender value for comparison."""
        g = str(gender).upper().strip()
        if g in ("M", "MALE", "MAN", "L"):
            return "M"
        if g in ("F", "FEMALE", "WOMAN", "P"):
            return "F"
        return g

    @staticmethod
    def _name_similarity(name1: str, name2: str) -> float:
        """
        Calculate similarity between two names.

        Uses basic token matching and handles common name formats.
        """
        if not name1 or not name2:
            return 0.0

        # Normalize
        n1 = name1.upper().strip()
        n2 = name2.upper().strip()

        if n1 == n2:
            return 1.0

        # Split into tokens
        tokens1 = set(re.findall(r"\b[A-Z]+\b", n1))
        tokens2 = set(re.findall(r"\b[A-Z]+\b", n2))

        if not tokens1 or not tokens2:
            return 0.0

        # Jaccard similarity on tokens
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)

        if union == 0:
            return 0.0

        return intersection / union

    def extract_patient_info(self, text: str) -> dict:
        """
        Attempt to extract patient information from raw OCR text.

        Args:
            text: Raw text from OCR.

        Returns:
            Dictionary with extracted fields.
        """
        result = {
            "patient_id": "",
            "name": "",
            "age": "",
            "gender": "",
            "exam_date": "",
        }

        # Extract Patient ID (various patterns)
        id_patterns = [
            r"Patient\s*ID[:\s]*([A-Z0-9\-]+)",
            r"ID[:\s]*([A-Z0-9\-]+)",
            r"MRN[:\s]*([A-Z0-9\-]+)",
            r"([0-9]{6,})",  # 6+ digit numbers often are IDs
        ]
        for pattern in id_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["patient_id"] = match.group(1)
                break

        # Extract Age
        age_patterns = [
            r"Age[:\s]*(\d+)",
            r"(\d+)\s*(?:yo|y\.o\.|years?\s*old)",
            r"(\d+)\s*th",
        ]
        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["age"] = match.group(1)
                break

        # Extract Gender
        gender_patterns = [
            r"Gender[:\s]*(Male|Female|M|F)",
            r"Sex[:\s]*(Male|Female|M|F)",
        ]
        for pattern in gender_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["gender"] = match.group(1)
                break

        # Extract Date
        date_patterns = [
            r"(\d{4}[-/]\d{2}[-/]\d{2})",
            r"(\d{2}[-/]\d{2}[-/]\d{4})",
            r"(\d{2}[A-Za-z]{3}\d{4})",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                result["exam_date"] = match.group(1)
                break

        # Extract Name (simplified heuristic)
        name_patterns = [
            r"Name[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            r"Patient[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                result["name"] = match.group(1)
                break

        return result

    @property
    def patient_count(self) -> int:
        """Return number of loaded patient records."""
        return len(self._patient_data)

    def clear(self) -> None:
        """Clear loaded patient data."""
        self._patient_data = []
