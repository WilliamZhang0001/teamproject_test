"""Analyze difference between old and new models"""
import json
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(PROJECT_ROOT))

from ml_engine.features.improved_preprocess import records_to_improved_dataframe, _label_from_outcome_and_polarity


def analyze_data_filtering():
    """Analyze data filtering"""
    print("\n" + "="*70)
    print("Data Filtering Analysis")
    print("="*70)
    
    # Load raw data
    records = []
    with open('literature_mining/storage/structured_store.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            records.append(json.loads(line))
    
    print(f"\n1. Total raw records: {len(records)}")
    
    # Analyze label generation
    no_label_count = 0
    no_params_count = 0
    valid_count = 0
    
    label_details = {
        'positive_polarity': 0,
        'negative_polarity': 0,
        'neutral_polarity': 0,
        'has_outcome_label': 0,
        'no_outcome_label': 0,
        'generated_label_1': 0,
        'generated_label_0': 0,
        'generated_label_none': 0
    }
    
    for r in records:
        outcome_label = r.get('outcome_label')
        polarity = r.get('polarity')
        params = r.get('parameters', {})
        
        # Count polarity
        if polarity == 'positive':
            label_details['positive_polarity'] += 1
        elif polarity == 'negative':
            label_details['negative_polarity'] += 1
        else:
            label_details['neutral_polarity'] += 1
        
        # Count outcome_label
        if outcome_label:
            label_details['has_outcome_label'] += 1
        else:
            label_details['no_outcome_label'] += 1
        
        # Generate label
        label = _label_from_outcome_and_polarity(outcome_label, polarity)
        
        if label == 1:
            label_details['generated_label_1'] += 1
        elif label == 0:
            label_details['generated_label_0'] += 1
        else:
            label_details['generated_label_none'] += 1
            no_label_count += 1
            continue
        
        # Check parameters
        has_params = any(params.get(k) is not None for k in [
            'pH', 'temperature_c', 'concentration_mg_ml', 'ionic_strength_mM',
            'additive', 'time_min', 'shear_rate_s1', 'pressure_bar'
        ] if k != 'raw_context')
        
        if not has_params:
            no_params_count += 1
        else:
            valid_count += 1
    
    print(f"\n2. Label generation:")
    print(f"   - Records with outcome_label: {label_details['has_outcome_label']}")
    print(f"   - Records without outcome_label: {label_details['no_outcome_label']}")
    print(f"   - Polarity distribution:")
    print(f"     - Positive: {label_details['positive_polarity']}")
    print(f"     - Negative: {label_details['negative_polarity']}")
    print(f"     - Neutral/None: {label_details['neutral_polarity']}")
    print(f"   - Generated labels:")
    print(f"     - Stable (1): {label_details['generated_label_1']}")
    print(f"     - Unstable (0): {label_details['generated_label_0']}")
    print(f"     - No label (None): {label_details['generated_label_none']}")
    
    print(f"\n3. Filtering results:")
    print(f"   - Records without label: {no_label_count} ({no_label_count/len(records)*100:.1f}%)")
    print(f"   - Records without parameters: {no_params_count} ({no_params_count/len(records)*100:.1f}%)")
    print(f"   - Valid records: {valid_count} ({valid_count/len(records)*100:.1f}%)")
    
    # Verify with actual function
    df = records_to_improved_dataframe(records)
    print(f"\n4. Actual DataFrame size: {len(df)} records")
    
    # By experiment type
    if 'property' in df.columns:
        print(f"\n5. By experiment type:")
        for exp_type, count in df['property'].value_counts().items():
            print(f"   - {exp_type}: {count} ({count/len(df)*100:.1f}%)")
    else:
        print(f"\n5. WARNING: 'property' field not found in DataFrame!")
    
    # Label distribution
    print(f"\n6. Label distribution in DataFrame:")
    print(f"   - Stable (1): {(df['label']==1).sum()} ({(df['label']==1).sum()/len(df)*100:.1f}%)")
    print(f"   - Unstable (0): {(df['label']==0).sum()} ({(df['label']==0).sum()/len(df)*100:.1f}%)")
    
    print(f"\n7. Data loss:")
    print(f"   - Raw: {len(records)} records")
    print(f"   - After processing: {len(df)} records")
    print(f"   - Loss: {len(records)-len(df)} records ({(len(records)-len(df))/len(records)*100:.1f}%)")


def compare_models():
    """Compare old and new models"""
    print("\n" + "="*70)
    print("Model Comparison")
    print("="*70)
    
    print("\nOld Dual-Track Model (models/dual_track/):")
    print("  - F1-Score: 0.945")
    print("  - Training data: 4,936 records")
    print("  - Trained by: train_dual_track_system.py")
    print("  - Features: High accuracy, less data")
    
    print("\nNew General Model (models/by_experiment_type/):")
    print("  - F1-Score: 0.645")
    print("  - Training data: 14,676 (valid) / 20,270 (raw)")
    print("  - Trained by: train_by_experiment_type.py")
    print("  - Features: More data, lower accuracy")
    
    print("\nPossible reasons for accuracy drop:")
    print("  1. Data quality: New data may contain more noise")
    print("  2. Label generation: 27% of data filtered due to failed label generation")
    print("  3. Class imbalance: Stable:Unstable = 80:20")
    print("  4. Not trained by experiment type: property field was not extracted (NOW FIXED)")
    
    print("\nRecommendations:")
    print("  1. Retrain models (property field now fixed)")
    print("  2. Check label generation logic accuracy")
    print("  3. Use SMOTE to handle class imbalance")
    print("  4. Train separate models for each experiment type")


if __name__ == '__main__':
    analyze_data_filtering()
    compare_models()

