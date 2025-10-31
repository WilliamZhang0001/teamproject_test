"""
文献数据库模型
存储从文献中提取的实验参数信息
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Float, Integer, Text, DateTime, JSON
from app.core.db import Base


class Literature(Base):
    """文献表"""
    __tablename__ = "literature"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    authors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pub_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 关联到提取记录
    extraction_records: Mapped[list["ExtractionRecord"]] = relationship(
        "ExtractionRecord", back_populates="literature", cascade="all, delete-orphan"
    )


class ExtractionRecord(Base):
    """文献提取记录表 - 存储实验参数和结果"""
    __tablename__ = "extraction_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 文献关联
    literature_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    
    # 生物分子信息
    biomolecule_type: Mapped[str] = mapped_column(String(64), nullable=False, default="protein", index=True)
    protein_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    polarity: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    property: Mapped[str] = mapped_column(String(64), nullable=False, default="stability")
    
    # 实验参数
    pH: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temperature_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    concentration_mg_ml: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ionic_strength_mM: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    additive: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    shear_rate_s1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pressure_bar: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # 结果信息
    outcome_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    outcome_label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    outcome_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_section: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # 元数据
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5, index=True)
    raw_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 存储完整的JSON数据用于检索
    full_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 关联到文献
    literature: Mapped[Optional["Literature"]] = relationship(
        "Literature", back_populates="extraction_records"
    )
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'literature_id': self.literature_id,
            'biomolecule_type': self.biomolecule_type,
            'protein_name': self.protein_name,
            'polarity': self.polarity,
            'property': self.property,
            'parameters': {
                'pH': self.pH,
                'temperature_c': self.temperature_c,
                'concentration_mg_ml': self.concentration_mg_ml,
                'ionic_strength_mM': self.ionic_strength_mM,
                'additive': self.additive,
                'time_min': self.time_min,
                'shear_rate_s1': self.shear_rate_s1,
                'pressure_bar': self.pressure_bar,
                'raw_context': self.raw_context
            },
            'outcome_score': self.outcome_score,
            'outcome_label': self.outcome_label,
            'outcome_text': self.outcome_text,
            'source_section': self.source_section,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'full_data': self.full_data
        }

