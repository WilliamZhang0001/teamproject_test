"""
多模型训练和对比脚本

支持的功能：
1. 多种分类算法对比（RandomForest, XGBoost, LightGBM, SVM）
2. 回归模型训练（预测具体参数值）
3. 分位数回归（预测参数范围）
4. 模型性能对比报告
"""
import argparse
import json
import pickle
import warnings
from pathlib import Path
from collections import defaultdict

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score, cross_val_predict, KFold
from sklearn.metrics import (classification_report, confusion_matrix, 
                             mean_squared_error, mean_absolute_error, r2_score)

# 尝试导入可选依赖
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("Warning: XGBoost not installed. Install with: pip install xgboost")

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False
    print("Warning: LightGBM not installed. Install with: pip install lightgbm")

# 导入本地模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from ml_engine.features.improved_preprocess import records_to_improved_dataframe

warnings.filterwarnings('ignore')


def load_records(file_path: str) -> list:
    """加载JSONL格式的记录"""
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            records.append(json.loads(line))
    return records


def prepare_classification_features(df: pd.DataFrame):
    """准备分类模型的特征"""
    # 创建副本
    df = df.copy()
    
    # 特征列表
    numeric_cols = ['pH', 'temperature_c', 'concentration_mg_ml', 'ionic_strength_mM', 
                    'time_min', 'shear_rate_s1', 'pressure_bar']
    
    # 创建缺失指示器
    for col in numeric_cols:
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


def train_classifier_comparison(df: pd.DataFrame, experiment_type: str, output_dir: Path):
    """
    训练和对比多种分类器
    
    Args:
        df: 数据DataFrame
        experiment_type: 实验类型
        output_dir: 输出目录
    
    Returns:
        dict: 对比结果
    """
    print(f"\n{'='*70}")
    print(f"多模型对比 - {experiment_type.upper()}")
    print(f"{'='*70}")
    
    # 准备特征
    df = prepare_classification_features(df)
    
    # 特征列
    feature_cols = [
        'pH', 'temperature_c', 'concentration_mg_ml', 'ionic_strength_mM', 
        'time_min', 'shear_rate_s1', 'pressure_bar',
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
    
    print(f"\nDataset: {len(df)} records")
    print(f"Label distribution:")
    print(y.value_counts())
    
    # 检查类别数量
    n_classes = len(y.unique())
    if n_classes < 2:
        print(f"\n[WARNING] Only {n_classes} class found. Skipping classification.")
        return None
    
    # 填充缺失值
    imputer = SimpleImputer(strategy='constant', fill_value=0)
    X_filled = pd.DataFrame(
        imputer.fit_transform(X),
        columns=X.columns,
        index=X.index
    )
    
    # 定义要对比的模型
    models = {
        'RandomForest': RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=20,
            min_samples_leaf=10,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
    }
    
    if HAS_XGBOOST:
        models['XGBoost'] = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            eval_metric='logloss'
        )
    
    if HAS_LIGHTGBM:
        models['LightGBM'] = lgb.LGBMClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
    
    # 训练和评估每个模型
    results = {}
    
    for model_name, model in models.items():
        print(f"\n--- {model_name} ---")
        
        # 交叉验证
        cv_scores = cross_val_score(model, X_filled, y, cv=5, scoring='f1_weighted', n_jobs=-1)
        print(f"Cross-validation F1: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
        
        # 训练最终模型
        model.fit(X_filled, y)
        
        # 预测
        y_pred = cross_val_predict(model, X_filled, y, cv=5, n_jobs=-1)
        
        # 分类报告
        unique_labels = sorted(y.unique())
        label_names = ['Unstable' if l == 0 else 'Stable' for l in unique_labels]
        report = classification_report(y, y_pred, labels=unique_labels, 
                                      target_names=label_names, 
                                      output_dict=True, zero_division=0)
        
        print(f"Accuracy: {report['accuracy']:.3f}")
        print(f"F1-score (weighted): {report['weighted avg']['f1-score']:.3f}")
        
        # 保存结果
        results[model_name] = {
            'cv_f1_mean': float(cv_scores.mean()),
            'cv_f1_std': float(cv_scores.std()),
            'accuracy': report['accuracy'],
            'f1_weighted': report['weighted avg']['f1-score'],
            'precision': report['weighted avg']['precision'],
            'recall': report['weighted avg']['recall']
        }
        
        # 保存模型
        if model_name in ['XGBoost', 'LightGBM']:
            model_filename = f"{experiment_type}_{model_name.lower()}.pkl"
            model_path = output_dir / model_filename
            with open(model_path, 'wb') as f:
                pickle.dump({
                    'model': model,
                    'imputer': imputer,
                    'feature_cols': feature_cols,
                    'experiment_type': experiment_type,
                    'model_type': model_name,
                    'f1_score': float(cv_scores.mean())
                }, f)
            print(f"Model saved: {model_path}")
    
    # 打印对比表
    print(f"\n{'='*70}")
    print("Model Comparison Summary")
    print(f"{'='*70}")
    print(f"{'Model':<15} {'CV F1':<10} {'Accuracy':<10} {'F1':<10} {'Precision':<10} {'Recall':<10}")
    print("-" * 70)
    for model_name, metrics in results.items():
        print(f"{model_name:<15} "
              f"{metrics['cv_f1_mean']:.3f}      "
              f"{metrics['accuracy']:.3f}      "
              f"{metrics['f1_weighted']:.3f}      "
              f"{metrics['precision']:.3f}       "
              f"{metrics['recall']:.3f}")
    
    return results


def train_regressor_for_parameter(df: pd.DataFrame, target_param: str, 
                                   experiment_type: str, output_dir: Path):
    """
    训练回归模型预测特定参数的值
    
    Args:
        df: 数据DataFrame
        target_param: 目标参数（如'pH', 'temperature_c'）
        experiment_type: 实验类型
        output_dir: 输出目录
    
    Returns:
        dict: 回归结果
    """
    print(f"\n{'='*70}")
    print(f"回归模型训练 - 预测 {target_param}")
    print(f"{'='*70}")
    
    # 过滤出有目标参数值的记录
    df_reg = df[df[target_param].notna()].copy()
    
    if len(df_reg) < 100:
        print(f"[WARNING] 数据太少 ({len(df_reg)} records), 跳过回归训练")
        return None
    
    print(f"Dataset: {len(df_reg)} records with {target_param}")
    
    # 准备特征
    df_reg = prepare_classification_features(df_reg)
    
    # 特征列（排除目标参数）
    all_params = ['pH', 'temperature_c', 'concentration_mg_ml', 'ionic_strength_mM', 
                  'time_min', 'shear_rate_s1', 'pressure_bar']
    feature_params = [p for p in all_params if p != target_param]
    
    feature_cols = feature_params + [
        'biomolecule_type_encoded', 'has_additive'
    ] + [f'{p}_missing' for p in feature_params]
    
    # 确保所有特征列存在
    for col in feature_cols:
        if col not in df_reg.columns:
            df_reg[col] = 0
    
    X = df_reg[feature_cols]
    y = df_reg[target_param]
    
    # 填充缺失值
    imputer = SimpleImputer(strategy='constant', fill_value=0)
    X_filled = pd.DataFrame(
        imputer.fit_transform(X),
        columns=X.columns,
        index=X.index
    )
    
    # 训练RandomForest回归器
    print("\nTraining RandomForest Regressor...")
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_split=20,
        min_samples_leaf=10,
        random_state=42,
        n_jobs=-1
    )
    
    # 交叉验证
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    y_pred = cross_val_predict(model, X_filled, y, cv=cv, n_jobs=-1)
    
    # 评估指标
    mse = mean_squared_error(y, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y, y_pred)
    r2 = r2_score(y, y_pred)
    
    print(f"\nRegression Metrics:")
    print(f"  RMSE: {rmse:.3f}")
    print(f"  MAE: {mae:.3f}")
    print(f"  R2 Score: {r2:.3f}")
    print(f"  Target range: [{y.min():.2f}, {y.max():.2f}]")
    print(f"  Mean absolute error %: {(mae / y.mean() * 100):.1f}%")
    
    # 训练最终模型
    model.fit(X_filled, y)
    
    # 保存模型
    model_path = output_dir / f"{experiment_type}_{target_param}_regressor.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump({
            'model': model,
            'imputer': imputer,
            'feature_cols': feature_cols,
            'target_param': target_param,
            'experiment_type': experiment_type,
            'model_type': 'RandomForestRegressor'
        }, f)
    print(f"\nModel saved: {model_path}")
    
    return {
        'target_param': target_param,
        'n_samples': len(df_reg),
        'rmse': float(rmse),
        'mae': float(mae),
        'r2': float(r2),
        'target_range': [float(y.min()), float(y.max())],
        'mae_percentage': float(mae / y.mean() * 100)
    }


def main():
    parser = argparse.ArgumentParser(description="多模型训练和对比")
    parser.add_argument(
        '--data',
        type=str,
        default='literature_mining/storage/structured_store.jsonl',
        help='JSONL数据文件路径'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='models/multi_models',
        help='模型输出目录'
    )
    parser.add_argument(
        '--experiment-type',
        type=str,
        default='stability',
        choices=['stability', 'solubility', 'aggregation'],
        help='实验类型'
    )
    parser.add_argument(
        '--mode',
        type=str,
        default='both',
        choices=['classification', 'regression', 'both'],
        help='训练模式：分类、回归或两者'
    )
    parser.add_argument(
        '--regress-params',
        type=str,
        default='pH,temperature_c,concentration_mg_ml',
        help='需要训练回归模型的参数（逗号分隔）'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("多模型训练系统")
    print("="*70)
    print(f"Data: {args.data}")
    print(f"Output: {args.output_dir}")
    print(f"Experiment type: {args.experiment_type}")
    print(f"Mode: {args.mode}")
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载数据
    print("\nLoading data...")
    records = load_records(args.data)
    print(f"Loaded {len(records)} records")
    
    # 转换为DataFrame
    df_all = records_to_improved_dataframe(records)
    print(f"Valid records: {len(df_all)}")
    
    # 过滤特定实验类型
    if 'property' in df_all.columns:
        df_exp = df_all[df_all['property'] == args.experiment_type]
        print(f"{args.experiment_type} records: {len(df_exp)}")
    else:
        df_exp = df_all
    
    all_results = {
        'experiment_type': args.experiment_type,
        'total_records': len(records),
        'valid_records': len(df_all),
        'experiment_records': len(df_exp)
    }
    
    # 分类模型对比
    if args.mode in ['classification', 'both']:
        classification_results = train_classifier_comparison(df_exp, args.experiment_type, output_dir)
        all_results['classification'] = classification_results
    
    # 回归模型训练
    if args.mode in ['regression', 'both']:
        regress_params = [p.strip() for p in args.regress_params.split(',')]
        regression_results = {}
        
        for param in regress_params:
            if param in df_exp.columns:
                result = train_regressor_for_parameter(df_exp, param, args.experiment_type, output_dir)
                if result:
                    regression_results[param] = result
        
        all_results['regression'] = regression_results
    
    # 保存对比结果
    results_file = output_dir / f"{args.experiment_type}_comparison.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*70)
    print("Training Complete!")
    print("="*70)
    print(f"Results saved to: {results_file}")


if __name__ == '__main__':
    main()

