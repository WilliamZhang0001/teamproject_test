from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class ExperimentalParameters(BaseModel):
    """
    Normalized experimental parameters - Extended version
    
    Supports comprehensive orthogonal parameters for DoE:
    - pH: unitless acidity measure (0-14)
    - temperature_c: temperature in Celsius
    - concentration_mg_ml: mass concentration in mg/mL
    - ionic_strength_mM: ionic strength in millimolar (mM)
    - additive: additive name(s) as string
    - time_min: incubation/storage time in minutes
    - shear_rate_s1: shear rate in per second (1/s or s⁻¹)
    - pressure_bar: pressure in bar
    - raw_context: original text context for provenance
    """

    pH: Optional[float] = Field(default=None, ge=0.0, le=14.0)
    temperature_c: Optional[float] = Field(default=None)
    concentration_mg_ml: Optional[float] = Field(default=None, ge=0.0)
    ionic_strength_mM: Optional[float] = Field(default=None, ge=0.0, description="Ionic strength in mM")
    additive: Optional[str] = Field(default=None, description="Additive names (comma-separated if multiple)")
    time_min: Optional[float] = Field(default=None, ge=0.0, description="Time in minutes")
    shear_rate_s1: Optional[float] = Field(default=None, ge=0.0, description="Shear rate in s⁻¹")
    pressure_bar: Optional[float] = Field(default=None, ge=0.0, description="Pressure in bar")
    raw_context: Optional[str] = None


class ExtractionRecord(BaseModel):
    """Structured parameter–outcome pair extracted from literature.

    Attributes
    ----------
    biomolecule_type: e.g., "protein", "peptide", "polysaccharide".
    protein_name: Specific protein name (e.g., "lysozyme", "insulin").
    property: Functional property, phase-1 uses "stability".
    parameters: Normalized experimental parameters.
    outcome_score: Optional numerical score (e.g., relative stability index).
    outcome_label: Optional categorical label (e.g., "stable", "aggregation").
    source_doi: Optional DOI string.
    source_section: Optional section hint (e.g., "Results").
    outcome_text: Raw text snippet supporting the extraction.
    confidence: Heuristic confidence score [0, 1].
    """

    biomolecule_type: str = Field(default="protein")
    protein_name: Optional[str] = None  # 兼容字段：实际可存储protein/peptide/polysaccharide名称
    polarity: Optional[str] = None  # 'positive', 'negative', 'mixed', 'neutral'
    property: str = Field(default="stability")
    parameters: ExperimentalParameters
    outcome_score: Optional[float] = None
    outcome_label: Optional[str] = None
    outcome_text: Optional[str] = None
    source_doi: Optional[str] = None
    source_section: Optional[str] = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)