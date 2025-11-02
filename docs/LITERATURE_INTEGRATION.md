# 文献数据库集成文档

## 概述

本文档描述了文献数据库的集成方案，该方案将文献数据存储到数据库中，并在ML预测结果中提供最相似的Top 3文献作为证据支持。

## 架构设计

### 数据库模型

#### 1. Literature（文献表）
存储文献的基本元数据：
- `id`: 主键
- `doi`: 文献DOI（唯一索引）
- `title`: 标题
- `authors`: 作者
- `pub_year`: 发表年份
- `source`: 来源
- `created_at`: 创建时间

#### 2. ExtractionRecord（提取记录表）
存储从文献中提取的实验参数：
- `id`: 主键
- `literature_id`: 外键关联Literature表
- 生物分子信息：`biomolecule_type`, `protein_name`, `polarity`, `property`
- 实验参数：`pH`, `temperature_c`, `concentration_mg_ml`, `ionic_strength_mM`, `additive`, `time_min`, `shear_rate_s1`, `pressure_bar`
- 结果信息：`outcome_score`, `outcome_label`, `outcome_text`, `source_section`
- 元数据：`confidence`, `raw_context`, `full_data` (JSON格式)

### 相似度算法

使用加权欧氏距离计算参数相似度：

```python
similarity = 1.0 - (weighted_distance / total_weight)
```

参数权重：
- pH: 0.25
- Temperature: 0.20
- Concentration: 0.20
- Ionic Strength: 0.15
- Additive: 0.10
- Time: 0.05
- Shear Rate: 0.03
- Pressure: 0.02

每个参数根据合理范围归一化，最终相似度会乘以置信度权重。

### API接口

#### 1. POST `/literature/load`
从JSONL文件加载文献数据到数据库

**响应示例：**
```json
{
  "status": "success",
  "message": "成功导入 20266 条文献记录",
  "count": 20266
}
```

#### 2. GET `/literature/search`
根据参数搜索相似文献

**参数：**
- `biomolecule_name`: 生物分子名称
- `property_type`: 属性类型（stability/solubility等）
- `pH`: pH值
- `temperature_c`: 温度
- `concentration_mg_ml`: 浓度
- `ionic_strength_mM`: 离子强度
- `limit`: 返回结果数量（默认3）

**响应示例：**
```json
{
  "status": "success",
  "count": 3,
  "results": [
    {
      "id": 1,
      "similarity_score": 0.85,
      "protein_name": "lysozyme",
      "parameters": {
        "pH": 7.0,
        "temperature_c": 25.0,
        "concentration_mg_ml": 10.0
      },
      "literature": {
        "doi": "10.xxx/xxx",
        "title": "Paper Title",
        "authors": "Author A, Author B",
        "pub_year": 2020
      }
    }
  ]
}
```

#### 3. POST `/literature/enhance-prediction`
增强ML预测结果，添加文献证据

**请求体：**
```json
{
  "ml_result": {
    "scenario": "classification",
    "prediction": "Good",
    "confidence": 0.85
  },
  "user_input": {
    "biomolecule_name": "lysozyme",
    "pH": 7.0,
    "temperature_c": 25.0
  },
  "top_k": 3
}
```

**响应示例：**
```json
{
  "prediction": {
    "scenario": "classification",
    "prediction": "Good",
    "confidence": 0.85
  },
  "evidence": {
    "top_similar_literature": [
      {
        "similarity_score": 0.85,
        "protein_name": "lysozyme",
        "literature": {
          "doi": "10.xxx/xxx",
          "title": "Paper Title"
        }
      }
    ],
    "count": 3
  },
  "input_parameters": {
    "pH": 7.0,
    "temperature_c": 25.0
  }
}
```

#### 4. GET `/literature/top-confidence`
获取高置信度的文献记录

**参数：**
- `biomolecule_name`: 生物分子名称
- `property_type`: 属性类型
- `limit`: 返回结果数量

## 使用指南

### 1. 初始化数据库

```bash
# 运行设置脚本
python scripts/setup_literature_db.py
```

这将：
- 创建数据库表
- 从JSONL文件导入文献数据
- 显示导入统计信息

### 2. 在ML引擎中使用

```python
from ml_engine.prediction.enhanced_predictor import EnhancedPredictor
from backend.app.services.literature_service import LiteratureService
from backend.app.core.db import SessionLocal

# 创建文献服务
db = SessionLocal()
literature_service = LiteratureService(db)

# 创建增强预测器
predictor = EnhancedPredictor(literature_service=literature_service)

# 预测并获取文献证据
user_input = {
    'biomolecule_name': 'lysozyme',
    'pH': 7.0,
    'temperature_c': 25.0
}

result = predictor.predict_with_evidence(user_input, top_k=3)

# 访问预测结果
print(f"预测: {result['prediction']}")
print(f"置信度: {result['confidence']}")

# 访问文献证据
evidence = result['evidence']['top_similar_literature']
print(f"找到 {len(evidence)} 篇相似文献")

for lit in evidence:
    print(f"- 相似度: {lit['similarity_score']:.2%}")
    print(f"  标题: {lit['literature']['title']}")
```

### 3. 运行测试

```bash
# 运行集成测试
python tests/test_literature_integration.py
```

测试内容：
1. 文献数据导入
2. 相似文献搜索
3. ML预测增强
4. 高置信度查询

## 文件结构

```
backend/app/
├── models/
│   └── literature.py           # 文献数据库模型
├── repos/
│   └── literature_repo.py      # 数据库访问层
├── services/
│   └── literature_service.py   # 文献服务层
└── routers/
    └── literature.py           # API路由

ml_engine/prediction/
└── enhanced_predictor.py       # 增强预测器

scripts/
└── setup_literature_db.py      # 数据库设置脚本

tests/
└── test_literature_integration.py  # 集成测试
```

## 工作流程

1. **数据导入**：从`literature_mining/storage/structured_store.jsonl`读取提取记录
2. **数据存储**：
   - 提取DOI创建Literature记录
   - 将参数和结果存储为ExtractionRecord记录
3. **相似度搜索**：
   - 根据用户输入/ML推荐参数计算相似度
   - 返回Top K个最相似的文献
4. **结果增强**：
   - 将文献证据附加到ML预测结果
   - 提供格式化的摘要信息

## 性能优化

1. **索引**：在`protein_name`, `doi`, `confidence`字段建立索引
2. **缓存**：可以缓存常用物质的相似文献结果
3. **分页**：大量结果时使用分页查询

## 未来改进

1. **向量化搜索**：使用向量数据库（如Faiss）加速相似度搜索
2. **NLP增强**：使用语义相似度补充参数相似度
3. **实时更新**：支持文献数据的增量更新
4. **多语言支持**：支持中文文献检索
5. **用户反馈**：记录用户对文献相关性的反馈，优化排序

## 注意事项

1. **数据库连接**：确保数据库配置正确（见`backend/app/core/config.py`）
2. **JSONL格式**：确保`structured_store.jsonl`格式正确
3. **内存使用**：大数据集导入时注意内存使用
4. **相似度阈值**：可以根据需要调整相似度阈值过滤结果

## 故障排查

### 问题：数据库连接失败
**解决方案**：检查数据库配置和服务状态

### 问题：导入数据为空
**解决方案**：检查JSONL文件路径和格式

### 问题：相似度搜索结果为空
**解决方案**：检查参数格式和数据库是否有相关数据

### 问题：相似度分数过低
**解决方案**：调整相似度算法权重或归一化方法




