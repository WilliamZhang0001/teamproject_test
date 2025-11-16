import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def get_params(rec: Dict[str, Any]):
    params = rec.get('experimental_parameters') or rec.get('parameters') or {}
    pH = params.get('pH')
    temp = params.get('temperature') if 'temperature' in params else params.get('temperature_c')
    conc = params.get('concentration_mg_ml')
    return pH, temp, conc


def analyze(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not records:
        return {"total_records": 0}
    total = len(records)
    with_ph = sum(1 for r in records if get_params(r)[0] is not None)
    with_temp = sum(1 for r in records if get_params(r)[1] is not None)
    with_conc = sum(1 for r in records if get_params(r)[2] is not None)
    with_all = sum(1 for r in records if all(v is not None for v in get_params(r)))
    confidences = [r.get('confidence_score', r.get('confidence', 0)) for r in records]
    avg_conf = sum(confidences) / len(confidences) if confidences else 0
    labels = defaultdict(int)
    for r in records:
        labels[r.get('outcome_label', 'unknown')] += 1
    biomol = defaultdict(int)
    for r in records:
        biomol[r.get('biomolecule_type', 'unknown')] += 1
    props = defaultdict(int)
    for r in records:
        props[(r.get('functional_property') or r.get('property') or 'unknown')] += 1
    param_keys = ['pH','temperature','temperature_c','concentration_mg_ml','ionic_strength_mM','additive','time_min','shear_rate_s1','pressure_bar']
    count_2 = 0
    count_3 = 0
    pols = defaultdict(int)
    for r in records:
        params = r.get('experimental_parameters') or r.get('parameters') or {}
        field_count = sum(1 for k in param_keys if params.get(k) is not None)
        if field_count == 2:
            count_2 += 1
        if field_count == 3:
            count_3 += 1
        pols[(r.get('polarity') or 'null')] += 1
    return {
        "total_records": total,
        "parameter_coverage": {
            "with_pH": with_ph,
            "with_temperature": with_temp,
            "with_concentration": with_conc,
            "with_all_parameters": with_all,
            "pH_rate": round(with_ph / total, 3),
            "temperature_rate": round(with_temp / total, 3),
            "concentration_rate": round(with_conc / total, 3),
            "complete_rate": round(with_all / total, 3),
        },
        "confidence": {
            "average": round(avg_conf, 3),
            "min": round(min(confidences), 3) if confidences else 0,
            "max": round(max(confidences), 3) if confidences else 0,
        },
        "label_distribution": dict(labels),
        "biomolecule_types": dict(biomol),
        "functional_properties": dict(props),
        "polarity_distribution": dict(pols),
        "param_field_counts": {
            "count_2": count_2,
            "count_3": count_3,
            "rate_2": round(count_2 / total, 3),
            "rate_3": round(count_3 / total, 3),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="literature_mining/storage/transfer_batch_test.jsonl")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {input_path}")
        return
    print(f"📊 正在分析: {input_path}")
    records = load_jsonl(input_path)
    report = analyze(records)
    print("\n=== 数据分布报告 ===\n")
    print(f"总记录数: {report['total_records']}")
    pc = report["parameter_coverage"]
    print("\n参数覆盖率:")
    print(f"  - pH: {pc['pH_rate']*100:.1f}% ({pc['with_pH']} 条)")
    print(f"  - 温度: {pc['temperature_rate']*100:.1f}% ({pc['with_temperature']} 条)")
    print(f"  - 浓度: {pc['concentration_rate']*100:.1f}% ({pc['with_concentration']} 条)")
    print(f"  - 完整参数: {pc['complete_rate']*100:.1f}% ({pc['with_all_parameters']} 条)")
    cf = report["confidence"]
    print("\n置信度:")
    print(f"  - 平均: {cf['average']:.3f}")
    print(f"  - 范围: [{cf['min']:.3f}, {cf['max']:.3f}]")
    print("\n标签分布:")
    for label, count in report["label_distribution"].items():
        pct = count / report['total_records'] * 100 if report['total_records'] else 0
        print(f"  - {label}: {count} ({pct:.1f}%)")
    print("\n生物分子类型:")
    for btype, count in report["biomolecule_types"].items():
        pct = count / report['total_records'] * 100 if report['total_records'] else 0
        print(f"  - {btype}: {count} ({pct:.1f}%)")
    print("\n极性分布:")
    for label, count in report["polarity_distribution"].items():
        pct = count / report['total_records'] * 100 if report['total_records'] else 0
        print(f"  - {label}: {count} ({pct:.1f}%)")
    pf = report["param_field_counts"]
    print("\n参数字段数量分布:")
    print(f"  - 恰好2个: {pf['rate_2']*100:.1f}% ({pf['count_2']} 条)")
    print(f"  - 恰好3个: {pf['rate_3']*100:.1f}% ({pf['count_3']} 条)")
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open('w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n✅ 报告已保存到: {out}")
    print("\n" + "="*50)


if __name__ == "__main__":
    main()