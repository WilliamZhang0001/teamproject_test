# Scripts 目录

## 核心脚本

### 项目管理
- `setup_project.py` - 项目初始化脚本
- `start_services.py` - 启动所有服务

### 模型训练
- `train_model.py` - 训练ML模型的统一脚本

### 数据处理
- `run_pipeline.py` - 运行完整的数据处理管道（文献抓取 → NLP提取 → ML训练）

### 质量分析
- `analyze_quality.py` - 统一的数据质量分析工具

## 已弃用（可删除）
以下脚本为调试用途，可以安全删除：
- `debug_regex.py`
- `debug_full.py`
- `debug_sentences.py`
- `relaxed_extractor.py`
- `ultra_simple_extractor.py`
- `test_extractor.py`
- `analyze_extraction_limits.py`
- `check_project.py`
- `run_closed_loop*.py` (所有closed loop脚本)

## 使用方法

### 初始化项目
```bash
python scripts/setup_project.py
```

### 训练模型
```bash
python scripts/train_model.py --store literature_mining/storage/structured_store.jsonl --out models/saved/stability.pkl
```

### 运行完整管道
```bash
python scripts/run_pipeline.py --query "protein stability pH temperature"
```

### 分析数据质量
```bash
python scripts/analyze_quality.py --input literature_mining/storage/structured_store.jsonl
```

