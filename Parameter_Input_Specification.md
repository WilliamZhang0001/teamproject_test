# Parameter Input Specification - Database Interface Documentation

---

## Required Fields (3)

| Field Name | Type | Description | Example Value | Constraints |
|------------|------|-------------|---------------|-------------|
| `biomolecule_name` | `string` | Biomolecule name | `"lysozyme"` | 1-100 characters |
| `biomolecule_type` | `string` | Biomolecule type | `"protein"` | Enum: `"protein"`, `"peptide"`, `"polysaccharide"` |
| `property` | `string` | Experiment type | `"stability"` | Enum: `"stability"`, `"solubility"`, `"aggregation"` |

---

## Experimental Parameters (8, optional but at least 1 required)

| Field Name | Type | Unit | Value Range | Example Value | Description |
|------------|------|------|-------------|---------------|-------------|
| `pH` | `float` | Unitless | 0-14 | `7.0` | pH value |
| `temperature_c` | `float` | °C (Celsius) | -20 - 150 | `25.0` | Temperature |
| `concentration_mg_ml` | `float` | mg/mL | 0.001 - 1000 | `10.0` | Biomolecule concentration |
| `ionic_strength_mM` | `float` | mM (millimolar) | 0 - 5000 | `150.0` | Ionic strength |
| `additive` | `string` | Text | - | `"glycerol"` | Additive name (comma-separated for multiple) |
| `time_min` | `float` | min (minutes) | 0 - 100000 | `60.0` | Experiment time |
| `shear_rate_s1` | `float` | s⁻¹ | 0 - 10000 | `100.0` | Shear rate |
| `pressure_bar` | `float` | bar | 0 - 10000 | `1.0` | Pressure (1 bar ≈ 1 atm) |

---

## Two Usage Scenarios

### Scenario 1: Parameter Validation (All Parameters Known)
**Input**: Fill in all parameters (or most parameters)  
**Output**: `stable` / `unstable` + confidence level

**JSON Example**:
```json
{
  "biomolecule_name": "lysozyme",
  "biomolecule_type": "protein",
  "property": "stability",
  "pH": 7.0,
  "temperature_c": 25.0,
  "concentration_mg_ml": 10.0,
  "ionic_strength_mM": 150.0,
  "additive": "glycerol",
  "time_min": 60.0,
  "shear_rate_s1": null,
  "pressure_bar": 1.0
}
```

### Scenario 2: Parameter Recommendation (Partial Parameters Known)
**Input**: Fill in partial parameters + parameter names to recommend  
**Output**: Recommended parameter ranges (IQR statistics)

**JSON Example**:
```json
{
  "biomolecule_name": "lysozyme",
  "biomolecule_type": "protein",
  "property": "stability",
  "pH": 7.0,
  "temperature_c": 25.0,
  "recommend_parameters": ["concentration_mg_ml", "ionic_strength_mM"]
}
```

---

