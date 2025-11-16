#!/bin/bash
# 模型部署脚本
# 用途：将训练好的模型复制到后端目录

echo "======================================================================"
echo "生物分子稳定性预测系统 - 模型部署脚本"
echo "======================================================================"

# 检查模型文件是否存在
if [ ! -d "models/by_biomolecule" ]; then
    echo "❌ 错误：models/by_biomolecule 目录不存在"
    echo "   请先运行: python scripts/train_by_biomolecule_type.py"
    exit 1
fi

# 创建后端模型目录
echo ""
echo "创建后端模型目录..."
mkdir -p backend/models/by_biomolecule
mkdir -p backend/models/multi_models

# 复制专门模型
echo ""
echo "复制专门模型..."

if [ -f "models/by_biomolecule/protein_lightgbm.pkl" ]; then
    cp models/by_biomolecule/protein_lightgbm.pkl backend/models/by_biomolecule/
    echo "  ✓ protein_lightgbm.pkl"
else
    echo "  ⚠️  protein_lightgbm.pkl 不存在"
fi

if [ -f "models/by_biomolecule/polysaccharide_lightgbm.pkl" ]; then
    cp models/by_biomolecule/polysaccharide_lightgbm.pkl backend/models/by_biomolecule/
    echo "  ✓ polysaccharide_lightgbm.pkl"
else
    echo "  ⚠️  polysaccharide_lightgbm.pkl 不存在"
fi

if [ -f "models/by_biomolecule/peptide_lightgbm.pkl" ]; then
    cp models/by_biomolecule/peptide_lightgbm.pkl backend/models/by_biomolecule/
    echo "  ✓ peptide_lightgbm.pkl"
else
    echo "  ⚠️  peptide_lightgbm.pkl 不存在"
fi

# 复制通用模型（作为fallback）
echo ""
echo "复制通用模型（fallback）..."

if [ -f "models/multi_models/stability_lightgbm.pkl" ]; then
    cp models/multi_models/stability_lightgbm.pkl backend/models/multi_models/
    echo "  ✓ stability_lightgbm.pkl"
else
    echo "  ⚠️  stability_lightgbm.pkl 不存在（可选）"
fi

# 复制对比报告
echo ""
echo "复制模型对比报告..."

if [ -f "models/by_biomolecule/biomolecule_models_comparison.json" ]; then
    cp models/by_biomolecule/biomolecule_models_comparison.json backend/models/by_biomolecule/
    echo "  ✓ biomolecule_models_comparison.json"
fi

# 显示文件大小
echo ""
echo "======================================================================"
echo "已部署的模型文件："
echo "======================================================================"
ls -lh backend/models/by_biomolecule/ 2>/dev/null || echo "  (空)"
ls -lh backend/models/multi_models/ 2>/dev/null || echo "  (空)"

echo ""
echo "======================================================================"
echo "部署完成！"
echo "======================================================================"
echo ""
echo "下一步："
echo "  1. 更新 backend/app/adapters/model_predictor_adapter.py"
echo "  2. 运行数据库迁移: psql -f scripts/migrate_db.sql"
echo "  3. 重启服务: docker-compose restart backend"
echo "  4. 健康检查: curl http://localhost:8000/api/models/health"
echo ""

