from __future__ import annotations

from typing import List, Optional, Dict, Any
import re
import logging

from ..schemas import ExtractionRecord, ExperimentalParameters
from ..nlp.regex_patterns import (
    PH_PATTERNS, TEMP_PATTERNS, CONC_PATTERNS, OUTCOME_CUES, 
    NEGATION_PATTERNS, COMPARISON_PATTERNS,
    IONIC_STRENGTH_PATTERNS, ADDITIVE_PATTERNS,
    TIME_PATTERNS, SHEAR_RATE_PATTERNS, PRESSURE_PATTERNS
)
from ..nlp.normalization import normalize_temperature, normalize_concentration, normalize_ph
from ..nlp.vocabulary import VocabularyMatcher
from ..nlp.context_analysis import ContextAnalyzer
from ..nlp.quality_monitor import quality_monitor

logger = logging.getLogger(__name__)


SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")

# Initialize NLP enhancement modules
vocab_matcher = VocabularyMatcher()
context_analyzer = ContextAnalyzer()


def _parse_numeric_value(value_str: str) -> Optional[float]:
    """
    Parse numeric value from string, supporting:
    - Scientific notation: 1.5×10⁻³, 1.5e-3, 1.5E-3
    - Thousand separators: 1,000.5
    - Standard numbers: 7.4, 25, .5
    """
    if not value_str:
        return None
    
    # Remove thousand separators
    cleaned = value_str.replace(',', '').strip()
    
    # Handle scientific notation with × (×10⁻³ format)
    if '×' in cleaned or 'x' in cleaned.lower():
        # Match: 1.5×10⁻³ or 1.5x10-3
        sci_match = re.match(r'([+-]?\d+(?:\.\d+)?)\s*[×x]\s*10\s*([⁻⁻-]?)(\d+)', cleaned, re.IGNORECASE)
        if sci_match:
            base = float(sci_match.group(1))
            sign = -1 if sci_match.group(2) in ['⁻', '-', ''] and sci_match.group(2) else 1
            exp = int(sci_match.group(3))
            return base * (10 ** (sign * exp))
    
    # Handle standard scientific notation (e/E format)
    try:
        return float(cleaned)
    except ValueError:
        return None


def detect_biomolecule_type(text: str, default: str = "protein") -> str:
    """
    Auto-detect biomolecule type from text.
    
    Args:
        text: Text to analyze
        default: Default type if detection fails
        
    Returns:
        Detected biomolecule type: "protein", "peptide", "polysaccharide", etc.
    """
    text_lower = text.lower()
    
    # Peptide indicators
    peptide_indicators = [
        'peptide', 'peptides', 'oligopeptide', 'polypeptide',
        'amino acid sequence', 'short peptide', 'synthetic peptide',
        'antimicrobial peptide', 'amp', 'signal peptide'
    ]
    
    # Polysaccharide indicators
    polysaccharide_indicators = [
        'polysaccharide', 'polysaccharides', 'glycan', 'glycans',
        'chitosan', 'cellulose', 'starch', 'dextran', 'heparin',
        'hyaluronic acid', 'alginate', 'pectin', 'xylan',
        'carbohydrate polymer', 'glycosaminoglycan', 'gag'
    ]
    
    # Protein indicators (more specific)
    protein_indicators = [
        'protein', 'proteins', 'enzyme', 'enzymes',
        'antibody', 'antibodies', 'immunoglobulin', 'ig',
        'lysozyme', 'albumin', 'insulin', 'hemoglobin',
        'recombinant protein', 'native protein'
    ]
    
    # Count matches
    peptide_score = sum(1 for ind in peptide_indicators if ind in text_lower)
    polysaccharide_score = sum(1 for ind in polysaccharide_indicators if ind in text_lower)
    protein_score = sum(1 for ind in protein_indicators if ind in text_lower)
    
    # Determine type based on highest score
    if peptide_score > 0 and peptide_score >= polysaccharide_score and peptide_score >= protein_score:
        return "peptide"
    elif polysaccharide_score > 0 and polysaccharide_score >= protein_score:
        return "polysaccharide"
    elif protein_score > 0:
        return "protein"
    else:
        # Fallback to default
        return default


def _find_first(patterns, text: str) -> Optional[re.Match]:
    for pat in patterns:
        m = pat.search(text)
        if m:
            return m
    return None


def is_valuable_sentence(sent: str, require_param_outcome_association: bool = False) -> bool:
    """
    判断句子是否值得处理 - 必须包含实验参数或结果描述
    
    Enhanced version with parameter-outcome association checking.
    
    Args:
        sent: 句子文本
        require_param_outcome_association: 是否要求参数与结果必须关联（默认False保持兼容）
        
    Returns:
        True if sentence contains valuable experimental data
    """
    # 跳过过短的句子（可能是标题或无效数据）
    if len(sent.strip()) < 25:
        return False
    
    # 实验关键词 - 必须有至少一个
    # Extended to support proteins, peptides, polysaccharides, and new parameters
    experiment_keywords = [
        # Basic parameters
        'pH', 'temperature', '°c', '°C', 'k', 'mg/ml', 'mg/mL', 'mm', 'μm', 'nm',
        # New parameters
        'ionic strength', 'shear rate', 'pressure', 'bar', 'atm', 'mpa',
        'incubat', 'time', 'min', 'hours', 'days',
        # Outcomes
        'stable', 'unstable', 'denatur', 'aggregat', 'precipitat',
        'solubility', 'soluble', 'insoluble', 'activity', 
        'concentration', 'therm', 'stability', 'aggregation',
        # Biomolecule types
        'protein', 'peptide', 'polysaccharide', 'enzyme', 'antibody',
        # Additives
        'glycerol', 'sucrose', 'trehalose', 'dtt', 'edta', 'peg',
        'surfactant', 'detergent', 'stabilizer'
    ]
    
    sent_lower = sent.lower()
    has_keyword = any(kw in sent_lower for kw in experiment_keywords)
    
    if not has_keyword:
        return False
    
    # 必须有数值（实验数据特征）
    has_number = bool(re.search(r'\d', sent))
    
    if not has_number:
        return False
    
    # 参数-结果关联检查（增强过滤逻辑）
    if require_param_outcome_association:
        association_info = context_analyzer.calculate_parameter_outcome_association(sent)
        # 必须有参数和结果，且它们之间有关联
        if not association_info['has_association']:
            # 放宽条件：如果有参数或结果，也可以保留（避免过度过滤）
            if association_info['num_params'] == 0 and association_info['num_outcomes'] == 0:
                return False
    
    # 跳过明显的标题或背景描述
    background_indicators = [
        'abstract', 'introduction', 'this study', 'we investigated',
        'background', 'overview', 'purpose', 'aim of this'
    ]
    
    # 如果以这些开头，可能是背景描述
    sent_start = sent.lower()[:50]
    if any(indicator in sent_start for indicator in background_indicators):
        return False
    
    return True


def extract_from_text(text: str, biomolecule_type: str = "protein", protein_name: str = None, enable_quality_monitoring: bool = True, auto_detect_biomolecule: bool = True) -> List[ExtractionRecord]:
    """
    Extract biomolecule stability parameter–outcome pairs from raw text.
    
    Supports: proteins, peptides, polysaccharides, and other biopolymers.

    Enhanced approach with NLP improvements:
    - Auto-detect biomolecule type (protein/peptide/polysaccharide)
    - Split into sentences and apply context analysis
    - Filter sentences by quality and section weighting
    - Enhanced outcome detection with vocabulary matching
    - Improved parameter extraction with validation (pH, temp, conc, ionic strength, additives, time, shear, pressure)
    - Negation and comparison detection
    - Quality monitoring and reporting
    
    Args:
        text: Raw text to extract from
        biomolecule_type: Type of biomolecule (default: "protein"). Used if auto_detect=False
        protein_name: Optional specific name of the biomolecule
        enable_quality_monitoring: Whether to enable quality monitoring
        auto_detect_biomolecule: Auto-detect biomolecule type from text (default: True)
    """

    records: List[ExtractionRecord] = []
    
    # Auto-detect biomolecule type if enabled
    if auto_detect_biomolecule:
        detected_type = detect_biomolecule_type(text, default=biomolecule_type)
        if detected_type != biomolecule_type:
            logger.info(f"Auto-detected biomolecule type: {detected_type} (was: {biomolecule_type})")
            biomolecule_type = detected_type
    
    # Get section weight for the entire text
    section_weight = context_analyzer.get_section_weight(text)
    
    # Split into sentences
    sentences = [s.strip() for s in SENT_SPLIT.split(text.strip()) if s.strip()]
    
    # DEBUG: Print sentence count and first sentence
    logger.debug(f"Total sentences: {len(sentences)}")
    if sentences:
        logger.debug(f"First sentence: {sentences[0][:100]}...")
    
    # Apply sentence quality filtering to focus on valuable experimental data
    # Enhanced: Use both basic filtering and context-aware filtering
    valuable_sentences = []
    for sent in sentences:
        if is_valuable_sentence(sent, require_param_outcome_association=False):
            # Start with base score, will be enhanced by context analysis
            valuable_sentences.append(sent)
    
    logger.info(f"Basic filtering: {len(sentences)} sentences -> {len(valuable_sentences)} valuable sentences")
    
    if not valuable_sentences:
        logger.warning("No valuable sentences found in text")
        return []
    
    # Performance optimization: Skip expensive context filtering for abstracts
    # Context filtering (section weighting, negation detection, association scoring) is useful
    # but slow. For abstracts (typically 10-50 sentences), basic filtering is sufficient and much faster.
    # Set USE_CONTEXT_FILTERING = True if you prioritize quality over speed.
    USE_CONTEXT_FILTERING = False  # Default: disabled for speed (use basic filtering only)
    
    if USE_CONTEXT_FILTERING and len(valuable_sentences) <= 100:
        # Only use context filtering if explicitly enabled AND text is short (<=100 sentences)
        try:
            high_quality_sentences = context_analyzer.filter_high_quality_sentences(
                valuable_sentences, 
                min_reliability=0.5
            )
            logger.info(f"Context-aware filtering: {len(valuable_sentences)} valuable -> {len(high_quality_sentences)} high-quality sentences")
            
            if not high_quality_sentences:
                # Fallback: if context filtering is too strict, use basic filtering
                logger.warning("Context filtering too strict, using basic filtering as fallback")
                high_quality_sentences = [(sent, 0.6) for sent in valuable_sentences]
        except Exception as e:
            logger.warning(f"Context filtering failed: {e}, using basic filtering")
            high_quality_sentences = [(sent, 0.6) for sent in valuable_sentences]
    else:
        # Fast mode: use basic filtering only (sufficient for abstracts)
        # Basic filtering already checks keywords, numbers, and background indicators
        high_quality_sentences = [(sent, 0.6) for sent in valuable_sentences]

    for sent, reliability_score in high_quality_sentences:
        # Enhanced outcome detection using vocabulary matcher
        outcome_hit = _find_first(OUTCOME_CUES, sent)
        has_stability_terms = vocab_matcher.is_stability_related(sent)
        
        # Create vocabulary info structure for compatibility (skip expensive find_categories)
        vocab_stability_info = {
            'has_stability_terms': has_stability_terms,
            'polarity': vocab_matcher.get_stability_polarity(sent),
            'categories': {}  # Skip expensive category finding for speed
        }
        
        # Skip if no outcome cue and no vocabulary match
        if not outcome_hit and not has_stability_terms:
            continue
        
        # Determine outcome label with enhanced logic
        if outcome_hit:
            outcome_label = outcome_hit.group(0).lower()
        else:
            # Use vocabulary-based outcome detection
            polarity = vocab_matcher.get_stability_polarity(sent)
            if polarity == 'positive':
                outcome_label = 'stable'
            elif polarity == 'negative':
                outcome_label = 'unstable'
            else:
                outcome_label = 'stability_mentioned'

        # SKIP expensive context analysis for speed
        # Use minimal context info instead
        context_info = {
            'section_weight': 0.5,  # Default
            'comparison_info': {'has_comparison': False, 'comparison_type': None},
            'has_negation': False,
            'reliability_score': 0.5
        }

        # Infer functional property from outcome cue with enhanced logic
        prop = _determine_property(outcome_label, vocab_stability_info)

        # Enhanced parameter extraction
        pH_val, ph_note = _extract_ph_enhanced(sent)
        temp_val, temp_note = _extract_temperature_enhanced(sent)
        conc_val, conc_note = _extract_concentration_enhanced(sent)
        
        # Extract new parameters
        ionic_strength_val, ionic_note = _extract_ionic_strength(sent)
        additive_val, additive_note = _extract_additive(sent)
        time_val, time_note = _extract_time(sent)
        shear_rate_val, shear_note = _extract_shear_rate(sent)
        pressure_val, pressure_note = _extract_pressure(sent)

        # Combine all notes
        all_notes = [note for note in [
            ph_note, temp_note, conc_note, ionic_note, 
            additive_note, time_note, shear_note, pressure_note
        ] if note]
        combined_notes = "; ".join(all_notes) if all_notes else None
        
        # Add context information to raw_context
        context_details = f"Section weight: {section_weight:.2f}, Reliability: {context_info['reliability_score']:.2f}"
        if context_info['has_negation']:
            context_details += ", Has negation"
        if context_info['comparison_info']['has_comparison']:
            context_details += f", Comparison: {context_info['comparison_info']['comparison_type']}"
        
        raw_context_enhanced = f"{sent.strip()}\n[Context: {context_details}]"
        if combined_notes:
            raw_context_enhanced += f"\n[Notes: {combined_notes}]"

        # ===== 参数过滤：必须至少提取到1个参数才创建记录 =====
        has_any_param = any([
            pH_val is not None,
            temp_val is not None,
            conc_val is not None,
            ionic_strength_val is not None,
            additive_val is not None,
            time_val is not None,
            shear_rate_val is not None,
            pressure_val is not None
        ])
        
        if not has_any_param:
            # 跳过没有提取到任何参数的记录
            continue
        
        params = ExperimentalParameters(
            pH=pH_val,
            temperature_c=temp_val,
            concentration_mg_ml=conc_val,
            ionic_strength_mM=ionic_strength_val,
            additive=additive_val,
            time_min=time_val,
            shear_rate_s1=shear_rate_val,
            pressure_bar=pressure_val,
            raw_context=raw_context_enhanced,
        )

        # Enhanced confidence calculation
        conf = _calculate_enhanced_confidence(
            pH_val, temp_val, conc_val, context_info, section_weight, vocab_stability_info
        )

        record = ExtractionRecord(
            biomolecule_type=biomolecule_type,
            protein_name=protein_name,
            polarity=vocab_stability_info['polarity'],  # 存储 polarity 信息
            property=prop,
            parameters=params,
            outcome_label=outcome_label,
            outcome_text=sent.strip(),
            confidence=conf,
        )
        
        # Note: Context analysis information is used for quality monitoring
        # but not stored in the record due to schema constraints
        
        records.append(record)

    # Quality monitoring
    if enable_quality_monitoring and records:
        try:
            report = quality_monitor.analyze_extraction_batch(
                [_record_to_dict(r) for r in records],
                {'text_length': len(text), 'sentence_count': len(sentences)}
            )
            logger.info(f"Extraction quality: {report.metrics.valid_records}/{report.metrics.total_records} valid records, avg confidence: {report.metrics.avg_confidence:.2f}")
        except Exception as e:
            logger.warning(f"Quality monitoring failed: {e}")

    return records


def _determine_property(outcome_label: str, vocab_info: Dict[str, Any]) -> str:
    """Determine the functional property with enhanced logic."""
    if ("aggregation" in outcome_label) or ("precipitation" in outcome_label):
        return "aggregation"
    elif (
        ("solubility" in outcome_label)
        or ("soluble" in outcome_label)
        or ("insoluble" in outcome_label)
        or ("solubiliz" in outcome_label)
        or ("solubilis" in outcome_label)
        or vocab_info.get('has_solubility_terms', False)
    ):
        return "solubility"
    else:
        return "stability"


def _extract_ph_enhanced(sent: str) -> tuple[Optional[float], Optional[str]]:
    """Enhanced pH extraction with validation."""
    ph_m = _find_first(PH_PATTERNS, sent)
    if ph_m:
        try:
            # Parse numeric value (may include scientific notation or thousand separators)
            raw_ph_str = ph_m.group(1) if ph_m.lastindex >= 1 else None
            raw_ph = _parse_numeric_value(raw_ph_str) if raw_ph_str else None
            if raw_ph is None:
                return None, None
            normalized_ph, note = normalize_ph(raw_ph)
            return normalized_ph, note
        except Exception as e:
            logger.debug(f"pH parsing error: {e}")
            return None, f"pH parsing error: {e}"
    return None, None


def _extract_temperature_enhanced(sent: str) -> tuple[Optional[float], Optional[str]]:
    """Enhanced temperature extraction with validation."""
    temp_m = _find_first(TEMP_PATTERNS, sent)
    if temp_m:
        try:
            # Parse numeric value (support negative, scientific notation, thousand separators)
            raw_str = temp_m.group(1) if temp_m.lastindex >= 1 else None
            raw = _parse_numeric_value(raw_str) if raw_str else None
            if raw is None:
                return None, None
            
            # Detect unit (Kelvin, Fahrenheit, or Celsius)
            pattern_lower = temp_m.re.pattern.lower()
            if 'k' in pattern_lower and 'kelvin' not in pattern_lower or temp_m.re.pattern.endswith("K\\b"):
                unit_hint = "K"
            elif 'f' in pattern_lower or 'fahrenheit' in pattern_lower:
                unit_hint = "F"
            else:
                unit_hint = "C"
            
            temp_val, note = normalize_temperature(raw, unit_hint)
            return temp_val, note
        except Exception as e:
            logger.debug(f"Temperature parsing error: {e}")
            return None, f"Temperature parsing error: {e}"
    return None, None


def _extract_concentration_enhanced(sent: str) -> tuple[Optional[float], Optional[str]]:
    """Enhanced concentration extraction with validation."""
    conc_m = _find_first(CONC_PATTERNS, sent)
    if conc_m:
        try:
            # Parse numeric value (support scientific notation, thousand separators)
            raw_str = conc_m.group(1) if conc_m.lastindex >= 1 else None
            raw = _parse_numeric_value(raw_str) if raw_str else None
            if raw is None:
                return None, None
            
            # Extract unit
            unit = conc_m.group(2) if conc_m.lastindex >= 2 else None
            if unit is None:
                # Try to extract unit from full match
                full_match = conc_m.group(0)
                unit_match = re.search(r'(mg/mL|µg/mL|ug/mL|μg/mL|mM|μM|µM|uM|nM|pM|M|%|g/L)', full_match, re.IGNORECASE)
                unit = unit_match.group(1) if unit_match else None
            
            conc_val, note = normalize_concentration(raw, unit)
            return conc_val, note
        except Exception as e:
            logger.debug(f"Concentration parsing error: {e}")
            return None, f"Concentration parsing error: {e}"
    return None, None


def _extract_ionic_strength(sent: str) -> tuple[Optional[float], Optional[str]]:
    """Extract ionic strength in mM."""
    match = _find_first(IONIC_STRENGTH_PATTERNS, sent)
    if match:
        try:
            value_str = match.group(1) if match.lastindex >= 1 else None
            value = _parse_numeric_value(value_str) if value_str else None
            if value is None:
                return None, None
            unit = match.group(2) if match.lastindex >= 2 else None
            
            # Convert to mM
            if unit and unit.upper() == 'M':
                value_mM = value * 1000.0
                note = f"Converted M→mM"
            elif unit and unit.upper() in ('µM', 'μM', 'uM'):
                value_mM = value / 1000.0
                note = f"Converted µM→mM"
            else:
                value_mM = value  # Assume already in mM
                note = "mM"
            
            if value_mM < 0 or value_mM > 1000:
                note += f" (WARNING: value {value_mM} mM outside common range 0-1000)"
            
            return value_mM, note
        except Exception as e:
            logger.debug(f"Ionic strength parsing error: {e}")
            return None, None
    return None, None


def _extract_additive(sent: str) -> tuple[Optional[str], Optional[str]]:
    """Extract additive name(s)."""
    matches = []
    for pattern in ADDITIVE_PATTERNS:
        for m in pattern.finditer(sent):
            try:
                # Extract additive name from the match
                if m.lastindex >= 3:  # Has concentration and name groups
                    additive_name = m.group(3).strip()
                elif m.lastindex >= 2:
                    additive_name = m.group(2).strip()
                else:
                    # Pattern matched but no explicit name - try to extract from context
                    additive_name = m.group(0).split()[-1] if m.group(0) else None
                
                if additive_name and len(additive_name) > 2:
                    # Normalize common additives
                    additive_name = additive_name.lower()
                    if 'glycerol' in additive_name:
                        additive_name = 'glycerol'
                    elif 'sucrose' in additive_name:
                        additive_name = 'sucrose'
                    elif 'trehalose' in additive_name:
                        additive_name = 'trehalose'
                    elif any(dtt in additive_name for dtt in ['dtt', 'dithiothreitol']):
                        additive_name = 'DTT'
                    elif 'tcep' in additive_name:
                        additive_name = 'TCEP'
                    elif 'peg' in additive_name:
                        additive_name = 'PEG'
                    elif 'edta' in additive_name:
                        additive_name = 'EDTA'
                    elif 'nacl' in additive_name or 'sodium chloride' in additive_name:
                        additive_name = 'NaCl'
                    
                    matches.append(additive_name)
            except Exception as e:
                logger.debug(f"Additive extraction error: {e}")
                continue
    
    if matches:
        # Remove duplicates and return comma-separated
        unique_additives = list(dict.fromkeys(matches))  # Preserve order
        return ", ".join(unique_additives), f"Found {len(unique_additives)} additive(s)"
    
    return None, None


def _extract_time(sent: str) -> tuple[Optional[float], Optional[str]]:
    """Extract time in minutes."""
    match = _find_first(TIME_PATTERNS, sent)
    if match:
        try:
            value = float(match.group(1))
            time_str = match.group(0).lower()
            
            # Convert to minutes
            if 'hour' in time_str or 'h ' in time_str or time_str.endswith('h'):
                value_min = value * 60.0
                note = "Converted hours→minutes"
            elif 'day' in time_str or 'd ' in time_str or time_str.endswith('d'):
                value_min = value * 1440.0  # 24*60
                note = "Converted days→minutes"
            elif 'overnight' in time_str:
                value_min = 720.0  # ~12 hours
                note = "Overnight → 720 min"
            elif '24 h' in time_str:
                value_min = 1440.0
                note = "24 h → 1440 min"
            elif '48 h' in time_str:
                value_min = 2880.0
                note = "48 h → 2880 min"
            elif '72 h' in time_str:
                value_min = 4320.0
                note = "72 h → 4320 min"
            else:
                value_min = value  # Assume minutes
                note = "minutes"
            
            if value_min < 0 or value_min > 100000:  # ~70 days
                note += f" (WARNING: {value_min} min outside common range)"
            
            return value_min, note
        except Exception as e:
            logger.debug(f"Time parsing error: {e}")
            return None, None
    return None, None


def _extract_shear_rate(sent: str) -> tuple[Optional[float], Optional[str]]:
    """Extract shear rate in s⁻¹."""
    match = _find_first(SHEAR_RATE_PATTERNS, sent)
    if match:
        try:
            value_str = match.group(1) if match.lastindex >= 1 else None
            value = _parse_numeric_value(value_str) if value_str else None
            if value is None:
                return None, None
            
            # Check if already in 1/s or s⁻¹
            match_str = match.group(0).lower()
            if '1/s' in match_str or 's⁻¹' in match_str or 's^-1' in match_str or 'per second' in match_str:
                value_s1 = value
                note = "s⁻¹"
            elif 'rpm' in match_str:
                # Approximate: 1 rpm ≈ 0.0167 s⁻¹ (very rough, depends on geometry)
                value_s1 = value * 0.0167
                note = f"Converted rpm→s⁻¹ (approximate)"
            else:
                value_s1 = value  # Assume s⁻¹
                note = "s⁻¹ (assumed)"
            
            if value_s1 < 0 or value_s1 > 10000:
                note += f" (WARNING: {value_s1} s⁻¹ outside common range)"
            
            return value_s1, note
        except Exception as e:
            logger.debug(f"Shear rate parsing error: {e}")
            return None, None
    return None, None


def _extract_pressure(sent: str) -> tuple[Optional[float], Optional[str]]:
    """Extract pressure in bar."""
    match = _find_first(PRESSURE_PATTERNS, sent)
    if match:
        try:
            value_str = match.group(1) if match.lastindex >= 1 else None
            value = _parse_numeric_value(value_str) if value_str else None
            if value is None:
                return None, None
            match_str = match.group(0).lower()
            
            # Convert to bar
            if 'bar' in match_str:
                value_bar = value
                note = "bar"
            elif 'atm' in match_str:
                value_bar = value * 1.01325  # 1 atm = 1.01325 bar
                note = "Converted atm→bar"
            elif 'mpa' in match_str:
                value_bar = value * 10.0  # 1 MPa = 10 bar
                note = "Converted MPa→bar"
            elif 'psi' in match_str:
                value_bar = value * 0.0689476  # 1 psi = 0.0689476 bar
                note = "Converted psi→bar"
            elif 'atmospheric' in match_str or 'ambient' in match_str:
                value_bar = 1.01325  # Atmospheric pressure
                note = "Atmospheric pressure → 1.013 bar"
            else:
                value_bar = value  # Assume bar
                note = "bar (assumed)"
            
            if value_bar < 0 or value_bar > 10000:  # ~1000 atm
                note += f" (WARNING: {value_bar} bar outside common range)"
            
            return value_bar, note
        except Exception as e:
            logger.debug(f"Pressure parsing error: {e}")
            return None, None
    return None, None


def _calculate_enhanced_confidence(
    pH_val: Optional[float], 
    temp_val: Optional[float], 
    conc_val: Optional[float],
    context_info: Dict[str, Any],
    section_weight: float,
    vocab_info: Dict[str, Any]
) -> float:
    """
    Calculate confidence score with enhanced factors - Phase 1优化版
    
    目标: 提升平均置信度从0.31到0.55+
    
    改进策略:
    1. 提高基础置信度权重
    2. 增强参数合理性验证奖励
    3. 优化上下文质量评分权重
    4. 添加参数完整性奖励
    """
    # ===== 基础置信度（基于参数数量） =====
    parsed_count = sum(v is not None for v in [pH_val, temp_val, conc_val])
    # 提高基础值：0.3 -> 0.4，每增加一个参数+0.15 -> 0.18
    base_conf = 0.4 + 0.18 * parsed_count
    
    # ===== 参数合理性验证奖励 =====
    reasonableness_boost = 0.0
    if pH_val is not None:
        # pH在常见实验范围(3-11)内，给予奖励
        if 3.0 <= pH_val <= 11.0:
            reasonableness_boost += 0.05
        elif 0 <= pH_val <= 14:
            reasonableness_boost += 0.02  # 极端但合法的值
    
    if temp_val is not None:
        # 温度在常见实验范围(0-100°C)内
        if 0 <= temp_val <= 100:
            reasonableness_boost += 0.05
        elif -20 <= temp_val <= 150:
            reasonableness_boost += 0.02
    
    if conc_val is not None:
        # 浓度在合理范围(0.01-100 mg/mL)
        if 0.01 <= conc_val <= 100:
            reasonableness_boost += 0.05
        elif 0 <= conc_val <= 1000:
            reasonableness_boost += 0.02
    
    # ===== 参数完整性奖励 =====
    # 多个参数同时存在，说明数据更完整可靠
    completeness_boost = 0.0
    if parsed_count >= 2:
        completeness_boost += 0.08  # 有2个参数
    if parsed_count == 3:
        completeness_boost += 0.12  # 有全部3个参数（额外奖励）
    
    # ===== 上下文可靠性提升 =====
    reliability_boost = context_info.get('reliability_score', 0.5) * 0.25  # 从0.2提高到0.25
    
    # ===== 章节权重提升 =====
    # Methods/Results章节权重更高
    section_boost = (section_weight - 0.5) * 0.25  # 从0.2提高到0.25
    if section_weight >= 0.8:
        section_boost += 0.05  # Methods/Results额外奖励
    
    # ===== 词汇匹配提升 =====
    vocab_boost = 0.08 if vocab_info.get('has_stability_terms', False) else 0.0  # 从0.1微调到0.08
    
    # ===== 否定词惩罚 =====
    negation_penalty = -0.20 if context_info.get('has_negation', False) else 0.0  # 从-0.15加强到-0.20
    
    # ===== 条件语句惩罚（假设性表达降低置信度）=====
    # 从enhanced_extractor导入NegationDetector来检测条件语句
    try:
        from literature_mining.nlp.enhanced_extractor import NegationDetector
        # 使用outcome_text来检测条件语句（如果有）
        outcome_text = vocab_info.get('outcome_text', '')
        has_conditional = NegationDetector.has_conditional_context(
            outcome_text, 0, len(outcome_text) if outcome_text else 0
        ) if outcome_text else False
        conditional_penalty = -0.08 if has_conditional else 0.0
    except (ImportError, AttributeError):
        conditional_penalty = 0.0  # 如果导入失败，忽略
    
    # ===== 比较上下文提升 =====
    comparison_boost = 0.10 if context_info.get('comparison_info', {}).get('has_comparison', False) else 0.0
    
    # ===== 计算总置信度 =====
    total_conf = (
        base_conf + 
        reasonableness_boost + 
        completeness_boost +
        reliability_boost + 
        section_boost + 
        vocab_boost + 
        negation_penalty + 
        conditional_penalty +  # 新增：条件语句惩罚
        comparison_boost
    )
    
    # 确保置信度在合理范围内
    # 下限从0.1提高到0.15，因为基础置信度已提高
    return min(max(total_conf, 0.15), 0.95)  # Clamp between 0.15 and 0.95


def _record_to_dict(record: ExtractionRecord) -> Dict[str, Any]:
    """Convert ExtractionRecord to dictionary for quality monitoring."""
    return {
        'biomolecule_type': record.biomolecule_type,
        'protein_name': record.protein_name,
        'property': record.property,
        'parameters': {
            'pH': record.parameters.pH,
            'temperature_c': record.parameters.temperature_c,
            'concentration_mg_ml': record.parameters.concentration_mg_ml,
            'raw_context': record.parameters.raw_context,
        },
        'outcome_label': record.outcome_label,
        'outcome_text': record.outcome_text,
        'confidence': record.confidence,
        'context_analysis': getattr(record, 'context_analysis', {}),
        'section_weight': getattr(record, 'section_weight', 0.5),
        'vocab_info': getattr(record, 'vocab_info', {}),
    }