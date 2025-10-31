"""
高级功能演示脚本

演示内容：
1. 使用回归模型预测具体参数值
2. 使用RandomForest的多棵树估计预测范围
3. 对比多个模型的预测结果
"""
import pickle
import json
import numpy as np
import pandas as pd
from pathlib import Path


def demo_regression_prediction():
    """演示1：使用回归模型预测pH值"""
    print("\n" + "="*70)
    print("演示1：回归模型预测具体参数值")
    print("="*70)
    
    # 检查回归模型是否存在
    script_dir = Path(__file__).parent.resolve()
    model_path = script_dir / "models" / "multi_models" / "stability_pH_regressor.pkl"
    
    if not model_path.exists():
        print("\n[INFO] 回归模型不存在，请先训练：")
        print("python scripts/train_multi_models.py --experiment-type stability --mode regression --regress-params pH")
        return
    
    # 加载模型
    print(f"\n加载回归模型: {model_path.name}")
    with open(model_path, 'rb') as f:
        model_dict = pickle.load(f)
    
    model = model_dict['model']
    imputer = model_dict['imputer']
    feature_cols = model_dict['feature_cols']
    
    print(f"目标参数: {model_dict['target_param']}")
    print(f"模型类型: {model_dict['model_type']}")
    
    # 准备输入（已知温度和浓度，预测最佳pH）
    print("\n输入条件:")
    input_data = {
        'temperature_c': 25.0,
        'concentration_mg_ml': 10.0,
        'ionic_strength_mM': 150.0,
        'time_min': 0,
        'shear_rate_s1': 0,
        'pressure_bar': 0,
        'biomolecule_type_encoded': 2,  # protein
        'has_additive': 0,
        'temperature_c_missing': 0,
        'concentration_mg_ml_missing': 0,
        'ionic_strength_mM_missing': 0,
        'time_min_missing': 1,
        'shear_rate_s1_missing': 1,
        'pressure_bar_missing': 1
    }
    
    print(f"  Temperature: {input_data['temperature_c']} °C")
    print(f"  Concentration: {input_data['concentration_mg_ml']} mg/mL")
    print(f"  Ionic Strength: {input_data['ionic_strength_mM']} mM")
    
    # 创建DataFrame
    X = pd.DataFrame([input_data])
    
    # 确保列顺序正确
    X_ordered = X[feature_cols]
    
    # 填充缺失值
    X_filled = imputer.transform(X_ordered)
    X_filled = pd.DataFrame(X_filled, columns=feature_cols)
    
    # 预测
    predicted_pH = model.predict(X_filled)[0]
    
    print(f"\n预测结果:")
    print(f"  推荐pH值: {predicted_pH:.2f}")
    
    # 使用RandomForest的多棵树估计不确定性
    if hasattr(model, 'estimators_'):
        print(f"\n不确定性分析（基于{len(model.estimators_)}棵决策树）:")
        predictions = np.array([tree.predict(X_filled)[0] for tree in model.estimators_])
        
        mean_pred = predictions.mean()
        std_pred = predictions.std()
        
        # 置信区间
        conf_68 = (mean_pred - std_pred, mean_pred + std_pred)  # ~68% CI
        conf_95 = (mean_pred - 1.96 * std_pred, mean_pred + 1.96 * std_pred)  # 95% CI
        
        print(f"  平均预测: {mean_pred:.2f}")
        print(f"  标准差: {std_pred:.2f}")
        print(f"  68%置信区间: [{conf_68[0]:.2f}, {conf_68[1]:.2f}]")
        print(f"  95%置信区间: [{conf_95[0]:.2f}, {conf_95[1]:.2f}]")
        print(f"  预测范围: ±{1.96 * std_pred:.2f} pH单位")


def demo_prediction_range_from_iqr():
    """演示2：使用IQR统计获取参数推荐范围"""
    print("\n" + "="*70)
    print("演示2：使用IQR统计预测参数范围")
    print("="*70)
    
    script_dir = Path(__file__).parent.resolve()
    iqr_path = script_dir / "models" / "iqr_statistics.json"
    
    if not iqr_path.exists():
        print("\n[INFO] IQR统计文件不存在，请先生成")
        return
    
    # 加载IQR统计
    with open(iqr_path, 'r', encoding='utf-8') as f:
        iqr_stats = json.load(f)
    
    print("\n查询: Stability实验的推荐参数范围")
    
    if 'by_experiment_type' in iqr_stats and 'stability' in iqr_stats['by_experiment_type']:
        stability_stats = iqr_stats['by_experiment_type']['stability']
        
        params_to_show = ['pH', 'temperature_c', 'concentration_mg_ml', 'ionic_strength_mM']
        
        for param in params_to_show:
            if param in stability_stats:
                stats = stability_stats[param]
                
                print(f"\n{param}:")
                print(f"  推荐范围 (IQR): [{stats['q1']:.2f}, {stats['q3']:.2f}]")
                print(f"  中位数: {stats['median']:.2f}")
                print(f"  全范围: [{stats['min']:.2f}, {stats['max']:.2f}]")
                print(f"  样本数: {stats['count']}")


def demo_model_comparison():
    """演示3：对比不同模型的预测结果"""
    print("\n" + "="*70)
    print("演示3：多模型预测对比")
    print("="*70)
    
    script_dir = Path(__file__).parent.resolve()
    
    # 模型路径
    models_to_compare = {
        'RandomForest': script_dir / "models" / "by_experiment_type" / "stability_classifier.pkl",
        'XGBoost': script_dir / "models" / "multi_models" / "stability_xgboost.pkl"
    }
    
    # 检查哪些模型存在
    available_models = {}
    for name, path in models_to_compare.items():
        if path.exists():
            available_models[name] = path
    
    if len(available_models) == 0:
        print("\n[INFO] 没有可用的模型，请先训练")
        return
    
    print(f"\n可用模型: {', '.join(available_models.keys())}")
    
    # 准备测试输入
    print("\n测试输入:")
    test_input = {
        'pH': 7.0,
        'temperature_c': 25.0,
        'concentration_mg_ml': 10.0,
        'ionic_strength_mM': 150.0,
        'time_min': 60.0,
        'shear_rate_s1': 0,
        'pressure_bar': 0,
        'biomolecule_type_encoded': 2,
        'has_additive': 1,
        'pH_missing': 0,
        'temperature_c_missing': 0,
        'concentration_mg_ml_missing': 0,
        'ionic_strength_mM_missing': 0,
        'time_min_missing': 0,
        'shear_rate_s1_missing': 1,
        'pressure_bar_missing': 1
    }
    
    print(f"  pH: {test_input['pH']}")
    print(f"  Temperature: {test_input['temperature_c']} °C")
    print(f"  Concentration: {test_input['concentration_mg_ml']} mg/mL")
    print(f"  Ionic Strength: {test_input['ionic_strength_mM']} mM")
    print(f"  Additive: glycerol")
    
    # 对比预测结果
    print("\n预测结果对比:")
    print(f"{'模型':<15} {'预测':<15} {'Stable概率':<15} {'Unstable概率':<15}")
    print("-" * 60)
    
    for model_name, model_path in available_models.items():
        # 加载模型
        with open(model_path, 'rb') as f:
            model_dict = pickle.load(f)
        
        model = model_dict['model']
        imputer = model_dict['imputer']
        feature_cols = model_dict['feature_cols']
        
        # 准备输入
        X = pd.DataFrame([test_input])
        X_ordered = X[feature_cols]
        X_filled = imputer.transform(X_ordered)
        X_filled = pd.DataFrame(X_filled, columns=feature_cols)
        
        # 预测
        prediction = model.predict(X_filled)[0]
        proba = model.predict_proba(X_filled)[0]
        
        pred_label = "Stable" if prediction == 1 else "Unstable"
        
        print(f"{model_name:<15} {pred_label:<15} {proba[1]:.2%}           {proba[0]:.2%}")
    
    print("\n说明: 如果不同模型预测不一致，可以:")
    print("  1. 使用概率投票（soft voting）")
    print("  2. 选择置信度最高的预测")
    print("  3. 使用模型集成（ensemble）")


def demo_ensemble_prediction():
    """演示4：模型集成预测"""
    print("\n" + "="*70)
    print("演示4：模型集成（Ensemble）预测")
    print("="*70)
    
    script_dir = Path(__file__).parent.resolve()
    
    # 加载所有可用模型
    models = {}
    model_paths = {
        'RandomForest': script_dir / "models" / "by_experiment_type" / "stability_classifier.pkl",
        'XGBoost': script_dir / "models" / "multi_models" / "stability_xgboost.pkl"
    }
    
    for name, path in model_paths.items():
        if path.exists():
            with open(path, 'rb') as f:
                models[name] = pickle.load(f)
    
    if len(models) < 2:
        print("\n[INFO] 需要至少2个模型进行集成")
        print("请先训练XGBoost模型: python scripts/train_multi_models.py --experiment-type stability")
        return
    
    print(f"\n使用 {len(models)} 个模型进行集成预测")
    
    # 测试输入
    test_input = {
        'pH': 7.0,
        'temperature_c': 25.0,
        'concentration_mg_ml': 10.0,
        'ionic_strength_mM': 150.0,
        'time_min': 60.0,
        'shear_rate_s1': 0,
        'pressure_bar': 0,
        'biomolecule_type_encoded': 2,
        'has_additive': 1,
        'pH_missing': 0,
        'temperature_c_missing': 0,
        'concentration_mg_ml_missing': 0,
        'ionic_strength_mM_missing': 0,
        'time_min_missing': 0,
        'shear_rate_s1_missing': 1,
        'pressure_bar_missing': 1
    }
    
    # 收集所有模型的预测概率
    all_probas = []
    
    for model_name, model_dict in models.items():
        model = model_dict['model']
        imputer = model_dict['imputer']
        feature_cols = model_dict['feature_cols']
        
        X = pd.DataFrame([test_input])
        X_ordered = X[feature_cols]
        X_filled = imputer.transform(X_ordered)
        X_filled = pd.DataFrame(X_filled, columns=feature_cols)
        
        proba = model.predict_proba(X_filled)[0]
        all_probas.append(proba)
        
        print(f"  {model_name}: Stable={proba[1]:.2%}, Unstable={proba[0]:.2%}")
    
    # 集成策略1：平均概率
    avg_proba = np.mean(all_probas, axis=0)
    avg_prediction = 1 if avg_proba[1] > 0.5 else 0
    
    print(f"\n集成预测 (平均概率):")
    print(f"  Stable概率: {avg_proba[1]:.2%}")
    print(f"  Unstable概率: {avg_proba[0]:.2%}")
    print(f"  最终预测: {'Stable' if avg_prediction == 1 else 'Unstable'}")
    
    # 集成策略2：加权投票（XGBoost权重更高）
    if 'XGBoost' in models and 'RandomForest' in models:
        weights = {'RandomForest': 1.0, 'XGBoost': 2.0}  # XGBoost权重2倍
        weighted_proba = np.average(all_probas, axis=0, 
                                    weights=[weights[name] for name in models.keys()])
        weighted_prediction = 1 if weighted_proba[1] > 0.5 else 0
        
        print(f"\n集成预测 (加权投票, XGBoost权重x2):")
        print(f"  Stable概率: {weighted_proba[1]:.2%}")
        print(f"  Unstable概率: {weighted_proba[0]:.2%}")
        print(f"  最终预测: {'Stable' if weighted_prediction == 1 else 'Unstable'}")


def main():
    print("\n" + "="*70)
    print("高级功能演示 - ML系统")
    print("="*70)
    print("\n本脚本演示以下功能:")
    print("1. 回归模型预测具体参数值 + 不确定性估计")
    print("2. 使用IQR统计获取参数范围")
    print("3. 多模型预测对比")
    print("4. 模型集成预测")
    
    # 运行所有演示
    demo_regression_prediction()
    demo_prediction_range_from_iqr()
    demo_model_comparison()
    demo_ensemble_prediction()
    
    print("\n" + "="*70)
    print("演示完成！")
    print("="*70)
    print("\n下一步:")
    print("1. 如果缺少某些模型，运行训练脚本:")
    print("   python scripts/train_multi_models.py --experiment-type stability --mode both")
    print("2. 查看多模型对比指南: 多模型对比指南.md")
    print("3. 集成到API中")


if __name__ == '__main__':
    main()

