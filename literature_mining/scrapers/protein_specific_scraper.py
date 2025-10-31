#!/usr/bin/env python3
"""
基于蛋白质的文献抓取器

策略：
1. 主键：特定蛋白质/酶名称
2. 条件：满足任意2个参数相关词即可
3. 数据量：更大，质量仍高

基于用户的testAPI2.py逻辑改进
"""
import os
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from tqdm import tqdm

from .enhanced_scraper import (
    CachedSession, ScraperConfig,
    EuropePMCScraper, SemanticScholarScraper, OpenAlexScraper, UnifiedScraper
)


# =========================
# 蛋白质和酶列表
# =========================
class BiomoleculeDatabase:
    """生物分子数据库 - 扩展版，支持蛋白质、肽、多糖"""
    
    # 常见蛋白质
    PROTEINS = [
        # 模型蛋白质
        'lysozyme', 'albumin', 'BSA', 'bovine serum albumin',
        'hemoglobin', 'myoglobin', 'insulin', 'cytochrome c',
        
        # 结构蛋白
        'collagen', 'elastin', 'fibrinogen', 'keratin',
        
        # 酶类
        'trypsin', 'pepsin', 'chymotrypsin', 'amylase',
        'lipase', 'protease', 'catalase', 'peroxidase',
        'lactase', 'cellulase', 'xylanase',
        
        # 抗体和免疫相关
        'immunoglobulin', 'IgG', 'antibody', 'antigen',
        
        # 其他重要蛋白
        'casein', 'gelatin', 'ovalbumin', 'lactoferrin',
        'ferritin', 'transferrin', 'thrombin'
    ]
    
    # 常见肽
    PEPTIDES = [
        # 抗菌肽
        'antimicrobial peptide', 'AMP', 'defensin', 'cathelicidin',
        'LL-37', 'melittin', 'magainin', 'cecropin',
        'tachyplesin', 'polyphemusin', 'histatin',
        
        # 治疗性肽
        'synthetic peptide', 'peptide drug', 'therapeutic peptide',
        'signal peptide', 'membrane peptide', 'cell penetrating peptide',
        
        # 疾病相关肽
        'amyloid peptide', 'beta-amyloid', 'Abeta',
        'insulin-like peptide', 'glucagon-like peptide', 'GLP-1',
        'vasopressin', 'oxytocin', 'somatostatin',
        
        # 功能肽
        'enzymatic peptide', 'catalytic peptide', 'hydrolytic peptide'
    ]
    
    # 常见多糖
    POLYSACCHARIDES = [
        # 几丁质类
        'chitosan', 'chitin',
        
        # 海藻多糖
        'alginate', 'carrageenan', 'agar', 'agarose', 'gellan gum',
        
        # 植物多糖
        'cellulose', 'hemicellulose', 'pectin', 'xylan',
        'starch', 'amylose', 'amylopectin', 'dextran',
        
        # 动物多糖
        'heparin', 'hyaluronic acid', 'chondroitin sulfate',
        'heparan sulfate', 'dermatan sulfate', 'keratan sulfate',
        'glycosaminoglycan', 'GAG',
        
        # 微生物多糖
        'xanthan gum', 'pullulan', 'curdlan', 'gellan gum'
    ]
    
    # 实验参数关键词
    PARAMETER_KEYWORDS = {
        'ph': ['pH', 'acidic', 'basic', 'alkaline', 'neutral pH'],
        'temperature': ['temperature', 'thermal', 'heat', 'heated', 'cooled', 
                       'room temperature', 'RT', 'incubated', 'cold'],
        'concentration': ['concentration', 'diluted', 'concentrated', 
                         'mg/mL', 'mM', 'µM', 'molarity'],
        'solubility': ['solubility', 'soluble', 'insoluble', 'dissolution', 
                      'precipitate', 'precipitation'],
        'stability': ['stability', 'stable', 'unstable', 'stabilization',
                     'denaturation', 'denature', 'aggregation', 'degradation'],
        'ionic strength': ['ionic strength', 'salt', 'NaCl', 'KCl', 'buffer'],
        'time': ['time', 'incubated', 'hours', 'minutes', 'days'],
        'shear': ['shear', 'shear rate', 'stirring', 'agitation'],
        'pressure': ['pressure', 'high pressure', 'HPP']
    }
    
    @classmethod
    def get_all_proteins(cls) -> List[str]:
        """获取所有蛋白质名称"""
        return cls.PROTEINS.copy()
    
    @classmethod
    def get_all_peptides(cls) -> List[str]:
        """获取所有肽名称"""
        return cls.PEPTIDES.copy()
    
    @classmethod
    def get_all_polysaccharides(cls) -> List[str]:
        """获取所有多糖名称"""
        return cls.POLYSACCHARIDES.copy()
    
    @classmethod
    def get_all_biomolecules(cls, biomolecule_types: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """
        获取指定类型的生物分子
        
        Args:
            biomolecule_types: 类型列表，如 ['protein', 'peptide', 'polysaccharide']
                             None表示全部类型
        
        Returns:
            {类型: [分子列表]} 字典
        """
        if biomolecule_types is None:
            biomolecule_types = ['protein', 'peptide', 'polysaccharide']
        
        result = {}
        if 'protein' in biomolecule_types:
            result['protein'] = cls.get_all_proteins()
        if 'peptide' in biomolecule_types:
            result['peptide'] = cls.get_all_peptides()
        if 'polysaccharide' in biomolecule_types:
            result['polysaccharide'] = cls.get_all_polysaccharides()
        
        return result
    
    @classmethod
    def get_parameter_keywords(cls) -> Dict[str, List[str]]:
        """获取所有参数关键词"""
        return cls.PARAMETER_KEYWORDS.copy()


# =========================
# 智能查询构建器
# =========================
class SmartQueryBuilder:
    """智能查询构建器 - 基于蛋白质+参数的组合"""
    
    def __init__(self):
        self.biomolecule_db = BiomoleculeDatabase()
    
    def build_protein_query(self, 
                           protein: str,
                           require_params: int = 2,
                           include_param_types: Optional[List[str]] = None) -> str:
        """
        构建基于蛋白质的查询
        
        Args:
            protein: 蛋白质名称
            require_params: 至少需要几个参数关键词（默认2个）
            include_param_types: 包含哪些参数类型（None=全部）
        
        Returns:
            查询字符串
        """
        param_keywords = self.biomolecule_db.get_parameter_keywords()
        
        # 选择参数类型
        if include_param_types:
            param_keywords = {k: v for k, v in param_keywords.items() 
                             if k in include_param_types}
        
        return f"{protein} AND (solubility OR pH OR temperature OR concentration OR stability)"
    
    def build_epmc_query(self, 
                         protein: str,
                         flexible: bool = True) -> str:
        """
        构建EuropePMC查询
        
        Args:
            protein: 蛋白质名称
            flexible: 是否使用灵活模式（满足任意参数即可）
        
        Returns:
            EuropePMC查询字符串
        """
        if flexible:
            # 灵活模式：只要有蛋白质 + 任意一个参数词
            param_keywords = self.biomolecule_db.get_parameter_keywords()
            
            # 构建OR条件（任意一个参数词即可）
            param_conditions = []
            for param_type, keywords in param_keywords.items():
                # 选项1：只取前3个关键词（默认，避免查询过长）
                for keyword in keywords[:3]:
                    param_conditions.append(f'(TITLE:"{keyword}" OR ABSTRACT:"{keyword}")')
                
                # 选项2：使用所有关键词（取消上面的注释，改用下面这行）
                # for keyword in keywords:
                #     param_conditions.append(f'(TITLE:"{keyword}" OR ABSTRACT:"{keyword}")')
            
            param_or_clause = " OR ".join(param_conditions)
            
            return f'("{protein}") AND ({param_or_clause})'
        else:
            # 严格模式：必须同时有pH和temperature
            return f"""
                ("{protein}")
                AND (TITLE:pH OR ABSTRACT:pH)
                AND (TITLE:temperature OR ABSTRACT:temperature)
            """


# =========================
# 基于蛋白质的抓取器
# =========================
class ProteinSpecificScraper:
    """基于蛋白质的文献抓取器"""
    
    def __init__(self, cache_dir: str = ".http_cache", use_s2: bool = None):
        """
        初始化抓取器
        
        Args:
            cache_dir: 缓存目录
            use_s2: 是否使用Semantic Scholar（None=使用配置值）
        """
        self.session = CachedSession(cache_dir=cache_dir)
        self.epmc = EuropePMCScraper(self.session)
        self.s2 = SemanticScholarScraper(self.session)
        self.openalex = OpenAlexScraper(self.session)
        # 使用UnifiedScraper来访问ArXiv功能
        self.unified_scraper = UnifiedScraper(cache_dir=cache_dir)
        self.query_builder = SmartQueryBuilder()
        self.biomolecule_db = BiomoleculeDatabase()
        
        # 允许运行时禁用S2
        if use_s2 is not None:
            ScraperConfig.S2_ENABLED = use_s2
    
    def search_by_protein(self,
                         protein: str,
                         max_per_source: int = 50,
                         use_flexible_query: bool = True) -> List[Dict[str, Any]]:
        """
        按蛋白质搜索文献
        
        Args:
            protein: 蛋白质名称
            max_per_source: 每个数据源的最大结果数
            use_flexible_query: 是否使用灵活查询（推荐）
        
        Returns:
            文献列表
        """
        all_results = []
        
        # EuropePMC（使用灵活查询，支持分页获取更多结果）
        epmc_query = self.query_builder.build_epmc_query(protein, flexible=use_flexible_query)
        print(f"  [EPMC] Query: {epmc_query[:100]}...")
        
        try:
            # EPMC单次最多1000条，支持用户设置的max_per_source
            epmc_results = self.epmc.search(
                epmc_query,
                page_size=min(max_per_source, 1000),  # 提高上限到1000
                use_cursor=False
            )
            all_results.extend(epmc_results)
            print(f"  [EPMC] Found: {len(epmc_results)} papers")
        except Exception as e:
            print(f"  [EPMC] Error: {e}")
        
        # Semantic Scholar（使用简单查询）- 可选的API
        # 注意：S2限流严格，如果禁用了会跳过
        if ScraperConfig.S2_ENABLED:
            s2_query = self.query_builder.build_protein_query(protein)
            print(f"  [S2] Query: {s2_query}")
            
            try:
                # 添加请求间延迟，帮助避免限流
                time.sleep(ScraperConfig.S2_MIN_DELAY)
                # S2 API限制：每次最多100条，使用用户设置的max_per_source
                s2_results = self.s2.search(s2_query, limit=min(max_per_source, 100))
                all_results.extend(s2_results)
                print(f"  [S2] Found: {len(s2_results)} papers")
            except Exception as e:
                print(f"  [S2] Error: {e}")
        else:
            print(f"  [S2] 已禁用（避免限流），跳过")
            s2_query = None  # 避免下面引用未定义变量
        
        # OpenAlex（使用简单查询，支持多页获取更多结果）
        openalex_query = self.query_builder.build_protein_query(protein)
        print(f"  [OpenAlex] Query: {openalex_query}")
        
        try:
            # OpenAlex单页最多200条，通过增加页数获取更多
            per_page = min(max_per_source, 200)  # 提高单页上限到200
            max_pages = max(1, (max_per_source + per_page - 1) // per_page)  # 计算需要的页数
            oa_results = self.openalex.search(
                openalex_query,
                per_page=per_page,
                max_pages=min(max_pages, 10)  # 最多10页，避免过多请求
            )
            all_results.extend(oa_results)
            print(f"  [OpenAlex] Found: {len(oa_results)} papers")
        except Exception as e:
            print(f"  [OpenAlex] Error: {e}")
        
        # ArXiv（使用简单查询）
        arxiv_query = f"{protein} AND (stability OR pH OR temperature OR concentration)"
        print(f"  [ArXiv] Query: {arxiv_query}")
        
        try:
            # 直接调用UnifiedScraper的私有方法（更高效，避免重复调用其他API）
            # 因为我们已经在上面分别调用了EPMC、S2、OpenAlex
            arxiv_results = self.unified_scraper._search_arxiv(arxiv_query)
            # 限制结果数量，使用用户设置的max_per_source（最多2000）
            arxiv_results = arxiv_results[:min(max_per_source, 2000)]
            all_results.extend(arxiv_results)
            print(f"  [ArXiv] Found: {len(arxiv_results)} papers")
        except Exception as e:
            print(f"  [ArXiv] Error: {e}")
        
        # 添加蛋白质标记
        for result in all_results:
            result['target_protein'] = protein
        
        return all_results
    
    def search_multiple_proteins(self,
                                proteins: Optional[List[str]] = None,
                                max_per_source: int = 50,
                                use_flexible_query: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """
        搜索多个蛋白质
        
        Args:
            proteins: 蛋白质列表（None=使用默认列表）
            max_per_source: 每个数据源的最大结果数
            use_flexible_query: 是否使用灵活查询
        
        Returns:
            {protein: [papers]} 字典
        """
        if proteins is None:
            proteins = self.biomolecule_db.get_all_proteins()
        
        results_by_protein = {}
        
        print(f"\n🔬 搜索 {len(proteins)} 个蛋白质的文献...\n")
        
        for protein in tqdm(proteins, desc="Processing proteins"):
            print(f"\n{'='*60}")
            print(f"搜索: {protein}")
            print('='*60)
            
            try:
                papers = self.search_by_protein(
                    protein,
                    max_per_source=max_per_source,
                    use_flexible_query=use_flexible_query
                )
                
                if papers:
                    results_by_protein[protein] = papers
                    print(f"✅ {protein}: {len(papers)} papers")
                else:
                    print(f"⚠️  {protein}: No papers found")
                
            except Exception as e:
                print(f"❌ {protein}: Error - {e}")
                continue
        
        return results_by_protein
    
    def deduplicate_all_results(self,
                                results_by_protein: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        去重所有结果（跨蛋白质）
        
        Args:
            results_by_protein: 按蛋白质分组的结果
        
        Returns:
            去重后的文献列表
        """
        all_papers = []
        for protein, papers in results_by_protein.items():
            all_papers.extend(papers)
        
        # 去重
        seen_keys = set()
        deduplicated = []
        
        for paper in all_papers:
            doi = paper.get('doi')
            title = paper.get('title')
            
            # 生成去重键
            if doi and isinstance(doi, str) and doi.strip():
                doi_clean = doi.replace('https://doi.org/', '').strip().lower()
                key = f"doi:{doi_clean}"
            elif title:
                key = f"title:{title.lower()}"
            else:
                deduplicated.append(paper)
                continue
            
            if key not in seen_keys:
                seen_keys.add(key)
                deduplicated.append(paper)
        
        return deduplicated


# =========================
# 便捷函数
# =========================
def search_proteins_for_training(
    proteins: Optional[List[str]] = None,
    max_per_protein_per_source: int = 30,
    output_file: str = "protein_specific_papers.json"
) -> Dict[str, Any]:
    """
    为训练模型搜索蛋白质文献的便捷函数
    
    Args:
        proteins: 蛋白质列表（None=使用默认列表）
        max_per_protein_per_source: 每个蛋白质每个数据源的最大结果数
        output_file: 输出文件名
    
    Returns:
        统计信息字典
    """
    scraper = ProteinSpecificScraper()
    
    # 搜索
    results_by_protein = scraper.search_multiple_proteins(
        proteins=proteins,
        max_per_source=max_per_protein_per_source,
        use_flexible_query=True
    )
    
    # 去重
    all_papers = scraper.deduplicate_all_results(results_by_protein)
    
    # 统计
    stats = {
        'total_proteins': len(results_by_protein),
        'total_papers_before_dedup': sum(len(papers) for papers in results_by_protein.values()),
        'total_papers_after_dedup': len(all_papers),
        'papers_per_protein': {
            protein: len(papers) 
            for protein, papers in results_by_protein.items()
        },
        'top_proteins': sorted(
            [(protein, len(papers)) for protein, papers in results_by_protein.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
    }
    
    # 保存结果
    output_path = Path(output_file)
    with output_path.open('w', encoding='utf-8') as f:
        json.dump({
            'papers': all_papers,
            'stats': stats
        }, f, indent=2, ensure_ascii=False)
    
    # 打印统计
    print("\n" + "="*60)
    print("📊 搜索统计")
    print("="*60)
    print(f"✅ 搜索蛋白质数: {stats['total_proteins']}")
    print(f"✅ 去重前文献数: {stats['total_papers_before_dedup']}")
    print(f"✅ 去重后文献数: {stats['total_papers_after_dedup']}")
    print(f"✅ 平均每个蛋白质: {stats['total_papers_after_dedup'] / max(1, stats['total_proteins']):.1f} 篇")
    
    print(f"\n🏆 Top 10 蛋白质（按文献数）:")
    for i, (protein, count) in enumerate(stats['top_proteins'], 1):
        print(f"  {i:2d}. {protein:20s} - {count:3d} 篇")
    
    print(f"\n💾 结果已保存到: {output_path}")
    print("="*60)
    
    return stats


# =========================
# 测试代码
# =========================
if __name__ == "__main__":
    # 测试：搜索几个常见蛋白质
    test_proteins = [
        'lysozyme',
        'albumin',
        'insulin',
        'casein',
        'hemoglobin'
    ]
    
    stats = search_proteins_for_training(
        proteins=test_proteins,
        max_per_protein_per_source=30,
        output_file="test_protein_papers.json"
    )
    
    print("\n✅ 测试完成！")

