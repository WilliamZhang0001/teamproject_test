# ML System Integration Documentation

## DemoB.version2:ML Update(CP)

### Implemented Features

1. **Data Collection and Extraction**
   - Scraped **4,936** experimental records from literature databases
   - Supports **3 types of biomolecules**: proteins, peptides, polysaccharides
   - Extracts **8 experimental parameters**: pH, temperature, concentration, ionic strength, additives, time, shear rate, pressure
   - Covers **154 different** biomolecules (Top 5: xylanase, cellulase, albumin, lysozyme, curdlan)

2. **Stability Prediction Model** (based on 8-parameter features)
   - **Input**: Experimental parameters (all or partial)
   - **Output**: Stability judgment + confidence level
   - Trained **3 models**, performance comparison shown in the table below

3. **Parameter Range Recommendation** (IQR statistics)
   - **Input**: Biomolecule name
   - **Output**: Parameter safety ranges from historical data
   - Supports **global recommendation** (all molecules) and **specific recommendation** (single molecule)

4. **Historical Literature Retrieval**
   - Retrieves stored 4,936 experimental records
   - Returns matching literature and experimental conditions

### Current Limitations

1. **Parameter Completion**: Can only provide **range recommendations**, cannot predict **optimal specific values**
   - **Reason**: Requires development of regression model + labeling of optimal condition data

2. **Unknown Substances**: Does not support real-time scraping and modeling
   - **Reason**: Real-time scraping + modeling takes 5-10 minutes, not suitable for online services

3. **Cross-Substance Prediction**: For substances outside the training set, prediction accuracy decreases
   - Can still predict using general features (pH, temperature, etc.), but with lower confidence

---

## Model Performance Comparison

| Model | F1-Score | Stable Recognition Rate | Unstable Recognition Rate | Characteristics | Recommended Scenario |
|-------|----------|-------------------------|-------------------------|-----------------|----------------------|
| **RandomForest** | **0.945** | **0.955** | 0.686 | Most accurate overall | General use |
| RF + SMOTE | 0.93 | 0.92 | **0.75** | More balanced | High balance requirements |
| **XGBoost** | 0.919 | 0.886 | **0.792** | Good unstable detection | Unstable detection focus |

**Key Metrics Explanation**:
- **F1-Score**: Overall prediction accuracy (higher is better)
- **Stable Recognition Rate**: Proportion of actually stable formulations correctly identified
- **Unstable Recognition Rate**: Proportion of actually unstable formulations correctly identified

## Integration Interface Documentation

### Use Case Classification

Based on current requirements, the system supports the following 4 use cases:

| Scenario | User Input | System Output | Implementation Status |
|----------|------------|---------------|----------------------|
| **Scenario 1: Complete Parameter Validation** | Substance name + all parameters | Stability judgment + confidence | ✅ Implemented |
| **Scenario 2: Partial Parameter Completion** | Substance name + partial parameters | **Recommended ranges** for other parameters | ✅ Implemented (ranges only) |
| **Scenario 3: Known Substance Query** | Substance name only | General model + IQR statistics + literature | ✅ Implemented |
| **Scenario 4: Unknown Substance Exploration** | Unknown substance name | Type identification + general prediction | ⚠️ Partially implemented |

---

### Scenario 1: Complete Parameter Validation

**User Input** - n parameters: Main key biomolecule is required, others are optional. Current parameters are used for complete parameter validation.

```json
{
  "biomolecule_name": "lysozyme",          // Required: biomolecule name
  "pH": 7.0,                               // Optional: pH value (0-14)
  "temperature_c": 25.0,                   // Optional: temperature °C
  "concentration_mg_ml": 10.0,             // Optional: concentration mg/mL
  "biomolecule_type": "protein",           // Optional: type protein/peptide/polysaccharide
  
  // Optional parameters
  "ionic_strength_mM": 150.0,              // Optional: ionic strength mM
  "additive": "glycerol",                  // Optional: additive
  "time_min": 60.0,                        // Optional: time minutes
  "shear_rate_s1": 100.0,                  // Optional: shear rate s⁻¹
  "pressure_bar": 1.0                      // Optional: pressure bar
}
```

**System Output**:

```json
{
  "scenario": "complete_validation",
  "is_stable": true,
  "confidence": 0.852,
  "recommendation": "This formulation is predicted to be stable (confidence 85.2%)",
  "model_used": "RandomForest",
  "warnings": []
}
```

---

### Scenario 2: Partial Parameter Completion (Returns Ranges Only)

**User Input** - Substance name + at least 1 parameter:

```json
{
  "biomolecule_name": "lysozyme",
  "pH": 7.0,
  "temperature_c": null,                   // Needs recommendation
  "concentration_mg_ml": null,             // Needs recommendation
  "biomolecule_type": "protein"
}
```

**System Output**:

```json
{
  "scenario": "parameter_recommendation",
  "filled_parameters": {
    "pH": 7.0
  },
  "recommended_ranges": {
    "temperature_c": {
      "min": 21.25,
      "max": 75.0,
      "median": 45.0,
      "unit": "°C",
      "confidence": "IQR statistics (38 literature records)"
    },
    "concentration_mg_ml": {
      "min": 5.0,
      "max": 645.0,
      "median": 50.0,
      "unit": "mg/mL",
      "confidence": "IQR statistics (55 literature records)"
    }
  },
  "note": "Returns safety ranges, not optimal specific values",
  "suggestion": "Suggest selecting values near the median within the range for experiments"
}
```

**Important Limitations**:
- **Currently only returns ranges**, cannot predict optimal specific values (e.g., "temperature=25°C")
- Ranges are based on historical data IQR statistics, not ML prediction
- To predict specific optimal values, regression model development is needed (Phase 2)

---

### Scenario 3: Known Substance Query

**User Input** - Substance name only:

```json
{
  "biomolecule_name": "lysozyme",
  "biomolecule_type": "protein"  // Optional
}
```

**System Output**:

```json
{
  "scenario": "known_biomolecule_search",
  "biomolecule_info": {
    "name": "lysozyme",
    "type": "protein",
    "records_count": 124,
    "data_quality": "high"
  },
  "general_model_prediction": {
    "typical_stable_range": {
      "pH": [3.0, 7.0],
      "temperature_c": [21.25, 75.0],
      "concentration_mg_ml": [5.0, 645.0]
    },
    "confidence": "Based on 124 literature records"
  },
  "iqr_statistics": {
    "pH": {"q1": 3.0, "q3": 7.0, "median": 5.0},
    "temperature_c": {"q1": 21.25, "q3": 75.0, "median": 37.0},
    "concentration_mg_ml": {"q1": 5.0, "q3": 645.0, "median": 50.0}
  },
  "reference_papers": [
    {
      "title": "Stability of lysozyme in...",
      "conditions": {"pH": 7.0, "temperature_c": 25.0, "concentration_mg_ml": 10.0},
      "outcome": "stable",
      "source": "DOI:xxx"
    }
    // ... more literature
  ],
  "recommendation": "Use IQR ranges for initial screening, combined with literature validation"
}
```

---

### Scenario 4: Unknown Substance Exploration (To Be Developed)

**Current Implementation**:

```json
Input: {"biomolecule_name": "Unknown Substance X"}
Output: {
  "scenario": "unknown_biomolecule",
  "biomolecule_type": "protein (auto-identified)",
  "general_model_prediction": {
    "note": "Using general protein model for prediction",
    "confidence": "Low (0.3-0.5)",
    "suggested_range": "Global IQR statistical range"
  },
  "recommendation": "Suggest providing more information or contact administrator to add this substance"
}
```

**Future Development (Phase 3)**:
- Real-time scraping of literature for this substance (5-10 minutes)
- Extract experimental parameters
- Temporary modeling (if data is sufficient)
- User can choose to wait or use general model

