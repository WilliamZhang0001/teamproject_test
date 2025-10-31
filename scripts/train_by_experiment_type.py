#!/usr/bin/env python3
"""
按实验类型训练分类模型

用法：
    python scripts/train_by_experiment_type.py --data literature_mining/storage/structured_store.jsonl
"""
import argparse
import sys
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, cross_val_predict
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ml_engine.features.improved_preprocess import records_to_improved_dataframe


def load_records(data_file: str) -> List[Dict]:
    """加载JSONL数据"""
    records = []
    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            records.append(json.loads(line))
    return records


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """准备特征（添加缺失指示器）"""
    # 创建副本避免SettingWithCopyWarning
    df = df.copy()
    
    # 特征列表
    feature_cols = [
        'pH', 'temperature_c', 'concentration_mg_ml',
        'ionic_strength_mM', 'time_min', 'shear_rate_s1', 'pressure_bar',
        'biomolecule_type'
    ]
    
    # 创建缺失指示器
    for col in ['pH', 'temperature_c', 'concentration_mg_ml', 'ionic_strength_mM', 
                'time_min', 'shear_rate_s1', 'pressure_bar']:
        if col in df.columns:
            df[f'{col}_missing'] = df[col].isna().astype(int)
    
    # 处理biomolecule_type（类别编码）
    if 'biomolecule_type' in df.columns:
        le = LabelEncoder()
        df['biomolecule_type_encoded'] = le.fit_transform(df['biomolecule_type'].fillna('unknown'))
    else:
        df['biomolecule_type_encoded'] = 0
    
    # 处理additive（是否有添加剂）
    if 'additive' in df.columns:
        df['has_additive'] = df['additive'].notna().astype(int)
    else:
        df['has_additive'] = 0
    
    return df


def train_model(df: pd.DataFrame, experiment_type: str, output_dir: Path):
    """训练单个实验类型的模型"""
    print(f"\n{'='*70}")
    print(f"Training model for: {experiment_type.upper()}")
    print('='*70)
    
    # 准备特征
    df = prepare_features(df)
    
    # 特征列
    feature_cols = [
        'pH', 'temperature_c', 'concentration_mg_ml',
        'ionic_strength_mM', 'time_min', 'shear_rate_s1', 'pressure_bar',
        'biomolecule_type_encoded', 'has_additive',
        'pH_missing', 'temperature_c_missing', 'concentration_mg_ml_missing',
        'ionic_strength_mM_missing', 'time_min_missing', 'shear_rate_s1_missing',
        'pressure_bar_missing'
    ]
    
    # 确保所有特征列存在
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0
    
    X = df[feature_cols]
    y = df['label']
    
    print(f"Dataset size: {len(df)} records")
    print(f"Features: {len(feature_cols)}")
    print(f"Label distribution:")
    print(y.value_counts())
    
    # 检查类别数量
    n_classes = len(y.unique())
    if n_classes < 2:
        print(f"\n[WARNING] Only {n_classes} class found in the data!")
        print(f"  Cannot train a binary classifier with single-class data.")
        print(f"  Skipping {experiment_type} model training.\n")
        return {
            'experiment_type': experiment_type,
            'n_samples': len(df),
            'n_classes': n_classes,
            'f1_score': None,
            'model_path': None,
            'status': 'skipped_single_class'
        }
    
    # 填充缺失值（处理全NaN列）
    # 对于全NaN的列，用0填充
    imputer = SimpleImputer(strategy='median', fill_value=0)
    X_imputed = imputer.fit_transform(X)
    
    # 检查输出列数是否匹配
    if X_imputed.shape[1] != len(X.columns):
        print(f"  WARNING: Imputer skipped some columns. Original: {len(X.columns)}, After: {X_imputed.shape[1]}")
        # 使用constant策略重新填充
        imputer = SimpleImputer(strategy='constant', fill_value=0)
        X_imputed = imputer.fit_transform(X)
    
    X_filled = pd.DataFrame(
        X_imputed,
        columns=X.columns,
        index=X.index
    )
    
    # 训练模型
    print("\nTraining RandomForest...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=4,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_filled, y)
    
    # 交叉验证
    print("\nCross-validation (5-fold)...")
    cv_scores = cross_val_score(model, X_filled, y, cv=5, scoring='f1_weighted', n_jobs=-1)
    print(f"F1-scores: {cv_scores}")
    print(f"Mean F1: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
    
    # 预测和评估
    y_pred = cross_val_predict(model, X_filled, y, cv=5, n_jobs=-1)
    print("\nClassification Report:")
    # 获取实际存在的类别，避免单类数据错误
    unique_labels = sorted(y.unique())
    label_names = ['Unstable' if l == 0 else 'Stable' for l in unique_labels]
    print(classification_report(y, y_pred, labels=unique_labels, target_names=label_names, zero_division=0))
    
    print("\nConfusion Matrix:")
    cm = confusion_matrix(y, y_pred)
    print(cm)
    
    # 特征重要性
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTop 10 Feature Importances:")
    print(feature_importance.head(10))
    
    # 保存模型
    output_dir.mkdir(parents=True, exist_ok=True)
    model_file = output_dir / f'{experiment_type}_classifier.pkl'
    
    with model_file.open('wb') as f:
        pickle.dump({
            'model': model,
            'imputer': imputer,
            'feature_cols': feature_cols,
            'experiment_type': experiment_type,
            'n_samples': len(df),
            'f1_score': cv_scores.mean(),
            'feature_importance': feature_importance.to_dict('records')
        }, f)
    
    print(f"\n✅ Model saved to: {model_file}")
    
    return {
        'experiment_type': experiment_type,
        'n_samples': len(df),
        'f1_score': cv_scores.mean(),
        'model_file': str(model_file)
    }


def main():
    parser = argparse.ArgumentParser(description="按实验类型训练分类模型")
    parser.add_argument(
        '--data',
        type=str,
        default='literature_mining/storage/structured_store.jsonl',
        help='JSONL数据文件路径'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='models/by_experiment_type',
        help='模型输出目录'
    )
    parser.add_argument(
        '--types',
        type=str,
        default='stability,solubility,general',
        help='要训练的实验类型（逗号分隔），general表示通用模型'
    )
    
    args = parser.parse_args()
    
    print("\n=== Training Models by Experiment Type ===")
    print(f"Data file: {args.data}")
    print(f"Output dir: {args.output_dir}")
    
    # 加载数据
    print("\nLoading data...")
    records = load_records(args.data)
    print(f"Loaded {len(records)} records")
    
    # 转换为DataFrame
    df_all = records_to_improved_dataframe(records)
    print(f"Valid records (with labels): {len(df_all)}")
    
    # 统计每种实验类型的数据量
    if 'property' in df_all.columns:
        print("\nExperiment type distribution:")
        print(df_all['property'].value_counts())
    
    # 训练模型
    output_dir = Path(args.output_dir)
    experiment_types = [t.strip() for t in args.types.split(',')]
    results = []
    
    for exp_type in experiment_types:
        if exp_type == 'general':
            # 训练通用模型（所有数据）
            df_subset = df_all
        else:
            # 训练特定实验类型的模型
            if 'property' not in df_all.columns:
                print(f"⚠️  Warning: 'property' column not found, skipping {exp_type}")
                continue
            df_subset = df_all[df_all['property'] == exp_type]
            
            if len(df_subset) < 100:
                print(f"⚠️  Warning: {exp_type} has only {len(df_subset)} records, skipping")
                continue
        
        result = train_model(df_subset, exp_type, output_dir)
        results.append(result)
    
    # 保存训练摘要
    summary_file = output_dir / 'training_summary.json'
    with summary_file.open('w', encoding='utf-8') as f:
        json.dump({
            'total_records': len(records),
            'valid_records': len(df_all),
            'models': results
        }, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*70)
    print("=== Training Complete! ===")
    print("="*70)
    print(f"\nTrained {len(results)} models:")
    for r in results:
        print(f"  - {r['experiment_type']}: {r['n_samples']} samples, F1={r['f1_score']:.3f}")
    print(f"\nSummary saved to: {summary_file}")


if __name__ == '__main__':
    main()

