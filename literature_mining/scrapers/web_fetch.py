#!/usr/bin/env python3
import io
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from pdfminer.high_level import extract_text

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

def _is_pdf_response(url: str, content_type: str | None) -> bool:
    if content_type and "application/pdf" in content_type.lower():
        return True
    parsed = urlparse(url)
    return parsed.path.lower().endswith(".pdf") or "pdf" in parsed.path.lower()

def _clean_html_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "form"]):
        tag.decompose()

    main = soup.find(["main", "article"])
    root = main if main else soup.body if soup.body else soup
    text = root.get_text(separator=" ", strip=True)

    text = re.sub(r"\s+", " ", text).strip()
    return text

# --- Domain-specific HTML extractors ---

def _find_meta_content(soup: BeautifulSoup, name: str) -> str | None:
    m = soup.find("meta", attrs={"name": name})
    return m.get("content") if m and m.get("content") else None

def _find_pdf_url(soup: BeautifulSoup, base_url: str) -> str | None:
    url = _find_meta_content(soup, "citation_pdf_url")
    if url:
        return url
    # Common anchors pointing to PDF
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.lower().endswith(".pdf") or "pdf" in href.lower():
            return href
    return None

def _extract_arxiv(soup: BeautifulSoup, html: str) -> str:
    # arXiv abstract page
    blk = soup.select_one("blockquote.abstract")
    if blk:
        return re.sub(r"\s+", " ", blk.get_text(" ", strip=True)).strip()
    meta_abs = _find_meta_content(soup, "citation_abstract")
    if meta_abs:
        return re.sub(r"\s+", " ", meta_abs).strip()
    return _clean_html_text(html)

def _extract_pubmed(soup: BeautifulSoup, html: str) -> str:
    for sel in ["div.abstract", "section#abstract", "div#abstr"]:
        el = soup.select_one(sel)
        if el:
            return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
    return _clean_html_text(html)

def _extract_nature(soup: BeautifulSoup, html: str) -> str:
    for sel in ["div.c-article-body", "article", "main"]:
        el = soup.select_one(sel)
        if el:
            return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
    return _clean_html_text(html)

def _extract_springer(soup: BeautifulSoup, html: str) -> str:
    for sel in ["section#Abs1", "div.c-article-section__content", "div#Abs1-content"]:
        el = soup.select_one(sel)
        if el:
            return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
    return _clean_html_text(html)

def _extract_wiley(soup: BeautifulSoup, html: str) -> str:
    for sel in ["div.article-section__content", "div.article-content", "section.article-section"]:
        el = soup.select_one(sel)
        if el:
            return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
    return _clean_html_text(html)

def _extract_science(soup: BeautifulSoup, html: str) -> str:
    for sel in ["div.article-body", "div#articleBody", "article"]:
        el = soup.select_one(sel)
        if el:
            return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
    return _clean_html_text(html)

def _extract_sciencedirect(soup: BeautifulSoup, html: str) -> str:
    # ScienceDirect often loads via JS; try abstract blocks
    for sel in ["div.Abstracts", "div.abstract", "section#abstract"]:
        el = soup.select_one(sel)
        if el:
            return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
    return _clean_html_text(html)

def _extract_by_domain(domain: str, soup: BeautifulSoup, html: str) -> str:
    if "arxiv.org" in domain:
        return _extract_arxiv(soup, html)
    if "pubmed." in domain or "ncbi.nlm.nih.gov" in domain:
        return _extract_pubmed(soup, html)
    if "nature.com" in domain:
        return _extract_nature(soup, html)
    if "springer.com" in domain or "link.springer.com" in domain:
        return _extract_springer(soup, html)
    if "wiley.com" in domain or "onlinelibrary.wiley.com" in domain:
        return _extract_wiley(soup, html)
    if "science.org" in domain:
        return _extract_science(soup, html)
    if "sciencedirect.com" in domain:
        return _extract_sciencedirect(soup, html)
    return _clean_html_text(html)

def _normalize_text(text: str) -> str:
    # Remove references and boilerplate-like lines heuristically
    text = re.sub(r"\s+", " ", text).strip()
    # Drop common footer/header tokens
    text = re.sub(r"(©\s*\d{4}.*?|All rights reserved\.|Supplementary Information.*?)", " ", text, flags=re.I)
    return text.strip()

def _fetch_pdf_text_from_url(url: str, timeout: int) -> str:
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        data = io.BytesIO(resp.content)
        pdf_text = extract_text(data) or ""
        return _normalize_text(pdf_text)
    except Exception:
        return ""

def fetch_url_text(url: str, timeout: int = 25, prefer_pdf: bool = False) -> str:
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            allow_redirects=True,
        )
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        is_pdf = _is_pdf_response(resp.url or url, content_type)

        if is_pdf:
            return _fetch_pdf_text_from_url(resp.url or url, timeout)

        # HTML path
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # If prefer PDF and a PDF link exists, use it
        pdf_url = _find_pdf_url(soup, resp.url or url)
        if prefer_pdf and pdf_url:
            pdf_text = _fetch_pdf_text_from_url(pdf_url, timeout)
            if pdf_text:
                return pdf_text

        # Domain-specific extraction
        domain = urlparse(resp.url or url).netloc
        body_text = _extract_by_domain(domain, soup, html)
        body_text = _normalize_text(body_text)

        # Fallback to PDF if HTML is too short
        if (not body_text or len(body_text) < 300) and pdf_url:
            pdf_text = _fetch_pdf_text_from_url(pdf_url, timeout)
            if pdf_text:
                return pdf_text
        return body_text
    except Exception:
        return ""

def fetch_many(urls: list[str], timeout: int = 25, prefer_pdf: bool = False) -> list[str]:
    texts: list[str] = []
    for u in urls:
        t = fetch_url_text(u, timeout=timeout, prefer_pdf=prefer_pdf)
        if t:
            texts.append(t)
    return texts