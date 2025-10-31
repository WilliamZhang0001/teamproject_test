# ML系统对接文档

## DemoB.version2:ML Update(CP)

### 已实现的功能

1. **数据采集与提取**
   - 从文献数据库抓取了 **4936条** 实验记录
   - 支持 **3种生物分子**：蛋白质、多肽、多糖
   - 提取 **8个实验参数**：pH、温度、浓度、离子强度、添加剂、时间、剪切速率、压力
   - 覆盖 **154种** 不同生物分子（Top 5: xylanase, cellulase, albumin, lysozyme, curdlan）

2. **稳定性预测模型**（基于8参数特征）
   - **输入**：实验参数（全部或部分）
   - **输出**：稳定性判断 + 置信度
   - 训练了 **3个模型**，性能对比见下表

3. **参数范围推荐**（IQR统计）
   - **输入**：生物分子名称
   - **输出**：历史数据中的参数安全范围
   - 支持 **全局推荐**（所有分子）和 **特定推荐**（单个分子）

4. **历史文献检索**
   - 检索已存储的 4936 条实验记录
   - 返回匹配的文献和实验条件

### 当前限制

1. **参数补全**：只能提供**范围推荐**，不能预测**最优具体值**
   - **原因**：需要开发回归模型 + 标注最优条件数据

2. **未知物质**：不支持实时爬取和建模
   - **原因**：实时爬取+建模耗时 5-10 分钟，不适合在线服务

3. **跨物质预测**：对训练集外的物质，预测精度会降低
   - 使用通用特征（pH、温度等）仍可预测，但置信度较低
---

## 模型性能对比

| 模型 | F1-Score | 稳定识别率 | 不稳定识别率 | 特点 | 推荐场景 |
|------|----------|------------|--------------|------|----------|
| **RandomForest** | **0.945** | **0.955** | 0.686 | 整体最准确 | 
| RF + SMOTE | 0.93 | 0.92 | **0.75** | 更平衡 | 平衡性要求高 |
| **XGBoost** | 0.919 | 0.886 | **0.792** | 不稳定检测好 | 

**关键指标说明**：
- **F1-Score**：整体预测准确性（越高越好）
- **稳定识别率**：实际稳定的配方被正确识别的比例
- **不稳定识别率**：实际不稳定的配方被正确识别的比例

## 对接接口说明

### 使用场景分类

根据目前需求，系统支持以下4种使用场景：
| 场景 | 用户输入 | 系统返回 | 实现状态 |
|------|----------|----------|----------|
| **场景1：完整参数验证** | 物质名 + 全部参数 | 稳定性判断 + 置信度 | ✅ 已实现 |
| **场景2：部分参数补全** | 物质名 + 部分参数 | 其他参数**推荐范围** | ✅ 已实现（仅范围）|
| **场景3：已知物质查询** | 仅物质名 | 通用模型 + IQR统计 + 文献 | ✅ 已实现 |
| **场景4：未知物质探索** | 未知物质名 | 种类识别 + 通用预测 | ⚠️ 部分实现 |

---

### 场景1：完整参数验证

**用户输入** - n个参数：主Key生物分子必填，其余选填，目前参数作为完整参数的验证

```json
{
  "biomolecule_name": "lysozyme",          // 必填：生物分子名称
  "pH": 7.0,                               // 选填：pH值 (0-14)
  "temperature_c": 25.0,                   // 选填：温度 °C
  "concentration_mg_ml": 10.0,             // 选填：浓度 mg/mL
  "biomolecule_type": "protein",           // 选填：类型 protein/peptide/polysaccharide
  
  // 可选参数
  "ionic_strength_mM": 150.0,              // 可选：离子强度 mM
  "additive": "glycerol",                  // 可选：添加剂
  "time_min": 60.0,                        // 可选：时间 分钟
  "shear_rate_s1": 100.0,                  // 可选：剪切速率 s⁻¹
  "pressure_bar": 1.0                      // 可选：压力 bar
}
```

**系统返回**：

```json
{
  "scenario": "complete_validation",
  "is_stable": true,
  "confidence": 0.852,
  "recommendation": "该配方预计稳定（置信度85.2%）",
  "model_used": "RandomForest",
  "warnings": []
}
```

---

### 场景2：部分参数补全（仅返回范围）

**用户输入** - 物质名 + 至少1个参数：

```json
{
  "biomolecule_name": "lysozyme",
  "pH": 7.0,
  "temperature_c": null,                   // 需要推荐
  "concentration_mg_ml": null,             // 需要推荐
  "biomolecule_type": "protein"
}
```

**系统返回**：

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
      "confidence": "IQR统计（38条文献）"
    },
    "concentration_mg_ml": {
      "min": 5.0,
      "max": 645.0,
      "median": 50.0,
      "unit": "mg/mL",
      "confidence": "IQR统计（55条文献）"
    }
  },
  "note": "返回的是安全范围，不是最优具体值",
  "suggestion": "建议在范围内选择中位数附近的值进行实验"
}
```

**重要限制**：
- **目前只能返回范围**，不能预测最优具体值（如"温度=25°C"）
- 范围基于历史数据IQR统计，不是ML预测
- 若要预测具体最优值，需要开发回归模型（Phase 2）

---

### 场景3：已知物质查询

**用户输入** - 仅物质名：

```json
{
  "biomolecule_name": "lysozyme",
  "biomolecule_type": "protein"  // 可选
}
```

**系统返回**：

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
    "confidence": "基于124条文献"
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
    // ... 更多文献
  ],
  "recommendation": "使用IQR范围作为初始筛选，结合文献验证"
}
```

---

### 场景4：未知物质探索 （需开发）

**当前实现**：

```json
输入: {"biomolecule_name": "未知物质X"}
输出: {
  "scenario": "unknown_biomolecule",
  "biomolecule_type": "protein (自动识别)",
  "general_model_prediction": {
    "note": "使用通用蛋白质模型预测",
    "confidence": "低 (0.3-0.5)",
    "suggested_range": "全局IQR统计范围"
  },
  "recommendation": "建议提供更多信息或联系管理员添加该物质"
}
```

**未来开发（Phase 3）**：
- 实时爬取该物质文献（5-10分钟）
- 提取实验参数
- 临时建模（如果数据足够）
- 用户可选择等待或使用通用模型

