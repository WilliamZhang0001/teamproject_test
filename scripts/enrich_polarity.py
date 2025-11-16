import json
import argparse
from pathlib import Path
from typing import List, Dict, Any


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


def save_jsonl(path: Path, records: List[Dict[str, Any]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def infer_polarity(text: str, existing: Any) -> Any:
    if existing and existing in {"positive", "mixed", "negative"}:
        return existing
    t = (text or "").lower()
    pos_kw = [
        "stabilize",
        "stabilizes",
        "stability",
        "stable",
        "soluble",
        "solubility",
        "improve",
        "improves",
        "improved",
        "increase stability",
        "enhance",
        "enhances",
        "enhanced",
        "extend",
        "extends",
        "extended",
        "reduce aggregation",
        "reduces aggregation",
        "reduced aggregation",
        "inhibit aggregation",
        "inhibits aggregation",
        "prevent aggregation",
        "prevents aggregation",
        "reduce precipitation",
        "reduces precipitation",
        "reduced precipitation",
        "decrease aggregation",
        "decreases aggregation",
        "decreased aggregation",
    ]
    neg_kw = [
        "aggregation",
        "aggregates",
        "aggregated",
        "precipitate",
        "precipitation",
        "denaturation",
        "denature",
        "insoluble",
        "decrease stability",
        "reduced stability",
        "increase aggregation",
        "increases aggregation",
        "induce aggregation",
        "induces aggregation",
    ]
    pos_hit = any(k in t for k in pos_kw)
    neg_hit = any(k in t for k in neg_kw)
    if pos_hit and neg_hit:
        return "mixed"
    if pos_hit:
        return "positive"
    if neg_hit:
        return "negative"
    return existing or None


def enrich(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for r in records:
        params = r.get("experimental_parameters") or r.get("parameters") or {}
        text = (r.get("outcome_text") or "") + " " + (params.get("raw_context") or "")
        r["polarity"] = infer_polarity(text, r.get("polarity"))
        out.append(r)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()
    ip = Path(args.input)
    if not ip.exists():
        print(f"❌ 文件不存在: {ip}")
        return
    print(f"📥 读取: {ip}")
    records = load_jsonl(ip)
    enriched = enrich(records)
    op = Path(args.output)
    save_jsonl(op, enriched)
    total = len(enriched)
    pos = sum(1 for r in enriched if r.get("polarity") == "positive")
    mix = sum(1 for r in enriched if r.get("polarity") == "mixed")
    neg = sum(1 for r in enriched if r.get("polarity") == "negative")
    print(f"✅ 已写入: {op}")
    print(f"总数: {total}, positive: {pos} ({pos/total if total else 0:.3f}), mixed: {mix} ({mix/total if total else 0:.3f}), negative: {neg} ({neg/total if total else 0:.3f})")


if __name__ == "__main__":
    main()