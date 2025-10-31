-- 用户实验记录表
-- 用于保存用户预测请求和使用历史

-- 用户实验预测表
CREATE TABLE IF NOT EXISTS user_experiment_records (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT,
  
  -- 基本信息
  biomolecule_type VARCHAR(64) NOT NULL,
  biomolecule_name VARCHAR(255) NOT NULL,
  experiment_type VARCHAR(64) NOT NULL DEFAULT 'stability',
  
  -- 用户输入的8个参数
  input_pH FLOAT,
  input_temperature_c FLOAT,
  input_concentration_mg_ml FLOAT,
  input_ionic_strength_mM FLOAT,
  input_additive TEXT,
  input_time_min FLOAT,
  input_shear_rate_s1 FLOAT,
  input_pressure_bar FLOAT,
  
  -- 预测结果
  prediction_type VARCHAR(32) NOT NULL, -- 'classification' 或 'parameter_prediction'
  prediction_result TEXT, -- JSON格式存储预测结果
  confidence FLOAT,
  
  -- 推荐的文献（Top K）
  recommended_literature TEXT, -- JSON格式存储文献信息
  
  -- 元数据
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  
  INDEX idx_user_id (user_id),
  INDEX idx_biomolecule_name (biomolecule_name),
  INDEX idx_experiment_type (experiment_type),
  INDEX idx_created_at (created_at),
  CONSTRAINT fk_user_experiment FOREIGN KEY (user_id)
    REFERENCES app_user(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

