"""
Literature Database Access Layer
"""
import math
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, or_, and_
from typing import List, Optional, Dict, Any
from backend.app.models.literature import Literature, ExtractionRecord
from collections import Counter


def create_literature(db: Session, **kwargs) -> Literature:
    """Create literature record"""
    literature = Literature(**kwargs)
    db.add(literature)
    db.commit()
    db.refresh(literature)
    return literature


def get_literature_by_doi(db: Session, doi: str) -> Optional[Literature]:
    """Get literature by DOI"""
    return db.scalar(select(Literature).where(Literature.doi == doi))


def create_extraction_record(db: Session, record_data: dict, literature_id: Optional[int] = None) -> ExtractionRecord:
    """Create extraction record"""
    # Extract parameters
    parameters = record_data.get('parameters', {})
    
    # Get from literature_id or from record_data
    if literature_id is None:
        doi = record_data.get('source_doi')
        if doi:
            literature = get_literature_by_doi(db, doi)
            if literature:
                literature_id = literature.id
    
    record = ExtractionRecord(
        literature_id=literature_id,
        biomolecule_type=record_data.get('biomolecule_type', 'protein'),
        protein_name=record_data.get('protein_name'),
        polarity=record_data.get('polarity'),
        property=record_data.get('property', 'stability'),
        pH=parameters.get('pH'),
        temperature_c=parameters.get('temperature_c'),
        concentration_mg_ml=parameters.get('concentration_mg_ml'),
        ionic_strength_mM=parameters.get('ionic_strength_mM'),
        additive=parameters.get('additive'),
        time_min=parameters.get('time_min'),
        shear_rate_s1=parameters.get('shear_rate_s1'),
        pressure_bar=parameters.get('pressure_bar'),
        outcome_score=record_data.get('outcome_score'),
        outcome_label=record_data.get('outcome_label'),
        outcome_text=record_data.get('outcome_text'),
        source_section=record_data.get('source_section'),
        confidence=record_data.get('confidence', 0.5),
        raw_context=parameters.get('raw_context'),
        full_data=record_data  # Save complete data for retrieval
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_all_extraction_records(db: Session, limit: int = 1000) -> List[ExtractionRecord]:
    """Get all extraction records"""
    stmt = select(ExtractionRecord).limit(limit)
    return list(db.scalars(stmt).all())


def search_similar_records(
    db: Session,
    target_params: Dict[str, Any],
    biomolecule_name: Optional[str] = None,
    property_type: str = 'stability',
    limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Search most similar records based on parameter similarity
    
    Args:
        db: Database session
        target_params: Target parameter dictionary (experimental conditions)
        biomolecule_name: Biomolecule name
        property_type: Property type
        limit: Number of records to return
    
    Returns:
        List of most similar records (including similarity scores)
    """
    # Build query with eager loading of literature relationship
    query = select(ExtractionRecord).options(
        joinedload(ExtractionRecord.literature)
    ).where(
        ExtractionRecord.property == property_type
    )
    
    # Filter by biomolecule
    if biomolecule_name:
        query = query.where(
            or_(
                ExtractionRecord.protein_name == biomolecule_name,
                ExtractionRecord.protein_name.like(f"%{biomolecule_name}%")
            )
        )
    
    # Get all candidate records
    candidates = list(db.scalars(query).unique().all())
    
    if not candidates:
        return []
    
    # Calculate similarity scores and sort
    scored_records = []
    for record in candidates:
        similarity_score = calculate_similarity(target_params, record)
        if similarity_score > 0:  # Only return records with similarity
            record_dict = record.to_dict()
            record_dict['similarity_score'] = similarity_score
            # Add literature information - only from real sources, no auto-generation
            literature_info = None
            
            # First, try from relationship
            if record.literature:
                literature_info = {
                    'doi': record.literature.doi,
                    'title': record.literature.title,
                    'authors': record.literature.authors,
                    'pub_year': record.literature.pub_year
                }
            # If no literature relationship, try to extract from full_data
            elif record.full_data:
                full_data = record.full_data if isinstance(record.full_data, dict) else {}
                # Extract from various possible fields (same place as raw_context would be)
                title = full_data.get('title') or full_data.get('source_title') or full_data.get('paper_title')
                authors = full_data.get('authors') or full_data.get('source_authors') or full_data.get('paper_authors')
                pub_year_raw = full_data.get('pub_year') or full_data.get('publication_year') or full_data.get('source_pub_year') or full_data.get('year') or full_data.get('paper_year')
                doi = full_data.get('source_doi') or full_data.get('doi') or full_data.get('paper_doi')
                
                # Convert pub_year to int if it's a string
                pub_year = None
                if pub_year_raw is not None:
                    try:
                        if isinstance(pub_year_raw, str):
                            pub_year = int(pub_year_raw.strip())
                        elif isinstance(pub_year_raw, (int, float)):
                            pub_year = int(pub_year_raw)
                    except (ValueError, TypeError):
                        pub_year = None
                
                # Create literature info if we have at least one field (not just title)
                # This allows displaying partial metadata even if title is missing
                if title or authors or pub_year or doi:
                    literature_info = {
                        'doi': doi,
                        'title': title,
                        'authors': authors,
                        'pub_year': pub_year
                    }
            
            # Add literature info if we found any metadata (not just title)
            if literature_info:
                record_dict['literature'] = literature_info
                # Also add fields to top level for easier access
                if literature_info.get('title'):
                    record_dict['title'] = literature_info['title']
                if literature_info.get('authors'):
                    record_dict['authors'] = literature_info['authors']
                if literature_info.get('pub_year'):
                    record_dict['pub_year'] = literature_info['pub_year']
                if literature_info.get('doi'):
                    record_dict['doi'] = literature_info['doi']
            
            scored_records.append(record_dict)
    
    # Sort by similarity
    scored_records.sort(key=lambda x: x['similarity_score'], reverse=True)
    
    # Remove duplicates based on DOI, literature ID, or title
    # This ensures we don't return the same literature multiple times
    seen_dois = set()
    seen_literature_ids = set()
    seen_titles = set()  # Also check by title as fallback
    deduplicated_records = []
    
    for record in scored_records:
        # Check for duplicate by DOI (most reliable)
        doi = None
        if record.get('literature') and isinstance(record['literature'], dict) and record['literature'].get('doi'):
            doi = record['literature']['doi'].strip() if record['literature']['doi'] else None
        elif record.get('doi'):
            doi = record['doi'].strip() if record['doi'] else None
        
        # Check for duplicate by literature_id
        lit_id = None
        if 'literature_id' in record and record['literature_id']:
            lit_id = record['literature_id']
        
        # Check for duplicate by title (fallback if no DOI or lit_id)
        title = None
        if record.get('literature') and isinstance(record['literature'], dict) and record['literature'].get('title'):
            title = record['literature']['title'].strip().lower() if record['literature']['title'] else None
        elif record.get('title'):
            title = record['title'].strip().lower() if record['title'] else None
        
        # Skip if we've seen this DOI, literature ID, or title before
        if doi and doi in seen_dois:
            continue
        if lit_id and lit_id in seen_literature_ids:
            continue
        if title and title in seen_titles:
            continue
        
        # Mark as seen
        if doi:
            seen_dois.add(doi)
        if lit_id:
            seen_literature_ids.add(lit_id)
        if title:
            seen_titles.add(title)
        
        deduplicated_records.append(record)
        
        # Stop if we have enough unique records
        if len(deduplicated_records) >= limit:
            break
    
    return deduplicated_records


def calculate_similarity(target_params: Dict[str, Any], record: ExtractionRecord) -> float:
    """
    Calculate parameter similarity score using joint feature vector approach.
    
    Priority strategy:
    1. Prefer records with ALL provided parameters (complete matches)
    2. Penalize records with missing parameters using penalty coefficients
    3. All parameters form a joint feature vector for comparison
    
    Uses weighted Euclidean distance on normalized feature vectors, with missing parameter penalties.
    
    Returns:
        Similarity score between 0.0 and 1.0
    """
    param_weights = {
        'pH': 0.25,
        'temperature_c': 0.20,
        'concentration_mg_ml': 0.20,
        'ionic_strength_mM': 0.15,
        'additive': 0.10,
        'time_min': 0.05,
        'shear_rate_s1': 0.03,
        'pressure_bar': 0.02
    }
    
    # Normalization ranges for converting parameters to [0, 1] range
    normalization_ranges = {
        'pH': 14.0,                    # 0-14 (standard pH scale)
        'temperature_c': 150.0,         # -20 to 130°C range
        'concentration_mg_ml': 1000.0,  # 0-1000 mg/mL
        'ionic_strength_mM': 500.0,     # 0-500 mM
        'time_min': 1440.0,            # 0-1440 minutes (24 hours)
        'shear_rate_s1': 1000.0,       # 0-1000 s⁻¹
        'pressure_bar': 1000.0         # 0-1000 bar
    }
    
    # Penalty coefficient for missing parameters
    # Higher values mean more severe penalty for missing parameters
    MISSING_PARAM_PENALTY = 0.5  # 50% penalty per missing parameter (weighted)
    
    record_params = {
        'pH': record.pH,
        'temperature_c': record.temperature_c,
        'concentration_mg_ml': record.concentration_mg_ml,
        'ionic_strength_mM': record.ionic_strength_mM,
        'additive': record.additive,
        'time_min': record.time_min,
        'shear_rate_s1': record.shear_rate_s1,
        'pressure_bar': record.pressure_bar
    }
    
    # Count provided parameters by user
    provided_params_count = sum(1 for param in param_weights.keys() 
                              if target_params.get(param) is not None)
    
    # If user provided no parameters, return based on confidence but very low
    if provided_params_count == 0:
        return record.confidence * 0.1
    
    # Build joint feature vectors: normalized and weighted parameter values
    target_vector = []
    record_vector = []
    weights_vector = []
    matched_params_count = 0
    missing_params_penalty_weight = 0.0  # Total weight of missing parameters
    
    for param, weight in param_weights.items():
        target_val = target_params.get(param)
        record_val = record_params.get(param)
        
        # Only consider parameters that user provided
        if target_val is None:
            continue
        
        # Check if record has this parameter
        if record_val is None:
            # Parameter is missing in record - apply penalty
            missing_params_penalty_weight += weight
            # For missing parameters, add penalty dimension to vectors
            # Target has value, record doesn't - maximum distance
            target_vector.append(1.0)  # Normalized target value would be 1.0
            record_vector.append(0.0)  # Missing = 0 (maximum distance)
            weights_vector.append(weight)
            continue
        
        # Both values exist - process normally
        if param == 'additive':
            # For additive, handle string comparison specially
            if str(target_val).lower().strip() == str(record_val).lower().strip():
                target_vector.append(1.0)
                record_vector.append(1.0)
            else:
                target_vector.append(1.0)
                record_vector.append(0.0)
            weights_vector.append(weight)
            matched_params_count += 1
        else:
            # Normalize numeric values to [0, 1] range
            if param in normalization_ranges:
                range_val = normalization_ranges[param]
                # Normalize: value / range (clamped to [0, 1])
                # Handle negative values for temperature
                if param == 'temperature_c' and range_val > 0:
                    # Temperature can be negative, shift to [0, range+offset]
                    offset = 20.0  # Shift -20°C to 0
                    target_normalized = max(0.0, min(1.0, (target_val + offset) / (range_val + offset)))
                    record_normalized = max(0.0, min(1.0, (record_val + offset) / (range_val + offset)))
                else:
                    target_normalized = max(0.0, min(1.0, target_val / range_val))
                    record_normalized = max(0.0, min(1.0, record_val / range_val))
            else:
                # Fallback normalization for parameters without predefined range
                max_val = max(abs(target_val), abs(record_val), 1.0)
                target_normalized = abs(target_val) / max_val if max_val > 0 else 0.0
                record_normalized = abs(record_val) / max_val if max_val > 0 else 0.0
                target_normalized = max(0.0, min(1.0, target_normalized))
                record_normalized = max(0.0, min(1.0, record_normalized))
            
            target_vector.append(target_normalized)
            record_vector.append(record_normalized)
            weights_vector.append(weight)
            matched_params_count += 1
    
    # If no parameters matched (all missing), return 0
    if matched_params_count == 0 and missing_params_penalty_weight > 0:
        return 0.0
    
    # If no parameters provided by user and no matching records
    if len(target_vector) == 0:
        return 0.0
    
    # Calculate weighted Euclidean distance on joint feature vectors
    # Distance = sqrt(sum(weight_i * (target_i - record_i)^2) / sum(weight_i))
    weighted_squared_diff = 0.0
    total_weight = 0.0
    
    for i in range(len(target_vector)):
        diff = target_vector[i] - record_vector[i]
        weighted_squared_diff += weights_vector[i] * (diff ** 2)
        total_weight += weights_vector[i]
    
    # Normalized weighted Euclidean distance
    normalized_distance = math.sqrt(weighted_squared_diff / total_weight) if total_weight > 0 else 1.0
    
    # Convert distance to similarity: similarity = 1 - distance
    base_similarity = 1.0 - normalized_distance
    
    # Apply penalty for missing parameters
    # Penalty reduces similarity based on the proportion of missing parameter weight
    if missing_params_penalty_weight > 0 and total_weight > 0:
        missing_proportion = missing_params_penalty_weight / total_weight
        # Apply penalty: multiply similarity by (1 - penalty * missing_proportion)
        # This ensures complete matches score higher than partial matches
        penalty_factor = 1.0 - (MISSING_PARAM_PENALTY * missing_proportion)
        base_similarity *= max(0.1, penalty_factor)  # Minimum 10% similarity even with penalties
    
    # Bonus for complete matches: if all parameters are matched, add small bonus
    # This ensures complete matches always rank above partial matches
    if missing_params_penalty_weight == 0 and matched_params_count == provided_params_count:
        # Complete match bonus: add 0.05 to similarity (max 1.0)
        base_similarity = min(1.0, base_similarity + 0.05)
    
    # Apply minimum similarity threshold
    MIN_SIMILARITY_THRESHOLD = 0.1
    if base_similarity < MIN_SIMILARITY_THRESHOLD:
        return 0.0
    
    # Adjust similarity by confidence: 80% similarity, 20% confidence
    adjusted_similarity = base_similarity * 0.8 + record.confidence * 0.2
    
    # Ensure result is between 0 and 1
    return max(0.0, min(1.0, adjusted_similarity))


def get_most_common_additives(
    db: Session,
    biomolecule_name: Optional[str] = None,
    property_type: str = 'stability',
    limit: int = 5
) -> Optional[Dict[str, Any]]:
    """Get most common additive value for a biomolecule
    
    Returns:
        Dict with 'recommended_value' (most common additive), 'common_values' (list of top additives), 
        'count' (total occurrences), or None if no additives found
    """
    query = select(ExtractionRecord).where(
        ExtractionRecord.property == property_type,
        ExtractionRecord.additive.isnot(None),
        ExtractionRecord.additive != ''
    )
    
    if biomolecule_name:
        query = query.where(
            or_(
                ExtractionRecord.protein_name == biomolecule_name,
                ExtractionRecord.protein_name.like(f"%{biomolecule_name}%")
            )
        )
    
    records = list(db.scalars(query).all())
    
    if not records:
        return None
    
    # Count additive occurrences
    additive_counts = Counter([r.additive for r in records if r.additive])
    if not additive_counts:
        return None
    
    most_common = additive_counts.most_common(limit)
    
    return {
        'recommended_value': most_common[0][0],  # Most common additive
        'common_values': [item[0] for item in most_common],  # Top additives
        'count': len(records),
        'top_count': most_common[0][1] if most_common else 0,
        'source': 'database_statistics'
    }


def get_top_records_by_confidence(
    db: Session,
    biomolecule_name: Optional[str] = None,
    property_type: str = 'stability',
    limit: int = 3
) -> List[Dict[str, Any]]:
    """Get high-confidence records"""
    query = select(ExtractionRecord).options(
        joinedload(ExtractionRecord.literature)
    ).where(
        ExtractionRecord.property == property_type
    )
    
    if biomolecule_name:
        query = query.where(
            or_(
                ExtractionRecord.protein_name == biomolecule_name,
                ExtractionRecord.protein_name.like(f"%{biomolecule_name}%")
            )
        )
    
    query = query.order_by(ExtractionRecord.confidence.desc())
    
    records = list(db.scalars(query.limit(limit)).unique().all())
    
    result = []
    for record in records:
        record_dict = record.to_dict()
        
        # Add literature information - only from real sources, no auto-generation
        literature_info = None
        
        # First, try from relationship
        if record.literature:
            literature_info = {
                'doi': record.literature.doi,
                'title': record.literature.title,
                'authors': record.literature.authors,
                'pub_year': record.literature.pub_year
            }
        # If no literature relationship, try to extract from full_data
        elif record.full_data:
            full_data = record.full_data if isinstance(record.full_data, dict) else {}
            # Extract from various possible fields (same place as raw_context would be)
            title = full_data.get('title') or full_data.get('source_title') or full_data.get('paper_title')
            authors = full_data.get('authors') or full_data.get('source_authors') or full_data.get('paper_authors')
            pub_year_raw = full_data.get('pub_year') or full_data.get('publication_year') or full_data.get('source_pub_year') or full_data.get('year') or full_data.get('paper_year')
            doi = full_data.get('source_doi') or full_data.get('doi') or full_data.get('paper_doi')
            
            # Convert pub_year to int if it's a string
            pub_year = None
            if pub_year_raw is not None:
                try:
                    if isinstance(pub_year_raw, str):
                        pub_year = int(pub_year_raw.strip())
                    elif isinstance(pub_year_raw, (int, float)):
                        pub_year = int(pub_year_raw)
                except (ValueError, TypeError):
                    pub_year = None
            
            # Create literature info if we have at least one field (not just title)
            # This allows displaying partial metadata even if title is missing
            if title or authors or pub_year or doi:
                literature_info = {
                    'doi': doi,
                    'title': title,
                    'authors': authors,
                    'pub_year': pub_year
                }
        
        # Add literature info if we found any metadata (not just title)
        if literature_info:
            record_dict['literature'] = literature_info
            # Also add fields to top level for easier access
            if literature_info.get('title'):
                record_dict['title'] = literature_info['title']
            if literature_info.get('authors'):
                record_dict['authors'] = literature_info['authors']
            if literature_info.get('pub_year'):
                record_dict['pub_year'] = literature_info['pub_year']
            if literature_info.get('doi'):
                record_dict['doi'] = literature_info['doi']
        
        result.append(record_dict)
    
    return result

