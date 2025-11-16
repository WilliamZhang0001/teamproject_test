from __future__ import annotations

from typing import Optional, Tuple, Dict
import re

VALIDATION_RANGES = {
    'ph': (0.0, 14.0),
    'temperature_c': (-100.0, 300.0),
    'concentration_mg_ml': (1e-9, 10000.0),
}

COMMON_MW = {
    'protein': 50000,
    'peptide': 2000,
    'antibody': 150000,
    'enzyme': 60000,
}

def validate_parameter_range(param_type: str, value: float, strict: bool = False) -> Tuple[bool, str]:
    if param_type not in VALIDATION_RANGES:
        return True, ""
    min_val, max_val = VALIDATION_RANGES[param_type]
    if param_type == 'ph':
        if value < min_val or value > max_val:
            return False, f"pH value {value} outside standard range ({min_val}-{max_val})"
    elif value < min_val:
        if strict:
            return False, f"{param_type} value {value} below reasonable range ({min_val}-{max_val})"
        allowed_min = min_val * 0.7 if min_val < 0 else min_val * 0.5
        if value >= allowed_min:
            return True, f"Warning: {param_type} value {value} slightly below typical range"
        return False, f"{param_type} value {value} far below reasonable range ({min_val}-{max_val})"
    elif value > max_val:
        if strict:
            return False, f"{param_type} value {value} above reasonable range ({min_val}-{max_val})"
        if value < max_val * 2:
            return True, f"Warning: {param_type} value {value} above typical range, may be special condition"
        return False, f"{param_type} value {value} far above reasonable range ({min_val}-{max_val})"
    return True, ""

def normalize_temperature(value: float, unit_hint: Optional[str]) -> Tuple[Optional[float], Optional[str]]:
    if not unit_hint:
        normalized = float(value)
        note = "Assumed Celsius (no unit specified)"
    else:
        unit = unit_hint.lower().strip()
        if unit.startswith("k") or "kelvin" in unit:
            normalized = float(value) - 273.15
            note = "Converted Kelvin→Celsius"
        elif unit.startswith("f") or "fahrenheit" in unit:
            normalized = (float(value) - 32) * 5/9
            note = "Converted Fahrenheit→Celsius"
        else:
            normalized = float(value)
            note = "Celsius"
    is_valid, warning = validate_parameter_range('temperature_c', normalized, strict=False)
    if not is_valid:
        return None, None
    if warning and "Warning:" in warning:
        note += f" ({warning})"
    return normalized, note

def normalize_concentration(value: float, unit: str, biomolecule_type: str = "protein") -> Tuple[Optional[float], Optional[str]]:
    u = unit.lower().replace(" ", "").replace("/", "")
    v = float(value)
    note = ""
    if "mgml" in u or "mg/ml" in unit.lower():
        normalized = v
        note = "mg/mL"
    elif any(variant in u for variant in ["µgml", "ugml", "mcgml", "μgml"]):
        normalized = v / 1000.0
        note = "Converted µg/mL→mg/mL"
    elif "ngml" in u:
        normalized = v / 1_000_000.0
        note = "Converted ng/mL→mg/mL"
    elif "gl" in u:
        normalized = v
        note = "Converted g/L→mg/mL (equivalent)"
    elif "mgl" in u:
        normalized = v / 1000.0
        note = "Converted mg/L→mg/mL"
    elif re.search(r"\bg/dl\b", unit.lower()):
        normalized = v * 10.0
        note = "Converted g/dL→mg/mL"
    elif re.search(r"\bmg/dl\b", unit.lower()):
        normalized = v / 100.0
        note = "Converted mg/dL→mg/mL"
    elif re.search(r"\bmg/(?:µ|u)l\b", unit.lower()):
        normalized = v * 1000.0
        note = "Converted mg/µL→mg/mL"
    elif re.search(r"\bg/(?:µ|u)l\b", unit.lower()):
        normalized = v * 1_000_000.0
        note = "Converted g/µL→mg/mL"
    elif u in {"m", "molar"} or re.search(r"\bmol\s*/\s*l\b|\bmol\s*l-1\b|\bmol\s*dm-3\b", unit.lower()):
        mw = COMMON_MW.get(biomolecule_type, COMMON_MW['protein'])
        normalized = v * mw / 1000.0
        note = f"Converted M→mg/mL (assumed MW={mw} Da)"
    elif u in {"mm", "millimolar"} or re.search(r"\bmmol\s*/\s*l\b|\bmmol\s*l-1\b|\bmmol\s*dm-3\b", unit.lower()):
        mw = COMMON_MW.get(biomolecule_type, COMMON_MW['protein'])
        normalized = v * mw / 1_000_000.0
        note = f"Converted mM→mg/mL (assumed MW={mw} Da)"
    elif u in {"µm", "um", "micromolar", "μm"} or re.search(r"(?:µ|μ|u)mol\s*/\s*l|(?:µ|μ|u)mol\s*l-1|(?:µ|μ|u)mol\s*dm-3", unit.lower()):
        mw = COMMON_MW.get(biomolecule_type, COMMON_MW['protein'])
        normalized = v * mw / 1_000_000_000.0
        note = f"Converted µM→mg/mL (assumed MW={mw} Da)"
    elif u in {"nm", "nanomolar"} or re.search(r"\bnmol\s*/\s*l\b|\bnmol\s*l-1\b|\bnmol\s*dm-3\b", unit.lower()):
        mw = COMMON_MW.get(biomolecule_type, COMMON_MW['protein'])
        normalized = v * mw / 1_000_000_000_000.0
        note = f"Converted nM→mg/mL (assumed MW={mw} Da)"
    elif u in {"pm", "picomolar"} or re.search(r"\bpmol\s*/\s*l\b|\bpmol\s*l-1\b|\bpmol\s*dm-3\b", unit.lower()):
        mw = COMMON_MW.get(biomolecule_type, COMMON_MW['protein'])
        normalized = v * mw / 1_000_000_000_000_000.0
        note = f"Converted pM→mg/mL (assumed MW={mw} Da)"
    elif "%" in u or "percent" in u:
        if "wv" in u or "w/v" in unit or "weight/volume" in unit.lower():
            normalized = v * 10.0
            note = "Converted %w/v→mg/mL (1%≈10 mg/mL)"
        elif "ww" in u or "w/w" in unit or "weight/weight" in unit.lower():
            normalized = v * 10.0
            note = "Converted %w/w→mg/mL (assumed density=1 g/mL)"
        else:
            normalized = v * 10.0
            note = "Converted %→mg/mL (assumed w/v, 1%≈10 mg/mL)"
    else:
        normalized = v
        note = f"Unrecognized unit '{unit}' - value unchanged"
    is_valid, warning = validate_parameter_range('concentration_mg_ml', normalized, strict=False)
    if not is_valid:
        return None, None
    if warning and "Warning:" in warning:
        note += f" ({warning})"
    return normalized, note

def normalize_ph(value: float) -> Tuple[Optional[float], Optional[str]]:
    normalized = float(value)
    is_valid, warning = validate_parameter_range('ph', normalized, strict=True)
    if not is_valid:
        return None, None
    note = "pH"
    return normalized, note