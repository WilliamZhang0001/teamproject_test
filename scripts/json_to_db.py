#!/usr/bin/env python3
"""
将JSON数据导入SQLite数据库（给前端同事用）
一次性运行，生成paramine.db文件
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("paramine.db")
JSONL_PATH = Path("literature_mining/storage/structured_store.jsonl")
RAW_JSON_PATH = Path("literature_mining/storage/raw_papers.json")


def create_tables(conn):
    """创建数据库表"""
    cursor = conn.cursor()
    
    # 文献表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            doi TEXT PRIMARY KEY,
            title TEXT,
            pub_year INTEGER,
            source TEXT,
            authors TEXT
        )
    """)
    
    # 提取记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS extraction_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doi TEXT REFERENCES papers(doi),
            protein_name TEXT,
            biomolecule_type TEXT DEFAULT 'protein',
            outcome_label TEXT,
            outcome_text TEXT,
            polarity TEXT,
            confidence REAL,
            pH REAL,
            temperature_c REAL,
            concentration_mg_ml REAL,
            ion_strength REAL,
            json_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 推荐结果缓存
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            protein_name TEXT,
            recommendation_type TEXT,
            parameters_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(protein_name, recommendation_type)
        )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_protein ON extraction_records(protein_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_confidence ON extraction_records(confidence)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_outcome ON extraction_records(outcome_label)")
    
    conn.commit()
    print("✓ 数据库表创建完成")


def import_papers(conn, raw_json_path):
    """导入文献"""
    print(f"\n导入文献: {raw_json_path}")
    
    with open(raw_json_path, 'r', encoding='utf-8') as f:
        papers = json.load(f)
    
    cursor = conn.cursor()
    count = 0
    
    for paper in papers:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO papers (doi, title, pub_year, source, authors)
                VALUES (?, ?, ?, ?, ?)
            """, (
                paper.get('doi'),
                paper.get('title'),
                paper.get('pub_year'),
                paper.get('source'),
                ', '.join(paper.get('authors', [])) if paper.get('authors') else None
            ))
            count += 1
        except Exception as e:
            print(f"跳过文献: {e}")
    
    conn.commit()
    print(f"✓ 导入 {count} 条文献")


def import_records(conn, jsonl_path):
    """导入提取记录"""
    print(f"\n导入提取记录: {jsonl_path}")
    
    cursor = conn.cursor()
    count = 0
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                record = json.loads(line.strip())
                params = record.get('parameters', {})
                
                cursor.execute("""
                    INSERT INTO extraction_records (
                        doi, protein_name, biomolecule_type,
                        outcome_label, outcome_text, polarity, confidence,
                        pH, temperature_c, concentration_mg_ml, ion_strength,
                        json_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.get('source_doi'),
                    record.get('protein_name'),
                    record.get('biomolecule_type', 'protein'),
                    record.get('outcome_label'),
                    record.get('outcome_text'),
                    record.get('polarity'),
                    record.get('confidence'),
                    params.get('pH'),
                    params.get('temperature_c'),
                    params.get('concentration_mg_ml'),
                    params.get('ion_strength'),
                    json.dumps(record)
                ))
                count += 1
                
                if count % 100 == 0:
                    print(f"  已导入 {count} 条...")
                    
            except Exception as e:
                print(f"跳过第 {line_num} 行: {e}")
    
    conn.commit()
    print(f"✓ 导入 {count} 条提取记录")


def main():
    """主函数"""
    print("=" * 60)
    print("JSON → SQLite 转换工具")
    print("=" * 60)
    
    # 检查文件
    if not JSONL_PATH.exists():
        print(f"错误: 未找到 {JSONL_PATH}")
        return
    
    # 删除旧数据库
    if DB_PATH.exists():
        print(f"删除旧数据库: {DB_PATH}")
        DB_PATH.unlink()
    
    # 创建连接
    conn = sqlite3.connect(DB_PATH)
    
    # 创建表
    create_tables(conn)
    
    # 导入文献
    if RAW_JSON_PATH.exists():
        import_papers(conn, RAW_JSON_PATH)
    else:
        print(f"跳过: 未找到 {RAW_JSON_PATH}")
    
    # 导入记录
    import_records(conn, JSONL_PATH)
    
    # 统计
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM extraction_records")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT protein_name) FROM extraction_records")
    proteins = cursor.fetchone()[0]
    
    print("\n" + "=" * 60)
    print("转换完成!")
    print(f"数据库: {DB_PATH}")
    print(f"总记录数: {total}")
    print(f"蛋白质数: {proteins}")
    print("=" * 60)
    
    conn.close()


if __name__ == "__main__":
    main()

