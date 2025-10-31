"""
双轨推荐系统 - 整合IQR统计和ML预测

核心思想:
- Track 1 (IQR): 基于文献证据的统计窗口
- Track 2 (ML): 基于机器学习的预测优化
- 输出: 统一的参数推荐 + 证据追溯
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
import numpy as np
import pandas as pd
from statistics import median


@dataclass
class Evidence:
    """证据条目"""
    doi: Optional[str] = None
    title: Optional[str] = None
    year: Optional[int] = None
    snippets: List[str] = field(default_factory=list)
    confidence: float = 0.5


@dataclass
class ParameterWindow:
    """参数窗口推荐"""
    min_value: float
    max_value: float
    median_value: Optional[float] = None
    n_samples: int = 0
    source_count: int = 0
    confidence: float = 0.5
    method: str = "iqr"  # 'iqr' or 'ml'


@dataclass
class RecommendationResult:
    """推荐结果"""
    protein_name: str
    property_type: str
    iqr_recommendations: Dict[str, ParameterWindow] = field(default_factory=dict)
    ml_recommendations: Dict[str, ParameterWindow] = field(default_factory=dict)
    consensus_recommendations: Dict[str, ParameterWindow] = field(default_factory=dict)
    evidence: List[Evidence] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class IQRAnalyzer:
    """IQR统计分析器 - 从文献数据中提取参数窗口"""
    
    def __init__(self):
        self.param_names = ["pH", "temperature_c", "concentration_mg_ml"]
    
    def _compute_iqr(self, values: List[float]) -> Tuple[float, float, float]:
        """计算IQR (Q1, Q3, median)"""
        if not values:
            return None, None, None
        
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        
        if n == 1:
            return sorted_vals[0], sorted_vals[0], sorted_vals[0]
        
        def percentile(p):
            k = (n - 1) * p / 100.0
            f = int(k)
            c = min(f + 1, n - 1)
            if f == c:
                return sorted_vals[f]
            return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)
        
        q1 = percentile(25)
        q3 = percentile(75)
        med = median(sorted_vals)
        
        return q1, q3, med
    
    def analyze(
        self, 
        records: List[Dict[str, Any]], 
        protein_filter: Optional[str] = None,
        polarity_filter: Optional[str] = None
    ) -> Dict[str, ParameterWindow]:
        """
        从记录中提取IQR参数窗口
        
        Args:
            records: 提取的记录列表
            protein_filter: 只分析特定蛋白质
            polarity_filter: 只分析特定polarity (如'positive'，设为None则不过滤)
        """
        # 过滤记录
        filtered = records
        if protein_filter:
            filtered = [r for r in filtered if r.get('protein_name') == protein_filter]
        if polarity_filter:  # 只有明确指定polarity_filter时才过滤
            filtered = [r for r in filtered if r.get('polarity') == polarity_filter]
        
        # 提取每个参数的值
        param_values = {param: [] for param in self.param_names}
        param_dois = {param: set() for param in self.param_names}
        
        for record in filtered:
            params = record.get('parameters', {})
            doi = record.get('source_doi')
            
            for param in self.param_names:
                val = params.get(param)
                if val is not None:
                    try:
                        param_values[param].append(float(val))
                        # 记录该参数的DOI
                        if doi:
                            param_dois[param].add(doi)
                    except (ValueError, TypeError):
                        continue
        
        # 计算IQR窗口
        windows = {}
        for param, values in param_values.items():
            if len(values) >= 3:  # 至少3个数据点
                q1, q3, med = self._compute_iqr(values)
                if q1 is not None:
                    windows[param] = ParameterWindow(
                        min_value=q1,
                        max_value=q3,
                        median_value=med,
                        n_samples=len(values),
                        source_count=len(param_dois[param]),  # 使用参数特定的DOI计数
                        confidence=min(len(values) / 20.0, 1.0),  # 20+样本=高置信度
                        method="iqr"
                    )
        
        return windows


class MLPredictor:
    """ML预测器 - 使用训练好的模型预测最优参数范围"""
    
    def __init__(self, model=None):
        self.model = model
    
    def predict_optimal_ranges(
        self,
        protein_name: str,
        target_stability: float = 0.65,
        resolution: int = 20
    ) -> Dict[str, ParameterWindow]:
        """
        使用ML模型预测最优参数范围
        
        Args:
            protein_name: 蛋白质名称
            target_stability: 目标稳定性概率阈值
            resolution: 网格搜索分辨率
        """
        if not self.model:
            return {}
        
        # 参数网格
        param_grids = {
            'pH': np.linspace(3, 11, resolution),
            'temperature_c': np.linspace(4, 80, resolution),
            'concentration_mg_ml': np.linspace(0.1, 50, resolution)
        }
        
        windows = {}
        
        # 对每个参数单独优化（固定其他参数为典型值）
        for param_name, grid_values in param_grids.items():
            stable_values = []
            
            for val in grid_values:
                # 构建测试样本 - 包含所有必需特征
                test_sample = pd.DataFrame([{
                    'pH': 7.0 if param_name != 'pH' else val,
                    'temperature_c': 25.0 if param_name != 'temperature_c' else val,
                    'concentration_mg_ml': 5.0 if param_name != 'concentration_mg_ml' else val,
                    'protein_name': protein_name,
                    'polarity': 'positive',
                    'confidence': 0.8
                }])
                
                # 预测
                try:
                    # predict_proba返回正类概率（已被模型处理为标量）
                    prob = self.model.predict_proba(test_sample)[0]
                    if prob >= target_stability:
                        stable_values.append(val)
                except Exception as e:
                    # 跳过预测失败的点（可能是特征工程问题）
                    continue
            
            # 找到连续稳定区间
            if stable_values:
                windows[param_name] = ParameterWindow(
                    min_value=min(stable_values),
                    max_value=max(stable_values),
                    median_value=np.median(stable_values),
                    n_samples=len(stable_values),
                    confidence=target_stability,
                    method="ml"
                )
        
        return windows


class DualTrackRecommender:
    """双轨推荐系统 - 整合IQR和ML"""
    
    def __init__(self, model_path: Optional[Path] = None):
        self.iqr_analyzer = IQRAnalyzer()
        self.ml_predictor = None
        
        # 加载ML模型
        if model_path and Path(model_path).exists():
            from joblib import load
            try:
                self.ml_predictor = MLPredictor(load(model_path))
            except Exception as e:
                print(f"Warning: Could not load ML model: {e}")
    
    def _merge_windows(
        self, 
        iqr_window: Optional[ParameterWindow],
        ml_window: Optional[ParameterWindow]
    ) -> Optional[ParameterWindow]:
        """合并IQR和ML窗口，取交集或加权平均"""
        if not iqr_window and not ml_window:
            return None
        
        if not iqr_window:
            return ml_window
        
        if not ml_window:
            return iqr_window
        
        # 计算交集
        min_val = max(iqr_window.min_value, ml_window.min_value)
        max_val = min(iqr_window.max_value, ml_window.max_value)
        
        # 如果有交集
        if min_val <= max_val:
            return ParameterWindow(
                min_value=min_val,
                max_value=max_val,
                median_value=(min_val + max_val) / 2,
                n_samples=iqr_window.n_samples + ml_window.n_samples,
                confidence=(iqr_window.confidence + ml_window.confidence) / 2,
                method="consensus"
            )
        else:
            # 无交集，返回IQR（更保守）
            return iqr_window
    
    def recommend(
        self,
        records: List[Dict[str, Any]],
        protein_name: Optional[str] = None,
        property_type: str = "stability",
        use_ml: bool = True
    ) -> RecommendationResult:
        """
        生成双轨推荐
        
        Args:
            records: 文献提取的记录
            protein_name: 目标蛋白质
            property_type: 属性类型
            use_ml: 是否使用ML预测
        """
        # IQR分析 - 使用所有数据，不过滤polarity
        iqr_windows = self.iqr_analyzer.analyze(
            records,
            protein_filter=protein_name,
            polarity_filter=None  # 不过滤polarity，使用所有数据
        )
        
        # ML预测
        ml_windows = {}
        if use_ml and self.ml_predictor and protein_name:
            ml_windows = self.ml_predictor.predict_optimal_ranges(protein_name)
        
        # 合并推荐
        consensus_windows = {}
        all_params = set(iqr_windows.keys()) | set(ml_windows.keys())
        
        for param in all_params:
            consensus_windows[param] = self._merge_windows(
                iqr_windows.get(param),
                ml_windows.get(param)
            )
        
        # 收集证据
        evidence = self._collect_evidence(records, protein_name)
        
        # 构建结果
        result = RecommendationResult(
            protein_name=protein_name or "unknown",
            property_type=property_type,
            iqr_recommendations=iqr_windows,
            ml_recommendations=ml_windows,
            consensus_recommendations=consensus_windows,
            evidence=evidence,
            metadata={
                'total_records': len(records),
                'filtered_records': len([r for r in records if r.get('protein_name') == protein_name]),
                'ml_available': use_ml and self.ml_predictor is not None
            }
        )
        
        return result
    
    def _collect_evidence(
        self, 
        records: List[Dict[str, Any]], 
        protein_filter: Optional[str] = None
    ) -> List[Evidence]:
        """收集证据条目"""
        evidence_map = {}
        
        for record in records:
            if protein_filter and record.get('protein_name') != protein_filter:
                continue
            
            doi = record.get('source_doi')
            if not doi:
                continue
            
            if doi not in evidence_map:
                evidence_map[doi] = Evidence(doi=doi)
            
            # 添加snippet
            outcome_text = record.get('outcome_text', '')
            if outcome_text and len(evidence_map[doi].snippets) < 3:
                evidence_map[doi].snippets.append(outcome_text[:150])
            
            # 更新confidence
            conf = record.get('confidence', 0.5)
            evidence_map[doi].confidence = max(evidence_map[doi].confidence, conf)
        
        return list(evidence_map.values())
    
    def to_dict(self, result: RecommendationResult) -> Dict[str, Any]:
        """转换为字典格式（用于JSON输出）"""
        
        def window_to_dict(w: ParameterWindow) -> Dict:
            return {
                'min': round(w.min_value, 2),
                'max': round(w.max_value, 2),
                'median': round(w.median_value, 2) if w.median_value else None,
                'n_samples': w.n_samples,
                'source_count': w.source_count,
                'confidence': round(w.confidence, 3),
                'method': w.method
            }
        
        return {
            'protein': result.protein_name,
            'property': result.property_type,
            'recommendations': {
                'iqr': {k: window_to_dict(v) for k, v in result.iqr_recommendations.items()},
                'ml': {k: window_to_dict(v) for k, v in result.ml_recommendations.items()},
                'consensus': {k: window_to_dict(v) for k, v in result.consensus_recommendations.items()}
            },
            'evidence': [
                {
                    'doi': e.doi,
                    'snippets': e.snippets,
                    'confidence': round(e.confidence, 3)
                }
                for e in result.evidence[:10]  # 最多10条
            ],
            'metadata': result.metadata
        }

