from __future__ import annotations

from typing import Optional, Tuple, Dict
import re
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Validation ranges for experimental parameters (放宽范围以提高提取率)
VALIDATION_RANGES = {
    'ph': (0.0, 14.0),  # pH标准范围，保持不变
    'temperature_c': (-100.0, 300.0),  # 放宽温度范围，包含极端实验条件（如高压灭菌、超低温保存）
    'concentration_mg_ml': (1e-9, 10000.0),  # 放宽浓度范围，包含极低和极高浓度
}

# Common molecular weights for concentration conversion (Da)
COMMON_MW = {
    'protein': 50000,  # Average protein MW
    'peptide': 2000,   # Average peptide MW
    'antibody': 150000, # Average antibody MW
    'enzyme': 60000,   # Average enzyme MW
}

def validate_parameter_range(param_type: str, value: float, strict: bool = False) -> Tuple[bool, str]:
    """
    Validate if a parameter value is within reasonable experimental ranges.
    
    Args:
        param_type: Type of parameter ('ph', 'temperature_c', 'concentration_mg_ml')
        value: Parameter value to validate
        strict: If True, use stricter validation (reject invalid values). 
                If False, use lenient validation (allow slightly out-of-range values with warning)
        
    Returns:
        Tuple of (is_valid, warning_message)
    """
    if param_type not in VALIDATION_RANGES:
        return True, ""
    
    min_val, max_val = VALIDATION_RANGES[param_type]
    
    # pH始终严格验证，因为它有明确的理论范围
    if param_type == 'ph':
        if value < min_val or value > max_val:
            return False, f"pH value {value} outside standard range ({min_val}-{max_val})"
    
    # 对于温度和浓度，使用更宽松的验证
    elif value < min_val:
        if strict:
            return False, f"{param_type} value {value} below reasonable range ({min_val}-{max_val})"
        else:
            # 允许稍微低于范围的值（可能是单位转换错误或特殊条件）
            # 计算允许的范围：允许到min_val的70%（对于负值更合理）
            allowed_min = min_val * 0.7 if min_val < 0 else min_val * 0.5
            if value >= allowed_min:
                return True, f"Warning: {param_type} value {value} slightly below typical range"
            return False, f"{param_type} value {value} far below reasonable range ({min_val}-{max_val})"
    elif value > max_val:
        if strict:
            return False, f"{param_type} value {value} above reasonable range ({min_val}-{max_val})"
        else:
            # 允许稍微高于范围的值（可能是特殊实验条件）
            if value < max_val * 2:  # 允许最多高于范围100%
                return True, f"Warning: {param_type} value {value} above typical range, may be special condition"
            return False, f"{param_type} value {value} far above reasonable range ({min_val}-{max_val})"
    
    return True, ""

def normalize_temperature(value: float, unit_hint: Optional[str]) -> Tuple[Optional[float], Optional[str]]:
    """
    Normalize temperature to Celsius with validation.

    Args:
        value: Temperature value
        unit_hint: Unit hint ('K', 'C', 'F', etc.)
        
    Returns:
        Tuple of (normalized_value, note) or (None, None) if invalid
    """
    if not unit_hint:
        # Assume Celsius if no unit hint
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
            # Assume Celsius for 'C', 'celsius', etc.
            normalized = float(value)
            note = "Celsius"
    
    # Validate range with lenient mode (允许稍超出范围的特殊实验条件)
    is_valid, warning = validate_parameter_range('temperature_c', normalized, strict=False)
    if not is_valid:
        logger.warning(f"Temperature validation failed: {warning} - rejecting invalid temperature value")
        return None, None  # Return None for严重超出范围的值
    elif warning and "Warning:" in warning:
        # 允许稍超出范围的值，但记录警告
        note += f" ({warning})"
        logger.debug(f"Temperature slightly out of typical range: {warning}")
    
    return normalized, note

def normalize_concentration(value: float, unit: str, biomolecule_type: str = "protein") -> Tuple[Optional[float], Optional[str]]:
    """
    Normalize concentration to mg/mL with enhanced unit support and validation.

    Args:
        value: Concentration value
        unit: Unit string
        biomolecule_type: Type of biomolecule for MW estimation
        
    Returns:
        Tuple of (normalized_value, note)
    """
    u = unit.lower().replace(" ", "").replace("/", "")
    v = float(value)
    note = ""
    
    # Direct mg/mL
    if "mgml" in u or "mg/ml" in unit.lower():
        normalized = v
        note = "mg/mL"
    
    # Microgram/mL variants
    elif any(variant in u for variant in ["µgml", "ugml", "mcgml", "μgml"]):
        normalized = v / 1000.0
        note = "Converted µg/mL→mg/mL"
    
    # Nanogram/mL
    elif "ngml" in u:
        normalized = v / 1_000_000.0
        note = "Converted ng/mL→mg/mL"
    
    # Gram/L
    elif "gl" in u:
        normalized = v
        note = "Converted g/L→mg/mL (equivalent)"
    
    # mg/L
    elif "mgl" in u:
        normalized = v / 1000.0
        note = "Converted mg/L→mg/mL"
    
    # Molar concentrations (require MW estimation)
    elif u in {"m", "molar"}:
        mw = COMMON_MW.get(biomolecule_type, COMMON_MW['protein'])
        normalized = v * mw / 1000.0  # M * (g/mol) / 1000 = mg/mL
        note = f"Converted M→mg/mL (assumed MW={mw} Da)"
    
    elif u in {"mm", "millimolar"}:
        mw = COMMON_MW.get(biomolecule_type, COMMON_MW['protein'])
        normalized = v * mw / 1_000_000.0  # mM * (g/mol) / 1,000,000 = mg/mL
        note = f"Converted mM→mg/mL (assumed MW={mw} Da)"
    
    elif u in {"µm", "um", "micromolar", "μm"}:
        mw = COMMON_MW.get(biomolecule_type, COMMON_MW['protein'])
        normalized = v * mw / 1_000_000_000.0  # µM * (g/mol) / 1,000,000,000 = mg/mL
        note = f"Converted µM→mg/mL (assumed MW={mw} Da)"
    
    elif u in {"nm", "nanomolar"}:
        mw = COMMON_MW.get(biomolecule_type, COMMON_MW['protein'])
        normalized = v * mw / 1_000_000_000_000.0  # nM * (g/mol) / 1,000,000,000,000 = mg/mL
        note = f"Converted nM→mg/mL (assumed MW={mw} Da)"
    
    elif u in {"pm", "picomolar"}:
        mw = COMMON_MW.get(biomolecule_type, COMMON_MW['protein'])
        normalized = v * mw / 1_000_000_000_000_000.0  # pM * (g/mol) / 1,000,000,000,000,000 = mg/mL
        note = f"Converted pM→mg/mL (assumed MW={mw} Da)"
    
    # Percentage concentrations
    elif "%" in u or "percent" in u:
        if "wv" in u or "w/v" in unit or "weight/volume" in unit.lower():
            # % w/v: 1% ≈ 10 mg/mL for aqueous solutions
            normalized = v * 10.0
            note = "Converted %w/v→mg/mL (1%≈10 mg/mL)"
        elif "ww" in u or "w/w" in unit or "weight/weight" in unit.lower():
            # % w/w: assume density ≈ 1 g/mL for aqueous solutions
            normalized = v * 10.0
            note = "Converted %w/w→mg/mL (assumed density=1 g/mL)"
        else:
            # Assume w/v if not specified
            normalized = v * 10.0
            note = "Converted %→mg/mL (assumed w/v, 1%≈10 mg/mL)"
    
    else:
        # Unrecognized unit - return as-is with warning
        normalized = v
        note = f"Unrecognized unit '{unit}' - value unchanged"
        logger.warning(f"Unrecognized concentration unit: {unit}")
    
    # Validate range with lenient mode (允许稍超出范围的特殊实验条件)
    is_valid, warning = validate_parameter_range('concentration_mg_ml', normalized, strict=False)
    if not is_valid:
        logger.warning(f"Concentration validation failed: {warning} - rejecting invalid concentration value")
        return None, None  # Return None for严重超出范围的值
    elif warning and "Warning:" in warning:
        # 允许稍超出范围的值，但记录警告
        note += f" ({warning})"
        logger.debug(f"Concentration slightly out of typical range: {warning}")
    
    return normalized, note

def normalize_ph(value: float) -> Tuple[Optional[float], Optional[str]]:
    """
    Normalize pH value with validation.
    
    Args:
        value: pH value
        
    Returns:
        Tuple of (normalized_value, note) or (None, None) if invalid
    """
    normalized = float(value)
    
    # pH始终严格验证（理论范围0-14）
    is_valid, warning = validate_parameter_range('ph', normalized, strict=True)
    if not is_valid:
        logger.warning(f"pH validation failed: {warning} - rejecting invalid pH value")
        return None, None  # Return None for invalid pH values to prevent Pydantic errors
    
    note = "pH"
    return normalized, note

def extract_numeric_range(text: str) -> Optional[Tuple[float, float]]:
    """
    Extract numeric ranges from text like "5-7", "5 to 7", "between 5 and 7".
    
    Args:
        text: Text containing potential range
        
    Returns:
        Tuple of (min_value, max_value) or None if no range found
    """
    # Pattern for ranges like "5-7", "5–7", "5~7"
    range_pattern = r"(\d+(?:\.\d+)?)\s*[-–—~]\s*(\d+(?:\.\d+)?)"
    match = re.search(range_pattern, text)
    if match:
        return (float(match.group(1)), float(match.group(2)))
    
    # Pattern for "X to Y"
    to_pattern = r"(\d+(?:\.\d+)?)\s+to\s+(\d+(?:\.\d+)?)"
    match = re.search(to_pattern, text, re.IGNORECASE)
    if match:
        return (float(match.group(1)), float(match.group(2)))
    
    # Pattern for "between X and Y"
    between_pattern = r"between\s+(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)"
    match = re.search(between_pattern, text, re.IGNORECASE)
    if match:
        return (float(match.group(1)), float(match.group(2)))
    
    return None

def get_parameter_statistics() -> Dict[str, Dict[str, float]]:
    """
    Get statistics about parameter validation ranges.
    
    Returns:
        Dictionary with parameter statistics
    """
    stats = {}
    for param, (min_val, max_val) in VALIDATION_RANGES.items():
        stats[param] = {
            'min_valid': min_val,
            'max_valid': max_val,
            'range_width': max_val - min_val
        }
    return stats