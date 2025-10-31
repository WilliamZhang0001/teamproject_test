#!/usr/bin/env python3
"""
增强型文献抓取器 - 集成多数据源和智能缓存

整合了以下优化：
1. 多数据源支持（EuropePMC, Semantic Scholar, OpenAlex）
2. 智能HTTP缓存机制
3. 退避重试策略
4. 基于DOI的智能去重
5. 命中率统计

作者: 基于testAPI.py优化方案
"""
import os
import re
import json
import time
import hashlib
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path
from .sources_arxiv import search_arxiv
import xml.etree.ElementTree as ET


# =========================
# 配置区
# =========================
class ScraperConfig:
    """抓取器配置"""
    # EuropePMC
    EPMC_BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    EPMC_PAGE_SIZE = 30
    EPMC_USE_CURSOR = False
    EPMC_MAX_PAGES = 1
    
    # Semantic Scholar
    # 注意：S2限流很严格，如果频繁遇到限流，建议禁用或使用API密钥
    S2_ENABLED = False  # 默认禁用，避免限流问题
    S2_BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    S2_LIMIT = 10
    S2_MAX_RETRIES = 3  # 减少重试次数
    S2_TIMEOUT = 30
    S2_BACKOFF_BASE = 1.6
    S2_USER_AGENT = "DoE-Assist/1.0 (mailto:research@example.com)"
    S2_MIN_DELAY = 2.0  # 每次请求之间的最小延迟（秒），帮助避免限流
    
    # OpenAlex
    OPENALEX_ENABLED = True
    OPENALEX_BASE_URL = "https://api.openalex.org/works"
    OPENALEX_PER_PAGE = 15
    OPENALEX_MAX_PAGES = 1
    
    # ArXiv
    ARXIV_ENABLED = True
    ARXIV_MAX_RESULTS = 2000  # 提高到2000以支持大规模数据采集
    
    # 缓存
    CACHE_DIR = ".http_cache"
    USE_CACHE = True
    
    # 超时
    DEFAULT_TIMEOUT = 30


# =========================
# HTTP 工具：Session + 缓存
# =========================
class CachedSession:
    """带缓存的HTTP会话"""
    
    def __init__(self, cache_dir: str = ScraperConfig.CACHE_DIR, user_agent: str = ScraperConfig.S2_USER_AGENT):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _cache_key(self, url: str, params: Dict[str, Any]) -> str:
        """生成缓存键"""
        key_str = url + "?" + "&".join(f"{k}={params[k]}" for k in sorted(params))
        return hashlib.sha1(key_str.encode()).hexdigest()
    
    def get_json(self, url: str, params: Dict[str, Any], 
                 timeout: int = ScraperConfig.DEFAULT_TIMEOUT, 
                 use_cache: bool = ScraperConfig.USE_CACHE,
                 headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """获取JSON数据（带缓存）"""
        # 检查缓存
        if use_cache:
            cache_key = self._cache_key(url, params)
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        
        # 发送请求
        req_headers = headers or {}
        r = self.session.get(url, params=params, headers=req_headers, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        
        # 保存缓存
        if use_cache:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        return data


# =========================
# EuropePMC 抓取器
# =========================
class EuropePMCScraper:
    """EuropePMC文献抓取器"""
    
    def __init__(self, session: CachedSession):
        self.session = session
    
    def build_query(self, user_query: str, open_access_only: bool = False) -> str:
        """构建查询字符串"""
        parts = [
            f'({user_query})',
            "(TITLE:pH OR ABSTRACT:pH)",
            "(TITLE:temperature OR ABSTRACT:temperature OR ABSTRACT:\"room temperature\")",
        ]
        if open_access_only:
            parts.append("OPEN_ACCESS:y")
        return " AND ".join(parts)
    
    def search(self, query: str, 
               page_size: int = ScraperConfig.EPMC_PAGE_SIZE,
               use_cursor: bool = ScraperConfig.EPMC_USE_CURSOR,
               max_pages: int = ScraperConfig.EPMC_MAX_PAGES) -> List[Dict[str, Any]]:
        """搜索文献"""
        rows = []
        
        if use_cursor:
            cursor = "*"
            pages = 0
            while True:
                params = {
                    "query": query,
                    "format": "json",
                    "resultType": "core",
                    "pageSize": page_size,
                    "cursorMark": cursor
                }
                data = self.session.get_json(ScraperConfig.EPMC_BASE_URL, params)
                result = data.get("resultList", {}).get("result", [])
                
                if not result:
                    break
                
                for item in result:
                    rows.append(self._parse_result(item))
                
                cursor_next = data.get("nextCursorMark")
                pages += 1
                
                if not cursor_next or cursor_next == cursor or pages >= max_pages:
                    break
                cursor = cursor_next
        else:
            params = {
                "query": query,
                "format": "json",
                "resultType": "core",
                "pageSize": page_size
            }
            data = self.session.get_json(ScraperConfig.EPMC_BASE_URL, params)
            result = data.get("resultList", {}).get("result", [])
            
            for item in result:
                rows.append(self._parse_result(item))
        
        return rows
    
    def _parse_result(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """解析搜索结果"""
        return {
            "source": "EuropePMC",
            "title": item.get("title"),
            "doi": item.get("doi"),
            "pub_year": item.get("pubYear"),
            "abstract": item.get("abstractText") or item.get("abstract"),
            "authors": item.get("authorString"),
            "journal": item.get("journalTitle"),
        }


# =========================
# Semantic Scholar 抓取器
# =========================
class SemanticScholarScraper:
    """Semantic Scholar文献抓取器"""
    
    def __init__(self, session: CachedSession):
        self.session = session
    
    def search(self, query: str, limit: int = ScraperConfig.S2_LIMIT) -> List[Dict[str, Any]]:
        """搜索文献（带退避重试）"""
        if not ScraperConfig.S2_ENABLED:
            return []
        
        fields = "title,abstract,year,externalIds,authors"
        api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        
        headers = {}
        if api_key:
            headers["x-api-key"] = api_key
        
        params = {"query": query, "limit": int(limit), "fields": fields}
        
        attempt = 0
        while attempt <= ScraperConfig.S2_MAX_RETRIES:
            try:
                r = self.session.session.get(
                    ScraperConfig.S2_BASE_URL,
                    headers={**self.session.session.headers, **headers},
                    params=params,
                    timeout=ScraperConfig.S2_TIMEOUT
                )
                
                if r.status_code == 429:
                    # 处理限流 - 改进版：遇到限流直接跳过，避免长时间阻塞
                    # Semantic Scholar限流很严格，与其等待不如跳过
                    if attempt == 0:
                        # 第一次限流，等待短时间再试一次
                        print(f"[S2] 限流，等待 3s 后重试...")
                        time.sleep(3.0)
                        attempt += 1
                        continue
                    else:
                        # 第二次及以后，直接跳过（避免阻塞整个流程）
                        print(f"[S2] 限流严重，跳过S2（已有EPMC、OpenAlex、ArXiv）")
                        return []
                
                r.raise_for_status()
                data = r.json()
                
                rows = []
                for item in data.get("data", []):
                    rows.append(self._parse_result(item))
                
                return rows
                
            except requests.HTTPError as e:
                status = getattr(e.response, "status_code", None)
                if status and 500 <= status < 600:
                    time.sleep(ScraperConfig.S2_BACKOFF_BASE ** attempt)
                    attempt += 1
                    continue
                print(f"[S2] HTTP错误 {status}，跳过S2")
                return []
            except requests.RequestException as e:
                time.sleep(ScraperConfig.S2_BACKOFF_BASE ** attempt)
                attempt += 1
                if attempt > ScraperConfig.S2_MAX_RETRIES:
                    print(f"[S2] 请求异常: {e}，跳过S2")
                    return []
        
        print("[S2] 重试次数用尽，跳过S2")
        return []
    
    def _parse_result(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """解析搜索结果"""
        ext_ids = item.get("externalIds") or {}
        authors = item.get("authors", [])
        author_names = ", ".join([a.get("name", "") for a in authors[:3]])
        
        return {
            "source": "SemanticScholar",
            "title": item.get("title"),
            "doi": ext_ids.get("DOI"),
            "pub_year": item.get("year"),
            "abstract": item.get("abstract"),
            "authors": author_names,
        }


# =========================
# OpenAlex 抓取器
# =========================
class OpenAlexScraper:
    """OpenAlex文献抓取器"""
    
    def __init__(self, session: CachedSession):
        self.session = session
    
    def search(self, query: str,
               per_page: int = ScraperConfig.OPENALEX_PER_PAGE,
               max_pages: int = ScraperConfig.OPENALEX_MAX_PAGES) -> List[Dict[str, Any]]:
        """搜索文献"""
        if not ScraperConfig.OPENALEX_ENABLED:
            return []
        
        rows = []
        for page in range(1, max_pages + 1):
            params = {
                "search": query,
                "per_page": per_page,
                "page": page,
                "mailto": "research@example.com"
            }
            
            data = self.session.get_json(ScraperConfig.OPENALEX_BASE_URL, params)
            
            for item in data.get("results", []):
                rows.append(self._parse_result(item))
        
        return rows
    
    def _parse_result(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """解析搜索结果"""
        # OpenAlex的摘要存储为倒排索引
        abstract_inv_idx = item.get("abstract_inverted_index")
        abstract = self._reconstruct_abstract(abstract_inv_idx)
        
        # 提取作者
        authorships = item.get("authorships", [])
        authors = ", ".join([
            a.get("author", {}).get("display_name", "") 
            for a in authorships[:3]
        ])
        
        doi = item.get("doi", "")
        if doi:
            doi = doi.replace("https://doi.org/", "")
        
        return {
            "source": "OpenAlex",
            "title": item.get("title"),
            "doi": doi,
            "pub_year": item.get("publication_year"),
            "abstract": abstract,
            "authors": authors,
        }
    
    def _reconstruct_abstract(self, inv_idx: Optional[Dict[str, List[int]]]) -> Optional[str]:
        """从倒排索引重构摘要"""
        if not isinstance(inv_idx, dict):
            return None
        
        positions = []
        for token, pos_list in inv_idx.items():
            for pos in pos_list:
                positions.append((pos, token))
        
        if not positions:
            return None
        
        positions.sort()
        return " ".join(token for _, token in positions)


# =========================
# 统一抓取器
# =========================
class UnifiedScraper:
    """统一的多源文献抓取器 - 整合 EuropePMC, Semantic Scholar, OpenAlex, ArXiv"""
    
    def __init__(self, cache_dir: str = ScraperConfig.CACHE_DIR):
        self.session = CachedSession(cache_dir=cache_dir)
        self.epmc = EuropePMCScraper(self.session)
        self.s2 = SemanticScholarScraper(self.session)
        self.openalex = OpenAlexScraper(self.session)
    
    def search(self, query: str,
               use_epmc: bool = True,
               use_s2: bool = True,
               use_openalex: bool = True,
               use_arxiv: bool = True) -> List[Dict[str, Any]]:
        """
        统一搜索接口
        
        Args:
            query: 搜索查询
            use_epmc: 是否使用EuropePMC
            use_s2: 是否使用Semantic Scholar
            use_openalex: 是否使用OpenAlex
            use_arxiv: 是否使用ArXiv
        
        Returns:
            去重后的文献列表
        """
        all_results = []
        
        # EuropePMC
        if use_epmc:
            print(f"[EPMC] 搜索中...")
            epmc_query = self.epmc.build_query(query)
            epmc_results = self.epmc.search(epmc_query)
            all_results.extend(epmc_results)
            print(f"[EPMC] 找到 {len(epmc_results)} 条结果")
        
        # Semantic Scholar
        if use_s2:
            print(f"[S2] 搜索中...")
            s2_results = self.s2.search(query)
            all_results.extend(s2_results)
            print(f"[S2] 找到 {len(s2_results)} 条结果")
        
        # OpenAlex
        if use_openalex:
            print(f"[OpenAlex] 搜索中...")
            openalex_results = self.openalex.search(query)
            all_results.extend(openalex_results)
            print(f"[OpenAlex] 找到 {len(openalex_results)} 条结果")
        
        # ArXiv
        if use_arxiv and ScraperConfig.ARXIV_ENABLED:
            print(f"[ArXiv] 搜索中...")
            arxiv_results = self._search_arxiv(query)
            all_results.extend(arxiv_results)
            print(f"[ArXiv] 找到 {len(arxiv_results)} 条结果")
        
        # 去重
        deduplicated = self._deduplicate(all_results)
        print(f"[总计] 去重后: {len(deduplicated)} 条结果")
        
        return deduplicated
    
    def _search_arxiv(self, query: str) -> List[Dict[str, Any]]:
        """搜索ArXiv并解析结果"""
        try:
            from urllib.parse import quote_plus
            encoded = quote_plus(query.strip())
            url = (
                f"http://export.arxiv.org/api/query?search_query=all:{encoded}"
                f"&start=0&max_results={ScraperConfig.ARXIV_MAX_RESULTS}"
            )
            
            resp = self.session.session.get(url, timeout=20)
            resp.raise_for_status()
            
            # Parse Atom feed
            root = ET.fromstring(resp.text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            results = []
            
            for entry in root.findall("atom:entry", ns):
                title_elem = entry.find("atom:title", ns)
                summary_elem = entry.find("atom:summary", ns)
                published_elem = entry.find("atom:published", ns)
                
                # Extract authors
                authors = []
                for author in entry.findall("atom:author", ns):
                    name_elem = author.find("atom:name", ns)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text)
                
                # Extract arXiv ID for DOI
                id_elem = entry.find("atom:id", ns)
                arxiv_id = None
                if id_elem is not None and id_elem.text:
                    # Extract ID from URL like http://arxiv.org/abs/2401.12345v1
                    arxiv_id = id_elem.text.split("/abs/")[-1] if "/abs/" in id_elem.text else None
                
                results.append({
                    "source": "ArXiv",
                    "title": title_elem.text.strip() if title_elem is not None else None,
                    "doi": f"arXiv:{arxiv_id}" if arxiv_id else None,
                    "pub_year": published_elem.text[:4] if published_elem is not None else None,
                    "abstract": summary_elem.text.strip() if summary_elem is not None else None,
                    "authors": ", ".join(authors) if authors else None,
                    "journal": "arXiv preprint",
                })
            
            return results
        
        except Exception as e:
            print(f"[ArXiv] 错误: {e}")
            return []
    
    def _deduplicate(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于DOI和标题的智能去重"""
        seen_keys = set()
        deduplicated = []
        
        for item in results:
            doi = item.get("doi")
            title = item.get("title")
            source = item.get("source")
            year = item.get("pub_year")
            
            # 生成去重键
            if doi and isinstance(doi, str) and doi.strip():
                # 优先使用DOI
                doi_clean = doi.replace("https://doi.org/", "").strip().lower()
                key = f"doi:{doi_clean}"
            elif title:
                # 使用标题+年份+来源
                key = f"{source}|{title}|{year}"
            else:
                # 无法去重，保留
                deduplicated.append(item)
                continue
            
            if key not in seen_keys:
                seen_keys.add(key)
                deduplicated.append(item)
        
        return deduplicated


# =========================
# 便捷函数
# =========================
def search_literature(query: str, cache_dir: str = ".http_cache") -> List[Dict[str, Any]]:
    """
    搜索文献的便捷函数
    
    Args:
        query: 搜索查询
        cache_dir: 缓存目录
    
    Returns:
        文献列表
    """
    scraper = UnifiedScraper(cache_dir=cache_dir)
    return scraper.search(query)


if __name__ == "__main__":
    # 测试
    results = search_literature("protein stability pH temperature solubility")
    print(f"\n搜索完成，共 {len(results)} 条结果")
    
    # 打印前3条
    for i, item in enumerate(results[:3], 1):
        print(f"\n{i}. [{item['source']}] {item['title']}")
        print(f"   DOI: {item.get('doi', 'N/A')}")
        print(f"   Year: {item.get('pub_year', 'N/A')}")

