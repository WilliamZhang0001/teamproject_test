#!/usr/bin/env python3
"""
增强型参数提取器 - Phase 1实现

改进点：
1. 上下文窗口分析
2. 否定词检测
3. 领域词典支持
4. 置信度评分
5. 多模式匹配

作者: NLP升级团队
版本: 1.0
"""
import re
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


# =========================
# 数据结构
# =========================
class ParameterType(Enum):
    """参数类型"""
    PH = "pH"
    TEMPERATURE = "temperature"
    CONCENTRATION = "concentration"
    IONIC_STRENGTH = "ionic_strength"
    TIME = "time"


class OutcomeType(Enum):
    """结果类型"""
    STABLE = "stable"
    UNSTABLE = "unstable"
    IMPROVED = "improved"
    DECREASED = "decreased"
    UNKNOWN = "unknown"


@dataclass
class ParameterMatch:
    """参数匹配结果"""
    param_type: ParameterType
    value: float
    unit: Optional[str]
    start: int
    end: int
    context: str
    confidence: float
    is_negated: bool = False


@dataclass
class OutcomeMatch:
    """结果匹配"""
    outcome_type: OutcomeType
    start: int
    end: int
    context: str
    confidence: float
    is_negated: bool = False


# =========================
# 否定词检测器
# =========================
class NegationDetector:
    """
    否定词检测器 - Phase 1增强版
    
    改进:
    1. 扩展否定词词典
    2. 添加条件语句检测（if/when/unless等）
    3. 改进上下文窗口分析
    """
    
    # 否定词列表 - 扩展版
    NEGATION_WORDS = {
        # 直接否定
        'not', 'no', 'never', 'none', 'neither', 'nor',
        'without', 'lacking', 'lack', 'absent', 'absence',
        'failed', 'failure', 'unable', 'unavailable',
        # 否定缩略词
        'cannot', 'couldn\'t', 'didn\'t', 'doesn\'t', 
        'don\'t', 'won\'t', 'wouldn\'t', 'shouldn\'t',
        'isn\'t', 'aren\'t', 'hasn\'t', 'haven\'t',
        # 阻止/抑制词
        'prevent', 'prevented', 'preventing', 'prevention',
        'avoid', 'avoided', 'avoiding',
        'inhibit', 'inhibited', 'inhibition', 'inhibiting',
        'suppress', 'suppressed', 'suppression', 'suppressing',
        'eliminate', 'eliminated', 'elimination', 'eliminating',
        'block', 'blocked', 'blocking', 'blocks',
        # 损失/减少词
        'loss', 'lose', 'lost', 'losing',
        'decrease', 'decreased', 'decreasing', 'reduction', 'reduced',
        'decline', 'declined', 'declining', 'deteriorate', 'deterioration',
        'diminish', 'diminished', 'diminishing',
        # 其他否定表达
        'exclude', 'excluding', 'excluded',
        'missing', 'miss', 'misleading',
        'contrary', 'opposite', 'opposed',
        'against', 'versus', 'vs'
    }
    
    # 否定前缀 - 扩展版
    NEGATION_PREFIXES = {
        'un', 'in', 'im', 'il', 'ir',  # un-, in-, im-, il-, ir-
        'dis', 'de', 'non', 'anti', 'a',  # dis-, de-, non-, anti-, a-
        'mis', 'mal', 'counter', 'contra'  # mis-, mal-, counter-, contra-
    }
    
    # 条件语句标记（可能影响可靠性）
    CONDITIONAL_MARKERS = {
        'if', 'when', 'unless', 'provided', 'assuming', 'supposing',
        'depending', 'depends', 'may', 'might', 'could', 'would',
        'should', 'possibly', 'potentially', 'hypothetical',
        'speculation', 'suggest', 'might be', 'could be'
    }
    
    @classmethod
    def is_negated(cls, text: str, match_start: int, match_end: int, window: int = 80) -> bool:
        """
        检测匹配是否在否定上下文中 - Phase 1增强版
        
        改进:
        1. 扩大上下文窗口（50 -> 80）
        2. 检查更多上下文词（10 -> 15）
        3. 改进否定前缀检测
        
        Args:
            text: 完整文本
            match_start: 匹配开始位置
            match_end: 匹配结束位置
            window: 上下文窗口大小（字符数）
        
        Returns:
            是否被否定
        """
        # 提取前文上下文（扩大窗口）
        context_start = max(0, match_start - window)
        context_text = text[context_start:match_end].lower()
        
        # 提取句子片段（在匹配之前的完整句子）
        sentence_start = context_start
        for i in range(match_start - 1, context_start - 1, -1):
            if i < 0:
                break
            if text[i] in '.!?;':
                sentence_start = i + 1
                break
        
        sentence_text = text[sentence_start:match_end].lower()
        
        # 检查否定词（在句子中）
        words = re.findall(r'\b\w+\b', sentence_text)
        for word in words[-15:]:  # 看最近15个词
            if word in cls.NEGATION_WORDS:
                # 检查是否是"not only"等特殊情况
                word_idx = len(words) - words[::-1].index(word) - 1
                if word_idx > 0 and words[word_idx - 1] == 'not' and word == 'only':
                    continue  # "not only" 不构成否定
                return True
            
            # 检查否定前缀（更严格的规则）
            for prefix in cls.NEGATION_PREFIXES:
                if word.startswith(prefix) and len(word) > len(prefix) + 2:
                    # 排除某些常见的非否定词
                    if word in ['union', 'unit', 'unique', 'universal', 
                               'important', 'improve', 'increase',
                               'direct', 'display', 'develop']:
                        continue
                    return True
        
        # 检查否定短语模式
        negation_phrases = [
            r'\b(?:did|does|do|was|were|is|are|has|have)\s+not\b',
            r'\b(?:cannot|couldn\'t|wouldn\'t|shouldn\'t|isn\'t|aren\'t)\b',
            r'\b(?:no\s+longer|not\s+only|not\s+just)\b',
            r'\b(?:lack\s+of|absence\s+of|failure\s+to)\b'
        ]
        for pattern in negation_phrases:
            if re.search(pattern, sentence_text):
                return True
        
        return False
    
    @classmethod
    def has_conditional_context(cls, text: str, match_start: int, match_end: int, window: int = 100) -> bool:
        """
        检测匹配是否在条件语句上下文中
        
        条件语句可能表示假设或不确定性，降低置信度
        
        Args:
            text: 完整文本
            match_start: 匹配开始位置
            match_end: 匹配结束位置
            window: 上下文窗口大小
        
        Returns:
            是否有条件语境
        """
        context_start = max(0, match_start - window)
        context_text = text[context_start:match_end].lower()
        
        words = re.findall(r'\b\w+\b', context_text)
        for word in words[-15:]:
            if word in cls.CONDITIONAL_MARKERS:
                return True
        
        # 检查条件短语
        conditional_phrases = [
            r'\b(?:if|when|unless)\s+(?:the|this|that|it)\b',
            r'\b(?:depending|depends)\s+(?:on|upon)\b',
            r'\b(?:may|might|could|would)\s+(?:be|have)\b'
        ]
        for pattern in conditional_phrases:
            if re.search(pattern, context_text):
                return True
        
        return False


# =========================
# 领域词典
# =========================
class DomainVocabulary:
    """领域词典"""
    
    # 蛋白质名称
    PROTEINS = {
        'lysozyme', 'albumin', 'insulin', 'hemoglobin', 'myoglobin',
        'bsa', 'collagen', 'fibrinogen', 'casein', 'pepsin', 'trypsin',
        'antibody', 'immunoglobulin', 'enzyme', 'cytochrome'
    }
    
    # 缓冲液
    BUFFERS = {
        'tris', 'hepes', 'phosphate', 'pbs', 'tbs', 'acetate',
        'citrate', 'borate', 'carbonate', 'mes', 'mops', 'pipes'
    }
    
    # 稳定剂
    STABILIZERS = {
        'glycerol', 'sucrose', 'trehalose', 'sorbitol', 'mannitol',
        'peg', 'dtt', 'tcep', 'bme', 'edta', 'egta'
    }
    
    # 稳定性相关词
    STABILITY_TERMS = {
        'stable', 'stability', 'unstable', 'instability',
        'stabilize', 'destabilize', 'stabilization',
        'thermostable', 'thermostability'
    }
    
    # 降解相关词
    DEGRADATION_TERMS = {
        'degrade', 'degradation', 'denature', 'denaturation',
        'unfold', 'unfolding', 'aggregate', 'aggregation',
        'precipitate', 'precipitation'
    }
    
    @classmethod
    def extract_entities(cls, text: str) -> Dict[str, List[str]]:
        """提取领域实体"""
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))
        
        return {
            'proteins': list(words & cls.PROTEINS),
            'buffers': list(words & cls.BUFFERS),
            'stabilizers': list(words & cls.STABILIZERS),
            'stability_terms': list(words & cls.STABILITY_TERMS),
            'degradation_terms': list(words & cls.DEGRADATION_TERMS)
        }


# =========================
# 增强型模式匹配器
# =========================
class EnhancedPatternMatcher:
    """增强型模式匹配器"""
    
    # pH模式（更全面）
    PH_PATTERNS = [
        re.compile(r'\bpH\s*[=:~]?\s*(\d+(?:\.\d+)?)', re.IGNORECASE),
        re.compile(r'\bat\s+pH\s+(\d+(?:\.\d+)?)', re.IGNORECASE),
        re.compile(r'\bpH\s+(\d+(?:\.\d+)?)\s+buffer', re.IGNORECASE),
        re.compile(r'\b(?:in|with|using)\s+pH\s+(\d+(?:\.\d+)?)', re.IGNORECASE),
        re.compile(r'\bpH\s+(?:of|was|is)\s+(\d+(?:\.\d+)?)', re.IGNORECASE),
        re.compile(r'\bpH\s+range\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)', re.IGNORECASE),
    ]
    
    # 温度模式
    TEMP_PATTERNS = [
        re.compile(r'(\d+(?:\.\d+)?)\s*°?\s*C(?:elsius)?\b', re.IGNORECASE),
        re.compile(r'(\d+(?:\.\d+)?)\s*degrees?\s+(?:celsius|centigrade)', re.IGNORECASE),
        re.compile(r'\bat\s+(\d+(?:\.\d+)?)\s*°C', re.IGNORECASE),
        re.compile(r'temperature\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*°?C', re.IGNORECASE),
        re.compile(r'(\d+(?:\.\d+)?)\s*K\b', re.IGNORECASE),  # Kelvin
    ]
    
    # 特殊温度
    SPECIAL_TEMPS = {
        'room temperature': 25.0,
        'rt': 25.0,
        'ambient': 25.0,
        'ice': 4.0,
        'cold': 4.0,
        'body temperature': 37.0,
        'physiological': 37.0
    }
    
    # 浓度模式
    CONC_PATTERNS = [
        re.compile(r'(\d+(?:\.\d+)?)\s*(mg\s*/?\s*mL|mg/mL|mg\s+mL\s*-1)', re.IGNORECASE),
        re.compile(r'(\d+(?:\.\d+)?)\s*(µg\s*/?\s*mL|ug\s*/?\s*mL|μg/mL)', re.IGNORECASE),
        re.compile(r'(\d+(?:\.\d+)?)\s*(g\s*/?\s*L|g/L)', re.IGNORECASE),
        re.compile(r'(\d+(?:\.\d+)?)\s*%\s*(?:w/v|wt/vol)?', re.IGNORECASE),
        re.compile(r'(\d+(?:\.\d+)?)\s*(mM|µM|uM|μM|nM|pM|M)\b', re.IGNORECASE),
    ]
    
    @classmethod
    def extract_ph(cls, text: str) -> List[ParameterMatch]:
        """提取pH值"""
        matches = []
        for pattern in cls.PH_PATTERNS:
            for m in pattern.finditer(text):
                try:
                    # 提取pH值
                    if len(m.groups()) == 2:  # pH range
                        val1, val2 = float(m.group(1)), float(m.group(2))
                        value = (val1 + val2) / 2  # 使用范围中点
                    else:
                        value = float(m.group(1))
                    
                    # 验证pH范围
                    if not (0 <= value <= 14):
                        continue
                    
                    # 上下文
                    start, end = m.span()
                    context = cls._get_context(text, start, end)
                    
                    # 置信度
                    confidence = cls._calculate_ph_confidence(text, start, end, value)
                    
                    # 否定检测
                    is_negated = NegationDetector.is_negated(text, start, end)
                    
                    matches.append(ParameterMatch(
                        param_type=ParameterType.PH,
                        value=value,
                        unit=None,
                        start=start,
                        end=end,
                        context=context,
                        confidence=confidence,
                        is_negated=is_negated
                    ))
                except (ValueError, IndexError):
                    continue
        
        return cls._deduplicate_matches(matches)
    
    @classmethod
    def extract_temperature(cls, text: str) -> List[ParameterMatch]:
        """提取温度"""
        matches = []
        
        # 数值温度
        for pattern in cls.TEMP_PATTERNS:
            for m in pattern.finditer(text):
                try:
                    value = float(m.group(1))
                    unit = "°C"
                    
                    # Kelvin转换
                    if 'K' in m.group(0) and value > 100:
                        value = value - 273.15
                    
                    # 验证温度范围
                    if not (-80 <= value <= 150):
                        continue
                    
                    start, end = m.span()
                    context = cls._get_context(text, start, end)
                    confidence = cls._calculate_temp_confidence(text, start, end, value)
                    is_negated = NegationDetector.is_negated(text, start, end)
                    
                    matches.append(ParameterMatch(
                        param_type=ParameterType.TEMPERATURE,
                        value=value,
                        unit=unit,
                        start=start,
                        end=end,
                        context=context,
                        confidence=confidence,
                        is_negated=is_negated
                    ))
                except (ValueError, IndexError):
                    continue
        
        # 特殊温度表达
        text_lower = text.lower()
        for term, temp_value in cls.SPECIAL_TEMPS.items():
            for m in re.finditer(r'\b' + term + r'\b', text_lower):
                start, end = m.span()
                context = cls._get_context(text, start, end)
                confidence = 0.7  # 特殊表达置信度稍低
                is_negated = NegationDetector.is_negated(text, start, end)
                
                matches.append(ParameterMatch(
                    param_type=ParameterType.TEMPERATURE,
                    value=temp_value,
                    unit="°C",
                    start=start,
                    end=end,
                    context=context,
                    confidence=confidence,
                    is_negated=is_negated
                ))
        
        return cls._deduplicate_matches(matches)
    
    @classmethod
    def extract_concentration(cls, text: str) -> List[ParameterMatch]:
        """提取浓度"""
        matches = []
        for pattern in cls.CONC_PATTERNS:
            for m in pattern.finditer(text):
                try:
                    value = float(m.group(1))
                    unit = m.group(2).strip() if len(m.groups()) > 1 else None
                    
                    # 验证浓度范围
                    if value < 0 or value > 1000:
                        continue
                    
                    start, end = m.span()
                    context = cls._get_context(text, start, end)
                    confidence = cls._calculate_conc_confidence(text, start, end, value, unit)
                    is_negated = NegationDetector.is_negated(text, start, end)
                    
                    matches.append(ParameterMatch(
                        param_type=ParameterType.CONCENTRATION,
                        value=value,
                        unit=unit,
                        start=start,
                        end=end,
                        context=context,
                        confidence=confidence,
                        is_negated=is_negated
                    ))
                except (ValueError, IndexError):
                    continue
        
        return cls._deduplicate_matches(matches)
    
    @staticmethod
    def _get_context(text: str, start: int, end: int, window: int = 80) -> str:
        """获取上下文"""
        ctx_start = max(0, start - window)
        ctx_end = min(len(text), end + window)
        return text[ctx_start:ctx_end].strip()
    
    @staticmethod
    def _calculate_ph_confidence(text: str, start: int, end: int, value: float) -> float:
        """计算pH提取置信度"""
        confidence = 0.5
        context = text[max(0, start-50):min(len(text), end+50)].lower()
        
        # 有明确pH关键词
        if 'ph' in context:
            confidence += 0.2
        
        # 在合理范围内
        if 3 <= value <= 11:
            confidence += 0.1
        
        # 有buffer或溶液相关词
        if any(word in context for word in ['buffer', 'solution', 'solvent']):
            confidence += 0.1
        
        # 有明确的实验动词
        if any(word in context for word in ['measured', 'adjusted', 'maintained', 'set']):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    @staticmethod
    def _calculate_temp_confidence(text: str, start: int, end: int, value: float) -> float:
        """计算温度提取置信度"""
        confidence = 0.5
        context = text[max(0, start-50):min(len(text), end+50)].lower()
        
        # 有温度单位
        if any(unit in context for unit in ['°c', 'celsius', 'degrees']):
            confidence += 0.2
        
        # 在常见实验温度范围
        if 0 <= value <= 100:
            confidence += 0.1
        
        # 有温度相关动词
        if any(word in context for word in ['heated', 'cooled', 'incubated', 'stored']):
            confidence += 0.1
        
        # 有明确的温度控制词
        if any(word in context for word in ['temperature', 'thermal']):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    @staticmethod
    def _calculate_conc_confidence(text: str, start: int, end: int, value: float, unit: Optional[str]) -> float:
        """计算浓度提取置信度"""
        confidence = 0.4  # 浓度基础置信度较低
        context = text[max(0, start-50):min(len(text), end+50)].lower()
        
        # 有明确单位
        if unit:
            confidence += 0.2
        
        # 有浓度相关词
        if any(word in context for word in ['concentration', 'diluted', 'concentrated']):
            confidence += 0.2
        
        # 有蛋白质或化合物名称
        entities = DomainVocabulary.extract_entities(context)
        if entities['proteins'] or entities['buffers']:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    @staticmethod
    def _deduplicate_matches(matches: List[ParameterMatch]) -> List[ParameterMatch]:
        """去重重叠的匹配"""
        if not matches:
            return []
        
        # 按置信度排序
        matches = sorted(matches, key=lambda x: x.confidence, reverse=True)
        
        # 去重
        result = []
        used_ranges = []
        
        for match in matches:
            # 检查是否与已有匹配重叠
            overlap = False
            for used_start, used_end in used_ranges:
                if not (match.end <= used_start or match.start >= used_end):
                    overlap = True
                    break
            
            if not overlap:
                result.append(match)
                used_ranges.append((match.start, match.end))
        
        return result


# =========================
# 结果提取器
# =========================
class OutcomeExtractor:
    """实验结果提取器"""
    
    STABILITY_PATTERNS = [
        (re.compile(r'\b(stable|stability|stabilized|stabilization)\b', re.I), OutcomeType.STABLE, 0.8),
        (re.compile(r'\b(maintained|retained|preserved)\b', re.I), OutcomeType.STABLE, 0.6),
        (re.compile(r'\b(unstable|instability|destabilized)\b', re.I), OutcomeType.UNSTABLE, 0.8),
        (re.compile(r'\b(degrad|denatur|unfold|aggregat|precipitat)\w*\b', re.I), OutcomeType.UNSTABLE, 0.7),
        (re.compile(r'\b(improved|enhanced|increased|better)\b', re.I), OutcomeType.IMPROVED, 0.6),
        (re.compile(r'\b(decreased|reduced|lowered|worse)\b', re.I), OutcomeType.DECREASED, 0.6),
    ]
    
    @classmethod
    def extract_outcomes(cls, text: str) -> List[OutcomeMatch]:
        """提取实验结果"""
        matches = []
        
        for pattern, outcome_type, base_conf in cls.STABILITY_PATTERNS:
            for m in pattern.finditer(text):
                start, end = m.span()
                context = EnhancedPatternMatcher._get_context(text, start, end)
                is_negated = NegationDetector.is_negated(text, start, end)
                
                # 否定会反转结果
                if is_negated:
                    if outcome_type == OutcomeType.STABLE:
                        outcome_type = OutcomeType.UNSTABLE
                    elif outcome_type == OutcomeType.UNSTABLE:
                        outcome_type = OutcomeType.STABLE
                    base_conf *= 0.8  # 降低置信度
                
                matches.append(OutcomeMatch(
                    outcome_type=outcome_type,
                    start=start,
                    end=end,
                    context=context,
                    confidence=base_conf,
                    is_negated=is_negated
                ))
        
        return matches


# =========================
# 主提取器
# =========================
class EnhancedExtractor:
    """增强型参数提取器 - 主类"""
    
    def __init__(self):
        self.pattern_matcher = EnhancedPatternMatcher()
        self.outcome_extractor = OutcomeExtractor()
        self.negation_detector = NegationDetector()
        self.vocabulary = DomainVocabulary()
    
    def extract(self, text: str) -> Dict[str, Any]:
        """
        提取所有参数和结果
        
        Args:
            text: 输入文本
        
        Returns:
            提取结果字典
        """
        # 提取参数
        ph_matches = self.pattern_matcher.extract_ph(text)
        temp_matches = self.pattern_matcher.extract_temperature(text)
        conc_matches = self.pattern_matcher.extract_concentration(text)
        
        # 提取结果
        outcome_matches = self.outcome_extractor.extract_outcomes(text)
        
        # 提取领域实体
        entities = self.vocabulary.extract_entities(text)
        
        # 计算整体置信度
        all_params = ph_matches + temp_matches + conc_matches
        avg_confidence = sum(m.confidence for m in all_params) / len(all_params) if all_params else 0.0
        
        return {
            'ph': [{'value': m.value, 'confidence': m.confidence, 'negated': m.is_negated} 
                   for m in ph_matches],
            'temperature': [{'value': m.value, 'unit': m.unit, 'confidence': m.confidence, 'negated': m.is_negated}
                           for m in temp_matches],
            'concentration': [{'value': m.value, 'unit': m.unit, 'confidence': m.confidence, 'negated': m.is_negated}
                             for m in conc_matches],
            'outcomes': [{'type': m.outcome_type.value, 'confidence': m.confidence, 'negated': m.is_negated}
                        for m in outcome_matches],
            'entities': entities,
            'overall_confidence': avg_confidence,
            'has_parameters': len(all_params) > 0,
            'has_outcomes': len(outcome_matches) > 0
        }


# =========================
# 测试代码
# =========================
if __name__ == "__main__":
    extractor = EnhancedExtractor()
    
    test_texts = [
        "The protein was stable at pH 7.4 and 25°C with 5 mg/mL concentration.",
        "At pH 3.0, the enzyme showed no activity and became unstable.",
        "The sample was not stable at room temperature but remained active at 4°C.",
        "Heating to 60°C did not cause denaturation when pH was maintained at 8.0."
    ]
    
    print("Enhanced Extractor Test\n" + "="*60)
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: {text}")
        result = extractor.extract(text)
        print(f"pH: {result['ph']}")
        print(f"Temperature: {result['temperature']}")
        print(f"Concentration: {result['concentration']}")
        print(f"Outcomes: {result['outcomes']}")
        print(f"Overall Confidence: {result['overall_confidence']:.2f}")

