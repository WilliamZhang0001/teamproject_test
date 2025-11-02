"""
统一预测接口 - 支持两种应用场景

场景1：判断实验条件是否合理（分类）
场景2：参数范围推荐（统计方法）
"""
import json
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np


class UnifiedPredictor:
    """统一预测器"""
    
    def __init__(self, models_dir: str = 'models', iqr_file: str = 'models/iqr_statistics.json'):
        """
        初始化预测器
        
        Args:
            models_dir: 模型目录
            iqr_file: IQR统计文件路径
        """
        self.models_dir = Path(models_dir)
        self.models = {}
        self.iqr_stats = None
        
        # 加载IQR统计
        self._load_iqr_statistics(iqr_file)
        
        # 加载模型（延迟加载）
        self.model_files = {
            'stability': self.models_dir / 'by_experiment_type' / 'stability_classifier.pkl',
            'solubility': self.models_dir / 'by_experiment_type' / 'solubility_classifier.pkl',
            'aggregation': self.models_dir / 'by_experiment_type' / 'aggregation_classifier.pkl',
            'general': self.models_dir / 'by_experiment_type' / 'general_classifier.pkl',
        }
    
    def _load_iqr_statistics(self, iqr_file: str):
        """加载IQR统计数据"""
        iqr_path = Path(iqr_file)
        if iqr_path.exists():
            with iqr_path.open('r', encoding='utf-8') as f:
                self.iqr_stats = json.load(f)
            print(f"✅ Loaded IQR statistics from {iqr_file}")
        else:
            print(f"⚠️  IQR statistics file not found: {iqr_file}")
            self.iqr_stats = None
    
    def _load_model(self, experiment_type: str) -> Optional[Dict]:
        """延迟加载模型"""
        if experiment_type in self.models:
            return self.models[experiment_type]
        
        model_file = self.model_files.get(experiment_type)
        if model_file and model_file.exists():
            with model_file.open('rb') as f:
                self.models[experiment_type] = pickle.load(f)
            print(f"✅ Loaded {experiment_type} model")
            return self.models[experiment_type]
        else:
            print(f"⚠️  Model not found for {experiment_type}, trying general model...")
            # 回退到通用模型
            if 'general' not in self.models and self.model_files['general'].exists():
                with self.model_files['general'].open('rb') as f:
                    self.models['general'] = pickle.load(f)
                return self.models['general']
            return self.models.get('general')
    
    def predict(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        统一预测接口
        
        Args:
            user_input: 用户输入
                {
                    'biomolecule_name': 'lysozyme',
                    'biomolecule_type': 'protein',
                    'experiment_type': 'stability',
                    'pH': 7.0,
                    'temperature_c': 25.0,
                    'concentration_mg_ml': 10.0,
                    'ionic_strength_mM': None,  # 可选
                    'additive': None,  # 可选
                    'time_min': None,  # 可选
                    'shear_rate_s1': None,  # 可选
                    'pressure_bar': None,  # 可选
                }
        
        Returns:
            预测结果
        """
        # 统计填充的参数数量
        param_fields = ['pH', 'temperature_c', 'concentration_mg_ml', 'ionic_strength_mM',
                       'additive', 'time_min', 'shear_rate_s1', 'pressure_bar']
        filled_params = sum(1 for field in param_fields if user_input.get(field) is not None)
        
        experiment_type = user_input.get('experiment_type', 'stability')
        
        # 场景1：参数足够（≥1），进行分类预测
        if filled_params >= 1:
            return self._classify(user_input, filled_params)
        
        # 场景2：没有参数，返回通用范围
        else:
            return self._recommend_general_ranges(user_input)
    
    def _classify(self, user_input: Dict[str, Any], filled_params: int) -> Dict[str, Any]:
        """
        场景1：分类预测
        
        判断给定的实验条件是否合理
        """
        experiment_type = user_input.get('experiment_type', 'stability')
        biomolecule_name = user_input.get('biomolecule_name', 'unknown')
        
        # 加载模型
        model_data = self._load_model(experiment_type)
        if not model_data:
            return {
                'error': f'Model not found for {experiment_type}',
                'recommendation': 'Please train the model first'
            }
        
        model = model_data['model']
        imputer = model_data['imputer']
        feature_cols = model_data['feature_cols']
        
        # 准备特征
        features = self._prepare_features(user_input, feature_cols)
        
        # 填充缺失值
        # 确保特征顺序与模型训练时一致
        X = pd.DataFrame([features])[feature_cols]
        X_filled = pd.DataFrame(
            imputer.transform(X),
            columns=feature_cols
        )
        
        # 预测
        prediction = model.predict(X_filled)[0]
        proba = model.predict_proba(X_filled)[0]
        confidence = float(proba.max())
        
        # 调整置信度（根据参数完整度和实验类型）
        confidence = self._adjust_confidence(confidence, filled_params, experiment_type)
        
        # 判断
        is_good = bool(prediction == 1)
        
        result = {
            'scenario': 'classification',
            'prediction': 'Good' if is_good else 'Bad',
            'confidence': confidence,
            'details': {
                'experiment_type': experiment_type,
                'biomolecule_name': biomolecule_name,
                'filled_params': filled_params,
                'total_params': 8,
                'model_used': model_data.get('experiment_type', 'general')
            },
            'explanation': self._generate_explanation(is_good, confidence, filled_params)
        }
        
        # 如果预测不好，提供推荐范围
        if not is_good:
            result['recommended_ranges'] = self._get_recommended_ranges(user_input)
        
        return result
    
    def _recommend_general_ranges(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        场景2：参数范围推荐（没有填参数时）
        """
        experiment_type = user_input.get('experiment_type', 'stability')
        biomolecule_name = user_input.get('biomolecule_name', 'unknown')
        
        ranges = self._get_recommended_ranges(user_input)
        
        return {
            'scenario': 'parameter_recommendation',
            'experiment_type': experiment_type,
            'biomolecule_name': biomolecule_name,
            'recommended_ranges': ranges,
            'note': '请至少填写1个参数以获得更准确的预测'
        }
    
    def get_parameter_recommendations(self, user_input: Dict[str, Any],
                                     request_params: List[str]) -> Dict[str, Any]:
        """
        场景2：指定参数推荐
        
        用户填入部分参数后，请求推荐其他参数的范围
        
        Args:
            user_input: 用户输入
            request_params: 需要推荐的参数列表，如 ['pH', 'temperature_c']
        
        Returns:
            推荐的参数范围
        """
        experiment_type = user_input.get('experiment_type', 'stability')
        biomolecule_name = user_input.get('biomolecule_name', 'unknown')
        
        # 获取完整的推荐范围
        all_ranges = self._get_recommended_ranges(user_input)
        
        # 筛选用户请求的参数
        recommended_ranges = {}
        for param in request_params:
            if param in all_ranges:
                recommended_ranges[param] = all_ranges[param]
        
        # 统计已填参数
        param_fields = ['pH', 'temperature_c', 'concentration_mg_ml', 'ionic_strength_mM',
                       'additive', 'time_min', 'shear_rate_s1', 'pressure_bar']
        filled_params = {k: v for k, v in user_input.items() 
                        if k in param_fields and v is not None}
        
        return {
            'scenario': 'parameter_recommendation',
            'experiment_type': experiment_type,
            'biomolecule_name': biomolecule_name,
            'filled_parameters': filled_params,
            'recommended_ranges': recommended_ranges,
            'confidence': self._get_recommendation_confidence(user_input),
            'note': 'Ranges based on historical IQR statistics'
        }
    
    def _get_recommended_ranges(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """获取推荐的参数范围"""
        if not self.iqr_stats:
            return {}
        
        experiment_type = user_input.get('experiment_type', 'stability')
        biomolecule_name = user_input.get('biomolecule_name', 'unknown')
        
        # 优先级1：实验类型+物质名称
        if biomolecule_name != 'unknown':
            exp_bio_stats = self.iqr_stats.get('by_experiment_and_biomolecule', {})
            if experiment_type in exp_bio_stats:
                if biomolecule_name in exp_bio_stats[experiment_type]:
                    return self._format_ranges(
                        exp_bio_stats[experiment_type][biomolecule_name],
                        source='specific (experiment + biomolecule)'
                    )
            
            # 优先级2：物质名称
            bio_stats = self.iqr_stats.get('by_biomolecule', {})
            if biomolecule_name in bio_stats:
                return self._format_ranges(
                    bio_stats[biomolecule_name],
                    source='biomolecule-specific'
                )
        
        # 优先级3：实验类型
        exp_stats = self.iqr_stats.get('by_experiment_type', {})
        if experiment_type in exp_stats:
            return self._format_ranges(
                exp_stats[experiment_type],
                source='experiment-specific'
            )
        
        # 优先级4：全局统计
        global_stats = self.iqr_stats.get('global', {})
        return self._format_ranges(global_stats, source='global')
    
    def _format_ranges(self, stats: Dict, source: str) -> Dict[str, Any]:
        """格式化范围输出"""
        ranges = {}
        param_map = {
            'pH': {'unit': '', 'name': 'pH'},
            'temperature_c': {'unit': '°C', 'name': 'Temperature'},
            'concentration_mg_ml': {'unit': 'mg/mL', 'name': 'Concentration'},
            'ionic_strength_mM': {'unit': 'mM', 'name': 'Ionic Strength'},
            'time_min': {'unit': 'min', 'name': 'Time'},
            'shear_rate_s1': {'unit': 's⁻¹', 'name': 'Shear Rate'},
            'pressure_bar': {'unit': 'bar', 'name': 'Pressure'}
        }
        
        for param, info in param_map.items():
            if param in stats:
                param_stats = stats[param]
                if isinstance(param_stats, dict) and 'q1' in param_stats:
                    ranges[param] = {
                        'min': param_stats['q1'],
                        'max': param_stats['q3'],
                        'median': param_stats['median'],
                        'recommended': [param_stats['q1'], param_stats['q3']],
                        'unit': info['unit'],
                        'name': info['name'],
                        'count': param_stats.get('count', 0),
                        'source': source
                    }
        
        return ranges
    
    def _prepare_features(self, user_input: Dict[str, Any], 
                         feature_cols: List[str]) -> Dict[str, float]:
        """准备特征向量"""
        features = {}
        
        # 数值特征
        for col in ['pH', 'temperature_c', 'concentration_mg_ml', 'ionic_strength_mM',
                   'time_min', 'shear_rate_s1', 'pressure_bar']:
            value = user_input.get(col)
            features[col] = float(value) if value is not None else np.nan
            features[f'{col}_missing'] = 1 if value is None else 0
        
        # 类别特征：biomolecule_type
        biomolecule_type_map = {'protein': 0, 'peptide': 1, 'polysaccharide': 2, 'unknown': 3}
        bio_type = user_input.get('biomolecule_type', 'protein')
        features['biomolecule_type_encoded'] = biomolecule_type_map.get(bio_type, 0)
        
        # 添加剂特征
        features['has_additive'] = 1 if user_input.get('additive') else 0
        
        # 确保所有 feature_cols 中的特征都存在，缺失的用 0 或 np.nan 填充
        for col in feature_cols:
            if col not in features:
                # 如果是数值特征，用 NaN；如果是缺失指示器或其他，用 0
                if col.endswith('_missing') or col == 'has_additive' or 'encoded' in col:
                    features[col] = 0
                else:
                    features[col] = np.nan
        
        return features
    
    def _adjust_confidence(self, confidence: float, filled_params: int, 
                          experiment_type: str) -> float:
        """调整置信度"""
        # 参数完整度调整
        if filled_params < 3:
            confidence *= 0.85  # 参数太少，降低置信度
        elif filled_params < 5:
            confidence *= 0.95  # 参数较少，略降置信度
        
        # 实验类型数据量调整
        type_factor = {
            'stability': 1.0,     # 数据充足
            'solubility': 0.95,   # 数据较少
            'aggregation': 0.90   # 数据不足
        }
        confidence *= type_factor.get(experiment_type, 0.90)
        
        return float(min(confidence, 0.99))  # 最高99%
    
    def _get_recommendation_confidence(self, user_input: Dict[str, Any]) -> str:
        """获取推荐置信度等级"""
        biomolecule_name = user_input.get('biomolecule_name', 'unknown')
        experiment_type = user_input.get('experiment_type', 'stability')
        
        if biomolecule_name != 'unknown' and self.iqr_stats:
            exp_bio_stats = self.iqr_stats.get('by_experiment_and_biomolecule', {})
            if experiment_type in exp_bio_stats:
                if biomolecule_name in exp_bio_stats[experiment_type]:
                    count = exp_bio_stats[experiment_type][biomolecule_name].get('_count', 0)
                    if count >= 50:
                        return 'high'
                    elif count >= 20:
                        return 'medium'
        
        return 'low'
    
    def _generate_explanation(self, is_good: bool, confidence: float, 
                             filled_params: int) -> str:
        """生成解释文本"""
        if is_good:
            base = f"This experimental condition is predicted to be STABLE"
        else:
            base = f"This experimental condition is predicted to be UNSTABLE"
        
        conf_level = "high" if confidence > 0.85 else "medium" if confidence > 0.70 else "low"
        
        return (f"{base} with {conf_level} confidence ({confidence:.1%}). "
                f"Prediction based on {filled_params} parameters.")


def main():
    """测试"""
    predictor = UnifiedPredictor()
    
    # 测试场景1：分类
    print("\n" + "="*70)
    print("场景1：判断实验条件是否合理")
    print("="*70)
    
    test_input = {
        'biomolecule_name': 'lysozyme',
        'biomolecule_type': 'protein',
        'experiment_type': 'stability',
        'pH': 7.0,
        'temperature_c': 25.0,
        'concentration_mg_ml': 10.0,
        'ionic_strength_mM': None,
        'additive': None,
        'time_min': None,
        'shear_rate_s1': None,
        'pressure_bar': None
    }
    
    result = predictor.predict(test_input)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 测试场景2：参数推荐
    print("\n" + "="*70)
    print("场景2：参数范围推荐")
    print("="*70)
    
    test_input2 = {
        'biomolecule_name': 'lysozyme',
        'biomolecule_type': 'protein',
        'experiment_type': 'solubility',
        'pH': 7.0,
        'temperature_c': 25.0,
    }
    
    result2 = predictor.get_parameter_recommendations(
        test_input2,
        request_params=['concentration_mg_ml', 'ionic_strength_mM']
    )
    print(json.dumps(result2, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()

