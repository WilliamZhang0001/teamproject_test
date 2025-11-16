# DoE-Assist ML System - DemoB Version3

---

## **Core System Features**

### Scenario 1: Parameter Feasibility Validation
- **Input**: Complete or partial parameters (pH, temperature, concentration, etc.)
- **Output**: Stable/Unstable prediction + confidence level
- **Model**: **LightGBM** (F1=0.703, best performance)

### Scenario 2: Parameter Range Recommendation
- **Input**: Partial known parameters
- **Output**: IQR statistical ranges (Q1-Q3, median)
- **Method**: 4-level priority lookup (substance + experiment > experiment > substance > global)

---

## **Model Performance Comparison**

| Model | F1-Score | Accuracy | Accuracy Improvement | Status |
|-------|----------|----------|---------------------|--------|
| **RandomForest** | 0.626 | 0.594 | baseline |
| **XGBoost** | 0.702 | 0.774 | **+12%** |
| **LightGBM** | **0.703** | **0.777** | **+12%** |

**Actual Test Results** (Stability experiments):
```
Model Comparison Summary
======================================================================
Model           CV F1      Accuracy   F1         Precision  Recall
----------------------------------------------------------------------
RandomForest    0.626      0.594      0.627      0.703       0.594
XGBoost         0.702      0.774      0.703      0.718       0.774
LightGBM        0.703      0.777      0.703      0.727       0.777   <- Best
```

---

## **Quick Start (3 Methods)**

### Method 1: One-Click Setup (Recommended)
```bash
# Automatically completes all training and testing
python setup_ml_system.py

# Includes:
# 1. Train multiple models (RF + XGBoost + LightGBM)
# 2. Train regression models (pH, temperature, concentration)
# 3. Generate IQR statistics
# 4. Test two scenarios
```

### Method 2: Train Multiple Models Only
```bash
# Train classification models (compare 3 algorithms)
python scripts/train_multi_models.py \
  --experiment-type stability \
  --mode classification

# View comparison results
cat models/multi_models/stability_comparison.json
```

### Method 3: Test Scenarios Only
```bash
# Test two application scenarios (using existing models)
python test_scenarios.py

# Includes:
# - Scenario 1: Complete parameter validation (Stability + Solubility)
# - Scenario 2: IQR parameter recommendation
# - Combined scenario: Recommendation + validation
```

## **File Structure**

### Core Scripts
```
capstone-project-25t3-9900-h15a-almond/
├── setup_ml_system.py               # ⭐ One-click setup script
├── test_scenarios.py                # ⭐ Two scenario tests
├── demo_advanced_features.py        # Advanced features demo
├── scripts/
│   ├── train_multi_models.py        # ⭐ Multi-model training system
│   ├── train_by_experiment_type.py  # RandomForest training
│   └── generate_iqr_statistics.py  # IQR statistics generation
└── ml_engine/
    ├── features/
    │   └── improved_preprocess.py    # ⭐ Data preprocessing (optimized label logic)
    └── prediction/
        └── unified_predictor.py     # Unified prediction interface
```

### Model Files
```
models/
├── by_experiment_type/              # RandomForest models (baseline)
│   ├── stability_classifier.pkl     (F1=0.626)
│   ├── solubility_classifier.pkl   (F1=0.805)
│   └── general_classifier.pkl       (F1=0.619)
├── multi_models/                    # High-performance models (new)
│   ├── stability_xgboost.pkl       (F1=0.702) 
│   ├── stability_lightgbm.pkl      (F1=0.703) Best
│   ├── stability_pH_regressor.pkl  (regression model)
│   ├── stability_temperature_c_regressor.pkl
│   └── stability_comparison.json    (performance comparison report)
└── iqr_statistics.json              # IQR statistics data
```

## **Two Application Scenarios Explained**

### Scenario 1: Parameter Feasibility Validation (Classification)

**Question**: User wants to know if a set of parameters is stable?

**Input Example**:
```python
{
  "biomolecule_name": "lysozyme",
  "biomolecule_type": "protein",
  "property": "stability",
  "pH": 7.0,
  "temperature_c": 25.0,
  "concentration_mg_ml": 10.0,
  "ionic_strength_mM": 150.0,
  "additive": "glycerol"
}
```

**Output Example**:
```python
{
  "prediction": "stable",
  "confidence": 0.85,
  "probabilities": {
    "stable": 0.85,
    "unstable": 0.15
  },
  "model_used": "LightGBM",
  "recommendation": "This experimental condition is predicted to be feasible, suggest experimental validation"
}
```

**Models Used**: 
- **LightGBM** (F1=0.703) - Automatically loads best model
- If LightGBM doesn't exist, automatically falls back to XGBoost or RandomForest

---

### Scenario 2: Parameter Range Recommendation (IQR Statistics)

**Question**: Given partial parameters, recommend appropriate ranges for other parameters?

**Input Example**:
```python
{
  "biomolecule_name": "lysozyme",
  "property": "stability",
  "known_parameters": {
    "pH": 7.0,
    "temperature_c": 25.0
  },
  "recommend_parameters": ["concentration_mg_ml", "ionic_strength_mM"]
}
```

**Output Example**:
```python
{
  "concentration_mg_ml": {
    "recommended_value": 10.0,          # Median
    "safe_range": [5.0, 20.0],         # IQR range (Q1-Q3)
    "full_range": [0.1, 100.0],         # Min-max values
    "sample_count": 1234,
    "source": "Based on all stability experimental data"
  },
  "ionic_strength_mM": {
    "recommended_value": 150.0,
    "safe_range": [100.0, 200.0],
    "full_range": [0.0, 500.0],
    "sample_count": 987,
    "source": "Based on lysozyme stability data"
  }
}
```

**Lookup Priority**:
1. Substance + experiment type (e.g., stability_lysozyme)
2. Experiment type (e.g., stability)
3. Substance (e.g., lysozyme)
4. Global statistics

---

## **Practical Usage Examples**

### Example 1: Python Script Call
```python
import pickle
import pandas as pd
from pathlib import Path

# Load best model
model_path = "models/multi_models/stability_lightgbm.pkl"
model_dict = pickle.load(open(model_path, 'rb'))

# Prepare input
user_input = {
    'pH': 7.0,
    'temperature_c': 25.0,
    'concentration_mg_ml': 10.0,
    # ... other parameters
}

# Predict
X = prepare_features(user_input)  # Use function from test_scenarios.py
prediction = model_dict['model'].predict(X)[0]
proba = model_dict['model'].predict_proba(X)[0]

print(f"Prediction: {'Stable' if prediction == 1 else 'Unstable'}")
print(f"Confidence: {proba[int(prediction)]:.2%}")
```

### Example 2: Command Line Quick Test
```bash
# Complete test (5 test cases)
python test_scenarios.py

# Output:
# - Scenario 1: Stability validation (Unstable, 67%)
# - Scenario 1: Solubility validation (Stable, 81%)
# - Scenario 2: IQR recommendation (concentration + ionic strength)
# - Scenario 2: IQR recommendation (temperature + concentration)
# - Combined: Recommendation + validation
```

---

## **System Capability Boundaries**

### **Currently Supported**
1. **Stability experiments**: 13,037 records, 3 high-performance models
2. **Solubility experiments**: 2,030 records, RandomForest model
3. **Parameters**: 8 types (pH, temperature, concentration, ionic strength, additives, time, shear force, pressure)
4. **Biomolecules**: Proteins, peptides, polysaccharides

### ⚠️ **Limitations**
1. **Aggregation model**: Not trained (single-class data)
2. **Regression accuracy**: MAE approximately 10% (needs more data for improvement)
3. **Data sparsity**: Some parameter combinations have few samples

### **Future Extensions**
1. Improve Aggregation data collection (include positive and negative samples)
2. Train high-performance models for Solubility (XGBoost/LightGBM)
3. Implement quantile regression (more precise range prediction)
4. Add more experiment types (Viscosity, Turbidity, etc.)

---

## **Quick Command Reference**

```bash
# === One-Click Setup ===
python setup_ml_system.py

# === Individual Training ===
# Multi-model comparison
python scripts/train_multi_models.py --experiment-type stability --mode classification

# Regression models
python scripts/train_multi_models.py --experiment-type stability --mode regression --regress-params "pH,temperature_c"

# === Testing and Demo ===
# Two scenario tests
python test_scenarios.py

# Advanced features demo
python demo_advanced_features.py

# === View Results ===
# Model comparison report
cat models/multi_models/stability_comparison.json

# IQR statistics
python -c "import json; print(json.dumps(json.load(open('models/iqr_statistics.json')), indent=2))"
```

---

