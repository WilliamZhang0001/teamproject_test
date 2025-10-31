#!/usr/bin/env python3
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def search_arxiv(query: str, max_results: int = 25, prefer_pdf: bool = True) -> list[str]:
    encoded = quote_plus(query.strip())
    url = (
        f"http://export.arxiv.org/api/query?search_query=all:{encoded}"
        f"&start=0&max_results={int(max_results)}"
    )
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
        resp.raise_for_status()
        # Parse Atom feed
        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        urls: list[str] = []
        for entry in root.findall("atom:entry", ns):
            html_url = None
            pdf_url = None
            for link in entry.findall("atom:link", ns):
                href = link.attrib.get("href")
                rel = link.attrib.get("rel", "")
                title = link.attrib.get("title", "")
                if rel == "alternate" and href:
                    html_url = href
                if title.lower() == "pdf" and href:
                    pdf_url = href
            # Prefer PDF when requested and available
            chosen = pdf_url if (prefer_pdf and pdf_url) else (html_url or pdf_url)
            if chosen:
                urls.append(chosen)
        return urls
    except Exception:
        return []