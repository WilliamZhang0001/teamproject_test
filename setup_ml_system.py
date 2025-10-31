"""
all set up 可参考

运行此脚本将完成：
1. 训练多种分类模型（RandomForest, XGBoost, LightGBM）
2. 训练回归模型（预测具体参数值）
3. 生成IQR统计数据
4. 测试两种应用场景
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description, optional=False):
    """运行命令"""
    print(f"\n{'='*70}")
    print(f"{description}")
    print('='*70)
    result = subprocess.run(cmd, shell=True, capture_output=False)
    if result.returncode != 0:
        if optional:
            print(f"WARNING: {description} failed (optional step, continuing...)")
            return True
        else:
            print(f"ERROR: {description} failed!")
            return False
    return True

def main():
    print("\n" + "="*70)
    print("ML System Setup v2.0")
    print("="*70)
    print("\n本脚本将自动完成以下步骤:")
    print("  1. 训练多模型对比（RandomForest + XGBoost + LightGBM）")
    print("  2. 训练回归模型（pH, 温度, 浓度预测）")
    print("  3. 生成IQR统计数据")
    print("  4. 测试两种应用场景")
    print("\n预计耗时: 10-15分钟")
    
    python_exe = sys.executable
    
    # Step 1: 训练多模型（分类）- Stability
    print("\n\n" + "="*70)
    print("阶段1: 训练多模型（分类）")
    print("="*70)
    cmd1 = f"{python_exe} scripts/train_multi_models.py --experiment-type stability --mode classification"
    if not run_command(cmd1, "训练Stability分类模型（RF + XGBoost + LightGBM）"):
        print("\n提示: 如果XGBoost或LightGBM安装失败，可以运行:")
        print("  pip install xgboost lightgbm")
        return
    
    # Step 2: 训练回归模型（可选）
    print("\n\n" + "="*70)
    print("阶段2: 训练回归模型（可选）")
    print("="*70)
    cmd2 = f"{python_exe} scripts/train_multi_models.py --experiment-type stability --mode regression --regress-params \"pH,temperature_c,concentration_mg_ml\""
    run_command(cmd2, "训练回归模型（预测pH/温度/浓度）", optional=True)
    
    # Step 3: 生成IQR统计数据
    print("\n\n" + "="*70)
    print("阶段3: 生成IQR统计")
    print("="*70)
    cmd3 = f"{python_exe} scripts/generate_iqr_statistics.py"
    if not run_command(cmd3, "生成IQR统计数据（用于参数推荐）"):
        return
    
    # Step 4: 测试两种场景
    print("\n\n" + "="*70)
    print("阶段4: 测试应用场景")
    print("="*70)
    cmd4 = f"{python_exe} test_scenarios.py"
    if not run_command(cmd4, "测试场景1（参数验证）和场景2（IQR推荐）"):
        return
    
    # 完成
    print("\n" + "="*70)
    print("=== 设置完成！ ===")
    print("="*70)
    
    print("\n已创建的模型:")
    print("  [分类模型]")
    print("    - models/multi_models/stability_xgboost.pkl (XGBoost)")
    print("    - models/multi_models/stability_lightgbm.pkl (LightGBM)")
    print("  [回归模型]")
    print("    - models/multi_models/stability_pH_regressor.pkl")
    print("    - models/multi_models/stability_temperature_c_regressor.pkl")
    print("    - models/multi_models/stability_concentration_mg_ml_regressor.pkl")
    print("  [统计数据]")
    print("    - models/iqr_statistics.json")
    
    print("\n使用方法:")
    print("  1. 运行测试脚本: python test_scenarios.py")
    print("  2. 查看模型对比: cat models/multi_models/stability_comparison.json")
    print("  3. 运行高级演示: python demo_advanced_features.py")
    
    print("\n模型性能（预期）:")
    print("  RandomForest:  F1=0.626 (baseline)")
    print("  XGBoost:       F1=0.702 (+12%)")
    print("  LightGBM:      F1=0.703 (+12%) <- 最佳性能")
    
    print("\n下一步:")
    print("  - 集成到API: 参考 ML系统使用指南.md")

if __name__ == '__main__':
    main()

