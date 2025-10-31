"""
改进的数据预处理
支持更多特征和更好的标签映射
"""
from __future__ import annotations

import pandas as pd
from typing import Iterable


def _label_from_outcome_and_polarity(
    outcome_label: str | None, 
    polarity: str | None,
    property_type: str | None = None
) -> int | None:
    """
    从outcome_label和polarity推断稳定性标签
    
    优先级:
    1. **检查防止/减少关键词（对aggregation特别重要）**
    2. **outcome_label中的明确关键词（绝对优先）**
    3. polarity作为辅助判断（仅在没有明确关键词时使用）
    
    Returns:
        1 = stable/good outcome, 0 = unstable/bad outcome, None = uncertain
    """
    if not outcome_label:
        # 如果没有outcome_label，尝试用polarity
        if polarity == 'positive':
            return 1
        elif polarity == 'negative':
            return 0
        return None
    
    t = outcome_label.lower()
    
    # 防止/减少问题的关键词（正面结果）
    prevention_keywords = [
        "prevent", "reduce", "inhibit", "suppress", "avoid", 
        "no aggregation", "without aggregation", "no precipitation",
        "no denaturation", "protected", "resistance"
    ]
    
    # 明确的正面标签
    positive_keywords = [
        "stable", "stability", "stabilize", "maintain", "preserve", 
        "soluble", "solubility", "active", "activity", "functional"
    ]
    
    # 明确的负面标签
    negative_keywords = [
        "unstable", "denatur", "aggregat", "precipitat", 
        "insoluble", "inactive", "degradation", "hydrolysis",
        "unfold", "unfolding", "fibril"
    ]
    
    # **首先检查防止/减少关键词（最高优先级）**
    has_prevention = any(kw in t for kw in prevention_keywords)
    if has_prevention:
        return 1  # 防止/减少问题 = 好结果
    
    has_positive = any(kw in t for kw in positive_keywords)
    has_negative = any(kw in t for kw in negative_keywords)
    
    # **outcome_label绝对优先**
    if has_negative:
        # 只要有negative关键词（且没有prevention），就标记为unstable
        return 0
    if has_positive:
        # 只要有positive关键词且没有negative，就标记为stable
        return 1
    
    # 没有明确关键词，使用polarity辅助
    if polarity == 'positive':
        return 1
    elif polarity == 'negative':
        return 0
    
    return None


def records_to_improved_dataframe(records: Iterable[dict | "ExtractionRecord"]) -> pd.DataFrame:
    """
    将extraction records转换为改进的DataFrame
    
    包含更多特征:
    - 基础参数: pH, temperature_c, concentration_mg_ml
    - 蛋白质: protein_name
    - 语义: polarity
    - 质量: confidence
    - 标签: label (结合outcome_label和polarity)
    """
    rows = []
    for r in records:
        # Support both dicts and pydantic models
        if hasattr(r, "model_dump"):
            r = r.model_dump()
        
        p = r.get("parameters", {})
        
        # 使用改进的标签推断
        label = _label_from_outcome_and_polarity(
            r.get("outcome_label"),
            r.get("polarity"),
            r.get("property")
        )
        
        rows.append({
            # 基础特征（8个参数）
            "pH": p.get("pH"),
            "temperature_c": p.get("temperature_c"),
            "concentration_mg_ml": p.get("concentration_mg_ml"),
            "ionic_strength_mM": p.get("ionic_strength_mM"),
            "additive": p.get("additive"),
            "time_min": p.get("time_min"),
            "shear_rate_s1": p.get("shear_rate_s1"),
            "pressure_bar": p.get("pressure_bar"),
            
            # 生物分子特征（支持所有类型）
            "biomolecule_type": r.get("biomolecule_type", "protein"),
            "protein_name": r.get("protein_name"),  # 兼容字段：存储所有类型名称
            
            # 实验类型（关键！用于分类训练）
            "property": r.get("property", "stability"),  # stability/solubility/aggregation
            
            # 语义特征
            "polarity": r.get("polarity"),
            
            # 质量特征
            "confidence": r.get("confidence", 0.5),
            
            # 标签
            "label": label,
            
            # 原始文本 (可选,用于调试)
            "outcome_text": r.get("outcome_text"),
            "outcome_label": r.get("outcome_label"),
        })

    df = pd.DataFrame(rows)
    
    # 过滤：移除没有标签的
    df = df.dropna(subset=["label"])
    
    # 过滤：移除所有参数都缺失的（包含新增的8种参数）
    has_any_param = (
        df.get("pH", pd.Series(dtype='float64')).notna() | 
        df.get("temperature_c", pd.Series(dtype='float64')).notna() | 
        df.get("concentration_mg_ml", pd.Series(dtype='float64')).notna() |
        df.get("ionic_strength_mM", pd.Series(dtype='float64')).notna() |
        df.get("additive", pd.Series(dtype='object')).notna() |
        df.get("time_min", pd.Series(dtype='float64')).notna() |
        df.get("shear_rate_s1", pd.Series(dtype='float64')).notna() |
        df.get("pressure_bar", pd.Series(dtype='float64')).notna()
    )
    # 如果DataFrame为空，has_any_param会是空Series，需要检查
    if len(has_any_param) > 0:
        df = df[has_any_param]
    
    return df


def analyze_dataframe_quality(df: pd.DataFrame) -> dict:
    """
    分析DataFrame质量
    
    Returns:
        dict with statistics
    """
    total = len(df)
    
    if total == 0:
        return {"error": "Empty dataframe"}
    
    stats = {
        "total_records": total,
        "features": {
            # 8个参数覆盖率
            "pH_coverage": df["pH"].notna().sum() / total if "pH" in df.columns else 0,
            "temperature_coverage": df["temperature_c"].notna().sum() / total if "temperature_c" in df.columns else 0,
            "concentration_coverage": df["concentration_mg_ml"].notna().sum() / total if "concentration_mg_ml" in df.columns else 0,
            "ionic_strength_coverage": df["ionic_strength_mM"].notna().sum() / total if "ionic_strength_mM" in df.columns else 0,
            "additive_coverage": df["additive"].notna().sum() / total if "additive" in df.columns else 0,
            "time_coverage": df["time_min"].notna().sum() / total if "time_min" in df.columns else 0,
            "shear_rate_coverage": df["shear_rate_s1"].notna().sum() / total if "shear_rate_s1" in df.columns else 0,
            "pressure_coverage": df["pressure_bar"].notna().sum() / total if "pressure_bar" in df.columns else 0,
            # 生物分子特征
            "biomolecule_type_coverage": df["biomolecule_type"].notna().sum() / total if "biomolecule_type" in df.columns else 0,
            "protein_name_coverage": df["protein_name"].notna().sum() / total if "protein_name" in df.columns else 0,
            "polarity_coverage": df["polarity"].notna().sum() / total if "polarity" in df.columns else 0,
        },
        "biomolecule_types": {
            col: count for col, count in df["biomolecule_type"].value_counts().items()
        } if "biomolecule_type" in df.columns else {},
        "labels": {
            "positive_count": (df["label"] == 1).sum(),
            "negative_count": (df["label"] == 0).sum(),
            "balance": None,
        },
        "quality": {
            "avg_confidence": df["confidence"].mean(),
            "min_confidence": df["confidence"].min(),
            "max_confidence": df["confidence"].max(),
        }
    }
    
    # 计算平衡度
    pos = stats["labels"]["positive_count"]
    neg = stats["labels"]["negative_count"]
    if pos > 0 and neg > 0:
        stats["labels"]["balance"] = min(pos, neg) / max(pos, neg)
    
    return stats

