#!/usr/bin/env python3
"""
统一的数据处理管道

功能：
1. 使用增强型抓取器获取文献（两种模式）
   - 模式1: 通用查询（原方案）
   - 模式2: 基于蛋白质（新方案，推荐用于训练）
2. NLP提取实验参数
3. 存储到structured_store.jsonl
4. 训练ML模型

用法:
    # 模式1: 通用查询
    python scripts/run_pipeline.py --query "protein stability pH temperature"
    
    # 模式2: 基于蛋白质
    python scripts/run_pipeline.py --mode protein --proteins lysozyme,albumin,insulin
    
    # 模式3: 所有生物聚合物（蛋白质、肽、多糖）- 推荐
    python scripts/run_pipeline.py --mode biomolecule --train
    
    # 模式3: 启用Semantic Scholar（可选，默认已禁用）
    python scripts/run_pipeline.py --mode biomolecule --enable-s2 --train
"""
import argparse
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from literature_mining.scrapers.enhanced_scraper import UnifiedScraper
from literature_mining.scrapers.protein_specific_scraper import search_proteins_for_training
from literature_mining.extractors.stability_extractor import extract_from_text

from literature_mining.storage.structured_store import StructuredStore
from ml_engine.training.train_stability import train_from_store, save_model


def run_scraping(query: str, output_file: str = "raw_papers.json") -> List[Dict[str, Any]]:
    """步骤1a：通用查询抓取文献"""
    print("\n" + "="*60)
    print("步骤 1/4: 抓取文献（通用查询模式）")
    print("="*60)
    
    scraper = UnifiedScraper(cache_dir=".http_cache")
    results = scraper.search(query)
    
    # 保存原始结果
    output_path = Path(output_file)
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 抓取完成，共 {len(results)} 条文献")
    print(f"✅ 原始数据已保存到: {output_path}")
    
    return results


def run_protein_scraping(proteins: List[str] = None, 
                        max_per_source: int = 300,
                        output_file: str = "raw_papers.json") -> List[Dict[str, Any]]:
    """步骤1b：基于蛋白质抓取文献（推荐用于训练）"""
    print("\n" + "="*60)
    print("步骤 1/4: 抓取文献（蛋白质模式）")
    print("="*60)
    
    if proteins:
        print(f"目标蛋白质: {', '.join(proteins)}")
    else:
        print("使用默认蛋白质列表（~30个蛋白质）")
    
    # 使用protein_specific_scraper
    stats = search_proteins_for_training(
        proteins=proteins,
        max_per_protein_per_source=max_per_source,
        output_file=output_file
    )
    
    # 读取结果
    with open(output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        papers = data['papers']
    
    print(f"\n✅ 抓取完成，共 {len(papers)} 条文献（去重后）")
    print(f"✅ 原始数据已保存到: {output_file}")
    
    return papers


def run_biomolecule_scraping(
    biomolecule_types: List[str] = None,
    max_per_source: int = 300,
    output_file: str = "raw_papers.json",
    enable_s2: bool = False,
    overwrite: bool = True
) -> List[Dict[str, Any]]:
    """
    步骤1c：基于生物聚合物抓取文献（支持蛋白质、肽、多糖）
    
    Args:
        biomolecule_types: 生物聚合物类型列表，如 ['protein', 'peptide', 'polysaccharide']
        max_per_source: 每个生物分子每个数据源的最大结果数
        output_file: 输出文件名
    """
    print("\n" + "="*60)
    print("步骤 1/4: 抓取文献（生物聚合物模式）")
    print("="*60)
    
    if biomolecule_types is None:
        biomolecule_types = ['protein', 'peptide', 'polysaccharide']
    
    print(f"目标类型: {', '.join(biomolecule_types)}")
    print(f"每个生物分子每个数据源最多: {max_per_source} 篇")
    
    from literature_mining.scrapers.protein_specific_scraper import (
        ProteinSpecificScraper, BiomoleculeDatabase
    )
    from literature_mining.scrapers.enhanced_scraper import ScraperConfig
    
    # 设置S2开关（默认关闭）
    ScraperConfig.S2_ENABLED = enable_s2
    
    scraper = ProteinSpecificScraper()
    biomolecule_db = BiomoleculeDatabase()
    
    # 获取所有类型的生物分子
    all_biomolecules = biomolecule_db.get_all_biomolecules(biomolecule_types)
    
    total_count = sum(len(molecules) for molecules in all_biomolecules.values())
    print(f"总计: {total_count} 个生物分子")
    for biomol_type, molecules in all_biomolecules.items():
        print(f"  - {biomol_type}: {len(molecules)} 个")
    
    # 搜索每种类型的生物分子
    results_by_biomolecule = {}
    all_papers_list = []
    
    for biomol_type, molecules in all_biomolecules.items():
        print(f"\n{'='*60}")
        print(f"搜索 {biomol_type.upper()}: {len(molecules)} 个")
        print('='*60)
        
        for i, biomolecule in enumerate(molecules, 1):
            try:
                print(f"\n[{i}/{len(molecules)}] {biomolecule}...")
                papers = scraper.search_by_protein(
                    protein=biomolecule,  # 复用现有函数，支持任何生物分子名称
                    max_per_source=max_per_source,
                    use_flexible_query=True
                )
                
                # 添加生物聚合物类型标签
                for paper in papers:
                    paper['target_protein'] = biomolecule
                    paper['biomolecule_type'] = biomol_type
                
                if papers:
                    results_by_biomolecule[f"{biomol_type}:{biomolecule}"] = papers
                    all_papers_list.extend(papers)
                    print(f"  ✅ 找到 {len(papers)} 篇文献")
                else:
                    print(f"  ⚠️  未找到文献")
                
            except Exception as e:
                print(f"  ❌ 错误: {e}")
                continue
    
    # 去重（基于DOI或标题）
    print(f"\n去重前总数: {len(all_papers_list)}")
    deduplicated = scraper.deduplicate_all_results(results_by_biomolecule)
    print(f"去重后总数: {len(deduplicated)}")
    
    # 按类型统计
    stats_by_type = {}
    for biomol_type in biomolecule_types:
        count = sum(1 for p in deduplicated if p.get('biomolecule_type') == biomol_type)
        stats_by_type[biomol_type] = count
    
    # 保存结果（只在overwrite模式下保存，追加模式在主函数中处理）
    if overwrite:
        output_path = Path(output_file)
        with output_path.open('w', encoding='utf-8') as f:
            json.dump({
                'papers': deduplicated,
                'stats': {
                    'total_biomolecules': total_count,
                    'total_papers_before_dedup': len(all_papers_list),
                    'total_papers_after_dedup': len(deduplicated),
                    'by_type': stats_by_type,
                    'biomolecules_per_type': {
                        biomol_type: len(molecules) 
                        for biomol_type, molecules in all_biomolecules.items()
                    }
                }
            }, f, indent=2, ensure_ascii=False)
        print(f"✅ 原始数据已保存到: {output_file}")
    
    print(f"\n✅ 抓取完成，共 {len(deduplicated)} 条文献（去重后）")
    print(f"✅ 按类型统计:")
    for biomol_type, count in stats_by_type.items():
        print(f"   - {biomol_type}: {count} 篇")
    
    return deduplicated


def run_extraction(papers: List[Dict[str, Any]], verbose: bool = False) -> List[Dict[str, Any]]:
    """
    步骤2：NLP提取参数
    
    Args:
        papers: 文献列表
        verbose: 是否显示详细输出（每条记录的提取详情和调试信息，默认False）
    """
    print("\n" + "="*60)
    print("步骤 2/4: NLP参数提取")
    print("="*60)
    
    # 设置日志级别：verbose=True时显示所有信息，False时只显示ERROR
    import logging
    if verbose:
        # 详细模式：显示所有日志
        logging.getLogger('literature_mining').setLevel(logging.DEBUG)
        logging.getLogger('literature_mining.extractors').setLevel(logging.DEBUG)
        logging.getLogger('literature_mining.nlp').setLevel(logging.DEBUG)
    else:
        # 静默模式：只显示ERROR，隐藏INFO/WARNING/DEBUG
        logging.getLogger('literature_mining').setLevel(logging.ERROR)
        logging.getLogger('literature_mining.extractors').setLevel(logging.ERROR)
        logging.getLogger('literature_mining.nlp').setLevel(logging.ERROR)
    
    all_records = []
    records_count = 0  # 统计提取到的记录数
    skipped_count = 0  # 统计跳过的文献数
    
    import time
    start_time = time.time()
    
    print(f"📄 开始处理 {len(papers)} 篇文献的摘要...")
    
    for i, paper in enumerate(papers, 1):
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        protein_name = paper.get('target_protein', None)  # 读取 target_protein
        text = f"{title}. {abstract}"
        
        if not text.strip():
            continue
        
        paper_start = time.time()
        
        # 从paper中获取biomolecule_type（如果有），否则使用自动检测
        biomolecule_type = paper.get('biomolecule_type', 'protein')
        
        try:
            records = extract_from_text(
                text=text,
                biomolecule_type=biomolecule_type,  # 使用从paper中获取的类型
                protein_name=protein_name,  # 传递生物分子名称
                enable_quality_monitoring=False,  # 关闭质量监控以提升速度
                auto_detect_biomolecule=True  # 自动检测类型（如果paper中没有）
            )
        except Exception as e:
            # 捕获验证错误等异常，继续处理下一篇文献
            if i % 100 == 0:  # 错误信息也只在每100条打印一次
                print(f"\n❌ 提取错误: {e}")
                print(f"   跳过这篇文献: {title[:60]}...")
            continue
        
        paper_time = time.time() - paper_start
        
        if records:
            all_records.extend(records)
            records_count += len(records)
        else:
            skipped_count += 1
        
        # 每1000条打印一次进度
        if i % 1000 == 0 or i == len(papers):
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = avg_time * (len(papers) - i)
            extraction_rate = (records_count / i * 100) if i > 0 else 0
            print(f"\n📊 进度: {i}/{len(papers)} ({i/len(papers)*100:.1f}%) | "
                  f"提取率: {extraction_rate:.1f}% ({records_count}条记录) | "
                  f"已耗时: {elapsed:.1f}秒 | 预计剩余: {remaining/60:.1f}分钟")
    
    total_papers = len(papers)
    extraction_rate = (len(all_records) / total_papers * 100) if total_papers > 0 else 0
    print(f"\n✅ 提取完成")
    print(f"   - 处理文献: {total_papers} 篇")
    print(f"   - 提取记录: {len(all_records)} 条")
    print(f"   - 提取率: {extraction_rate:.1f}% ({len(all_records)}/{total_papers})")
    print(f"   - 跳过文献: {skipped_count} 篇（未提取到有效参数）")
    
    return all_records


def run_storage(records: List[Dict[str, Any]], 
                store_path: str = "literature_mining/storage/structured_store.jsonl",
                overwrite: bool = False) -> None:
    """
    步骤3：存储到数据库
    
    Args:
        records: 要存储的记录列表
        store_path: 存储文件路径
        overwrite: 是否覆盖已有文件（默认追加）
    """
    print("\n" + "="*60)
    print("步骤 3/4: 存储数据")
    print("="*60)
    
    # 如果覆盖模式且文件存在，先删除旧文件
    store_file = Path(store_path)
    if overwrite and store_file.exists():
        old_count = len(store_file.read_text(encoding='utf-8').strip().split('\n'))
        store_file.unlink()
        print(f"🗑️  删除旧文件（原有 {old_count} 条记录）")
    
    store = StructuredStore(store_path)
    
    for record in records:
        store.add(record)
    
    print(f"✅ 数据已存储到: {store_path}")
    print(f"✅ 本次存储记录数: {len(records)}")
    
    # 显示文件总记录数（如果是追加模式）
    if not overwrite and store_file.exists():
        total_lines = len(store_file.read_text(encoding='utf-8').strip().split('\n'))
        if total_lines > len(records):
            print(f"✅ 文件总记录数: {total_lines} 条（追加模式）")


def run_training(store_path: str = "literature_mining/storage/structured_store.jsonl",
                 model_path: str = "models/saved/stability.pkl") -> None:
    """步骤4：训练ML模型"""
    print("\n" + "="*60)
    print("步骤 4/4: 训练ML模型")
    print("="*60)
    
    print(f"从 {store_path} 加载数据...")
    model = train_from_store(store_path, use_synth=True)
    
    print("训练完成")
    
    # 保存模型
    model_file = Path(model_path)
    model_file.parent.mkdir(parents=True, exist_ok=True)
    save_model(model, model_file)
    
    print(f"✅ 模型已保存到: {model_path}")


def main():
    parser = argparse.ArgumentParser(description="运行完整的数据处理管道")
    
    # 模式选择
    parser.add_argument(
        "--mode",
        type=str,
        choices=["query", "protein", "biomolecule"],
        default="query",
        help="抓取模式：query=通用查询，protein=基于蛋白质，biomolecule=所有生物聚合物（推荐）"
    )
    
    # 通用查询模式参数
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="搜索查询字符串（mode=query时必需）"
    )
    
    # 蛋白质模式参数
    parser.add_argument(
        "--proteins",
        type=str,
        default=None,
        help="蛋白质列表，逗号分隔（mode=protein时可选，默认使用内置列表）"
    )
    
    # 生物聚合物模式参数
    parser.add_argument(
        "--biomolecule-types",
        type=str,
        default="protein,peptide,polysaccharide",
        help="生物聚合物类型，逗号分隔（mode=biomolecule时有效）：protein,peptide,polysaccharide"
    )
    
    parser.add_argument(
        "--max-per-source",
        type=int,
        default=300,
        help="每个生物分子每个数据源的最大结果数（mode=protein或biomolecule时有效，默认100）"
    )
    parser.add_argument(
        "--enable-s2",
        action="store_true",
        help="启用Semantic Scholar（默认禁用，避免限流）"
    )
    
    # 通用参数
    parser.add_argument(
        "--store",
        type=str,
        default="literature_mining/storage/structured_store.jsonl",
        help="数据存储路径"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="models/saved/stability.pkl",
        help="模型保存路径"
    )
    parser.add_argument(
        "--train",
        action="store_true",
        help="是否训练模型"
    )
    parser.add_argument(
        "--skip-scraping",
        action="store_true",
        help="跳过抓取步骤（使用已有的raw_papers.json）"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖已存在的文件（raw_papers.json和structured_store.jsonl，默认追加）"
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="追加到已有数据（默认行为，与--overwrite互斥）"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出模式（显示每条记录的提取详情和调试信息，默认关闭）"
    )
    
    args = parser.parse_args()
    
    # 验证参数
    if args.mode == "query" and not args.query and not args.skip_scraping:
        parser.error("--query is required when --mode=query")
    
    # 检查overwrite和append的互斥性
    if args.overwrite and args.append:
        parser.error("--overwrite and --append cannot be used together")
    
    # S2开关：默认关闭，只有显式启用才会打开
    from literature_mining.scrapers.enhanced_scraper import ScraperConfig
    if args.enable_s2:
        ScraperConfig.S2_ENABLED = True
    else:
        ScraperConfig.S2_ENABLED = False  # 确保默认关闭
    
    print("\n🚀 DoE-Assist 数据处理管道")
    print(f"模式: {args.mode}")
    if args.mode == "query":
        print(f"查询: {args.query}")
    elif args.mode == "protein":
        if args.proteins:
            print(f"蛋白质: {args.proteins}")
        else:
            print(f"蛋白质: 使用默认列表（~30个）")
        print(f"每个数据源最大结果数: {args.max_per_source}")
    elif args.mode == "biomolecule":
        print(f"生物聚合物类型: {args.biomolecule_types}")
        print(f"每个数据源最大结果数: {args.max_per_source}")
    print(f"Semantic Scholar: {'启用' if ScraperConfig.S2_ENABLED else '禁用（避免限流）'}")
    print(f"存储: {args.store}")
    if args.train:
        print(f"模型: {args.model}")
    
    try:
        # 步骤1：抓取文献
        if args.skip_scraping:
            print("\n⏭️  跳过抓取步骤")
            raw_file = Path("raw_papers.json")
            if not raw_file.exists():
                print(f"❌ 找不到 {raw_file}，请先运行抓取步骤")
                sys.exit(1)
            with raw_file.open('r', encoding='utf-8') as f:
                data = json.load(f)
                # 兼容两种格式
                if isinstance(data, dict) and 'papers' in data:
                    papers = data['papers']
                else:
                    papers = data
        else:
            # 确定是否覆盖已有文件
            overwrite_mode = args.overwrite or (not args.append and not Path("raw_papers.json").exists())
            
            if args.mode == "biomolecule":
                # 生物聚合物模式（支持蛋白质、肽、多糖）
                biomolecule_types = [t.strip() for t in args.biomolecule_types.split(',')]
                
                # 如果追加模式且文件存在，先读取已有数据
                existing_papers = []
                if not overwrite_mode and Path("raw_papers.json").exists():
                    print("\n📂 检测到已有文献数据，将追加新数据")
                    try:
                        with Path("raw_papers.json").open('r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                            if isinstance(existing_data, dict) and 'papers' in existing_data:
                                existing_papers = existing_data['papers']
                            elif isinstance(existing_data, list):
                                existing_papers = existing_data
                    except Exception as e:
                        print(f"⚠️  读取已有数据时出错: {e}，将创建新文件")
                
                papers = run_biomolecule_scraping(
                    biomolecule_types=biomolecule_types,
                    max_per_source=args.max_per_source,
                    output_file="raw_papers.json",
                    enable_s2=getattr(args, 'enable_s2', False),
                    overwrite=overwrite_mode
                )
                
                # 如果是追加模式，合并已有数据并保存
                if not overwrite_mode and existing_papers:
                    # 基于DOI去重
                    existing_dois = {p.get('doi') for p in existing_papers if p.get('doi')}
                    new_papers = [p for p in papers if p.get('doi') not in existing_dois]
                    papers = existing_papers + new_papers
                    print(f"✅ 合并完成：已有 {len(existing_papers)} 篇，新增 {len(new_papers)} 篇，总计 {len(papers)} 篇")
                    
                    # 保存合并后的数据
                    output_path = Path("raw_papers.json")
                    with output_path.open('w', encoding='utf-8') as f:
                        json.dump({
                            'papers': papers,
                            'stats': {
                                'total_papers': len(papers),
                                'existing_count': len(existing_papers),
                                'new_count': len(new_papers)
                            }
                        }, f, indent=2, ensure_ascii=False)
                    print(f"✅ 合并后的数据已保存到: raw_papers.json")
            elif args.mode == "protein":
                # 蛋白质模式
                protein_list = args.proteins.split(',') if args.proteins else None
                papers = run_protein_scraping(
                    proteins=protein_list,
                    max_per_source=args.max_per_source
                )
            else:
                # 查询模式
                papers = run_scraping(args.query)
        
        if not papers:
            print("❌ 没有找到文献，退出")
            sys.exit(1)
        
        # 步骤2：NLP提取
        records = run_extraction(papers, verbose=getattr(args, 'verbose', False))
        
        if not records:
            print("❌ 没有提取到有效记录，退出")
            sys.exit(1)
        
        # 步骤3：存储
        # 如果使用--overwrite，也覆盖structured_store.jsonl
        store_overwrite = getattr(args, 'overwrite', False)
        run_storage(records, args.store, overwrite=store_overwrite)
        
        # 步骤4：训练模型（可选）
        if args.train:
            run_training(args.store, args.model)
        
        print("\n" + "="*60)
        print("🎉 管道运行完成！")
        print("="*60)
        print(f"✅ 文献数: {len(papers)}")
        print(f"✅ 提取记录数: {len(records)}")
        print(f"✅ 数据存储: {args.store}")
        if args.train:
            print(f"✅ 模型: {args.model}")
        print()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

