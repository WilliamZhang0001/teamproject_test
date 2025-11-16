-- 数据库迁移脚本
-- 用途：更新predictions表以支持专门模型

-- ====================================================================
-- 生物分子稳定性预测系统 - 数据库迁移
-- 版本：v2.0
-- 日期：2025-01-15
-- ====================================================================

BEGIN;

-- 1. 添加新字段
ALTER TABLE predictions 
ADD COLUMN IF NOT EXISTS biomolecule_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS model_used VARCHAR(50),
ADD COLUMN IF NOT EXISTS model_source VARCHAR(20);

-- 2. 为新字段添加注释
COMMENT ON COLUMN predictions.biomolecule_type IS '生物分子类型：protein, polysaccharide, peptide';
COMMENT ON COLUMN predictions.model_used IS '使用的模型名称：LightGBM, XGBoost等';
COMMENT ON COLUMN predictions.model_source IS '模型来源：specialized（专门模型）或 general（通用模型）';

-- 3. 添加索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_predictions_biomolecule_type 
ON predictions(biomolecule_type);

CREATE INDEX IF NOT EXISTS idx_predictions_model_source 
ON predictions(model_source);

CREATE INDEX IF NOT EXISTS idx_predictions_created_at 
ON predictions(created_at DESC);

-- 4. 迁移历史数据：为现有记录推断biomolecule_type
UPDATE predictions 
SET biomolecule_type = CASE
    -- 基于biomolecule_name推断
    WHEN LOWER(biomolecule_name) LIKE '%protein%' THEN 'protein'
    WHEN LOWER(biomolecule_name) LIKE '%albumin%' THEN 'protein'
    WHEN LOWER(biomolecule_name) LIKE '%lysozyme%' THEN 'protein'
    WHEN LOWER(biomolecule_name) LIKE '%antibody%' THEN 'protein'
    WHEN LOWER(biomolecule_name) LIKE '%enzyme%' THEN 'protein'
    
    WHEN LOWER(biomolecule_name) LIKE '%polysaccharide%' THEN 'polysaccharide'
    WHEN LOWER(biomolecule_name) LIKE '%dextran%' THEN 'polysaccharide'
    WHEN LOWER(biomolecule_name) LIKE '%chitosan%' THEN 'polysaccharide'
    WHEN LOWER(biomolecule_name) LIKE '%cellulose%' THEN 'polysaccharide'
    
    WHEN LOWER(biomolecule_name) LIKE '%peptide%' THEN 'peptide'
    
    -- 默认为protein（最常见）
    ELSE 'protein'
END
WHERE biomolecule_type IS NULL;

-- 5. 更新历史记录的模型信息
UPDATE predictions 
SET 
    model_used = 'LightGBM',
    model_source = 'general'
WHERE model_used IS NULL;

-- 6. 验证数据完整性
DO $$
DECLARE
    null_count INTEGER;
    total_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO null_count 
    FROM predictions 
    WHERE biomolecule_type IS NULL;
    
    SELECT COUNT(*) INTO total_count 
    FROM predictions;
    
    IF null_count > 0 THEN
        RAISE WARNING '警告：有 % 条记录的 biomolecule_type 为 NULL (总共 % 条)', 
                      null_count, total_count;
    ELSE
        RAISE NOTICE '✓ 数据完整性检查通过：所有记录都有 biomolecule_type';
    END IF;
END $$;

-- 7. 创建视图：各物质类型的统计
CREATE OR REPLACE VIEW v_predictions_by_biomolecule AS
SELECT 
    biomolecule_type,
    model_source,
    COUNT(*) as prediction_count,
    AVG(confidence) as avg_confidence,
    SUM(CASE WHEN prediction = 'stable' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as stable_rate,
    MIN(created_at) as first_prediction,
    MAX(created_at) as latest_prediction
FROM predictions
GROUP BY biomolecule_type, model_source
ORDER BY biomolecule_type, model_source;

-- 8. 创建视图：模型使用情况
CREATE OR REPLACE VIEW v_model_usage_stats AS
SELECT 
    model_used,
    model_source,
    COUNT(*) as usage_count,
    AVG(confidence) as avg_confidence,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM predictions) as usage_percentage
FROM predictions
GROUP BY model_used, model_source
ORDER BY usage_count DESC;

COMMIT;

-- ====================================================================
-- 验证迁移结果
-- ====================================================================

-- 显示各物质类型的分布
SELECT '各物质类型分布：' as info;
SELECT 
    biomolecule_type,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM predictions
GROUP BY biomolecule_type
ORDER BY count DESC;

-- 显示模型使用情况
SELECT '模型使用情况：' as info;
SELECT * FROM v_model_usage_stats;

-- 显示最近的预测记录
SELECT '最近10条预测记录：' as info;
SELECT 
    id,
    biomolecule_name,
    biomolecule_type,
    prediction,
    confidence,
    model_source,
    created_at
FROM predictions
ORDER BY created_at DESC
LIMIT 10;

-- ====================================================================
-- 迁移完成
-- ====================================================================

SELECT '====================================================================';
SELECT '数据库迁移完成！';
SELECT '====================================================================';
SELECT '';
SELECT '新增字段：';
SELECT '  - biomolecule_type (生物分子类型)';
SELECT '  - model_used (使用的模型)';
SELECT '  - model_source (模型来源)';
SELECT '';
SELECT '新增索引：';
SELECT '  - idx_predictions_biomolecule_type';
SELECT '  - idx_predictions_model_source';
SELECT '  - idx_predictions_created_at';
SELECT '';
SELECT '新增视图：';
SELECT '  - v_predictions_by_biomolecule';
SELECT '  - v_model_usage_stats';
SELECT '';

