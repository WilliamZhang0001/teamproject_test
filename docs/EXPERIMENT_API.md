# 实验预测API使用文档

## 概述

本系统提供两个核心功能：
1. **分类预测**：根据用户输入的实验参数，判断该参数组合是好还是坏
2. **参数预测**：用户选择需要预测的参数，系统返回预测值和相关文献

## 功能1：分类预测

### 功能描述

用户输入物质类别、物质名称、实验类别，以及8个可选参数中的任意组合。系统返回该参数组合的预测结果（好/坏）、置信度以及最相似的文献。

### API端点

```
POST /api/v1/experiments/predict-classification
```

### 请求参数

```json
{
  "biomolecule_type": "protein",          // 必填：物质类别
  "biomolecule_name": "lysozyme",         // 必填：物质名称
  "experiment_type": "stability",         // 可选：实验类别（默认stability）
  
  // 以下8个参数为可选，至少填写1个
  "pH": 7.0,                              // 可选：pH值 (0-14)
  "temperature_c": 25.0,                  // 可选：温度 (°C)
  "concentration_mg_ml": 10.0,            // 可选：浓度 (mg/mL)
  "ionic_strength_mM": 150.0,             // 可选：离子浓度 (mM)
  "additive": "glycerol",                 // 可选：添加剂
  "time_min": 60.0,                       // 可选：时间 (分钟)
  "shear_rate_s1": 100.0,                 // 可选：剪切速率 (s⁻¹)
  "pressure_bar": 1.0                     // 可选：压力 (bar)
}
```

### 查询参数

- `top_k` (可选): 返回最相似的文献数量，默认值为3，范围1-10

### 响应格式

```json
{
  "status": "success",
  "data": {
    "biomolecule_type": "protein",
    "biomolecule_name": "lysozyme",
    "experiment_type": "stability",
    "prediction": "Good",
    "confidence": 0.852,
    "input_parameters": {
      "pH": 7.0,
      "temperature_c": 25.0,
      "concentration_mg_ml": 10.0,
      "ionic_strength_mM": 150.0,
      "additive": "glycerol",
      "time_min": 60.0,
      "shear_rate_s1": 100.0,
      "pressure_bar": 1.0
    },
    "similar_literature": [
      {
        "id": 1234,
        "similarity_score": 0.92,
        "literature": {
          "doi": "10.1234/example",
          "title": "Stability of lysozyme in...",
          "authors": "Smith, J. et al.",
          "pub_year": 2020
        },
        "parameters": {
          "pH": 7.0,
          "temperature_c": 25.0,
          "concentration_mg_ml": 10.0
        },
        "outcome_text": "Lysozyme remained stable..."
      }
    ],
    "model_info": {
      "experiment_type": "stability",
      "filled_params": 8,
      "model_used": "RandomForest"
    }
  }
}
```

### 使用示例

#### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/experiments/predict-classification?top_k=3" \
  -H "Content-Type: application/json" \
  -d '{
    "biomolecule_type": "protein",
    "biomolecule_name": "lysozyme",
    "experiment_type": "stability",
    "pH": 7.0,
    "temperature_c": 25.0,
    "concentration_mg_ml": 10.0,
    "ionic_strength_mM": 150.0
  }'
```

#### Python

```python
import requests

url = "http://localhost:8000/api/v1/experiments/predict-classification"
params = {"top_k": 3}

data = {
    "biomolecule_type": "protein",
    "biomolecule_name": "lysozyme",
    "experiment_type": "stability",
    "pH": 7.0,
    "temperature_c": 25.0,
    "concentration_mg_ml": 10.0,
    "ionic_strength_mM": 150.0
}

response = requests.post(url, json=data, params=params)
result = response.json()

print(f"预测结果: {result['data']['prediction']}")
print(f"置信度: {result['data']['confidence']}")
print(f"相似文献数量: {len(result['data']['similar_literature'])}")
```

---

## 功能2：参数预测

### 功能描述

用户输入实验条件后，选择需要预测的一个或多个参数。系统返回这些参数的预测值、置信度以及相关文献。

### API端点

```
POST /api/v1/experiments/predict-parameter
```

### 请求参数

```json
{
  "input": {
    "biomolecule_type": "protein",        // 必填：物质类别
    "biomolecule_name": "lysozyme",       // 必填：物质名称
    "experiment_type": "stability",       // 可选：实验类别
    
    // 以下8个参数为可选，至少填写1个
    "pH": 7.0,
    "temperature_c": 25.0,
    "concentration_mg_ml": 10.0,
    "ionic_strength_mM": 150.0,
    "additive": "glycerol",
    "time_min": 60.0,
    "shear_rate_s1": 100.0,
    "pressure_bar": 1.0
  },
  "predict_parameters": [                 // 必填：需要预测的参数列表
    "pH",
    "temperature_c"
  ],
  "top_k": 3                              // 可选：返回最相似的文献数量
}
```

### 可预测的参数

- `pH`
- `temperature_c`
- `concentration_mg_ml`
- `ionic_strength_mM`
- `additive`
- `time_min`
- `shear_rate_s1`
- `pressure_bar`

### 响应格式

```json
{
  "status": "success",
  "data": {
    "biomolecule_type": "protein",
    "biomolecule_name": "lysozyme",
    "experiment_type": "stability",
    "input_parameters": {
      "pH": 7.0,
      "temperature_c": 25.0,
      "concentration_mg_ml": 10.0
    },
    "predicted_parameters": {
      "ionic_strength_mM": {
        "recommended_value": 150.0,
        "min": 100.0,
        "max": 200.0,
        "confidence": 55
      },
      "additive": {
        "recommended_value": "glycerol",
        "min": null,
        "max": null,
        "confidence": 38
      }
    },
    "confidence": 0.7,
    "similar_literature": [
      {
        "id": 1234,
        "similarity_score": 0.85,
        "literature": {
          "doi": "10.1234/example",
          "title": "Stability of lysozyme in...",
          "authors": "Smith, J. et al."
        },
        "parameters": {
          "pH": 7.0,
          "temperature_c": 25.0,
          "concentration_mg_ml": 10.0,
          "ionic_strength_mM": 150.0
        }
      }
    ],
    "model_info": {
      "experiment_type": "stability"
    }
  }
}
```

### 使用示例

#### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/experiments/predict-parameter" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "biomolecule_type": "protein",
      "biomolecule_name": "lysozyme",
      "experiment_type": "stability",
      "pH": 7.0,
      "temperature_c": 25.0
    },
    "predict_parameters": ["concentration_mg_ml", "ionic_strength_mM"],
    "top_k": 3
  }'
```

#### Python

```python
import requests

url = "http://localhost:8000/api/v1/experiments/predict-parameter"

data = {
    "input": {
        "biomolecule_type": "protein",
        "biomolecule_name": "lysozyme",
        "experiment_type": "stability",
        "pH": 7.0,
        "temperature_c": 25.0
    },
    "predict_parameters": ["concentration_mg_ml", "ionic_strength_mM"],
    "top_k": 3
}

response = requests.post(url, json=data)
result = response.json()

print("预测的参数:")
for param, info in result['data']['predicted_parameters'].items():
    print(f"{param}: {info['recommended_value']} (置信度: {info['confidence']})")
```

---

## 其他端点

### 获取预测历史

```
GET /api/v1/experiments/history?limit=100
```

获取当前用户的历史预测记录。

### 获取单条记录

```
GET /api/v1/experiments/{experiment_id}
```

根据ID获取单条实验记录的详细信息。

---

## 数据说明

### 物质类别 (biomolecule_type)

- `protein` - 蛋白质
- `peptide` - 多肽
- `polysaccharide` - 多糖

### 实验类别 (experiment_type)

- `stability` - 稳定性
- `solubility` - 溶解度
- `aggregation` - 聚集性

### 预测结果 (prediction)

- `Good` - 该实验条件预计表现良好
- `Bad` - 该实验条件预计表现不佳

### 置信度 (confidence)

- 范围：0.0 - 1.0
- 数值越高表示预测越可靠

---

## 注意事项

1. **参数验证**：系统会对所有输入参数进行验证，确保数值在合理范围内
2. **数据保存**：如果用户已登录，预测结果会自动保存到数据库
3. **文献检索**：系统会根据输入参数在文献数据库中搜索最相似的记录
4. **ML模型**：预测基于训练好的机器学习模型和历史统计数据

---

## 错误处理

### 400 Bad Request

```json
{
  "detail": "无效的参数: invalid_param。有效值: ['pH', 'temperature_c', ...]"
}
```

### 500 Internal Server Error

```json
{
  "detail": "预测失败: 具体错误信息"
}
```

---

## 联系信息

如有问题或建议，请联系开发团队。

