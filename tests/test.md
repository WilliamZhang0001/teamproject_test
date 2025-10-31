# 进入正确的项目目录
cd "C:\Users\12618\Desktop\C\capstone-project-25t3-9900-h15a-almond-ml_version1\capstone-project-25t3-9900-h15a-almond-ml_version1"

# 使用colab环境的Python运行（测试版本）
& D:/anaconda3/envs/colab/python.exe scripts/run_pipeline.py --mode protein --proteins lysozyme,albumin --max-per-source 5

# 或者使用完整数据集（训练模型）
& D:/anaconda3/envs/colab/python.exe scripts/run_pipeline.py --mode protein --train --max-per-source 10

& D:/anaconda3/envs/colab/python.exe scripts/run_pipeline.py --skip-scraping

D:/anaconda3/envs/colab/python.exe scripts/train_dual_track_system.py --model rf --cv --data literature_mining/storage/structured_store.jsonl --output-dir models/dual_track

cd "C:\Users\12618\Desktop\C\version1" ; D:/anaconda3/envs/colab/python.exe scripts/train_dual_track_system.py --model rf --cv --output-dir models/dual_track

D:/anaconda3/envs/colab/python.exe scripts/run_recommendation.py --interactive

# 1. 只提取记录（不训练模型）
python scripts/run_pipeline.py --mode biomolecule --skip-scraping

# 2. 提取记录 + 存储到数据库
python scripts/run_pipeline.py --mode biomolecule --skip-scraping --store literature_mining/storage/structured_store.jsonl

# 3. 提取记录 + 存储 + 训练模型（完整流程）
python scripts/run_pipeline.py --mode biomolecule --skip-scraping --train

python scripts/run_pipeline.py --mode biomolecule --overwrite --train

python scripts/run_pipeline.py --mode biomolecule --max-per-source 300 --overwrite --train
# 完全替换 raw_papers.json
python scripts/run_pipeline.py --mode biomolecule --append --train
# 会自动追加到已有数据，去重后合并

python scripts/run_pipeline.py --mode biomolecule --skip-scraping --overwrite --train

python scripts/train_dual_track_system.py --model rf --cv --smote --data literature_mining/storage/structured_store.jsonl --output-dir models/dual_track

# 3. 训练XGBoost进行性能对比
python scripts/train_dual_track_system.py --model xgb --cv --data literature_mining/storage/structured_store.jsonl 
--output-dir models/dual_track_xgb


  # 方法1：直接在 PowerShell 中运行
python scripts/train_dual_track_system.py --model rf --cv --smote --data literature_mining/storage/structured_store.jsonl --output-dir models/dual_track_rf_smote


python scripts/train_by_experiment_type.py --types stability,solubility,aggregation,general

python scripts/train_multi_models.py --experiment-type stability --mode classification

python scripts/train_multi_models.py --experiment-type stability --mode both --regress-params "pH,temperature_c"

python demo_advanced_features.py

python test_scenarios.py