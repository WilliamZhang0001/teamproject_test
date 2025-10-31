-- 文献数据库表结构
-- 用于Docker容器初始化或手动创建数据库

-- 文献表
CREATE TABLE IF NOT EXISTS literature (
  id INT PRIMARY KEY AUTO_INCREMENT,
  doi VARCHAR(255),
  title TEXT,
  authors TEXT,
  pub_year INT,
  source VARCHAR(255),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_doi (doi)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 文献提取记录表
CREATE TABLE IF NOT EXISTS extraction_records (
  id INT PRIMARY KEY AUTO_INCREMENT,
  literature_id INT,
  biomolecule_type VARCHAR(64) NOT NULL DEFAULT 'protein',
  protein_name VARCHAR(255),
  polarity VARCHAR(32),
  property VARCHAR(64) NOT NULL DEFAULT 'stability',
  pH FLOAT,
  temperature_c FLOAT,
  concentration_mg_ml FLOAT,
  ionic_strength_mM FLOAT,
  additive TEXT,
  time_min FLOAT,
  shear_rate_s1 FLOAT,
  pressure_bar FLOAT,
  outcome_score FLOAT,
  outcome_label VARCHAR(255),
  outcome_text TEXT,
  source_section VARCHAR(255),
  confidence FLOAT NOT NULL DEFAULT 0.5,
  raw_context TEXT,
  full_data JSON,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_literature_id (literature_id),
  INDEX idx_protein_name (protein_name),
  INDEX idx_biomolecule_type (biomolecule_type),
  INDEX idx_confidence (confidence),
  CONSTRAINT fk_extraction_literature FOREIGN KEY (literature_id)
    REFERENCES literature(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

