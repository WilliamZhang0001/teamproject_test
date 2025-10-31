#!/usr/bin/env python3
"""
生成IQR统计数据（按实验类型和物质分组）

用法：
    python scripts/generate_iqr_statistics.py --data literature_mining/storage/structured_store.jsonl
"""
import argparse
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def load_records(data_file: str) -> List[Dict]:
    """加载JSONL数据"""
    records = []
    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            records.append(json.loads(line))
    return records


def calculate_iqr_stats(values: pd.Series) -> Dict:
    """计算IQR统计"""
    if len(values) == 0:
        return None
    
    values = values.dropna()
    if len(values) == 0:
        return None
    
    return {
        'count': int(len(values)),
        'min': float(values.min()),
        'max': float(values.max()),
        'median': float(values.median()),
        'q1': float(values.quantile(0.25)),
        'q3': float(values.quantile(0.75)),
        'iqr': float(values.quantile(0.75) - values.quantile(0.25)),
        'mean': float(values.mean()),
        'std': float(values.std()) if len(values) > 1 else 0.0
    }


def generate_iqr_statistics(records: List[Dict], output_file: str):
    """生成IQR统计数据"""
    print("\n=== Generating IQR Statistics ===")
    
    # 提取参数数据
    data_rows = []
    for record in records:
        params = record.get('parameters', {})
        data_rows.append({
            'biomolecule_name': record.get('protein_name', 'unknown'),
            'biomolecule_type': record.get('biomolecule_type', 'unknown'),
            'experiment_type': record.get('property', 'unknown'),
            'pH': params.get('pH'),
            'temperature_c': params.get('temperature_c'),
            'concentration_mg_ml': params.get('concentration_mg_ml'),
            'ionic_strength_mM': params.get('ionic_strength_mM'),
            'time_min': params.get('time_min'),
            'shear_rate_s1': params.get('shear_rate_s1'),
            'pressure_bar': params.get('pressure_bar'),
        })
    
    df = pd.DataFrame(data_rows)
    print(f"Loaded {len(df)} records")
    
    param_cols = ['pH', 'temperature_c', 'concentration_mg_ml', 'ionic_strength_mM',
                  'time_min', 'shear_rate_s1', 'pressure_bar']
    
    # 1. 全局统计
    print("\n1. Global statistics (all data)...")
    global_stats = {}
    for param in param_cols:
        stats = calculate_iqr_stats(df[param])
        if stats:
            global_stats[param] = stats
    
    # 2. 按实验类型统计
    print("\n2. Statistics by experiment type...")
    by_experiment = {}
    for exp_type in df['experiment_type'].unique():
        if exp_type == 'unknown':
            continue
        df_exp = df[df['experiment_type'] == exp_type]
        exp_stats = {'_count': len(df_exp)}
        for param in param_cols:
            stats = calculate_iqr_stats(df_exp[param])
            if stats:
                exp_stats[param] = stats
        if len(exp_stats) > 1:  # 至少有一个参数
            by_experiment[exp_type] = exp_stats
            print(f"  {exp_type}: {len(df_exp)} records")
    
    # 3. 按生物分子类型统计
    print("\n3. Statistics by biomolecule type...")
    by_biomolecule_type = {}
    for bio_type in df['biomolecule_type'].unique():
        if bio_type == 'unknown':
            continue
        df_bio = df[df['biomolecule_type'] == bio_type]
        bio_stats = {'_count': len(df_bio)}
        for param in param_cols:
            stats = calculate_iqr_stats(df_bio[param])
            if stats:
                bio_stats[param] = stats
        if len(bio_stats) > 1:
            by_biomolecule_type[bio_type] = bio_stats
            print(f"  {bio_type}: {len(df_bio)} records")
    
    # 4. 按物质名称统计（Top 50）
    print("\n4. Statistics by biomolecule name (Top 50)...")
    biomolecule_counts = df['biomolecule_name'].value_counts()
    top_biomolecules = biomolecule_counts[biomolecule_counts >= 10].head(50).index
    
    by_biomolecule = {}
    for biomolecule in top_biomolecules:
        df_bio = df[df['biomolecule_name'] == biomolecule]
        bio_stats = {
            '_count': len(df_bio),
            '_biomolecule_type': df_bio['biomolecule_type'].mode()[0] if len(df_bio) > 0 else 'unknown'
        }
        for param in param_cols:
            stats = calculate_iqr_stats(df_bio[param])
            if stats:
                bio_stats[param] = stats
        if len(bio_stats) > 2:  # 至少有一个参数
            by_biomolecule[biomolecule] = bio_stats
            print(f"  {biomolecule}: {len(df_bio)} records")
    
    # 5. 按实验类型+物质名称统计（详细版）
    print("\n5. Statistics by experiment type + biomolecule (Top 30 per type)...")
    by_experiment_and_biomolecule = {}
    for exp_type in df['experiment_type'].unique():
        if exp_type == 'unknown':
            continue
        df_exp = df[df['experiment_type'] == exp_type]
        biomolecule_counts = df_exp['biomolecule_name'].value_counts()
        top_biomolecules = biomolecule_counts[biomolecule_counts >= 5].head(30).index
        
        exp_bio_stats = {}
        for biomolecule in top_biomolecules:
            df_subset = df_exp[df_exp['biomolecule_name'] == biomolecule]
            bio_stats = {'_count': len(df_subset)}
            for param in param_cols:
                stats = calculate_iqr_stats(df_subset[param])
                if stats:
                    bio_stats[param] = stats
            if len(bio_stats) > 1:
                exp_bio_stats[biomolecule] = bio_stats
        
        if exp_bio_stats:
            by_experiment_and_biomolecule[exp_type] = exp_bio_stats
            print(f"  {exp_type}: {len(exp_bio_stats)} biomolecules")
    
    # 保存结果
    output = {
        'metadata': {
            'total_records': len(records),
            'valid_records': len(df),
            'parameters': param_cols,
            'experiment_types': list(by_experiment.keys()),
            'biomolecule_types': list(by_biomolecule_type.keys()),
            'top_biomolecules_count': len(by_biomolecule)
        },
        'global': global_stats,
        'by_experiment_type': by_experiment,
        'by_biomolecule_type': by_biomolecule_type,
        'by_biomolecule': by_biomolecule,
        'by_experiment_and_biomolecule': by_experiment_and_biomolecule
    }
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== IQR statistics saved to: {output_path}")
    
    # 打印摘要
    print("\n" + "="*70)
    print("=== Statistics Summary ===")
    print("="*70)
    print(f"Global stats: {len(global_stats)} parameters")
    print(f"Experiment types: {len(by_experiment)}")
    print(f"Biomolecule types: {len(by_biomolecule_type)}")
    print(f"Top biomolecules: {len(by_biomolecule)}")
    print(f"Detailed (experiment + biomolecule): {sum(len(v) for v in by_experiment_and_biomolecule.values())} combinations")
    
    return output


def main():
    parser = argparse.ArgumentParser(description="生成IQR统计数据")
    parser.add_argument(
        '--data',
        type=str,
        default='literature_mining/storage/structured_store.jsonl',
        help='JSONL数据文件路径'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='models/iqr_statistics.json',
        help='输出JSON文件路径'
    )
    
    args = parser.parse_args()
    
    print("\n=== IQR Statistics Generator ===")
    print(f"Data file: {args.data}")
    print(f"Output file: {args.output}")
    
    # 加载数据
    records = load_records(args.data)
    
    # 生成统计
    generate_iqr_statistics(records, args.output)
    
    print("\n=== Done! ===")


if __name__ == '__main__':
    main()

