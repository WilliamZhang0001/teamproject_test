"""
User Experiment Record Model
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Float, Integer, Text, DateTime, ForeignKey
from backend.app.core.db import Base

if TYPE_CHECKING:
    from .user import AppUser


class UserExperimentRecord(Base):
    """User Experiment Prediction Record Table"""
    __tablename__ = "user_experiment_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # User relationship
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("app_user.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Basic information
    biomolecule_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    biomolecule_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    experiment_type: Mapped[str] = mapped_column(String(64), nullable=False, default="stability", index=True)
    
    # 8 user input parameters
    input_pH: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    input_temperature_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    input_concentration_mg_ml: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    input_ionic_strength_mM: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    input_additive: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    input_time_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    input_shear_rate_s1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    input_pressure_bar: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Prediction results
    prediction_type: Mapped[str] = mapped_column(String(32), nullable=False)  # 'classification' or 'parameter_prediction'
    prediction_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON format
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Recommended literature (Top K)
    recommended_literature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON format
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationship to user
    user: Mapped[Optional["AppUser"]] = relationship("AppUser", back_populates="experiment_records")
    
    def to_dict(self) -> dict:
        """Convert to dictionary format"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'biomolecule_type': self.biomolecule_type,
            'biomolecule_name': self.biomolecule_name,
            'experiment_type': self.experiment_type,
            'input_parameters': {
                'pH': self.input_pH,
                'temperature_c': self.input_temperature_c,
                'concentration_mg_ml': self.input_concentration_mg_ml,
                'ionic_strength_mM': self.input_ionic_strength_mM,
                'additive': self.input_additive,
                'time_min': self.input_time_min,
                'shear_rate_s1': self.input_shear_rate_s1,
                'pressure_bar': self.input_pressure_bar
            },
            'prediction_type': self.prediction_type,
            'prediction_result': self.prediction_result,
            'confidence': self.confidence,
            'recommended_literature': self.recommended_literature,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

