from __future__ import annotations

from typing import List, Optional, Dict, Any, Tuple
import re

import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification

from ..schemas import ExtractionRecord, ExperimentalParameters
from .normalization_transfer import normalize_ph, normalize_temperature, normalize_concentration
from .regex_patterns import PH_PATTERNS, TEMP_PATTERNS, CONC_PATTERNS


SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _find_number(text: str) -> Optional[float]:
    m = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


def _find_unit(text: str) -> Optional[str]:
    t = text.lower()
    if re.search(r"mg\s*/\s*m(?:l)?|mg\s*m(?:l)?\s*(?:-1|\^?-1)|mg\s*per\s*m(?:l)?|mg\s*·?\s*m(?:l)?\s*-?1", t):
        return "mg/mL"
    if re.search(r"(?:µ|μ|u|mcg)g\s*/\s*m(?:l)?|(?:µ|μ|u|mcg)g\s*m(?:l)?\s*(?:-1|\^?-1)", t):
        return "µg/mL"
    if re.search(r"ng\s*/\s*m(?:l)?|ng\s*m(?:l)?\s*(?:-1|\^?-1)", t):
        return "ng/mL"
    if re.search(r"g\s*/\s*l", t):
        return "g/L"
    if re.search(r"mg\s*/\s*l", t):
        return "mg/L"
    if re.search(r"g\s*/\s*dl", t):
        return "g/dL"
    if re.search(r"mg\s*/\s*dl", t):
        return "mg/dL"
    if re.search(r"mg\s*/\s*(?:µ|u)l", t):
        return "mg/µL"
    if re.search(r"\bmol\s*/\s*l\b|\bmol\s*l-1\b|\bmol\s*dm-3\b", t):
        return "M"
    if re.search(r"\bmmol\s*/\s*l\b|\bmmol\s*l-1\b|\bmmol\s*dm-3\b|\bmmolar\b", t):
        return "mM"
    if re.search(r"(?:µ|μ|u)mol\s*/\s*l|(?:µ|μ|u)mol\s*l-1|(?:µ|μ|u)mol\s*dm-3", t):
        return "µM"
    if re.search(r"\bnmol\s*/\s*l\b|\bnmol\s*l-1\b|\bnmol\s*dm-3\b|\bnm\b", t):
        return "nM"
    if re.search(r"\bpmol\s*/\s*l\b|\bpmol\s*l-1\b|\bpmol\s*dm-3\b|\bpm\b", t):
        return "pM"
    if "%" in text:
        return "%"
    if "°c" in t or re.search(r"\b\d+\s*c\b", t):
        return "°C"
    if "kelvin" in t or re.search(r"\bk\b", t):
        return "K"
    if "fahrenheit" in t or re.search(r"\bf\b", t):
        return "F"
    if re.search(r"\bmpa\b", t):
        return "MPa"
    if re.search(r"\bbar\b", t):
        return "bar"
    if re.search(r"\bpa\b", t):
        return "Pa"
    return None


def _normalize_ionic_strength(value: float, unit: Optional[str]) -> Optional[float]:
    if unit is None:
        return value
    u = unit.lower()
    if u == "m":
        return value * 1000.0
    if u == "mm":
        return value
    if u in {"µm", "um", "μm"}:
        return value / 1000.0
    return value


def _normalize_pressure_bar(value: float, unit: Optional[str]) -> Optional[float]:
    if unit is None:
        return value
    u = unit.lower()
    if u == "mpa":
        return value * 10.0
    if u == "bar":
        return value
    if u == "pa":
        return value / 100000.0
    return value


def _span_value_and_unit(label: str, span_text: str) -> Tuple[Optional[float], Optional[str]]:
    v = _find_number(span_text)
    unit = _find_unit(span_text)
    if label in {"PH_VALUE", "pH", "PH"}:
        return v, None
    if label in {"TEMP", "TEMPERATURE", "TEMP_VALUE"}:
        return v, unit
    if label in {"CONC", "CONCENTRATION", "CONC_VALUE"}:
        return v, unit
    if label in {"IONIC_STRENGTH", "IONIC"}:
        return v, unit
    if label in {"PRESSURE"}:
        return v, unit
    if label in {"TIME"}:
        return v, unit
    if label in {"SHEAR_RATE"}:
        return v, unit
    return v, unit


def _group_entities(offsets: List[Tuple[int, int]], labels: List[str]) -> List[Tuple[int, int, str]]:
    spans: List[Tuple[int, int, str]] = []
    start = None
    end = None
    etype = None
    for i, (s, e) in enumerate(offsets):
        lab = labels[i]
        if e == 0 and s == 0:
            continue
        if lab.startswith("B-"):
            if start is not None:
                spans.append((start, end, etype))
            start = s
            end = e
            etype = lab[2:]
        elif lab.startswith("I-") and etype == lab[2:]:
            if start is not None:
                end = e
        else:
            if start is not None:
                spans.append((start, end, etype))
                start = None
                end = None
                etype = None
    if start is not None:
        spans.append((start, end, etype))
    return spans


class TransferExtractor:
    def __init__(self, model_name_or_path: str, label_mapping: Optional[Dict[str, str]] = None, device: Optional[str] = None):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        self.model = AutoModelForTokenClassification.from_pretrained(model_name_or_path)
        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"
        self.device = device
        self.model.to(self.device)
        self.model.eval()
        self.id2label = {int(k): v for k, v in getattr(self.model.config, "id2label", {}).items()} or {}
        self.label_mapping = label_mapping or {}

    def _map_label(self, label: str) -> str:
        if label in self.label_mapping:
            return self.label_mapping[label]
        return label

    def extract(self, text: str, biomolecule_type: str = "protein", protein_name: Optional[str] = None) -> List[ExtractionRecord]:
        sentences = [s.strip() for s in SENT_SPLIT.split(text.strip()) if s.strip()]
        records: List[ExtractionRecord] = []
        last_pH: Optional[float] = None
        last_temp: Optional[float] = None
        last_conc: Optional[float] = None
        for sent in sentences:
            enc = self.tokenizer(
                sent,
                return_offsets_mapping=True,
                return_tensors="pt",
                truncation=True,
                max_length=512,
            )
            offsets = enc.pop("offset_mapping")[0].tolist()
            enc = {k: v.to(self.device) for k, v in enc.items()}
            with torch.no_grad():
                logits = self.model(**enc).logits
            preds = logits.argmax(-1)[0].tolist()
            labels = [self.id2label.get(p, "O") for p in preds]
            spans = _group_entities(offsets, labels)
            pH_val: Optional[float] = None
            temp_val: Optional[float] = None
            conc_val: Optional[float] = None
            ionic_strength_val: Optional[float] = None
            additive_val: Optional[str] = None
            time_val: Optional[float] = None
            shear_rate_val: Optional[float] = None
            pressure_val: Optional[float] = None
            for s_idx, e_idx, et in spans:
                mapped = self._map_label(et)
                span_text = sent[s_idx:e_idx]
                v, unit = _span_value_and_unit(mapped, span_text)
                if mapped in {"PH_VALUE", "pH", "PH"} and v is not None:
                    v2, note = normalize_ph(v)
                    pH_val = v2
                elif mapped in {"TEMP", "TEMPERATURE", "TEMP_VALUE"} and v is not None:
                    v2, note = normalize_temperature(v, unit)
                    temp_val = v2
                elif mapped in {"CONC", "CONCENTRATION", "CONC_VALUE"} and v is not None:
                    v2, note = normalize_concentration(v, unit or "", biomolecule_type)
                    conc_val = v2
                elif mapped in {"IONIC_STRENGTH", "IONIC"} and v is not None:
                    ionic_strength_val = _normalize_ionic_strength(v, unit)
                elif mapped in {"ADDITIVE", "ADD"}:
                    additive_val = span_text.strip()
                elif mapped in {"TIME"} and v is not None:
                    time_val = v
                elif mapped in {"SHEAR_RATE"} and v is not None:
                    shear_rate_val = v
                elif mapped in {"PRESSURE"} and v is not None:
                    pressure_val = _normalize_pressure_bar(v, unit)
            has_any = any([pH_val, temp_val, conc_val, ionic_strength_val, additive_val, time_val, shear_rate_val, pressure_val])
            if not has_any:
                try:
                    if pH_val is None:
                        for pat in PH_PATTERNS:
                            m = pat.search(sent)
                            if m:
                                val = _find_number(m.group(0))
                                if val is not None:
                                    v2, note = normalize_ph(val)
                                    pH_val = v2
                                    break
                    if temp_val is None:
                        for pat in TEMP_PATTERNS:
                            m = pat.search(sent)
                            if m:
                                val = _find_number(m.group(0))
                                unit = _find_unit(m.group(0))
                                if val is not None:
                                    v2, note = normalize_temperature(val, unit)
                                    temp_val = v2
                                    break
                    if conc_val is None:
                        for pat in CONC_PATTERNS:
                            m = pat.search(sent)
                            if m:
                                val = _find_number(m.group(0))
                                unit = _find_unit(m.group(0))
                                if val is not None:
                                    v2, note = normalize_concentration(val, unit or "", biomolecule_type)
                                    conc_val = v2
                                    break
                except Exception:
                    pass
                has_any = any([pH_val, temp_val, conc_val, ionic_strength_val, additive_val, time_val, shear_rate_val, pressure_val])
                if not has_any:
                    continue
            if pH_val is None and last_pH is not None:
                pH_val = last_pH
            if temp_val is None and last_temp is not None:
                temp_val = last_temp
            if conc_val is None and last_conc is not None:
                conc_val = last_conc
            params = ExperimentalParameters(
                pH=pH_val,
                temperature_c=temp_val,
                concentration_mg_ml=conc_val,
                ionic_strength_mM=ionic_strength_val,
                additive=additive_val,
                time_min=time_val,
                shear_rate_s1=shear_rate_val,
                pressure_bar=pressure_val,
                raw_context=sent
            )
            parsed_count = sum(v is not None for v in [pH_val, temp_val, conc_val])
            conf = 0.5 + 0.1 * parsed_count
            if conf > 0.95:
                conf = 0.95
            record = ExtractionRecord(
                biomolecule_type=biomolecule_type,
                protein_name=protein_name,
                polarity=None,
                property="stability",
                parameters=params,
                outcome_score=None,
                outcome_label=None,
                outcome_text=sent,
                source_doi=None,
                source_title=None,
                source_authors=None,
                source_pub_year=None,
                source_section=None,
                confidence=conf
            )
            records.append(record)
            if pH_val is not None:
                last_pH = pH_val
            if temp_val is not None:
                last_temp = temp_val
            if conc_val is not None:
                last_conc = conc_val
        return records