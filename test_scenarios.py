"""
测试脚本：演示两种应用场景

场景1：完整参数验证 - 判断实验条件是否可行
场景2：参数推荐 - 根据部分参数推荐其他参数
"""
import pickle
import json
import pandas as pd
import numpy as np
from pathlib import Path


def load_model(model_path: str):
    """加载训练好的模型（包含模型、imputer和特征列）"""
    with open(model_path, 'rb') as f:
        model_dict = pickle.load(f)
    
    # 模型文件是字典格式，包含model、imputer、feature_cols等
    return model_dict


def load_iqr_statistics(stats_path: str):
    """加载IQR统计数据"""
    with open(stats_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def prepare_input_features(params: dict, biomolecule_type: str = "protein") -> pd.DataFrame:
    """
    准备模型输入特征
    
    Args:
        params: 参数字典（pH, temperature_c, concentration_mg_ml等）
        biomolecule_type: 生物分子类型（protein/peptide/polysaccharide）
    
    Returns:
        包含16个特征的DataFrame
    """
    # 生物分子类型编码
    type_mapping = {'peptide': 0, 'polysaccharide': 1, 'protein': 2, 'unknown': 3}
    type_encoded = type_mapping.get(biomolecule_type, 2)
    
    # 基础参数
    feature_dict = {
        'pH': params.get('pH'),
        'temperature_c': params.get('temperature_c'),
        'concentration_mg_ml': params.get('concentration_mg_ml'),
        'ionic_strength_mM': params.get('ionic_strength_mM'),
        'time_min': params.get('time_min'),
        'shear_rate_s1': params.get('shear_rate_s1'),
        'pressure_bar': params.get('pressure_bar'),
        'biomolecule_type_encoded': type_encoded,
        'has_additive': 1 if params.get('additive') else 0,
    }
    
    # 缺失指示器
    for param in ['pH', 'temperature_c', 'concentration_mg_ml', 'ionic_strength_mM', 
                  'time_min', 'shear_rate_s1', 'pressure_bar']:
        feature_dict[f'{param}_missing'] = 1 if feature_dict[param] is None else 0
        # 填充缺失值为0
        if feature_dict[param] is None:
            feature_dict[param] = 0
    
    return pd.DataFrame([feature_dict])


def scenario1_validate_parameters(model_dict, params: dict, biomolecule_type: str, property_type: str):
    """
    场景1：完整参数验证
    
    用户提供完整或大部分参数，模型判断该实验条件是否可行
    """
    print("\n" + "="*70)
    print("场景1：参数可行性验证")
    print("="*70)
    
    print(f"\n输入参数:")
    print(f"  生物分子类型: {biomolecule_type}")
    print(f"  实验类型: {property_type}")
    for key, value in params.items():
        if value is not None:
            print(f"  {key}: {value}")
    
    # 提取模型和imputer
    model = model_dict['model']
    imputer = model_dict['imputer']
    feature_cols = model_dict['feature_cols']
    
    # 准备特征
    X_raw = prepare_input_features(params, biomolecule_type)
    
    # 确保列顺序与训练时一致
    X_ordered = X_raw[feature_cols]
    
    # 使用相同的imputer填充缺失值
    X_imputed = imputer.transform(X_ordered)
    
    # 将numpy数组转回DataFrame，保留列名
    X_filled = pd.DataFrame(X_imputed, columns=feature_cols)
    
    # 预测
    prediction = model.predict(X_filled)[0]
    proba = model.predict_proba(X_filled)[0]
    
    # 结果
    result = "Stable (稳定)" if prediction == 1 else "Unstable (不稳定)"
    confidence = proba[int(prediction)]
    
    print(f"\n预测结果:")
    print(f"  结论: {result}")
    print(f"  置信度: {confidence:.2%}")
    print(f"  概率分布: Unstable={proba[0]:.2%}, Stable={proba[1]:.2%}")
    
    # 建议
    if prediction == 1 and confidence > 0.7:
        print(f"\n建议: 该实验条件预计可行，建议进行实验验证")
    elif prediction == 1 and confidence <= 0.7:
        print(f"\n建议: 该实验条件可能可行，但置信度较低，建议谨慎验证或调整参数")
    elif prediction == 0 and confidence > 0.7:
        print(f"\n建议: 该实验条件预计不稳定，建议调整参数")
    else:
        print(f"\n建议: 预测不确定，建议参考文献或进行小规模测试")
    
    return {
        'prediction': 'stable' if prediction == 1 else 'unstable',
        'confidence': float(confidence),
        'probabilities': {'unstable': float(proba[0]), 'stable': float(proba[1])}
    }


def scenario2_recommend_parameters(iqr_stats: dict, known_params: dict, 
                                   biomolecule_name: str, property_type: str,
                                   recommend_params: list):
    """
    场景2：参数推荐
    
    用户提供部分参数，系统推荐其他参数的合适范围
    """
    print("\n" + "="*70)
    print("场景2：参数推荐")
    print("="*70)
    
    print(f"\n查询信息:")
    print(f"  生物分子: {biomolecule_name}")
    print(f"  实验类型: {property_type}")
    print(f"\n已知参数:")
    for key, value in known_params.items():
        if value is not None:
            print(f"  {key}: {value}")
    print(f"\n需要推荐的参数: {', '.join(recommend_params)}")
    
    # 查找最匹配的统计数据
    # 优先级: 按物质 > 按实验类型 > 通用
    recommendations = {}
    
    for param in recommend_params:
        print(f"\n--- {param} 推荐 ---")
        
        stats = None
        source = None
        
        # 优先级1: 按物质+实验类型查找
        if 'by_experiment_and_biomolecule' in iqr_stats:
            key_combined = f"{property_type}_{biomolecule_name}"
            if key_combined in iqr_stats['by_experiment_and_biomolecule']:
                if param in iqr_stats['by_experiment_and_biomolecule'][key_combined]:
                    stats = iqr_stats['by_experiment_and_biomolecule'][key_combined][param]
                    source = f"基于 {biomolecule_name} 的 {property_type} 数据"
        
        # 优先级2: 按实验类型查找
        if stats is None and 'by_experiment_type' in iqr_stats:
            if property_type in iqr_stats['by_experiment_type']:
                if param in iqr_stats['by_experiment_type'][property_type]:
                    stats = iqr_stats['by_experiment_type'][property_type][param]
                    source = f"基于所有 {property_type} 实验数据"
        
        # 优先级3: 按物质查找（所有实验类型）
        if stats is None and 'by_biomolecule' in iqr_stats:
            if biomolecule_name in iqr_stats['by_biomolecule']:
                if param in iqr_stats['by_biomolecule'][biomolecule_name]:
                    stats = iqr_stats['by_biomolecule'][biomolecule_name][param]
                    source = f"基于 {biomolecule_name} 的所有实验数据"
        
        # 优先级4: 使用全局统计
        if stats is None and 'global' in iqr_stats:
            if param in iqr_stats['global']:
                stats = iqr_stats['global'][param]
                source = "基于所有实验数据"
        
        if stats is None:
            print(f"  [未找到数据] 该参数暂无统计数据")
            recommendations[param] = None
            continue
        
        # 提取统计信息
        q1 = stats.get('q1', stats.get('25%'))
        median = stats.get('median', stats.get('50%'))
        q3 = stats.get('q3', stats.get('75%'))
        min_val = stats.get('min')
        max_val = stats.get('max')
        count = stats.get('count', 0)
        
        print(f"  数据来源: {source} ({count} 条记录)")
        print(f"  推荐范围 (IQR): {q1:.2f} - {q3:.2f}")
        print(f"  中位数: {median:.2f}")
        print(f"  最小-最大值: {min_val:.2f} - {max_val:.2f}")
        
        # 给出具体建议
        if median is not None:
            print(f"  建议值: {median:.2f} (基于中位数)")
        
        recommendations[param] = {
            'recommended_value': float(median) if median is not None else None,
            'safe_range': [float(q1), float(q3)] if q1 is not None and q3 is not None else None,
            'full_range': [float(min_val), float(max_val)] if min_val is not None and max_val is not None else None,
            'sample_count': int(count),
            'source': source
        }
    
    return recommendations


def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("ML系统测试 - 两种应用场景演示")
    print("="*70)
    
    # 自动定位项目根目录（test_scenarios.py所在目录）
    script_dir = Path(__file__).parent.resolve()
    print(f"\n项目根目录: {script_dir}")
    
    # 检查必要文件
    model_dir = script_dir / "models" / "by_experiment_type"
    if not model_dir.exists():
        print(f"\n[ERROR] 模型目录不存在: {model_dir}")
        print("请先训练模型: python scripts/train_by_experiment_type.py")
        return
    
    iqr_path = script_dir / "models" / "iqr_statistics.json"
    if not iqr_path.exists():
        print(f"\n[ERROR] IQR统计文件不存在: {iqr_path}")
        print("请先生成统计数据: python scripts/generate_iqr_statistics.py")
        return
    
    # 加载资源
    print("\n加载模型和统计数据...")
    models = {}
    
    # 对每种实验类型，优先加载高性能模型（LightGBM > XGBoost > RandomForest）
    for model_type in ['stability', 'solubility', 'general']:
        model_loaded = False
        
        # 尝试加载多模型目录下的高性能模型
        multi_models_dir = script_dir / "models" / "multi_models"
        
        # 优先级1: LightGBM
        lightgbm_file = multi_models_dir / f"{model_type}_lightgbm.pkl"
        if lightgbm_file.exists():
            models[model_type] = load_model(str(lightgbm_file))
            model_info = models[model_type].get('model_type', 'LightGBM')
            f1_score = models[model_type].get('f1_score', None)
            f1_str = f"{f1_score:.3f}" if isinstance(f1_score, (int, float)) else "N/A"
            print(f"  [OK] {model_type} 模型已加载 ({model_info}, F1={f1_str})")
            model_loaded = True
        
        # 优先级2: XGBoost
        if not model_loaded:
            xgboost_file = multi_models_dir / f"{model_type}_xgboost.pkl"
            if xgboost_file.exists():
                models[model_type] = load_model(str(xgboost_file))
                model_info = models[model_type].get('model_type', 'XGBoost')
                f1_score = models[model_type].get('f1_score', None)
                f1_str = f"{f1_score:.3f}" if isinstance(f1_score, (int, float)) else "N/A"
                print(f"  [OK] {model_type} 模型已加载 ({model_info}, F1={f1_str})")
                model_loaded = True
        
        # 优先级3: RandomForest（默认）
        if not model_loaded:
            rf_file = model_dir / f"{model_type}_classifier.pkl"
            if rf_file.exists():
                models[model_type] = load_model(str(rf_file))
                print(f"  [OK] {model_type} 模型已加载 (RandomForest, baseline)")
                model_loaded = True
        
        if not model_loaded:
            print(f"  [SKIP] {model_type} 模型不存在")
    
    iqr_stats = load_iqr_statistics(str(iqr_path))
    print(f"  [OK] IQR统计数据已加载")
    
    # ========================================================================
    # 测试案例1: Stability - 完整参数验证
    # ========================================================================
    if 'stability' in models:
        test_case_1 = {
            'pH': 7.0,
            'temperature_c': 25.0,
            'concentration_mg_ml': 10.0,
            'ionic_strength_mM': 150.0,
            'additive': 'glycerol',
            'time_min': 60.0,
            'shear_rate_s1': None,
            'pressure_bar': None
        }
        
        result1 = scenario1_validate_parameters(
            model_dict=models['stability'],
            params=test_case_1,
            biomolecule_type='protein',
            property_type='stability'
        )
    
    # ========================================================================
    # 测试案例2: Solubility - 完整参数验证
    # ========================================================================
    if 'solubility' in models:
        test_case_2 = {
            'pH': 5.0,
            'temperature_c': 20.0,
            'concentration_mg_ml': 50.0,
            'ionic_strength_mM': 100.0,
            'additive': None,
            'time_min': None,
            'shear_rate_s1': None,
            'pressure_bar': None
        }
        
        result2 = scenario1_validate_parameters(
            model_dict=models['solubility'],
            params=test_case_2,
            biomolecule_type='protein',
            property_type='solubility'
        )
    
    # ========================================================================
    # 测试案例3: 参数推荐 - 已知pH和温度，推荐浓度和离子强度
    # ========================================================================
    test_case_3_known = {
        'pH': 7.4,
        'temperature_c': 37.0
    }
    
    result3 = scenario2_recommend_parameters(
        iqr_stats=iqr_stats,
        known_params=test_case_3_known,
        biomolecule_name='lysozyme',
        property_type='stability',
        recommend_params=['concentration_mg_ml', 'ionic_strength_mM']
    )
    
    # ========================================================================
    # 测试案例4: 参数推荐 - 仅已知pH，推荐温度和浓度
    # ========================================================================
    test_case_4_known = {
        'pH': 6.5
    }
    
    result4 = scenario2_recommend_parameters(
        iqr_stats=iqr_stats,
        known_params=test_case_4_known,
        biomolecule_name='insulin',
        property_type='solubility',
        recommend_params=['temperature_c', 'concentration_mg_ml']
    )
    
    # ========================================================================
    # 综合测试：先推荐参数，再验证可行性
    # ========================================================================
    print("\n" + "="*70)
    print("综合测试：参数推荐 + 可行性验证")
    print("="*70)
    
    if 'stability' in models:
        print("\n步骤1: 用户提供部分参数")
        user_input = {
            'pH': 7.0,
            'temperature_c': 25.0
        }
        print(f"  pH: {user_input['pH']}")
        print(f"  Temperature: {user_input['temperature_c']} °C")
        
        print("\n步骤2: 系统推荐其他参数")
        recommendations = scenario2_recommend_parameters(
            iqr_stats=iqr_stats,
            known_params=user_input,
            biomolecule_name='lysozyme',
            property_type='stability',
            recommend_params=['concentration_mg_ml', 'ionic_strength_mM']
        )
        
        # 使用推荐值
        complete_params = user_input.copy()
        for param, rec in recommendations.items():
            if rec and rec['recommended_value'] is not None:
                complete_params[param] = rec['recommended_value']
        
        # 填充其他参数为None
        for param in ['additive', 'time_min', 'shear_rate_s1', 'pressure_bar']:
            if param not in complete_params:
                complete_params[param] = None
        
        print("\n步骤3: 验证完整参数的可行性")
        result_combined = scenario1_validate_parameters(
            model_dict=models['stability'],
            params=complete_params,
            biomolecule_type='protein',
            property_type='stability'
        )
    
    # ========================================================================
    # 测试总结
    # ========================================================================
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    print("\n成功演示:")
    print("  1. 场景1（完整参数验证）- Stability实验")
    print("  2. 场景1（完整参数验证）- Solubility实验")
    print("  3. 场景2（参数推荐）- 基于部分参数推荐浓度和离子强度")
    print("  4. 场景2（参数推荐）- 基于pH推荐温度和浓度")
    print("  5. 综合场景 - 参数推荐 + 可行性验证")
    
    print("\n系统状态:")
    print(f"  可用模型: {len(models)}个")
    for model_name in models.keys():
        print(f"    - {model_name}")
    print(f"  IQR统计组数: {len(iqr_stats)}组")
    
    print("\n测试完成！系统已就绪，可以集成到API中。")


if __name__ == '__main__':
    main()

