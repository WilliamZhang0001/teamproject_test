#!/usr/bin/env python3
"""
Unified data processing pipeline

Features:
1. Use enhanced scraper to fetch literature (two modes)
   - Mode 1: General query (original approach)
   - Mode 2: Protein-based (new approach, recommended for training)
2. NLP extraction of experimental parameters
3. Store to structured_store.jsonl
4. Train ML model (optional)
5. Auto-import to database (enabled by default)

Usage:
    # Mode 1: General query
    python scripts/run_pipeline.py --query "protein stability pH temperature"
    
    # Mode 2: Protein-based
    python scripts/run_pipeline.py --mode protein --proteins lysozyme,albumin,insulin
    
    # Mode 3: All biomolecules (proteins, peptides, polysaccharides) - Recommended
    python scripts/run_pipeline.py --mode biomolecule --train
    
    # Mode 3: Enable Semantic Scholar (optional, disabled by default)
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
from backend.app.core.db import SessionLocal, init_db
from backend.app.services.literature_service import LiteratureService


def run_scraping(query: str, output_file: str = "raw_papers.json") -> List[Dict[str, Any]]:
    """Step 1a: General query scraping"""
    print("\n" + "="*60)
    print("Step 1/5: Scrape Literature (General Query Mode)")
    print("="*60)
    
    scraper = UnifiedScraper(cache_dir=".http_cache")
    results = scraper.search(query)
    
    # Save raw results
    output_path = Path(output_file)
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nScraping completed: {len(results)} papers")
    print(f"Raw data saved to: {output_path}")
    
    return results


def run_protein_scraping(proteins: List[str] = None, 
                        max_per_source: int = 300,
                        output_file: str = "raw_papers.json") -> List[Dict[str, Any]]:
    """Step 1b: Protein-based scraping (recommended for training)"""
    print("\n" + "="*60)
    print("Step 1/5: Scrape Literature (Protein Mode)")
    print("="*60)
    
    if proteins:
        print(f"Target proteins: {', '.join(proteins)}")
    else:
        print("Using default protein list (~30 proteins)")
    
    # Use protein_specific_scraper
    stats = search_proteins_for_training(
        proteins=proteins,
        max_per_protein_per_source=max_per_source,
        output_file=output_file
    )
    
    # Read results
    with open(output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        papers = data['papers']
    
    print(f"\nScraping completed: {len(papers)} papers (after deduplication)")
    print(f"Raw data saved to: {output_file}")
    
    return papers


def run_biomolecule_scraping(
    biomolecule_types: List[str] = None,
    max_per_source: int = 300,
    output_file: str = "raw_papers.json",
    enable_s2: bool = False,
    overwrite: bool = True
) -> List[Dict[str, Any]]:
    """
    Step 1c: Biomolecule-based scraping (supports proteins, peptides, polysaccharides)
    
    Args:
        biomolecule_types: List of biomolecule types, e.g., ['protein', 'peptide', 'polysaccharide']
        max_per_source: Maximum results per biomolecule per data source
        output_file: Output file name
    """
    print("\n" + "="*60)
    print("Step 1/5: Scrape Literature (Biomolecule Mode)")
    print("="*60)
    
    if biomolecule_types is None:
        biomolecule_types = ['protein', 'peptide', 'polysaccharide']
    
    print(f"Target types: {', '.join(biomolecule_types)}")
    print(f"Max per biomolecule per source: {max_per_source} papers")
    
    from literature_mining.scrapers.protein_specific_scraper import (
        ProteinSpecificScraper, BiomoleculeDatabase
    )
    from literature_mining.scrapers.enhanced_scraper import ScraperConfig
    
    # Set S2 switch (disabled by default)
    ScraperConfig.S2_ENABLED = enable_s2
    
    scraper = ProteinSpecificScraper()
    biomolecule_db = BiomoleculeDatabase()
    
    # Get all biomolecules by type
    all_biomolecules = biomolecule_db.get_all_biomolecules(biomolecule_types)
    
    total_count = sum(len(molecules) for molecules in all_biomolecules.values())
    print(f"Total: {total_count} biomolecules")
    for biomol_type, molecules in all_biomolecules.items():
        print(f"  - {biomol_type}: {len(molecules)}")
    
    # Search each type of biomolecule
    results_by_biomolecule = {}
    all_papers_list = []
    
    for biomol_type, molecules in all_biomolecules.items():
        print(f"\n{'='*60}")
        print(f"Searching {biomol_type.upper()}: {len(molecules)} items")
        print('='*60)
        
        for i, biomolecule in enumerate(molecules, 1):
            try:
                print(f"\n[{i}/{len(molecules)}] {biomolecule}...")
                papers = scraper.search_by_protein(
                    protein=biomolecule,  # Reuse existing function, supports any biomolecule name
                    max_per_source=max_per_source,
                    use_flexible_query=True
                )
                
                # Add biomolecule type label
                for paper in papers:
                    paper['target_protein'] = biomolecule
                    paper['biomolecule_type'] = biomol_type
                
                if papers:
                    results_by_biomolecule[f"{biomol_type}:{biomolecule}"] = papers
                    all_papers_list.extend(papers)
                    print(f"  Found {len(papers)} papers")
                else:
                    print(f"  No papers found")
                
            except Exception as e:
                print(f"  Error: {e}")
                continue
    
    # Deduplicate (based on DOI or title)
    print(f"\nTotal before deduplication: {len(all_papers_list)}")
    deduplicated = scraper.deduplicate_all_results(results_by_biomolecule)
    print(f"Total after deduplication: {len(deduplicated)}")
    
    # Statistics by type
    stats_by_type = {}
    for biomol_type in biomolecule_types:
        count = sum(1 for p in deduplicated if p.get('biomolecule_type') == biomol_type)
        stats_by_type[biomol_type] = count
    
    # Save results (only in overwrite mode, append mode handled in main function)
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
        print(f"Raw data saved to: {output_file}")
    
    print(f"\nScraping completed: {len(deduplicated)} papers (after deduplication)")
    print(f"Statistics by type:")
    for biomol_type, count in stats_by_type.items():
        print(f"   - {biomol_type}: {count} papers")
    
    return deduplicated


def run_extraction(papers: List[Dict[str, Any]], verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Step 2: NLP parameter extraction
    
    Args:
        papers: List of papers
        verbose: Whether to show detailed output (extraction details and debug info for each record, default False)
    """
    print("\n" + "="*60)
    print("Step 2/5: NLP Parameter Extraction")
    print("="*60)
    
    # Set log level: verbose=True shows all info, False shows only ERROR
    import logging
    if verbose:
        # Verbose mode: show all logs
        logging.getLogger('literature_mining').setLevel(logging.DEBUG)
        logging.getLogger('literature_mining.extractors').setLevel(logging.DEBUG)
        logging.getLogger('literature_mining.nlp').setLevel(logging.DEBUG)
    else:
        # Silent mode: show only ERROR, hide INFO/WARNING/DEBUG
        logging.getLogger('literature_mining').setLevel(logging.ERROR)
        logging.getLogger('literature_mining.extractors').setLevel(logging.ERROR)
        logging.getLogger('literature_mining.nlp').setLevel(logging.ERROR)
    
    all_records = []
    records_count = 0  # Count of extracted records
    skipped_count = 0  # Count of skipped papers
    
    import time
    start_time = time.time()
    
    print(f"Starting to process abstracts from {len(papers)} papers...")
    
    for i, paper in enumerate(papers, 1):
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        protein_name = paper.get('target_protein', None)  # Read target_protein
        text = f"{title}. {abstract}"
        
        # Extract paper metadata
        paper_doi = paper.get('doi', None)
        paper_title = paper.get('title', None)
        paper_authors = paper.get('authors', None)
        paper_pub_year = paper.get('pub_year', None)
        
        if not text.strip():
            continue
        
        paper_start = time.time()
        
        # Get biomolecule_type from paper (if available), otherwise use auto-detection
        biomolecule_type = paper.get('biomolecule_type', 'protein')
        
        try:
            records = extract_from_text(
                text=text,
                biomolecule_type=biomolecule_type,  # Use type from paper
                protein_name=protein_name,  # Pass biomolecule name
                enable_quality_monitoring=False,  # Disable quality monitoring for speed
                auto_detect_biomolecule=True  # Auto-detect type (if not in paper)
            )
        except Exception as e:
            # Catch validation errors and other exceptions, continue with next paper
            if i % 100 == 0:  # Error messages also only printed every 100 items
                print(f"\nExtraction error: {e}")
                print(f"   Skipping this paper: {title[:60]}...")
            continue
        
        paper_time = time.time() - paper_start
        
        # Add paper metadata to each record
        if records:
            for record in records:
                record.source_doi = paper_doi
                record.source_title = paper_title
                record.source_authors = paper_authors
                record.source_pub_year = paper_pub_year
            
            all_records.extend(records)
            records_count += len(records)
        else:
            skipped_count += 1
        
        # Print progress every 1000 items
        if i % 1000 == 0 or i == len(papers):
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = avg_time * (len(papers) - i)
            extraction_rate = (records_count / i * 100) if i > 0 else 0
            print(f"\nProgress: {i}/{len(papers)} ({i/len(papers)*100:.1f}%) | "
                  f"Extraction rate: {extraction_rate:.1f}% ({records_count} records) | "
                  f"Elapsed: {elapsed:.1f}s | Estimated remaining: {remaining/60:.1f} minutes")
    
    total_papers = len(papers)
    extraction_rate = (len(all_records) / total_papers * 100) if total_papers > 0 else 0
    print(f"\nExtraction completed")
    print(f"   - Processed papers: {total_papers}")
    print(f"   - Extracted records: {len(all_records)}")
    print(f"   - Extraction rate: {extraction_rate:.1f}% ({len(all_records)}/{total_papers})")
    print(f"   - Skipped papers: {skipped_count} (no valid parameters extracted)")
    
    return all_records


def run_storage(records: List[Dict[str, Any]], 
                store_path: str = "literature_mining/storage/structured_store.jsonl",
                overwrite: bool = False) -> None:
    """
    Step 3: Store to database
    
    Args:
        records: List of records to store
        store_path: Storage file path
        overwrite: Whether to overwrite existing file (default: append)
    """
    print("\n" + "="*60)
    print("Step 3/5: Store Data")
    print("="*60)
    
    # If overwrite mode and file exists, delete old file first
    store_file = Path(store_path)
    if overwrite and store_file.exists():
        old_count = len(store_file.read_text(encoding='utf-8').strip().split('\n'))
        store_file.unlink()
        print(f"Deleted old file ({old_count} records)")
    
    store = StructuredStore(store_path)
    
    for record in records:
        store.add(record)
    
    print(f"Data stored to: {store_path}")
    print(f"Records stored this time: {len(records)}")
    
    # Show total record count (if in append mode)
    if not overwrite and store_file.exists():
        total_lines = len(store_file.read_text(encoding='utf-8').strip().split('\n'))
        if total_lines > len(records):
            print(f"Total records in file: {total_lines} (append mode)")


def run_db_import(store_path: str, incremental: bool = True) -> int:
    """
    Step 5: Import data to database automatically
    
    Args:
        store_path: Path to structured_store.jsonl file
        incremental: If True, only import new records (default: True)
        
    Returns:
        Number of imported records
    """
    print("\n" + "="*60)
    print("Step 5/5: Auto-import to Database")
    print("="*60)
    
    try:
        # Initialize database
        init_db()
        
        # Create database session
        db = SessionLocal()
        try:
            service = LiteratureService(db)
            
            if incremental:
                print("Using incremental import mode (import new records only)...")
                # For incremental import, we'll track which records are already in DB
                # by checking DOI and parameter combination
                imported_count = service.load_literature_to_db_incremental()
            else:
                print("Using full import mode (re-import all records)...")
                imported_count = service.load_literature_to_db()
            
            print(f"Successfully imported {imported_count} records to database")
            return imported_count
        finally:
            db.close()
    except Exception as e:
        print(f"Database import failed: {e}")
        print("   Data still saved in JSONL file, can be imported manually later")
        import traceback
        traceback.print_exc()
        return 0


def run_training(store_path: str = "literature_mining/storage/structured_store.jsonl",
                 model_path: str = "models/saved/stability.pkl") -> None:
    """Step 4: Train ML model"""
    print("\n" + "="*60)
    print("Step 4/5: Train ML Model")
    print("="*60)
    
    print(f"Loading data from {store_path}...")
    model = train_from_store(store_path, use_synth=True)
    
    print("Training completed")
    
    # Save model
    model_file = Path(model_path)
    model_file.parent.mkdir(parents=True, exist_ok=True)
    save_model(model, model_file)
    
    print(f"Model saved to: {model_path}")


def main():
    parser = argparse.ArgumentParser(description="Run complete data processing pipeline")
    
    # Mode selection
    parser.add_argument(
        "--mode",
        type=str,
        choices=["query", "protein", "biomolecule"],
        default="query",
        help="Scraping mode: query=general query, protein=protein-based, biomolecule=all biomolecules (recommended)"
    )
    
    # General query mode parameters
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Search query string (required when mode=query)"
    )
    
    # Protein mode parameters
    parser.add_argument(
        "--proteins",
        type=str,
        default=None,
        help="Protein list, comma-separated (optional when mode=protein, default uses built-in list)"
    )
    
    # Biomolecule mode parameters
    parser.add_argument(
        "--biomolecule-types",
        type=str,
        default="protein,peptide,polysaccharide",
        help="Biomolecule types, comma-separated (effective when mode=biomolecule): protein,peptide,polysaccharide"
    )
    
    parser.add_argument(
        "--max-per-source",
        type=int,
        default=300,
        help="Maximum results per biomolecule per data source (effective when mode=protein or biomolecule, default 100)"
    )
    parser.add_argument(
        "--enable-s2",
        action="store_true",
        help="Enable Semantic Scholar (disabled by default to avoid rate limiting)"
    )
    
    # General parameters
    parser.add_argument(
        "--store",
        type=str,
        default="literature_mining/storage/structured_store.jsonl",
        help="Data storage path"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="models/saved/stability.pkl",
        help="Model save path"
    )
    parser.add_argument(
        "--train",
        action="store_true",
        help="Whether to train model"
    )
    parser.add_argument(
        "--skip-scraping",
        action="store_true",
        help="Skip scraping step (use existing raw_papers.json)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files (raw_papers.json and structured_store.jsonl, default: append)"
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing data (default behavior, mutually exclusive with --overwrite)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output mode (show extraction details and debug info for each record, default off)"
    )
    parser.add_argument(
        "--auto-import-db",
        action="store_true",
        help="Auto-import data to database (enabled by default)"
    )
    parser.add_argument(
        "--no-auto-import-db",
        action="store_true",
        dest="skip_db_import",
        help="Skip auto-import to database (if --auto-import-db is enabled)"
    )
    parser.add_argument(
        "--incremental-import",
        action="store_true",
        default=True,
        help="Use incremental import mode (import new records only, enabled by default)"
    )
    parser.add_argument(
        "--full-import",
        action="store_true",
        dest="full_import",
        help="Use full import mode (re-import all records, overwrite existing data)"
    )
    
    args = parser.parse_args()
    
    # Validate parameters
    if args.mode == "query" and not args.query and not args.skip_scraping:
        parser.error("--query is required when --mode=query")
    
    # Check mutual exclusivity of overwrite and append
    if args.overwrite and args.append:
        parser.error("--overwrite and --append cannot be used together")
    
    # S2 switch: disabled by default, only enabled if explicitly requested
    from literature_mining.scrapers.enhanced_scraper import ScraperConfig
    if args.enable_s2:
        ScraperConfig.S2_ENABLED = True
    else:
        ScraperConfig.S2_ENABLED = False  # Ensure disabled by default
    
    print("\nDoE-Assist Data Processing Pipeline")
    print(f"Mode: {args.mode}")
    if args.mode == "query":
        print(f"Query: {args.query}")
    elif args.mode == "protein":
        if args.proteins:
            print(f"Proteins: {args.proteins}")
        else:
            print(f"Proteins: Using default list (~30)")
        print(f"Max results per source: {args.max_per_source}")
    elif args.mode == "biomolecule":
        print(f"Biomolecule types: {args.biomolecule_types}")
        print(f"Max results per source: {args.max_per_source}")
    print(f"Semantic Scholar: {'Enabled' if ScraperConfig.S2_ENABLED else 'Disabled (to avoid rate limiting)'}")
    print(f"Storage: {args.store}")
    if args.train:
        print(f"Model: {args.model}")
    
    try:
        # Step 1: Scrape literature
        if args.skip_scraping:
            print("\nSkipping scraping step")
            raw_file = Path("raw_papers.json")
            if not raw_file.exists():
                print(f"File not found: {raw_file}, please run scraping step first")
                sys.exit(1)
            with raw_file.open('r', encoding='utf-8') as f:
                data = json.load(f)
                # Compatible with both formats
                if isinstance(data, dict) and 'papers' in data:
                    papers = data['papers']
                else:
                    papers = data
        else:
            # Determine whether to overwrite existing file
            overwrite_mode = args.overwrite or (not args.append and not Path("raw_papers.json").exists())
            
            if args.mode == "biomolecule":
                # Biomolecule mode (supports proteins, peptides, polysaccharides)
                biomolecule_types = [t.strip() for t in args.biomolecule_types.split(',')]
                
                # If append mode and file exists, read existing data first
                existing_papers = []
                if not overwrite_mode and Path("raw_papers.json").exists():
                    print("\nExisting literature data detected, will append new data")
                    try:
                        with Path("raw_papers.json").open('r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                            if isinstance(existing_data, dict) and 'papers' in existing_data:
                                existing_papers = existing_data['papers']
                            elif isinstance(existing_data, list):
                                existing_papers = existing_data
                    except Exception as e:
                        print(f"Error reading existing data: {e}, will create new file")
                
                papers = run_biomolecule_scraping(
                    biomolecule_types=biomolecule_types,
                    max_per_source=args.max_per_source,
                    output_file="raw_papers.json",
                    enable_s2=getattr(args, 'enable_s2', False),
                    overwrite=overwrite_mode
                )
                
                # If append mode, merge existing data and save
                if not overwrite_mode and existing_papers:
                    # Deduplicate based on DOI
                    existing_dois = {p.get('doi') for p in existing_papers if p.get('doi')}
                    new_papers = [p for p in papers if p.get('doi') not in existing_dois]
                    papers = existing_papers + new_papers
                    print(f"Merging completed: {len(existing_papers)} existing, {len(new_papers)} new, {len(papers)} total")
                    
                    # Save merged data
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
                    print(f"Merged data saved to: raw_papers.json")
            elif args.mode == "protein":
                # Protein mode
                protein_list = args.proteins.split(',') if args.proteins else None
                papers = run_protein_scraping(
                    proteins=protein_list,
                    max_per_source=args.max_per_source
                )
            else:
                # Query mode
                papers = run_scraping(args.query)
        
        if not papers:
            print("No literature found, exiting")
            sys.exit(1)
        
        # Step 2: NLP extraction
        records = run_extraction(papers, verbose=getattr(args, 'verbose', False))
        
        if not records:
            print("No valid records extracted, exiting")
            sys.exit(1)
        
        # Step 3: Storage
        # If using --overwrite, also overwrite structured_store.jsonl
        store_overwrite = getattr(args, 'overwrite', False)
        run_storage(records, args.store, overwrite=store_overwrite)
        
        # Step 4: Train model (optional)
        if args.train:
            run_training(args.store, args.model)
        
        # Step 5: Auto-import to database (enabled by default)
        imported_count = 0
        if getattr(args, 'auto_import_db', True) and not getattr(args, 'skip_db_import', False):
            incremental = getattr(args, 'incremental_import', True) and not getattr(args, 'full_import', False)
            imported_count = run_db_import(args.store, incremental=incremental)
        else:
            print("\nSkipping database import step")
        
        print("\n" + "="*60)
        print("Pipeline completed!")
        print("="*60)
        print(f"Papers: {len(papers)}")
        print(f"Extracted records: {len(records)}")
        print(f"Data storage: {args.store}")
        if imported_count > 0:
            print(f"Database import: {imported_count} records")
        if args.train:
            print(f"Model: {args.model}")
        print()
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
