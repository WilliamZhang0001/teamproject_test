#!/usr/bin/env python3
"""
双轨系统演示脚本 - 快速展示系统能力

这个脚本会:
1. 快速训练一个简化模型
2. 运行IQR统计
3. 展示双轨推荐
4. 生成可视化对比
"""
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from ml_engine.recommendation.dual_track_recommender import (
    DualTrackRecommender,
    IQRAnalyzer
)
from ml_engine.models.improved_stability_model import ImprovedStabilityClassifier
from ml_engine.features.improved_preprocess import records_to_improved_dataframe


def load_jsonl(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def demo():
    print("=" * 80)
    print(" " * 20 + "双轨推荐系统 - 快速演示")
    print("=" * 80)
    
    # 加载数据
    print("\n[1/5] 加载数据...")
    data_path = "literature_mining/storage/structured_store.jsonl"
    records = load_jsonl(data_path)
    print(f"      ✓ 加载了 {len(records)} 条记录")
    
    # 统计蛋白质
    protein_counts = {}
    for r in records:
        prot = r.get('protein_name')
        if prot:
            protein_counts[prot] = protein_counts.get(prot, 0) + 1
    
    top_proteins = sorted(protein_counts.items(), key=lambda x: -x[1])[:5]
    print(f"      主要蛋白质: {', '.join([p for p, _ in top_proteins])}")
    
    # 训练ML模型
    print("\n[2/5] 训练ML模型 (RandomForest)...")
    df = records_to_improved_dataframe(records)
    print(f"      ✓ 预处理后: {len(df)} 条可用记录")
    
    if len(df) >= 10:
        model = ImprovedStabilityClassifier(model_type='rf', use_smote=False)
        model.fit(df)
        print(f"      ✓ 模型训练完成")
        
        # 快速评估
        try:
            cv_results = model.cross_validate(df, cv=3)
            f1 = cv_results.get('f1', {}).get('mean', 0)
            print(f"      F1-Score: {f1:.3f}")
        except:
            print("      (跳过交叉验证)")
    else:
        model = None
        print(f"      ⚠️  数据不足，跳过ML训练")
    
    # IQR统计
    print("\n[3/5] 计算IQR统计...")
    iqr_analyzer = IQRAnalyzer()
    global_iqr = iqr_analyzer.analyze(records)
    print(f"      ✓ 计算了 {len(global_iqr)} 个参数的IQR窗口")
    
    # 创建推荐器
    print("\n[4/5] 创建双轨推荐器...")
    recommender = DualTrackRecommender()
    if model:
        recommender.ml_predictor.model = model
        print(f"      ✓ ML模型已加载")
    else:
        print(f"      ⊗ 仅使用IQR推荐")
    
    # 为前3种蛋白质生成推荐
    print("\n[5/5] 生成推荐...")
    print("=" * 80)
    
    for i, (protein, count) in enumerate(top_proteins[:3], 1):
        print(f"\n{'=' * 80}")
        print(f"示例 {i}: {protein} ({count} 条记录)")
        print('=' * 80)
        
        result = recommender.recommend(
            records,
            protein_name=protein,
            use_ml=(model is not None)
        )
        
        # 显示推荐
        if result.iqr_recommendations:
            print("\n📊 IQR统计推荐:")
            print("-" * 80)
            for param, window in result.iqr_recommendations.items():
                print(f"  {param:20s}: [{window.min_value:6.2f}, {window.max_value:6.2f}]  "
                      f"(n={window.n_samples:3d}, sources={window.source_count:2d})")
        
        if result.ml_recommendations:
            print("\n🤖 ML模型推荐:")
            print("-" * 80)
            for param, window in result.ml_recommendations.items():
                print(f"  {param:20s}: [{window.min_value:6.2f}, {window.max_value:6.2f}]  "
                      f"(conf={window.confidence:.2f})")
        
        if result.consensus_recommendations:
            print("\n✨ 共识推荐 (推荐用于DoE):")
            print("-" * 80)
            for param, window in result.consensus_recommendations.items():
                print(f"  {param:20s}: [{window.min_value:6.2f}, {window.max_value:6.2f}]  "
                      f"(method={window.method})")
        
        print(f"\n📚 证据: {len(result.evidence)} 篇文献")
        
        # 显示一条证据示例
        if result.evidence and result.evidence[0].snippets:
            print(f"\n示例证据:")
            snippet = result.evidence[0].snippets[0]
            print(f"  \"{snippet[:100]}...\"")
    
    # 总结
    print("\n" + "=" * 80)
    print("演示完成!")
    print("=" * 80)
    print("\n💡 建议的下一步:")
    print("  1. 完整训练: python scripts/train_dual_track_system.py --model rf --cv")
    print("  2. 交互使用: python scripts/run_recommendation.py --interactive")
    print("  3. 查看文档: cat 双轨系统快速开始.md")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        demo()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

