from __future__ import annotations

import pandas as pd
from typing import Iterable


def _label_from_outcome(outcome_label: str | None) -> int | None:
    if not outcome_label:
        return None
    t = outcome_label.lower()
    # Map cues to binary stability label: 1=stable/less aggregation, 0=unstable
    if any(x in t for x in ["stable", "stability"]):
        return 1
    if any(x in t for x in ["unstable", "denatur", "aggregation", "precipitation"]):
        return 0
    return None


def records_to_dataframe(records: Iterable[dict | "ExtractionRecord"]) -> pd.DataFrame:
    """Convert extraction records into a model-ready DataFrame.

    Expected fields: `parameters.pH`, `parameters.temperature_c`,
    `parameters.concentration_mg_ml`, `outcome_label`.
    """
    rows = []
    for r in records:
        # Support both dicts and pydantic models
        if hasattr(r, "model_dump"):
            r = r.model_dump()
        p = r.get("parameters", {})
        label = _label_from_outcome(r.get("outcome_label"))
        rows.append({
            "pH": p.get("pH"),
            "temperature_c": p.get("temperature_c"),
            "concentration_mg_ml": p.get("concentration_mg_ml"),
            "label": label,
            "confidence": r.get("confidence", 0.5),
        })

    df = pd.DataFrame(rows)
    # Drop rows with missing label; keep NaNs for features to be imputed later
    df = df.dropna(subset=["label"])
    return df