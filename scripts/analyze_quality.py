#!/usr/bin/env python3
"""
统一的数据质量分析工具

用法:
    python scripts/analyze_quality.py --input literature_mining/storage/structured_store.jsonl
    python scripts/analyze_quality.py --input literature_mining/storage/structured_store.jsonl --output quality_reports/analysis.json
"""
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """加载JSONL文件"""
    if not path.exists():
        return []
    
    records = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def analyze_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """分析记录质量"""
    if not records:
        return {
            "total_records": 0,
            "error": "No records found"
        }
    
    total = len(records)
    
    # 基础统计
    with_ph = sum(1 for r in records if r.get('experimental_parameters', {}).get('pH') is not None)
    with_temp = sum(1 for r in records if r.get('experimental_parameters', {}).get('temperature') is not None)
    with_conc = sum(1 for r in records if r.get('experimental_parameters', {}).get('concentration_mg_ml') is not None)
    with_all_params = sum(1 for r in records 
                          if all([
                              r.get('experimental_parameters', {}).get('pH') is not None,
                              r.get('experimental_parameters', {}).get('temperature') is not None,
                              r.get('experimental_parameters', {}).get('concentration_mg_ml') is not None
                          ]))
    
    # 置信度统计
    confidences = [r.get('confidence_score', 0) for r in records]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    
    # 标签分布
    labels = defaultdict(int)
    for r in records:
        label = r.get('outcome_label', 'unknown')
        labels[label] += 1
    
    # 生物分子类型
    biomolecule_types = defaultdict(int)
    for r in records:
        btype = r.get('biomolecule_type', 'unknown')
        biomolecule_types[btype] += 1
    
    # 功能属性
    functional_properties = defaultdict(int)
    for r in records:
        fprop = r.get('functional_property', 'unknown')
        functional_properties[fprop] += 1
    
    return {
        "total_records": total,
        "parameter_coverage": {
            "with_pH": with_ph,
            "with_temperature": with_temp,
            "with_concentration": with_conc,
            "with_all_parameters": with_all_params,
            "pH_rate": round(with_ph / total, 3) if total > 0 else 0,
            "temperature_rate": round(with_temp / total, 3) if total > 0 else 0,
            "concentration_rate": round(with_conc / total, 3) if total > 0 else 0,
            "complete_rate": round(with_all_params / total, 3) if total > 0 else 0
        },
        "confidence": {
            "average": round(avg_confidence, 3),
            "min": round(min(confidences), 3) if confidences else 0,
            "max": round(max(confidences), 3) if confidences else 0
        },
        "label_distribution": dict(labels),
        "biomolecule_types": dict(biomolecule_types),
        "functional_properties": dict(functional_properties)
    }


def main():
    parser = argparse.ArgumentParser(description="分析数据质量")
    parser.add_argument(
        "--input",
        type=str,
        default="literature_mining/storage/structured_store.jsonl",
        help="输入JSONL文件路径"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出JSON报告路径（可选）"
    )
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {input_path}")
        sys.exit(1)
    
    print(f"📊 正在分析: {input_path}")
    records = load_jsonl(input_path)
    analysis = analyze_records(records)
    
    # 打印结果
    print("\n=== 数据质量分析报告 ===\n")
    print(f"总记录数: {analysis['total_records']}")
    print(f"\n参数覆盖率:")
    print(f"  - pH: {analysis['parameter_coverage']['pH_rate']*100:.1f}% ({analysis['parameter_coverage']['with_pH']} 条)")
    print(f"  - 温度: {analysis['parameter_coverage']['temperature_rate']*100:.1f}% ({analysis['parameter_coverage']['with_temperature']} 条)")
    print(f"  - 浓度: {analysis['parameter_coverage']['concentration_rate']*100:.1f}% ({analysis['parameter_coverage']['with_concentration']} 条)")
    print(f"  - 完整参数: {analysis['parameter_coverage']['complete_rate']*100:.1f}% ({analysis['parameter_coverage']['with_all_parameters']} 条)")
    
    print(f"\n置信度:")
    print(f"  - 平均: {analysis['confidence']['average']:.3f}")
    print(f"  - 范围: [{analysis['confidence']['min']:.3f}, {analysis['confidence']['max']:.3f}]")
    
    print(f"\n标签分布:")
    for label, count in analysis['label_distribution'].items():
        percentage = count / analysis['total_records'] * 100
        print(f"  - {label}: {count} ({percentage:.1f}%)")
    
    print(f"\n生物分子类型:")
    for btype, count in analysis['biomolecule_types'].items():
        percentage = count / analysis['total_records'] * 100
        print(f"  - {btype}: {count} ({percentage:.1f}%)")
    
    # 保存报告
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"\n✅ 报告已保存到: {output_path}")
    
    print("\n" + "="*50)


if __name__ == "__main__":
    main()

