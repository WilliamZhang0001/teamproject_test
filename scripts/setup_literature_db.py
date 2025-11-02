#!/usr/bin/env python3
"""
设置文献数据库 - 从JSONL导入数据

使用方法:
    python scripts/setup_literature_db.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from backend.app.core.db import SessionLocal, init_db
from backend.app.services.literature_service import LiteratureService


def main():
    """主函数"""
    print("="*70)
    print("文献数据库设置")
    print("="*70)
    
    # 初始化数据库
    print("\n1. 初始化数据库...")
    try:
        init_db()
        print("   ✅ 数据库表创建成功")
    except Exception as e:
        print(f"   ⚠️  数据库初始化警告: {e}")
    
    # 创建数据库会话
    print("\n2. 创建数据库会话...")
    db = SessionLocal()
    
    try:
        # 创建文献服务
        print("\n3. 创建文献服务...")
        service = LiteratureService(db)
        
        # 导入文献数据
        print("\n4. 从JSONL文件导入文献数据...")
        print("   这可能需要一些时间，请耐心等待...")
        
        count = service.load_literature_to_db()
        
        print(f"\n   ✅ 成功导入 {count} 条文献记录")
        
        # 查询统计信息
        print("\n5. 查询统计信息...")
        from backend.app.repos import literature_repo
        
        all_records = literature_repo.get_all_extraction_records(db, limit=5)
        total_count = len(literature_repo.get_all_extraction_records(db, limit=10000))
        
        print(f"   总记录数: {total_count}")
        
        if all_records:
            print("\n   示例记录:")
            for i, record in enumerate(all_records[:3], 1):
                print(f"\n   记录 {i}:")
                print(f"     蛋白质: {record.protein_name}")
                print(f"     pH: {record.pH}")
                print(f"     温度: {record.temperature_c}°C")
                print(f"     浓度: {record.concentration_mg_ml} mg/mL")
                print(f"     置信度: {record.confidence:.2f}")
        
        print("\n" + "="*70)
        print("✅ 文献数据库设置完成！")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == '__main__':
    main()




