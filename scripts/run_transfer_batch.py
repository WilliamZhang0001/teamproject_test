from __future__ import annotations

import argparse
import sys
import json
from pathlib import Path
from typing import List
import requests
from bs4 import BeautifulSoup


def read_urls(args: argparse.Namespace) -> List[str]:
    urls: List[str] = []
    if args.url:
        urls.extend(args.url)
    if args.urls_file:
        p = Path(args.urls_file)
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    urls.append(line)
    return urls


def fetch_text(url: str, timeout: int = 20) -> str:
    headers = {"User-Agent": "DoE-Assist/TransferBatch/1.0"}
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        html = r.text
    except Exception:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup.find("article")
    if main:
        text = "\n".join([t.get_text(" ", strip=True) for t in main.find_all(["p", "li", "div"])])
    else:
        text = "\n".join([t.get_text(" ", strip=True) for t in soup.find_all("p")])
    return text


def run(model: str, label_mapping: dict, urls: List[str], output: Path, biomolecule_type: str, protein_name: str):
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))
    from literature_mining.nlp.transfer_extractor import TransferExtractor
    output.parent.mkdir(parents=True, exist_ok=True)
    extractor = TransferExtractor(model_name_or_path=model, label_mapping=label_mapping)
    with output.open("w", encoding="utf-8") as f:
        for url in urls:
            text = fetch_text(url)
            if not text:
                continue
            records = extractor.extract(text, biomolecule_type=biomolecule_type, protein_name=protein_name)
            for r in records:
                f.write(json.dumps(r.model_dump()) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", action="append")
    parser.add_argument("--urls_file")
    parser.add_argument("--model", default="d4data/biomedical-ner-all")
    parser.add_argument("--output", default="literature_mining/storage/transfer_batch.jsonl")
    parser.add_argument("--protein_name", default="lysozyme")
    parser.add_argument("--biomolecule_type", default="protein")
    args = parser.parse_args()
    urls = read_urls(args)
    if not urls:
        print("No URLs provided")
        return
    label_mapping = {"Medication": "ADDITIVE", "CHEMICAL": "ADDITIVE", "DRUG": "ADDITIVE"}
    run(args.model, label_mapping, urls, Path(args.output), args.biomolecule_type, args.protein_name)
    print(f"Wrote output to {args.output}")


if __name__ == "__main__":
    main()