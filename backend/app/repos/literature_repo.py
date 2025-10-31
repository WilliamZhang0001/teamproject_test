"""
Literature Database Access Layer
"""
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, and_
from typing import List, Optional, Dict, Any
from app.models.literature import Literature, ExtractionRecord


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
    # Build query
    query = select(ExtractionRecord).where(
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
    candidates = list(db.scalars(query).all())
    
    if not candidates:
        return []
    
    # Calculate similarity scores and sort
    scored_records = []
    for record in candidates:
        similarity_score = calculate_similarity(target_params, record)
        if similarity_score > 0:  # Only return records with similarity
            record_dict = record.to_dict()
            record_dict['similarity_score'] = similarity_score
            # Add literature information
            if record.literature:
                record_dict['literature'] = {
                    'doi': record.literature.doi,
                    'title': record.literature.title,
                    'authors': record.literature.authors,
                    'pub_year': record.literature.pub_year
                }
            scored_records.append(record_dict)
    
    # Sort by similarity and return Top K
    scored_records.sort(key=lambda x: x['similarity_score'], reverse=True)
    return scored_records[:limit]


def calculate_similarity(target_params: Dict[str, Any], record: ExtractionRecord) -> float:
    """
    Calculate parameter similarity score
    
    Uses inverse of weighted Euclidean distance as similarity
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
    
    total_weight = 0.0
    weighted_distance = 0.0
    
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
    
    for param, weight in param_weights.items():
        target_val = target_params.get(param)
        record_val = record_params.get(param)
        
        # 如果两者都有值，计算归一化距离
        if target_val is not None and record_val is not None:
            # 归一化距离
            distance = abs(target_val - record_val)
            # 使用合理的范围进行归一化
            ranges = {
                'pH': 14.0,
                'temperature_c': 80.0,
                'concentration_mg_ml': 100.0,
                'ionic_strength_mM': 200.0,
                'time_min': 1440.0,  # 24小时
                'shear_rate_s1': 1000.0,
                'pressure_bar': 10.0
            }
            
            if param in ranges:
                normalized_distance = distance / ranges[param]
            else:
                normalized_distance = min(distance / (abs(record_val) + 1), 1.0)
            
            weighted_distance += weight * normalized_distance
            total_weight += weight
        
        # 对于additive等字符串字段，做简单的匹配
        elif param == 'additive' and target_val and record_val:
            if str(target_val).lower() == str(record_val).lower():
                weighted_distance += 0  # 完全匹配
            else:
                weighted_distance += weight  # 不匹配
            total_weight += weight
    
    # 如果有任何匹配的参数
    if total_weight == 0:
        return 0.0
    
    # 计算相似度分数 (1 - 归一化距离)
    similarity = 1.0 - (weighted_distance / total_weight)
    
    # 应用置信度权重
    similarity *= record.confidence
    
    return max(0.0, similarity)


def get_top_records_by_confidence(
    db: Session,
    biomolecule_name: Optional[str] = None,
    property_type: str = 'stability',
    limit: int = 3
) -> List[Dict[str, Any]]:
    """Get high-confidence records"""
    query = select(ExtractionRecord).where(
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
    
    records = list(db.scalars(query.limit(limit)).all())
    
    result = []
    for record in records:
        record_dict = record.to_dict()
        if record.literature:
            record_dict['literature'] = {
                'doi': record.literature.doi,
                'title': record.literature.title,
                'authors': record.literature.authors,
                'pub_year': record.literature.pub_year
            }
        result.append(record_dict)
    
    return result

