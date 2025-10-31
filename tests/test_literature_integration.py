#!/usr/bin/env python3
"""
测试文献集成功能

测试内容:
1. 文献数据导入
2. 相似文献检索
3. ML预测结果增强
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
from sqlalchemy.orm import Session
from backend.app.core.db import SessionLocal, init_db
from backend.app.services.literature_service import LiteratureService
from backend.app.repos import literature_repo


def test_literature_import():
    """测试文献数据导入"""
    print("\n" + "="*70)
    print("测试1: 文献数据导入")
    print("="*70)
    
    try:
        # 初始化数据库
        init_db()
        
        # 创建服务
        db = SessionLocal()
        service = LiteratureService(db)
        
        # 导入数据
        count = service.load_literature_to_db()
        
        print(f"\n✅ 成功导入 {count} 条记录")
        
        # 查询总数
        all_records = literature_repo.get_all_extraction_records(db, limit=10000)
        print(f"✅ 数据库中共有 {len(all_records)} 条记录")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_similarity_search():
    """测试相似文献搜索"""
    print("\n" + "="*70)
    print("测试2: 相似文献搜索")
    print("="*70)
    
    try:
        db = SessionLocal()
        
        # 测试参数
        target_params = {
            'pH': 7.0,
            'temperature_c': 25.0,
            'concentration_mg_ml': 10.0
        }
        
        # 搜索相似记录
        similar_records = literature_repo.search_similar_records(
            db,
            target_params=target_params,
            biomolecule_name='lysozyme',
            property_type='stability',
            limit=3
        )
        
        print(f"\n找到 {len(similar_records)} 个相似记录")
        
        for i, record in enumerate(similar_records, 1):
            print(f"\n  记录 {i}:")
            print(f"    相似度: {record['similarity_score']:.2%}")
            print(f"    蛋白质: {record.get('protein_name')}")
            print(f"    参数: {record.get('parameters', {})}")
            
            if 'literature' in record:
                lit = record['literature']
                print(f"    文献: {lit.get('title', 'N/A')}")
                print(f"    年份: {lit.get('pub_year', 'N/A')}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"\n❌ 搜索失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ml_enhancement():
    """测试ML预测结果增强"""
    print("\n" + "="*70)
    print("测试3: ML预测结果增强")
    print("="*70)
    
    try:
        db = SessionLocal()
        service = LiteratureService(db)
        
        # 模拟ML预测结果
        ml_result = {
            'scenario': 'classification',
            'prediction': 'Good',
            'confidence': 0.85,
            'recommended_ranges': {
                'pH': {'min': 6.0, 'max': 8.0, 'median': 7.0},
                'temperature_c': {'min': 20.0, 'max': 30.0, 'median': 25.0},
                'concentration_mg_ml': {'min': 5.0, 'max': 15.0, 'median': 10.0}
            }
        }
        
        user_input = {
            'biomolecule_name': 'lysozyme',
            'biomolecule_type': 'protein',
            'experiment_type': 'stability'
        }
        
        # 增强结果
        enhanced_result = service.get_evidence_for_prediction(
            user_input=user_input,
            ml_prediction=ml_result,
            top_k=3
        )
        
        print("\n增强结果:")
        print(json.dumps({
            'prediction': enhanced_result['prediction'],
            'evidence_count': enhanced_result['evidence']['count']
        }, indent=2, ensure_ascii=False))
        
        evidence = enhanced_result['evidence']['top_similar_literature']
        print(f"\n找到 {len(evidence)} 篇相似文献:")
        
        for i, lit in enumerate(evidence[:3], 1):
            print(f"\n  {i}. 相似度: {lit['similarity_score']:.2%}")
            if 'literature' in lit:
                print(f"     标题: {lit['literature'].get('title', 'N/A')}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"\n❌ 增强失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_top_confidence():
    """测试高置信度记录查询"""
    print("\n" + "="*70)
    print("测试4: 高置信度记录查询")
    print("="*70)
    
    try:
        db = SessionLocal()
        
        records = literature_repo.get_top_records_by_confidence(
            db,
            biomolecule_name='lysozyme',
            property_type='stability',
            limit=5
        )
        
        print(f"\n找到 {len(records)} 条高置信度记录")
        
        for i, record in enumerate(records[:3], 1):
            print(f"\n  记录 {i}:")
            print(f"    置信度: {record.get('confidence', 0):.2f}")
            print(f"    蛋白质: {record.get('protein_name')}")
            print(f"    参数: pH={record.get('parameters', {}).get('pH', 'N/A')}")
            
            if 'literature' in record:
                lit = record['literature']
                print(f"    文献: {lit.get('title', 'N/A')}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"\n❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("文献集成功能测试")
    print("="*70)
    
    results = []
    
    # 运行测试
    results.append(("文献数据导入", test_literature_import()))
    results.append(("相似文献搜索", test_similarity_search()))
    results.append(("ML预测增强", test_ml_enhancement()))
    results.append(("高置信度查询", test_top_confidence()))
    
    # 汇总结果
    print("\n" + "="*70)
    print("测试结果汇总")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")


if __name__ == '__main__':
    main()

