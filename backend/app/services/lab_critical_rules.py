"""Deterministic clinical critical result detection rules for laboratory diagnostics."""
import re
from typing import Optional, Tuple
from app.models.lab import ResultFlag


CRITICAL_THRESHOLDS = {
    "GLUCOSE": {
        "critical_low": 50.0,
        "normal_low": 70.0,
        "normal_high": 99.0,
        "critical_high": 400.0,
        "unit": "mg/dL",
    },
    "POTASSIUM": {
        "critical_low": 2.8,
        "normal_low": 3.5,
        "normal_high": 5.0,
        "critical_high": 6.0,
        "unit": "mmol/L",
    },
    "SODIUM": {
        "critical_low": 120.0,
        "normal_low": 135.0,
        "normal_high": 145.0,
        "critical_high": 160.0,
        "unit": "mmol/L",
    },
    "HEMOGLOBIN": {
        "critical_low": 7.0,
        "normal_low": 12.0,
        "normal_high": 17.5,
        "critical_high": 20.0,
        "unit": "g/dL",
    },
    "PLATELETS": {
        "critical_low": 20.0,  # 20 x10^3/uL
        "normal_low": 150.0,
        "normal_high": 450.0,
        "critical_high": 1000.0,
        "unit": "x10^3/uL",
    },
    "WBC": {
        "critical_low": 2.0,
        "normal_low": 4.5,
        "normal_high": 11.0,
        "critical_high": 30.0,
        "unit": "x10^3/uL",
    },
    "CALCIUM": {
        "critical_low": 6.5,
        "normal_low": 8.5,
        "normal_high": 10.5,
        "critical_high": 13.0,
        "unit": "mg/dL",
    },
    "CREATININE": {
        "critical_low": None,
        "normal_low": 0.6,
        "normal_high": 1.3,
        "critical_high": 5.0,
        "unit": "mg/dL",
    },
    "TROPONIN": {
        "critical_low": None,
        "normal_low": 0.0,
        "normal_high": 0.04,
        "critical_high": 0.04,
        "unit": "ng/mL",
    },
    "INR": {
        "critical_low": None,
        "normal_low": 0.8,
        "normal_high": 1.2,
        "critical_high": 4.5,
        "unit": "ratio",
    },
}


def evaluate_result_flag(
    test_code: str,
    test_name: str,
    numeric_value: Optional[float],
    text_value: Optional[str] = None,
    custom_reference_range: Optional[str] = None,
) -> Tuple[ResultFlag, bool, str]:
    """
    Deterministically calculate diagnostic result flag and identify life-threatening critical values.
    Returns: (ResultFlag, is_critical: bool, explanation: str)
    """
    # 1. Check qualitative text-based critical keywords
    if text_value:
        norm_text = text_value.strip().upper()
        if any(term in norm_text for term in ["POSITIVE FOR MALIGNANCY", "HIGHLY REACTIVE", "CRITICAL POSITIVE"]):
            return ResultFlag.CRITICAL, True, f"Qualitative text finding '{text_value}' indicates critical clinical hazard."
        if any(term in norm_text for term in ["POSITIVE", "REACTIVE", "ABNORMAL"]):
            return ResultFlag.HIGH, False, f"Qualitative finding '{text_value}' is outside normal reference bounds."

    if numeric_value is None:
        return ResultFlag.NORMAL, False, "Non-numeric qualitative result entered within acceptable parameters."

    val = float(numeric_value)
    name_code = f"{test_code.upper()} {test_name.upper()}"

    # Match test against known clinical panic threshold configurations
    matched_key = None
    if "GLUCOSE" in name_code or "GLU" in name_code or "FBS" in name_code or "RBS" in name_code:
        matched_key = "GLUCOSE"
    elif "POTASSIUM" in name_code or " K " in f" {name_code} " or name_code.startswith("K-"):
        matched_key = "POTASSIUM"
    elif "SODIUM" in name_code or " NA " in f" {name_code} " or name_code.startswith("NA-"):
        matched_key = "SODIUM"
    elif "HEMOGLOBIN" in name_code or "HGB" in name_code or "HB" in name_code:
        matched_key = "HEMOGLOBIN"
    elif "PLATELET" in name_code or "PLT" in name_code:
        # Scale if platelets entered as raw count (e.g. 150000 -> 150)
        if val > 5000:
            val = val / 1000.0
        matched_key = "PLATELETS"
    elif "WBC" in name_code or "LEUKOCYTE" in name_code or "WHITE BLOOD" in name_code:
        if val > 500:
            val = val / 1000.0
        matched_key = "WBC"
    elif "CALCIUM" in name_code:
        matched_key = "CALCIUM"
    elif "CREATININE" in name_code:
        matched_key = "CREATININE"
    elif "TROPONIN" in name_code or "TROP" in name_code:
        matched_key = "TROPONIN"
    elif "INR" in name_code or "PROTHROMBIN" in name_code:
        matched_key = "INR"

    if matched_key and matched_key in CRITICAL_THRESHOLDS:
        cfg = CRITICAL_THRESHOLDS[matched_key]
        crit_low = cfg.get("critical_low")
        crit_high = cfg.get("critical_high")
        norm_low = cfg.get("normal_low")
        norm_high = cfg.get("normal_high")

        # 1. Critical Low check
        if crit_low is not None and val < crit_low:
            return (
                ResultFlag.CRITICAL,
                True,
                f"CRITICAL PANIC VALUE: {val} {cfg['unit']} is dangerously below critical threshold ({crit_low} {cfg['unit']}).",
            )
        # 2. Critical High check
        if crit_high is not None and val >= crit_high:
            return (
                ResultFlag.CRITICAL,
                True,
                f"CRITICAL PANIC VALUE: {val} {cfg['unit']} is dangerously above critical threshold ({crit_high} {cfg['unit']}).",
            )
        # 3. Abnormal Low check
        if norm_low is not None and val < norm_low:
            return (
                ResultFlag.LOW,
                False,
                f"Value {val} {cfg['unit']} is below reference interval ({norm_low} - {norm_high} {cfg['unit']}).",
            )
        # 4. Abnormal High check
        if norm_high is not None and val > norm_high:
            return (
                ResultFlag.HIGH,
                False,
                f"Value {val} {cfg['unit']} is above reference interval ({norm_low} - {norm_high} {cfg['unit']}).",
            )
        return (
            ResultFlag.NORMAL,
            False,
            f"Value {val} {cfg['unit']} is within standard reference interval ({norm_low} - {norm_high} {cfg['unit']}).",
        )

    # Generic range parsing if custom reference range string provided (e.g. "12.0 - 16.0")
    if custom_reference_range:
        range_match = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", custom_reference_range)
        if range_match:
            low_bound = float(range_match.group(1))
            high_bound = float(range_match.group(2))
            if val < low_bound * 0.6:
                return ResultFlag.CRITICAL, True, f"Value {val} is critically below reference range ({custom_reference_range})."
            if val > high_bound * 2.0:
                return ResultFlag.CRITICAL, True, f"Value {val} is critically above reference range ({custom_reference_range})."
            if val < low_bound:
                return ResultFlag.LOW, False, f"Value {val} is below reference range ({custom_reference_range})."
            if val > high_bound:
                return ResultFlag.HIGH, False, f"Value {val} is above reference range ({custom_reference_range})."

    return ResultFlag.NORMAL, False, "Value is within normal physiological parameters."
