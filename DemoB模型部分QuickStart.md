# DoE-Assist ML系统 - DemoB Version3


---

##  **系统核心功能**

### 场景1：参数可行性验证
- **输入**: 完整或部分参数（pH, 温度, 浓度等）
- **输出**: Stable/Unstable预测 + 置信度
- **模型**: **LightGBM** (F1=0.703, 最佳性能)

### 场景2：参数范围推荐
- **输入**: 部分已知参数
- **输出**: IQR统计范围（Q1-Q3, 中位数）
- **方法**: 4级优先级查找（物质+实验 > 实验 > 物质 > 全局）
---

##  **模型性能对比**

| 模型 | F1-Score | Accuracy | 准确率提升 | 状态 |
|---|---|---|---|---|
| **RandomForest** | 0.626 | 0.594 | baseline |
| **XGBoost** | 0.702 | 0.774 | **+12%** |
| **LightGBM** | **0.703** | **0.777** | **+12%** |

**实际测试结果**（Stability实验）:
```
Model Comparison Summary
======================================================================
Model           CV F1      Accuracy   F1         Precision  Recall
----------------------------------------------------------------------
RandomForest    0.626      0.594      0.627      0.703       0.594
XGBoost         0.702      0.774      0.703      0.718       0.774
LightGBM        0.703      0.777      0.703      0.727       0.777   <- 最佳
```

---

##  **快速开始（3种方式）**

### 方式1：一键设置（推荐）
```bash
# 自动完成所有训练和测试
python setup_ml_system.py

# 包含：
# 1. 训练多模型（RF + XGBoost + LightGBM）
# 2. 训练回归模型（pH, 温度, 浓度）
# 3. 生成IQR统计
# 4. 测试两种场景
```

### 方式2：仅训练多模型
```bash
# 训练分类模型（对比3种算法）
python scripts/train_multi_models.py \
  --experiment-type stability \
  --mode classification

# 查看对比结果
cat models/multi_models/stability_comparison.json
```

### 方式3：仅测试场景
```bash
# 测试两种应用场景（使用现有模型）
python test_scenarios.py

# 包括：
# - 场景1：完整参数验证（Stability + Solubility）
# - 场景2：IQR参数推荐
# - 综合场景：推荐 + 验证
```

##  **文件结构**

### 核心脚本
```
capstone-project-25t3-9900-h15a-almond/
├── setup_ml_system.py               # ⭐ 一键设置脚本
├── test_scenarios.py                # ⭐ 两种场景测试
├── demo_advanced_features.py        # 高级功能演示
├── scripts/
│   ├── train_multi_models.py        # ⭐ 多模型训练系统
│   ├── train_by_experiment_type.py  # RandomForest训练
│   └── generate_iqr_statistics.py   # IQR统计生成
└── ml_engine/
    ├── features/
    │   └── improved_preprocess.py   # ⭐ 数据预处理（已优化标签逻辑）
    └── prediction/
        └── unified_predictor.py     # 统一预测接口
```

### 模型文件
```
models/
├── by_experiment_type/              # RandomForest模型（baseline）
│   ├── stability_classifier.pkl     (F1=0.626)
│   ├── solubility_classifier.pkl    (F1=0.805)
│   └── general_classifier.pkl       (F1=0.619)
├── multi_models/                    # 高性能模型（新增）
│   ├── stability_xgboost.pkl        (F1=0.702) 
│   ├── stability_lightgbm.pkl       (F1=0.703) 最佳
│   ├── stability_pH_regressor.pkl   (回归模型)
│   ├── stability_temperature_c_regressor.pkl
│   └── stability_comparison.json    (性能对比报告)
└── iqr_statistics.json              # IQR统计数据
```

##  **两种应用场景详解**

### 场景1：参数可行性验证（分类）

**问题**: 用户想知道某组参数是否稳定？

**输入示例**:
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

**输出示例**:
```python
{
  "prediction": "stable",
  "confidence": 0.85,
  "probabilities": {
    "stable": 0.85,
    "unstable": 0.15
  },
  "model_used": "LightGBM",
  "recommendation": "该实验条件预计可行，建议进行实验验证"
}
```

**使用的模型**: 
- **LightGBM** (F1=0.703) - 自动加载最佳模型
- 如果LightGBM不存在，自动降级到XGBoost或RandomForest
---

### 场景2：参数范围推荐（IQR统计）

**问题**: 已知部分参数，推荐其他参数的合适范围？

**输入示例**:
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

**输出示例**:
```python
{
  "concentration_mg_ml": {
    "recommended_value": 10.0,          # 中位数
    "safe_range": [5.0, 20.0],          # IQR范围 (Q1-Q3)
    "full_range": [0.1, 100.0],         # 最小-最大值
    "sample_count": 1234,
    "source": "基于所有 stability 实验数据"
  },
  "ionic_strength_mM": {
    "recommended_value": 150.0,
    "safe_range": [100.0, 200.0],
    "full_range": [0.0, 500.0],
    "sample_count": 987,
    "source": "基于 lysozyme 的 stability 数据"
  }
}
```

**查找优先级**:
1. 物质+实验类型（如：stability_lysozyme）
2. 实验类型（如：stability）
3. 物质（如：lysozyme）
4. 全局统计

---

##  **实际使用示例**

### 示例1：Python脚本调用
```python
import pickle
import pandas as pd
from pathlib import Path

# 加载最佳模型
model_path = "models/multi_models/stability_lightgbm.pkl"
model_dict = pickle.load(open(model_path, 'rb'))

# 准备输入
user_input = {
    'pH': 7.0,
    'temperature_c': 25.0,
    'concentration_mg_ml': 10.0,
    # ... 其他参数
}

# 预测
X = prepare_features(user_input)  # 使用test_scenarios.py中的函数
prediction = model_dict['model'].predict(X)[0]
proba = model_dict['model'].predict_proba(X)[0]

print(f"预测: {'Stable' if prediction == 1 else 'Unstable'}")
print(f"置信度: {proba[int(prediction)]:.2%}")
```

### 示例2：命令行快速测试
```bash
# 完整测试（5个测试案例）
python test_scenarios.py

# 输出：
# - 场景1：Stability验证（Unstable, 67%）
# - 场景1：Solubility验证（Stable, 81%）
# - 场景2：IQR推荐（浓度 + 离子强度）
# - 场景2：IQR推荐（温度 + 浓度）
# - 综合：推荐 + 验证
```

---

##  **系统能力边界**

###  **当前支持**
1. **Stability实验**: 13,037条数据，3种高性能模型
2. **Solubility实验**: 2,030条数据，RandomForest模型
3. **参数**: 8种（pH, 温度, 浓度, 离子强度, 添加剂, 时间, 剪切力, 压力）
4. **生物分子**: 蛋白质, 肽, 多糖

### ⚠️ **限制**
1. **Aggregation模型**: 未训练（数据单类）
2. **回归精度**: MAE约10%（需要更多数据改进）
3. **数据稀疏性**: 某些参数组合样本少

###  **未来扩展**
1. 改进Aggregation数据采集（包含正负样本）
2. 训练Solubility的高性能模型（XGBoost/LightGBM）
3. 实现分位数回归（更精确的范围预测）
4. 添加更多实验类型（Viscosity, Turbidity等）

---

##  **快速命令参考**

```bash
# === 一键设置 ===
python setup_ml_system.py

# === 单独训练 ===
# 多模型对比
python scripts/train_multi_models.py --experiment-type stability --mode classification

# 回归模型
python scripts/train_multi_models.py --experiment-type stability --mode regression --regress-params "pH,temperature_c"

# === 测试和演示 ===
# 两种场景测试
python test_scenarios.py

# 高级功能演示
python demo_advanced_features.py

# === 查看结果 ===
# 模型对比报告
cat models/multi_models/stability_comparison.json

# IQR统计
python -c "import json; print(json.dumps(json.load(open('models/iqr_statistics.json')), indent=2))"
```

---

