"""
初始化实验记录数据库表
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.core.db import init_db, engine


def main():
    """初始化数据库表"""
    print("="*70)
    print("初始化实验记录数据库表")
    print("="*70)
    
    try:
        # 初始化数据库（创建所有表）
        init_db()
        print("✅ 数据库表创建成功")
        
        # 验证表是否创建
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print("\n已创建的表:")
        for table in tables:
            print(f"  - {table}")
        
        # 检查关键表
        expected_tables = [
            'app_user',
            'auth_login_audit',
            'literature',
            'extraction_records',
            'user_experiment_records'
        ]
        
        print("\n" + "="*70)
        print("表创建状态:")
        for table in expected_tables:
            if table in tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} (缺失)")
        
        print("="*70)
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

