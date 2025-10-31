"""
数据过滤器模块
用于过滤低质量的提取记录，提高数据质量
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path


class DataFilter:
    """数据质量过滤器"""
    
    def __init__(self, 
                 min_confidence: float = 0.5,
                 require_parameters: bool = True,
                 min_text_length: int = 20):
        """
        初始化过滤器
        
        Args:
            min_confidence: 最小置信度阈值
            require_parameters: 是否要求至少有一个参数
            min_text_length: 最小文本长度
        """
        self.min_confidence = min_confidence
        self.require_parameters = require_parameters
        self.min_text_length = min_text_length
    
    def has_valid_parameters(self, record: Dict[str, Any]) -> bool:
        """检查记录是否包含有效参数"""
        parameters = record.get('parameters', {})
        if not parameters:
            return False
        
        # 检查是否至少有一个非空参数（除了raw_context）
        param_keys = ['pH', 'temperature_c', 'concentration_mg_ml', 'additive', 'ionic_strength_mM']
        return any(parameters.get(key) is not None for key in param_keys)
    
    def is_experimental_text(self, text: str) -> bool:
        """判断文本是否包含实验性内容"""
        experimental_keywords = [
            'temperature', 'pH', 'concentration', 'buffer', 'solution',
            'incubated', 'heated', 'cooled', 'measured', 'observed',
            'experiment', 'assay', 'test', 'analysis', 'method',
            '°C', 'mM', 'mg/ml', 'μM', 'nM', 'M', 'mol/L'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in experimental_keywords)
    
    def is_title_or_abstract(self, text: str) -> bool:
        """判断文本是否可能是标题或摘要（通常缺乏具体参数）"""
        # 短文本通常是标题
        if len(text) < 50:
            return True
        
        # 包含这些词汇的通常是摘要或理论描述
        abstract_indicators = [
            'abstract', 'introduction', 'conclusion', 'summary',
            'review', 'overview', 'perspective', 'chapter',
            'we present', 'we describe', 'we report', 'this study',
            'in this work', 'here we', 'we investigated'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in abstract_indicators)
    
    def filter_record(self, record: Dict[str, Any]) -> bool:
        """
        过滤单个记录
        
        Returns:
            True if record should be kept, False if should be filtered out
        """
        # 检查置信度
        confidence = record.get('confidence', 0)
        if confidence < self.min_confidence:
            return False
        
        # 检查文本长度
        outcome_text = record.get('outcome_text', '')
        if len(outcome_text) < self.min_text_length:
            return False
        
        # 如果要求参数，检查是否有有效参数
        if self.require_parameters and not self.has_valid_parameters(record):
            # 但如果文本明显是实验性的，即使没有提取到参数也保留
            if not self.is_experimental_text(outcome_text):
                return False
        
        # 过滤掉明显的标题或摘要
        if self.is_title_or_abstract(outcome_text):
            return False
        
        return True
    
    def filter_data(self, input_file: str, output_file: str) -> Dict[str, int]:
        """
        过滤数据文件
        
        Returns:
            统计信息字典
        """
        stats = {
            'total_records': 0,
            'filtered_records': 0,
            'kept_records': 0,
            'low_confidence': 0,
            'no_parameters': 0,
            'short_text': 0,
            'title_abstract': 0
        }
        
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(input_path, 'r', encoding='utf-8') as infile, \
             open(output_path, 'w', encoding='utf-8') as outfile:
            
            for line in infile:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                    stats['total_records'] += 1
                    
                    # 详细统计过滤原因
                    confidence = record.get('confidence', 0)
                    outcome_text = record.get('outcome_text', '')
                    
                    if confidence < self.min_confidence:
                        stats['low_confidence'] += 1
                        stats['filtered_records'] += 1
                        continue
                    
                    if len(outcome_text) < self.min_text_length:
                        stats['short_text'] += 1
                        stats['filtered_records'] += 1
                        continue
                    
                    if self.require_parameters and not self.has_valid_parameters(record):
                        if not self.is_experimental_text(outcome_text):
                            stats['no_parameters'] += 1
                            stats['filtered_records'] += 1
                            continue
                    
                    if self.is_title_or_abstract(outcome_text):
                        stats['title_abstract'] += 1
                        stats['filtered_records'] += 1
                        continue
                    
                    # 记录通过过滤
                    stats['kept_records'] += 1
                    outfile.write(line + '\n')
                    
                except json.JSONDecodeError:
                    continue
        
        return stats
    
    def analyze_quality(self, file_path: str) -> Dict[str, Any]:
        """分析数据质量"""
        stats = {
            'total_records': 0,
            'with_parameters': 0,
            'with_ph': 0,
            'with_temperature': 0,
            'with_concentration': 0,
            'high_confidence': 0,
            'experimental_text': 0,
            'confidence_distribution': {'0.0-0.2': 0, '0.2-0.4': 0, '0.4-0.6': 0, '0.6-0.8': 0, '0.8-1.0': 0}
        }
        
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                    stats['total_records'] += 1
                    
                    # 分析参数
                    parameters = record.get('parameters', {})
                    if self.has_valid_parameters(record):
                        stats['with_parameters'] += 1
                    
                    if parameters.get('pH') is not None:
                        stats['with_ph'] += 1
                    if parameters.get('temperature_c') is not None:
                        stats['with_temperature'] += 1
                    if parameters.get('concentration_mg_ml') is not None:
                        stats['with_concentration'] += 1
                    
                    # 分析置信度
                    confidence = record.get('confidence', 0)
                    if confidence >= 0.7:
                        stats['high_confidence'] += 1
                    
                    # 置信度分布
                    if confidence < 0.2:
                        stats['confidence_distribution']['0.0-0.2'] += 1
                    elif confidence < 0.4:
                        stats['confidence_distribution']['0.2-0.4'] += 1
                    elif confidence < 0.6:
                        stats['confidence_distribution']['0.4-0.6'] += 1
                    elif confidence < 0.8:
                        stats['confidence_distribution']['0.6-0.8'] += 1
                    else:
                        stats['confidence_distribution']['0.8-1.0'] += 1
                    
                    # 分析文本类型
                    outcome_text = record.get('outcome_text', '')
                    if self.is_experimental_text(outcome_text):
                        stats['experimental_text'] += 1
                        
                except json.JSONDecodeError:
                    continue
        
        return stats


def main():
    """主函数，用于测试过滤器"""
    filter_obj = DataFilter(
        min_confidence=0.5,
        require_parameters=False,  # 暂时不强制要求参数
        min_text_length=30
    )
    
    input_file = "literature_mining/storage/structured_store.jsonl"
    output_file = "literature_mining/storage/filtered_store.jsonl"
    
    # 分析原始数据质量
    print("分析原始数据质量...")
    original_stats = filter_obj.analyze_quality(input_file)
    print(f"原始数据统计: {original_stats}")
    
    # 过滤数据
    print("\n过滤数据...")
    filter_stats = filter_obj.filter_data(input_file, output_file)
    print(f"过滤统计: {filter_stats}")
    
    # 分析过滤后数据质量
    print("\n分析过滤后数据质量...")
    filtered_stats = filter_obj.analyze_quality(output_file)
    print(f"过滤后数据统计: {filtered_stats}")


if __name__ == "__main__":
    main()