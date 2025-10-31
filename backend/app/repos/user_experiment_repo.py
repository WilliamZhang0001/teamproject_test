"""
User Experiment Record Database Access Layer
"""
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Dict, Any, Optional
import json
from app.models.user_experiment import UserExperimentRecord


def create_experiment_record(db: Session, record_data: Dict[str, Any]) -> UserExperimentRecord:
    """Create experiment record"""
    record = UserExperimentRecord(
        user_id=record_data.get('user_id'),
        biomolecule_type=record_data.get('biomolecule_type'),
        biomolecule_name=record_data.get('biomolecule_name'),
        experiment_type=record_data.get('experiment_type', 'stability'),
        input_pH=record_data.get('input_pH'),
        input_temperature_c=record_data.get('input_temperature_c'),
        input_concentration_mg_ml=record_data.get('input_concentration_mg_ml'),
        input_ionic_strength_mM=record_data.get('input_ionic_strength_mM'),
        input_additive=record_data.get('input_additive'),
        input_time_min=record_data.get('input_time_min'),
        input_shear_rate_s1=record_data.get('input_shear_rate_s1'),
        input_pressure_bar=record_data.get('input_pressure_bar'),
        prediction_type=record_data.get('prediction_type'),
        prediction_result=json.dumps(record_data.get('prediction_result'), ensure_ascii=False) if record_data.get('prediction_result') else None,
        confidence=record_data.get('confidence'),
        recommended_literature=json.dumps(record_data.get('recommended_literature'), ensure_ascii=False) if record_data.get('recommended_literature') else None
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_user_experiments(
    db: Session,
    user_id: Optional[int] = None,
    limit: int = 100
) -> List[UserExperimentRecord]:
    """Get user's experiment records"""
    query = select(UserExperimentRecord)
    
    if user_id:
        query = query.where(UserExperimentRecord.user_id == user_id)
    
    query = query.order_by(UserExperimentRecord.created_at.desc())
    query = query.limit(limit)
    
    return list(db.scalars(query).all())


def get_experiment_by_id(db: Session, experiment_id: int) -> Optional[UserExperimentRecord]:
    """Get experiment record by ID"""
    return db.scalar(select(UserExperimentRecord).where(UserExperimentRecord.id == experiment_id))

