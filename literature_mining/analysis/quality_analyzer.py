"""
数据质量分析工具
用于深入分析提取数据的质量和分布特征
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import seaborn as sns


class QualityAnalyzer:
    """数据质量分析器"""
    
    def __init__(self):
        self.data = []
        self.analysis_results = {}
    
    def load_data(self, file_path: str) -> int:
        """加载JSONL数据文件"""
        self.data = []
        
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        self.data.append(record)
                    except json.JSONDecodeError:
                        continue
        
        return len(self.data)
    
    def analyze_basic_stats(self) -> Dict[str, Any]:
        """分析基本统计信息"""
        if not self.data:
            return {}
        
        stats = {
            'total_records': len(self.data),
            'biomolecule_types': Counter(record.get('biomolecule_type', 'unknown') for record in self.data),
            'properties': Counter(record.get('property', 'unknown') for record in self.data),
            'outcome_labels': Counter(record.get('outcome_label', 'unknown') for record in self.data),
        }
        
        # 置信度统计
        confidences = [record.get('confidence', 0) for record in self.data]
        stats['confidence_stats'] = {
            'mean': np.mean(confidences),
            'median': np.median(confidences),
            'std': np.std(confidences),
            'min': np.min(confidences),
            'max': np.max(confidences),
            'quartiles': np.percentile(confidences, [25, 50, 75]).tolist()
        }
        
        # 置信度分布
        confidence_bins = {
            '0.0-0.2': 0, '0.2-0.4': 0, '0.4-0.6': 0, 
            '0.6-0.8': 0, '0.8-1.0': 0
        }
        
        for conf in confidences:
            if conf < 0.2:
                confidence_bins['0.0-0.2'] += 1
            elif conf < 0.4:
                confidence_bins['0.2-0.4'] += 1
            elif conf < 0.6:
                confidence_bins['0.4-0.6'] += 1
            elif conf < 0.8:
                confidence_bins['0.6-0.8'] += 1
            else:
                confidence_bins['0.8-1.0'] += 1
        
        stats['confidence_distribution'] = confidence_bins
        
        return stats
    
    def analyze_parameters(self) -> Dict[str, Any]:
        """分析参数提取情况"""
        param_stats = {
            'total_records': len(self.data),
            'with_any_parameter': 0,
            'with_ph': 0,
            'with_temperature': 0,
            'with_concentration': 0,
            'with_additive': 0,
            'with_ionic_strength': 0,
            'parameter_combinations': defaultdict(int),
            'parameter_values': {
                'ph_values': [],
                'temperature_values': [],
                'concentration_values': []
            }
        }
        
        for record in self.data:
            parameters = record.get('parameters', {})
            
            # 检查各个参数
            has_ph = parameters.get('pH') is not None
            has_temp = parameters.get('temperature_c') is not None
            has_conc = parameters.get('concentration_mg_ml') is not None
            has_additive = parameters.get('additive') is not None
            has_ionic = parameters.get('ionic_strength_mM') is not None
            
            if any([has_ph, has_temp, has_conc, has_additive, has_ionic]):
                param_stats['with_any_parameter'] += 1
            
            if has_ph:
                param_stats['with_ph'] += 1
                param_stats['parameter_values']['ph_values'].append(parameters['pH'])
            
            if has_temp:
                param_stats['with_temperature'] += 1
                param_stats['parameter_values']['temperature_values'].append(parameters['temperature_c'])
            
            if has_conc:
                param_stats['with_concentration'] += 1
                param_stats['parameter_values']['concentration_values'].append(parameters['concentration_mg_ml'])
            
            if has_additive:
                param_stats['with_additive'] += 1
            
            if has_ionic:
                param_stats['with_ionic_strength'] += 1
            
            # 参数组合统计
            combo = []
            if has_ph: combo.append('pH')
            if has_temp: combo.append('temp')
            if has_conc: combo.append('conc')
            if has_additive: combo.append('add')
            if has_ionic: combo.append('ionic')
            
            combo_key = '+'.join(combo) if combo else 'none'
            param_stats['parameter_combinations'][combo_key] += 1
        
        # 计算参数值统计
        for param_type, values in param_stats['parameter_values'].items():
            if values:
                param_stats[f'{param_type}_stats'] = {
                    'count': len(values),
                    'mean': np.mean(values),
                    'median': np.median(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'range': np.max(values) - np.min(values)
                }
        
        return param_stats
    
    def analyze_text_quality(self) -> Dict[str, Any]:
        """分析文本质量"""
        text_stats = {
            'total_records': len(self.data),
            'text_lengths': [],
            'has_raw_context': 0,
            'context_lengths': [],
            'outcome_text_lengths': [],
            'empty_outcome_text': 0,
            'very_short_text': 0,  # < 20 characters
            'short_text': 0,       # 20-50 characters
            'medium_text': 0,      # 50-200 characters
            'long_text': 0,        # > 200 characters
        }
        
        for record in self.data:
            outcome_text = record.get('outcome_text', '')
            raw_context = record.get('parameters', {}).get('raw_context', '')
            
            # 分析outcome_text
            outcome_length = len(outcome_text)
            text_stats['outcome_text_lengths'].append(outcome_length)
            
            if outcome_length == 0:
                text_stats['empty_outcome_text'] += 1
            elif outcome_length < 20:
                text_stats['very_short_text'] += 1
            elif outcome_length < 50:
                text_stats['short_text'] += 1
            elif outcome_length < 200:
                text_stats['medium_text'] += 1
            else:
                text_stats['long_text'] += 1
            
            # 分析raw_context
            if raw_context:
                text_stats['has_raw_context'] += 1
                text_stats['context_lengths'].append(len(raw_context))
        
        # 计算文本长度统计
        if text_stats['outcome_text_lengths']:
            lengths = text_stats['outcome_text_lengths']
            text_stats['outcome_text_stats'] = {
                'mean': np.mean(lengths),
                'median': np.median(lengths),
                'std': np.std(lengths),
                'min': np.min(lengths),
                'max': np.max(lengths)
            }
        
        if text_stats['context_lengths']:
            lengths = text_stats['context_lengths']
            text_stats['context_stats'] = {
                'mean': np.mean(lengths),
                'median': np.median(lengths),
                'std': np.std(lengths),
                'min': np.min(lengths),
                'max': np.max(lengths)
            }
        
        return text_stats
    
    def analyze_data_quality_issues(self) -> Dict[str, Any]:
        """分析数据质量问题"""
        issues = {
            'total_records': len(self.data),
            'low_confidence': 0,        # confidence < 0.5
            'very_low_confidence': 0,   # confidence < 0.3
            'no_parameters': 0,         # 没有任何参数
            'empty_outcome': 0,         # 空的outcome_text
            'short_outcome': 0,         # 很短的outcome_text
            'missing_biomolecule': 0,   # 缺失biomolecule_type
            'missing_property': 0,      # 缺失property
            'duplicate_texts': 0,       # 重复的文本
            'potential_titles': 0,      # 可能是标题的文本
        }
        
        seen_texts = set()
        
        for record in self.data:
            confidence = record.get('confidence', 0)
            outcome_text = record.get('outcome_text', '')
            biomolecule_type = record.get('biomolecule_type', '')
            property_type = record.get('property', '')
            parameters = record.get('parameters', {})
            
            # 置信度问题
            if confidence < 0.5:
                issues['low_confidence'] += 1
            if confidence < 0.3:
                issues['very_low_confidence'] += 1
            
            # 参数问题
            param_keys = ['pH', 'temperature_c', 'concentration_mg_ml', 'additive', 'ionic_strength_mM']
            has_any_param = any(parameters.get(key) is not None for key in param_keys)
            if not has_any_param:
                issues['no_parameters'] += 1
            
            # 文本问题
            if not outcome_text:
                issues['empty_outcome'] += 1
            elif len(outcome_text) < 20:
                issues['short_outcome'] += 1
            
            # 缺失字段
            if not biomolecule_type:
                issues['missing_biomolecule'] += 1
            if not property_type:
                issues['missing_property'] += 1
            
            # 重复文本
            if outcome_text in seen_texts:
                issues['duplicate_texts'] += 1
            else:
                seen_texts.add(outcome_text)
            
            # 可能的标题
            if (len(outcome_text) < 100 and 
                outcome_text.count('.') <= 1 and 
                not any(char.isdigit() for char in outcome_text)):
                issues['potential_titles'] += 1
        
        # 计算问题比例
        total = issues['total_records']
        if total > 0:
            issues['issue_rates'] = {
                'low_confidence_rate': issues['low_confidence'] / total,
                'no_parameters_rate': issues['no_parameters'] / total,
                'empty_outcome_rate': issues['empty_outcome'] / total,
                'short_outcome_rate': issues['short_outcome'] / total,
                'potential_titles_rate': issues['potential_titles'] / total
            }
        
        return issues
    
    def generate_recommendations(self) -> List[str]:
        """生成数据质量改进建议"""
        recommendations = []
        
        if not hasattr(self, 'analysis_results') or not self.analysis_results:
            return ["请先运行完整分析"]
        
        basic_stats = self.analysis_results.get('basic_stats', {})
        param_stats = self.analysis_results.get('parameter_stats', {})
        text_stats = self.analysis_results.get('text_quality', {})
        issues = self.analysis_results.get('quality_issues', {})
        
        total_records = basic_stats.get('total_records', 0)
        
        # 置信度相关建议
        if issues.get('low_confidence', 0) / max(1, total_records) > 0.5:
            recommendations.append("超过50%的记录置信度较低，建议优化提取算法或提高数据源质量")
        
        # 参数提取相关建议
        param_rate = param_stats.get('with_any_parameter', 0) / max(1, total_records)
        if param_rate < 0.3:
            recommendations.append(f"只有{param_rate:.1%}的记录包含参数，建议增强参数提取模式")
        
        # 文本质量相关建议
        if issues.get('potential_titles', 0) / max(1, total_records) > 0.2:
            recommendations.append("检测到较多标题类文本，建议改进文本过滤策略")
        
        if issues.get('short_outcome', 0) / max(1, total_records) > 0.3:
            recommendations.append("较多记录的文本过短，建议提高最小文本长度阈值")
        
        # 数据分布相关建议
        biomolecule_dist = basic_stats.get('biomolecule_types', {})
        if len(biomolecule_dist) == 1:
            recommendations.append("生物分子类型单一，建议扩展数据源覆盖更多类型")
        
        # 参数值分布建议
        if 'ph_values_stats' in param_stats:
            ph_range = param_stats['ph_values_stats'].get('range', 0)
            if ph_range < 2:
                recommendations.append("pH值范围较窄，建议扩展数据源以覆盖更广泛的pH条件")
        
        if not recommendations:
            recommendations.append("数据质量总体良好，建议继续监控和优化")
        
        return recommendations
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """运行完整的数据质量分析"""
        if not self.data:
            return {"error": "没有加载数据"}
        
        self.analysis_results = {
            'basic_stats': self.analyze_basic_stats(),
            'parameter_stats': self.analyze_parameters(),
            'text_quality': self.analyze_text_quality(),
            'quality_issues': self.analyze_data_quality_issues(),
        }
        
        self.analysis_results['recommendations'] = self.generate_recommendations()
        
        return self.analysis_results
    
    def save_analysis_report(self, output_file: str):
        """保存分析报告"""
        if not self.analysis_results:
            self.run_full_analysis()
        
        # 转换numpy类型为Python原生类型
        def convert_numpy_types(obj):
            if hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj
        
        serializable_results = convert_numpy_types(self.analysis_results)
        
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(serializable_results, file, indent=2, ensure_ascii=False)
    
    def print_summary(self):
        """打印分析摘要"""
        if not self.analysis_results:
            print("请先运行分析")
            return
        
        basic = self.analysis_results['basic_stats']
        params = self.analysis_results['parameter_stats']
        issues = self.analysis_results['quality_issues']
        
        print("=== 数据质量分析摘要 ===")
        print(f"总记录数: {basic['total_records']}")
        print(f"平均置信度: {basic['confidence_stats']['mean']:.3f}")
        print(f"包含参数的记录: {params['with_any_parameter']} ({params['with_any_parameter']/basic['total_records']:.1%})")
        print(f"低置信度记录: {issues['low_confidence']} ({issues['low_confidence']/basic['total_records']:.1%})")
        print(f"无参数记录: {issues['no_parameters']} ({issues['no_parameters']/basic['total_records']:.1%})")
        
        print("\n=== 改进建议 ===")
        for i, rec in enumerate(self.analysis_results['recommendations'], 1):
            print(f"{i}. {rec}")


def main():
    """主函数，用于测试分析器"""
    analyzer = QualityAnalyzer()
    
    # 加载数据
    data_file = "literature_mining/storage/structured_store.jsonl"
    if Path(data_file).exists():
        count = analyzer.load_data(data_file)
        print(f"加载了 {count} 条记录")
        
        # 运行分析
        results = analyzer.run_full_analysis()
        
        # 打印摘要
        analyzer.print_summary()
        
        # 保存报告
        analyzer.save_analysis_report("quality_reports/detailed_quality_analysis.json")
        print("\n详细分析报告已保存到 quality_reports/detailed_quality_analysis.json")
    else:
        print(f"数据文件不存在: {data_file}")


if __name__ == "__main__":
    main()