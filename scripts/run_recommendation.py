#!/usr/bin/env python3
"""
运行双轨推荐系统 - 交互式或API模式

使用示例:
    # 交互模式
    python scripts/run_recommendation.py --interactive
    
    # 命令行模式
    python scripts/run_recommendation.py --protein lysozyme
    
    # JSON输出
    python scripts/run_recommendation.py --protein BSA --json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ml_engine.recommendation.dual_track_recommender import DualTrackRecommender
from joblib import load


def load_jsonl(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def print_recommendations(result, verbose=False):
    """打印推荐结果"""
    print("\n" + "=" * 70)
    print(f"蛋白质: {result.protein_name}")
    print(f"属性: {result.property_type}")
    print("=" * 70)
    
    # IQR推荐
    if result.iqr_recommendations:
        print("\n[IQR统计推荐] (基于文献证据):")
        print("-" * 70)
        for param, window in result.iqr_recommendations.items():
            median_str = f"{window.median_value:6.2f}" if window.median_value else "   N/A"
            print(f"  {param:20s}: [{window.min_value:6.2f}, {window.max_value:6.2f}] "
                  f"(median: {median_str}, n={window.n_samples}, conf={window.confidence:.2f})")
    
    # ML推荐
    if result.ml_recommendations:
        print("\n[ML模型推荐] (基于预测优化):")
        print("-" * 70)
        for param, window in result.ml_recommendations.items():
            median_str = f"{window.median_value:6.2f}" if window.median_value else "   N/A"
            print(f"  {param:20s}: [{window.min_value:6.2f}, {window.max_value:6.2f}] "
                  f"(median: {median_str}, conf={window.confidence:.2f})")
    
    # 共识推荐
    if result.consensus_recommendations:
        print("\n[共识推荐] (综合建议 - 用于DoE设计):")
        print("-" * 70)
        for param, window in result.consensus_recommendations.items():
            print(f"  {param:20s}: [{window.min_value:6.2f}, {window.max_value:6.2f}] "
                  f"(method: {window.method})")
    
    # 证据
    if verbose and result.evidence:
        print(f"\n[支持证据] (前5条):")
        print("-" * 70)
        for i, ev in enumerate(result.evidence[:5], 1):
            print(f"\n  [{i}] DOI: {ev.doi}")
            if ev.snippets:
                for snippet in ev.snippets[:2]:
                    print(f"      \"{snippet[:100]}...\"")
    
    print(f"\n[统计信息]:")
    print(f"  总记录数: {result.metadata.get('total_records', 'N/A')}")
    print(f"  过滤后记录: {result.metadata.get('filtered_records', 'N/A')}")
    print(f"  证据文献数: {len(result.evidence)}")
    print(f"  ML可用: {'是' if result.metadata.get('ml_available') else '否'}")
    print("=" * 70)


def interactive_mode(recommender, records, proteins):
    """交互模式"""
    print("\n" + "=" * 70)
    print("双轨推荐系统 - 交互模式")
    print("=" * 70)
    print(f"\n可用蛋白质 ({len(proteins)} 种):")
    for i, (prot, count) in enumerate(proteins[:10], 1):
        print(f"  {i:2d}. {prot:20s} ({count} 条记录)")
    
    if len(proteins) > 10:
        print(f"  ... 还有 {len(proteins) - 10} 种")
    
    while True:
        print("\n" + "-" * 70)
        protein = input("\n请输入蛋白质名称 (或 'q' 退出): ").strip()
        
        if protein.lower() in ['q', 'quit', 'exit']:
            print("再见!")
            break
        
        if not protein:
            continue
        
        # 检查是否存在
        protein_dict = dict(proteins)
        if protein not in protein_dict:
            print(f"未找到 '{protein}'，请从列表中选择")
            continue
        
        # 生成推荐
        print(f"\n正在生成 {protein} 的推荐...")
        result = recommender.recommend(
            records,
            protein_name=protein,
            use_ml=True
        )
        
        print_recommendations(result, verbose=True)
        
        # 询问是否保存
        save = input("\n是否保存结果到JSON? (y/n): ").strip().lower()
        if save == 'y':
            output_file = f"{protein}_recommendation.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(recommender.to_dict(result), f, indent=2, ensure_ascii=False)
            print(f"已保存至: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="双轨推荐系统 - 运行推荐"
    )
    parser.add_argument(
        "--data",
        type=str,
        default="literature_mining/storage/structured_store.jsonl",
        help="数据文件"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="models/dual_track/improved_model.pkl",
        help="ML模型路径"
    )
    parser.add_argument(
        "--protein",
        type=str,
        help="目标蛋白质名称"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="交互模式"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON输出（用于API）"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="输出文件路径"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出（包含证据）"
    )
    
    args = parser.parse_args()
    
    # 加载数据
    records = load_jsonl(args.data)
    if not records:
        print(f"错误: 无法加载数据 {args.data}")
        sys.exit(1)
    
    # 统计蛋白质
    protein_counts = {}
    for r in records:
        prot = r.get('protein_name')
        if prot:
            protein_counts[prot] = protein_counts.get(prot, 0) + 1
    
    proteins = sorted(protein_counts.items(), key=lambda x: -x[1])
    
    # 创建推荐器
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"警告: ML模型未找到 ({model_path})，仅使用IQR")
        recommender = DualTrackRecommender()
    else:
        recommender = DualTrackRecommender(model_path=model_path)
        print(f"已加载ML模型: {model_path}")
    
    # 交互模式
    if args.interactive:
        interactive_mode(recommender, records, proteins)
        return
    
    # 命令行模式
    if not args.protein:
        print("错误: 请指定 --protein 或使用 --interactive 模式")
        print(f"\n可用蛋白质: {', '.join([p for p, _ in proteins[:10]])}")
        sys.exit(1)
    
    # 生成推荐
    result = recommender.recommend(
        records,
        protein_name=args.protein,
        use_ml=True
    )
    
    # 输出
    if args.json:
        output = recommender.to_dict(result)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            print(f"结果已保存至: {args.output}")
        else:
            print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print_recommendations(result, verbose=args.verbose)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(recommender.to_dict(result), f, indent=2, ensure_ascii=False)
            print(f"\nJSON结果已保存至: {args.output}")


if __name__ == "__main__":
    main()

