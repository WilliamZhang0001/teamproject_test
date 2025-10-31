"""
文本预处理器模块
用于优化文本处理，优先处理实验性章节和高质量内容
"""

import re
from typing import List, Dict, Tuple, Optional, Any
from ..nlp.regex_patterns import SECTION_PATTERNS


class TextPreprocessor:
    """文本预处理器，用于优化文本质量和相关性"""
    
    def __init__(self):
        self.section_weights = {
            'methods': 1.0,      # 最高权重 - 实验方法
            'results': 0.9,      # 高权重 - 实验结果
            'discussion': 0.6,   # 中等权重 - 讨论
            'introduction': 0.3, # 低权重 - 介绍
            'abstract': 0.4,     # 中低权重 - 摘要
            'conclusion': 0.5,   # 中等权重 - 结论
            'default': 0.5       # 默认权重
        }
        
        # 实验性关键词
        self.experimental_keywords = [
            'temperature', 'pH', 'concentration', 'buffer', 'solution',
            'incubated', 'heated', 'cooled', 'measured', 'observed',
            'experiment', 'assay', 'test', 'analysis', 'method',
            '°C', 'mM', 'mg/ml', 'μM', 'nM', 'M', 'mol/L',
            'stability', 'aggregation', 'precipitation', 'solubility',
            'denaturation', 'unfolding', 'activity', 'functional'
        ]
        
        # 理论性/非实验性关键词
        self.theoretical_keywords = [
            'review', 'overview', 'perspective', 'introduction',
            'background', 'literature', 'previous', 'reported',
            'known', 'established', 'generally', 'typically',
            'chapter', 'section', 'summary', 'conclusion'
        ]
    
    def get_section_type(self, text: str) -> str:
        """识别文本所属的章节类型"""
        text_lower = text.lower()
        
        for section, pattern in SECTION_PATTERNS.items():
            if pattern.search(text_lower):
                return section
        
        return 'default'
    
    def calculate_experimental_score(self, text: str) -> float:
        """计算文本的实验性得分"""
        text_lower = text.lower()
        
        # 计算实验性关键词密度
        exp_count = sum(1 for keyword in self.experimental_keywords 
                       if keyword in text_lower)
        
        # 计算理论性关键词密度
        theo_count = sum(1 for keyword in self.theoretical_keywords 
                        if keyword in text_lower)
        
        # 文本长度归一化
        text_length = len(text.split())
        if text_length == 0:
            return 0.0
        
        exp_density = exp_count / text_length
        theo_density = theo_count / text_length
        
        # 计算实验性得分
        experimental_score = exp_density - 0.5 * theo_density
        
        # 归一化到 0-1 范围
        return max(0.0, min(1.0, experimental_score * 10))
    
    def has_numerical_parameters(self, text: str) -> bool:
        """检查文本是否包含数值参数"""
        # 检查是否包含数值和单位的组合
        numerical_patterns = [
            r'\d+\.?\d*\s*°?C',           # 温度
            r'\d+\.?\d*\s*mM',            # 浓度
            r'pH\s*\d+\.?\d*',            # pH值
            r'\d+\.?\d*\s*mg/ml',         # 浓度
            r'\d+\.?\d*\s*%',             # 百分比
            r'\d+\.?\d*\s*[μu]M',         # 微摩尔浓度
        ]
        
        for pattern in numerical_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def is_title_like(self, text: str) -> bool:
        """判断文本是否像标题"""
        # 短文本通常是标题
        if len(text) < 100:
            return True
        
        # 没有句号的短文本可能是标题
        if len(text) < 200 and '.' not in text:
            return True
        
        # 全大写或首字母大写的短文本
        if len(text) < 150 and (text.isupper() or text.istitle()):
            return True
        
        return False
    
    def calculate_text_quality(self, text: str) -> Dict[str, float]:
        """计算文本质量指标"""
        section_type = self.get_section_type(text)
        section_weight = self.section_weights.get(section_type, self.section_weights['default'])
        
        experimental_score = self.calculate_experimental_score(text)
        has_parameters = self.has_numerical_parameters(text)
        is_title = self.is_title_like(text)
        
        # 计算综合质量得分
        quality_score = section_weight * 0.4 + experimental_score * 0.4
        
        if has_parameters:
            quality_score += 0.15
        
        if is_title:
            quality_score -= 0.3  # 标题通常缺乏具体参数
        
        # 文本长度因子
        text_length = len(text.split())
        if text_length < 10:
            quality_score -= 0.2
        elif text_length > 50:
            quality_score += 0.1
        
        return {
            'overall_quality': max(0.0, min(1.0, quality_score)),
            'section_weight': section_weight,
            'experimental_score': experimental_score,
            'has_parameters': has_parameters,
            'is_title': is_title,
            'section_type': section_type,
            'text_length': text_length
        }
    
    def prioritize_sentences(self, sentences: List[str], 
                           min_quality: float = 0.5) -> List[Tuple[str, Dict[str, float]]]:
        """
        对句子进行优先级排序
        
        Returns:
            List of (sentence, quality_metrics) tuples, sorted by quality
        """
        sentence_qualities = []
        
        for sentence in sentences:
            quality_metrics = self.calculate_text_quality(sentence)
            if quality_metrics['overall_quality'] >= min_quality:
                sentence_qualities.append((sentence, quality_metrics))
        
        # 按质量得分排序
        sentence_qualities.sort(key=lambda x: x[1]['overall_quality'], reverse=True)
        
        return sentence_qualities
    
    def filter_high_quality_text(self, text_chunks: List[str], 
                                min_quality: float = 0.5) -> List[Tuple[str, Dict[str, float]]]:
        """
        过滤高质量文本块
        
        Args:
            text_chunks: 文本块列表
            min_quality: 最小质量阈值
            
        Returns:
            高质量文本块及其质量指标
        """
        high_quality_chunks = []
        
        for chunk in text_chunks:
            quality_metrics = self.calculate_text_quality(chunk)
            
            if quality_metrics['overall_quality'] >= min_quality:
                high_quality_chunks.append((chunk, quality_metrics))
        
        # 按质量排序
        high_quality_chunks.sort(key=lambda x: x[1]['overall_quality'], reverse=True)
        
        return high_quality_chunks
    
    def preprocess_document(self, document: str, 
                          chunk_size: int = 500) -> Dict[str, Any]:
        """
        预处理整个文档
        
        Args:
            document: 原始文档文本
            chunk_size: 文本块大小（按字符数）
            
        Returns:
            预处理结果字典
        """
        # 分割成句子
        sentences = re.split(r'(?<=[.!?])\s+', document.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 分割成文本块
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # 分析句子质量
        sentence_analysis = self.prioritize_sentences(sentences, min_quality=0.3)
        
        # 分析文本块质量
        chunk_analysis = self.filter_high_quality_text(chunks, min_quality=0.4)
        
        # 计算文档级别统计
        total_sentences = len(sentences)
        high_quality_sentences = len(sentence_analysis)
        total_chunks = len(chunks)
        high_quality_chunks = len(chunk_analysis)
        
        # 计算平均质量得分
        avg_sentence_quality = (sum(metrics['overall_quality'] 
                                  for _, metrics in sentence_analysis) / 
                              max(1, len(sentence_analysis)))
        
        avg_chunk_quality = (sum(metrics['overall_quality'] 
                                for _, metrics in chunk_analysis) / 
                            max(1, len(chunk_analysis)))
        
        return {
            'sentences': {
                'total': total_sentences,
                'high_quality': high_quality_sentences,
                'analysis': sentence_analysis,
                'avg_quality': avg_sentence_quality
            },
            'chunks': {
                'total': total_chunks,
                'high_quality': high_quality_chunks,
                'analysis': chunk_analysis,
                'avg_quality': avg_chunk_quality
            },
            'document_stats': {
                'total_length': len(document),
                'word_count': len(document.split()),
                'sentence_retention_rate': high_quality_sentences / max(1, total_sentences),
                'chunk_retention_rate': high_quality_chunks / max(1, total_chunks)
            }
        }


def main():
    """测试文本预处理器"""
    preprocessor = TextPreprocessor()
    
    # 测试文本
    test_texts = [
        "The protein was incubated at 37°C for 2 hours in pH 7.4 buffer containing 150 mM NaCl.",
        "Protein stability is an important factor in biotechnology applications.",
        "Chapter 1: Introduction to Protein Folding",
        "Results showed that the enzyme maintained 85% activity after heating to 60°C.",
        "This review discusses recent advances in protein engineering."
    ]
    
    print("文本质量分析:")
    for i, text in enumerate(test_texts):
        quality = preprocessor.calculate_text_quality(text)
        print(f"\n文本 {i+1}: {text[:50]}...")
        print(f"质量得分: {quality['overall_quality']:.3f}")
        print(f"章节类型: {quality['section_type']}")
        print(f"实验性得分: {quality['experimental_score']:.3f}")
        print(f"包含参数: {quality['has_parameters']}")


if __name__ == "__main__":
    main()