"""
增强预测器 - 整合ML预测与文献检索
"""
import json
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ml_engine.prediction.unified_predictor import UnifiedPredictor


class EnhancedPredictor:
    """增强预测器 - 在ML预测基础上添加文献证据"""
    
    def __init__(
        self,
        models_dir: str = 'models',
        iqr_file: str = 'models/iqr_statistics.json',
        literature_service=None
    ):
        """
        初始化增强预测器
        
        Args:
            models_dir: 模型目录
            iqr_file: IQR统计文件路径
            literature_service: 文献服务实例（可选）
        """
        self.base_predictor = UnifiedPredictor(models_dir=models_dir, iqr_file=iqr_file)
        self.literature_service = literature_service
    
    def predict_with_evidence(
        self,
        user_input: Dict[str, Any],
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        预测并返回文献证据
        
        Args:
            user_input: 用户输入
            top_k: 返回Top K个最相似的文献
        
        Returns:
            增强的预测结果，包含文献证据
        """
        # 基础预测
        base_result = self.base_predictor.predict(user_input)
        
        # 如果启用文献服务，添加文献证据
        if self.literature_service:
            try:
                enhanced_result = self.literature_service.get_evidence_for_prediction(
                    user_input=user_input,
                    ml_prediction=base_result,
                    top_k=top_k
                )
                return enhanced_result
            except Exception as e:
                print(f"警告: 文献检索失败: {e}")
                # 即使失败也返回基础结果
                base_result['evidence'] = {
                    'status': 'failed',
                    'message': f'文献检索失败: {str(e)}',
                    'top_similar_literature': [],
                    'count': 0
                }
                return base_result
        else:
            # 没有文献服务，只返回基础结果
            base_result['evidence'] = {
                'status': 'disabled',
                'message': '文献检索服务未启用',
                'top_similar_literature': [],
                'count': 0
            }
            return base_result
    
    def get_recommendations_with_evidence(
        self,
        user_input: Dict[str, Any],
        request_params: List[str],
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        获取参数推荐并返回文献证据
        
        Args:
            user_input: 用户输入
            request_params: 需要推荐的参数列表
            top_k: 返回Top K个最相似的文献
        
        Returns:
            增强的推荐结果
        """
        # 基础推荐
        base_result = self.base_predictor.get_parameter_recommendations(
            user_input, request_params
        )
        
        # 添加文献证据
        if self.literature_service:
            try:
                enhanced_result = self.literature_service.get_evidence_for_prediction(
                    user_input=user_input,
                    ml_prediction=base_result,
                    top_k=top_k
                )
                return enhanced_result
            except Exception as e:
                print(f"警告: 文献检索失败: {e}")
                base_result['evidence'] = {
                    'status': 'failed',
                    'message': f'文献检索失败: {str(e)}',
                    'top_similar_literature': [],
                    'count': 0
                }
                return base_result
        else:
            base_result['evidence'] = {
                'status': 'disabled',
                'message': '文献检索服务未启用',
                'top_similar_literature': [],
                'count': 0
            }
            return base_result
    
    def format_evidence_summary(self, evidence_list: List[Dict[str, Any]]) -> str:
        """
        格式化文献证据摘要
        
        Args:
            evidence_list: 文献证据列表
        
        Returns:
            格式化的摘要文本
        """
        if not evidence_list:
            return "暂无相似文献证据"
        
        summary_parts = []
        summary_parts.append(f"\n找到 {len(evidence_list)} 篇相似文献：")
        
        for i, lit in enumerate(evidence_list, 1):
            similarity = lit.get('similarity_score', 0)
            similarity_pct = similarity * 100
            
            # 构建文献信息
            lit_info = []
            if lit.get('literature', {}).get('title'):
                lit_info.append(lit['literature']['title'])
            if lit.get('literature', {}).get('authors'):
                lit_info.append(f"作者: {lit['literature']['authors']}")
            if lit.get('literature', {}).get('pub_year'):
                lit_info.append(f"年份: {lit['literature']['pub_year']}")
            if lit.get('literature', {}).get('doi'):
                lit_info.append(f"DOI: {lit['literature']['doi']}")
            
            # 实验条件
            conditions = []
            params = lit.get('parameters', {})
            if params.get('pH'):
                conditions.append(f"pH={params['pH']}")
            if params.get('temperature_c'):
                conditions.append(f"温度={params['temperature_c']}°C")
            if params.get('concentration_mg_ml'):
                conditions.append(f"浓度={params['concentration_mg_ml']} mg/mL")
            
            summary_parts.append(f"\n{i}. 相似度: {similarity_pct:.1f}%")
            if lit_info:
                summary_parts.append(f"   {' | '.join(lit_info)}")
            if conditions:
                summary_parts.append(f"   实验条件: {', '.join(conditions)}")
            
            # 结果文本
            if lit.get('outcome_text'):
                outcome_text = lit['outcome_text'][:150]
                if len(lit['outcome_text']) > 150:
                    outcome_text += "..."
                summary_parts.append(f"   结果: {outcome_text}")
        
        return "\n".join(summary_parts)


def main():
    """测试增强预测器"""
    # 尝试创建文献服务
    literature_service = None
    try:
        # 需要数据库连接
        from sqlalchemy.orm import Session
        from backend.app.core.db import SessionLocal
        from backend.app.services.literature_service import LiteratureService
        
        db = SessionLocal()
        literature_service = LiteratureService(db)
        print("✅ 文献服务已启用")
    except Exception as e:
        print(f"⚠️  文献服务未启用: {e}")
        print("   将仅返回ML预测结果")
    
    # 创建增强预测器
    predictor = EnhancedPredictor(literature_service=literature_service)
    
    # 测试场景1：预测实验条件
    print("\n" + "="*70)
    print("场景1：预测实验条件（带文献证据）")
    print("="*70)
    
    test_input = {
        'biomolecule_name': 'lysozyme',
        'biomolecule_type': 'protein',
        'experiment_type': 'stability',
        'pH': 7.0,
        'temperature_c': 25.0,
        'concentration_mg_ml': 10.0,
    }
    
    result = predictor.predict_with_evidence(test_input, top_k=3)
    
    # 打印结果
    print(json.dumps({
        'scenario': result.get('scenario'),
        'prediction': result.get('prediction'),
        'confidence': result.get('confidence'),
    }, indent=2, ensure_ascii=False))
    
    # 打印文献摘要
    if literature_service:
        evidence = result.get('evidence', {}).get('top_similar_literature', [])
        print(predictor.format_evidence_summary(evidence))
    
    # 测试场景2：参数推荐
    print("\n" + "="*70)
    print("场景2：参数推荐（带文献证据）")
    print("="*70)
    
    test_input2 = {
        'biomolecule_name': 'lysozyme',
        'biomolecule_type': 'protein',
        'experiment_type': 'solubility',
        'pH': 7.0,
    }
    
    result2 = predictor.get_recommendations_with_evidence(
        test_input2,
        request_params=['concentration_mg_ml', 'temperature_c'],
        top_k=3
    )
    
    print(json.dumps({
        'scenario': result2.get('scenario'),
        'recommended_ranges': result2.get('recommended_ranges'),
    }, indent=2, ensure_ascii=False))
    
    if literature_service:
        evidence2 = result2.get('evidence', {}).get('top_similar_literature', [])
        print(predictor.format_evidence_summary(evidence2))


if __name__ == '__main__':
    main()

