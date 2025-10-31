#!/usr/bin/env python3
"""
双轨系统完整训练脚本

功能:
1. 训练改进的ML模型（支持RF/XGBoost/LR）
2. 生成IQR统计报告
3. 对比双轨输出
4. 保存完整系统
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml_engine.models.improved_stability_model import ImprovedStabilityClassifier
from ml_engine.features.improved_preprocess import (
    records_to_improved_dataframe,
    analyze_dataframe_quality
)
from ml_engine.recommendation.dual_track_recommender import (
    DualTrackRecommender,
    IQRAnalyzer
)
from joblib import dump, load


def load_jsonl(path: str | Path) -> list[dict]:
    """加载JSONL数据"""
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def train_ml_model(records, args):
    """训练ML模型"""
    print("\n" + "=" * 60)
    print("第1步: 训练ML模型")
    print("=" * 60)
    
    # 预处理
    print("\n预处理数据...")
    df = records_to_improved_dataframe(records)
    print(f"可用记录: {len(df)}")
    
    if len(df) < 10:
        print("警告: 数据量太少 (<10)，模型可能不可靠")
        return None
    
    # 数据质量分析
    print("\n数据质量分析:")
    stats = analyze_dataframe_quality(df)
    print(f"  总记录: {stats['total_records']}")
    print(f"  标签分布: Positive={stats['labels']['positive_count']}, "
          f"Negative={stats['labels']['negative_count']}")
    if stats['labels']['balance']:
        print(f"  平衡度: {stats['labels']['balance']:.2f}")
    
    # 训练模型
    print(f"\n训练 {args.model.upper()} 模型...")
    use_smote = args.smote and not args.no_smote
    
    model = ImprovedStabilityClassifier(
        model_type=args.model,
        use_smote=use_smote,
        random_state=42
    )
    
    model.fit(df)
    print("模型训练完成")
    
    # 交叉验证
    if args.cv:
        print("\n交叉验证评估:")
        cv_results = model.cross_validate(df, cv=min(5, len(df) // 2))
        # cross_validate已经在内部打印了详细结果，这里不需要重复打印
    
    # 特征重要性
    if args.model in ["rf", "xgb"]:
        print("\n特征重要性 (Top 10):")
        print("-" * 40)
        importance_df = model.feature_importance()
        for _, row in importance_df.head(10).iterrows():
            print(f"  {row['feature']:25s}: {row['importance']:.4f}")
    
    return model


def analyze_iqr_statistics(records, proteins):
    """分析IQR统计"""
    print("\n" + "=" * 60)
    print("第2步: IQR统计分析")
    print("=" * 60)
    
    analyzer = IQRAnalyzer()
    
    iqr_results = {}
    
    # 全局IQR
    print("\n全局IQR统计 (所有蛋白质):")
    global_windows = analyzer.analyze(records)
    iqr_results['global'] = global_windows
    
    for param, window in global_windows.items():
        print(f"  {param:20s}: [{window.min_value:.2f}, {window.max_value:.2f}] "
              f"(n={window.n_samples}, sources={window.source_count})")
    
    # 每种主要蛋白质的IQR
    print("\n各蛋白质IQR统计:")
    for protein in proteins[:5]:  # 前5种
        windows = analyzer.analyze(records, protein_filter=protein)
        if windows:
            iqr_results[protein] = windows
            print(f"\n  {protein}:")
            for param, window in windows.items():
                print(f"    {param:18s}: [{window.min_value:.2f}, {window.max_value:.2f}] "
                      f"(n={window.n_samples})")
    
    return iqr_results


def test_dual_track_system(records, model, proteins):
    """测试双轨系统"""
    print("\n" + "=" * 60)
    print("第3步: 双轨系统测试")
    print("=" * 60)
    
    # 创建推荐器
    recommender = DualTrackRecommender()
    if model and recommender.ml_predictor:
        recommender.ml_predictor.model = model
    
    # 为每种主要蛋白质生成推荐
    results = {}
    
    for protein in proteins[:3]:  # 测试前3种
        print(f"\n测试蛋白质: {protein}")
        print("-" * 40)
        
        result = recommender.recommend(
            records,
            protein_name=protein,
            use_ml=(model is not None)
        )
        
        results[protein] = result
        
        # 打印推荐
        print("\nIQR推荐:")
        for param, window in result.iqr_recommendations.items():
            print(f"  {param:20s}: [{window.min_value:.2f}, {window.max_value:.2f}]")
        
        if result.ml_recommendations:
            print("\nML推荐:")
            for param, window in result.ml_recommendations.items():
                print(f"  {param:20s}: [{window.min_value:.2f}, {window.max_value:.2f}]")
        
        print("\n共识推荐:")
        for param, window in result.consensus_recommendations.items():
            print(f"  {param:20s}: [{window.min_value:.2f}, {window.max_value:.2f}]")
        
        print(f"\n证据: {len(result.evidence)}条文献")
    
    return results


def save_system(model, iqr_results, test_results, args):
    """保存完整系统"""
    print("\n" + "=" * 60)
    print("第4步: 保存系统")
    print("=" * 60)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存ML模型
    if model:
        model_path = output_dir / "improved_model.pkl"
        dump(model, model_path)
        print(f"ML模型保存至: {model_path}")
    
    # 保存IQR统计
    iqr_path = output_dir / "iqr_statistics.json"
    iqr_dict = {}
    for key, windows in iqr_results.items():
        iqr_dict[key] = {
            param: {
                'min': float(w.min_value),
                'max': float(w.max_value),
                'median': float(w.median_value) if w.median_value else None,
                'n_samples': w.n_samples,
                'source_count': w.source_count
            }
            for param, w in windows.items()
        }
    
    with open(iqr_path, 'w', encoding='utf-8') as f:
        json.dump(iqr_dict, f, indent=2, ensure_ascii=False)
    print(f"IQR统计保存至: {iqr_path}")
    
    # 保存测试结果
    test_path = output_dir / "dual_track_results.json"
    recommender = DualTrackRecommender()
    test_dict = {
        protein: recommender.to_dict(result)
        for protein, result in test_results.items()
    }
    
    with open(test_path, 'w', encoding='utf-8') as f:
        json.dump(test_dict, f, indent=2, ensure_ascii=False)
    print(f"双轨结果保存至: {test_path}")
    
    # 保存元数据
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'model_type': args.model if model else None,
        'use_smote': args.smote and not args.no_smote,
        'data_file': args.data,
        'total_records': len(load_jsonl(args.data))
    }
    
    meta_path = output_dir / "metadata.json"
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"元数据保存至: {meta_path}")


def main():
    parser = argparse.ArgumentParser(
        description="训练双轨推荐系统 (IQR + ML)"
    )
    parser.add_argument(
        "--model",
        type=str,
        choices=["rf", "xgb", "lr"],
        default="rf",
        help="ML模型类型"
    )
    parser.add_argument("--smote", action="store_true", help="使用SMOTE")
    parser.add_argument("--no-smote", action="store_true", help="不使用SMOTE")
    parser.add_argument(
        "--data",
        type=str,
        default="literature_mining/storage/structured_store.jsonl",
        help="数据文件路径"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/dual_track",
        help="输出目录"
    )
    parser.add_argument("--cv", action="store_true", help="运行交叉验证")
    parser.add_argument("--skip-ml", action="store_true", help="跳过ML训练（仅IQR）")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("双轨推荐系统训练")
    print("=" * 60)
    print(f"数据: {args.data}")
    print(f"ML模型: {args.model.upper()}")
    print(f"输出: {args.output_dir}")
    
    # 加载数据
    print("\n加载数据...")
    records = load_jsonl(args.data)
    print(f"总记录数: {len(records)}")
    
    # 分析蛋白质分布
    protein_counts = {}
    for r in records:
        prot = r.get('protein_name')
        if prot:
            protein_counts[prot] = protein_counts.get(prot, 0) + 1
    
    top_proteins = sorted(protein_counts.items(), key=lambda x: -x[1])
    print(f"\n主要蛋白质 (Top 5):")
    for prot, count in top_proteins[:5]:
        print(f"  {prot:20s}: {count}")
    
    # 训练ML模型
    model = None
    if not args.skip_ml:
        model = train_ml_model(records, args)
    else:
        print("\n跳过ML训练")
    
    # IQR统计分析
    iqr_results = analyze_iqr_statistics(
        records, 
        [p for p, _ in top_proteins]
    )
    
    # 测试双轨系统
    test_results = test_dual_track_system(
        records,
        model,
        [p for p, _ in top_proteins]
    )
    
    # 保存系统
    save_system(model, iqr_results, test_results, args)
    
    # 总结
    print("\n" + "=" * 60)
    print("训练完成!")
    print("=" * 60)
    print(f"\n输出目录: {args.output_dir}/")
    print("  - improved_model.pkl       (ML模型)")
    print("  - iqr_statistics.json      (IQR统计)")
    print("  - dual_track_results.json  (双轨测试结果)")
    print("  - metadata.json            (元数据)")
    
    print("\n下一步:")
    print(f"  1. 查看结果: cat {args.output_dir}/dual_track_results.json")
    print(f"  2. 使用系统: python scripts/run_recommendation.py")
    print("=" * 60)


if __name__ == "__main__":
    main()

