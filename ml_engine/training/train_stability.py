from __future__ import annotations

from pathlib import Path
import json
import os
import pandas as pd
from joblib import dump, load

from ..features.preprocess import records_to_dataframe
from ..models.stability_model import StabilityClassifier


def load_jsonl(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def train_from_store(
    path: str | Path = "literature_mining/storage/structured_store.jsonl",
    use_synth: bool = True,
) -> StabilityClassifier:
    records = load_jsonl(path)
    df = records_to_dataframe(records)
    if len(df) < 5:
        if use_synth:
            # Too few samples; create a dummy balanced dataset by jittering plausible values
            # This keeps the pipeline testable without real data.
            synth = pd.DataFrame({
                "pH": [6.0, 7.0, 8.0, 5.0, 9.0, 3.0, 10.0],
                "temperature_c": [25, 37, 50, 60, 20, 4, 75],
                "concentration_mg_ml": [1, 5, 10, 20, 2, 0.5, 50],
                "label": [1, 1, 1, 0, 1, 0, 0],
            })
            df = synth
        else:
            raise ValueError(
                "Insufficient samples (<5) and synthetic augmentation disabled. Provide more data or enable synth."
            )

    model = StabilityClassifier().fit(df)
    return model


def save_model(model: StabilityClassifier, model_path: str | Path) -> None:
    """Persist the trained model to disk using joblib."""
    model_path = Path(model_path)
    if model_path.parent:
        os.makedirs(model_path.parent, exist_ok=True)
    dump(model, model_path)


def load_model(model_path: str | Path) -> StabilityClassifier:
    """Load a persisted model from disk using joblib."""
    return load(model_path)