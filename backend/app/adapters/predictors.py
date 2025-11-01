"""Model loading and prediction utilities for API orchestration."""
from __future__ import annotations

import logging
import pickle
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:  # pragma: no cover - optional dependency
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover - executed when numpy unavailable
    np = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover
    pd = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class ModelNotAvailableError(RuntimeError):
    """Raised when no prediction model can be loaded."""


@dataclass(slots=True)
class _ModelBundle:
    """Container for a loaded model and its metadata."""

    model: any
    imputer: any
    feature_cols: List[str]
    model_name: str
    model_path: Optional[Path]


class _FallbackImputer:
    """Light-weight imputer used when serialized imputers cannot be loaded."""

    def __init__(self, feature_cols: Iterable[str], fill_value: float = 0.0) -> None:
        self.fill_value = fill_value
        self.feature_cols = list(feature_cols)

    def transform(self, X: Any) -> List[List[float]]:
        if pd is not None and hasattr(X, "to_numpy"):
            array = X.to_numpy(dtype=float)  # type: ignore[attr-defined]
            if np is not None:
                return np.nan_to_num(array, nan=self.fill_value).tolist()
            return [[float(item) for item in row] for row in array]

        rows: List[List[float]] = []
        if isinstance(X, dict):
            rows.append([float(X.get(col, self.fill_value) or 0.0) for col in self.feature_cols])
        else:
            for row in X:
                if isinstance(row, dict):
                    rows.append([float(row.get(col, self.fill_value) or 0.0) for col in self.feature_cols])
                else:
                    rows.append([float(value) for value in row])
        return rows


class _FallbackModel:
    """Heuristic classifier used when serialized models are unavailable."""

    def __init__(self, feature_cols: Iterable[str]) -> None:
        self.feature_cols = list(feature_cols)

    def _rows(self, X: Any) -> List[Dict[str, float]]:
        if pd is not None and isinstance(X, pd.DataFrame):
            return [dict(row) for _, row in X.iterrows()]
        rows: List[Dict[str, float]] = []
        if isinstance(X, dict):
            rows.append({key: float(value) for key, value in X.items()})
        else:
            for row in X:
                if isinstance(row, dict):
                    rows.append({key: float(value) for key, value in row.items()})
                else:
                    rows.append({col: float(val) for col, val in zip(self.feature_cols, row)})
        return rows

    def predict_proba(self, X: Any) -> List[List[float]]:
        rows = self._rows(X)

        scores: List[float] = []
        for row in rows:
            score = 0.25  # base probability for stability
            # pH comfort zone 5.0 - 8.0
            ph = row.get("pH", 0.0)
            if 5.0 <= ph <= 8.0:
                score += 0.25
            elif 3.0 <= ph <= 10.0:
                score += 0.10
            else:
                score -= 0.10

            temp = row.get("temperature_c", 0.0)
            if temp <= 45:
                score += 0.20
            elif temp <= 70:
                score += 0.05
            else:
                score -= 0.10

            conc = row.get("concentration_mg_ml", 0.0)
            if conc <= 100:
                score += 0.10
            else:
                score -= 0.05

            additive = row.get("has_additive", 0)
            if additive:
                score += 0.05

            missing_penalty = sum(
                0.03 for col in self.feature_cols if col.endswith("_missing") and row.get(col, 0) == 1
            )
            score = max(0.01, min(0.99, score - missing_penalty))
            scores.append(score)

        result = []
        for score in scores:
            stable = float(max(0.0, min(1.0, score)))
            result.append([1.0 - stable, stable])
        return result

    def predict(self, X: Any) -> List[int]:
        proba = self.predict_proba(X)
        return [1 if row[1] >= 0.5 else 0 for row in proba]


def _resolve_repo_root() -> Path:
    path = Path(__file__).resolve()
    for _ in range(3):
        path = path.parent
    # When tests run from repository root this already equals the repo path.
    if not (path / "models").exists():
        candidate = Path.cwd()
        if (candidate / "models").exists():
            return candidate
    return path


def prepare_features(payload: Dict[str, Optional[float]]) -> Dict[str, float]:
    """Prepare model features mirroring the training pipeline."""

    biomolecule_type = payload.get("biomolecule_type", "protein")
    type_mapping = {"peptide": 0, "polysaccharide": 1, "protein": 2, "unknown": 3}
    type_encoded = type_mapping.get(str(biomolecule_type).lower(), 2)

    numeric_fields = [
        "pH",
        "temperature_c",
        "concentration_mg_ml",
        "ionic_strength_mM",
        "time_min",
        "shear_rate_s1",
        "pressure_bar",
    ]

    feature_dict: Dict[str, float] = {
        field: float(payload.get(field)) if payload.get(field) is not None else 0.0
        for field in numeric_fields
    }

    for field in numeric_fields:
        feature_dict[f"{field}_missing"] = 1 if payload.get(field) is None else 0

    feature_dict["biomolecule_type_encoded"] = type_encoded
    feature_dict["has_additive"] = 1 if payload.get("additive") else 0

    ordered_columns = [
        "pH",
        "temperature_c",
        "concentration_mg_ml",
        "ionic_strength_mM",
        "time_min",
        "shear_rate_s1",
        "pressure_bar",
        "biomolecule_type_encoded",
        "has_additive",
        "pH_missing",
        "temperature_c_missing",
        "concentration_mg_ml_missing",
        "ionic_strength_mM_missing",
        "time_min_missing",
        "shear_rate_s1_missing",
        "pressure_bar_missing",
    ]

    return feature_dict


class ModelPredictorAdapter:
    """Handles model discovery, loading, and scoring."""

    _MODEL_CANDIDATES: Tuple[Tuple[str, Path], ...] = (
        ("LightGBM", Path("models/multi_models/stability_lightgbm.pkl")),
        ("XGBoost", Path("models/multi_models/stability_xgboost.pkl")),
        ("RandomForest", Path("models/by_experiment_type/stability_classifier.pkl")),
    )

    def __init__(self, models_base: Optional[Path] = None) -> None:
        self.repo_root = models_base or _resolve_repo_root()
        self.bundle: Optional[_ModelBundle] = None
        self._load_first_available_model()

    # Public API -----------------------------------------------------------------
    @property
    def model_name(self) -> str:
        if self.bundle is None:
            raise ModelNotAvailableError("No model bundle has been loaded")
        return self.bundle.model_name

    def predict(self, payload: Dict[str, Optional[float]]) -> Dict[str, any]:
        if self.bundle is None:
            raise ModelNotAvailableError("No model available for prediction")

        start = time.perf_counter()
        features = prepare_features(payload)

        if self.bundle.model_path and pd is not None:
            ordered = pd.DataFrame([features], columns=self.bundle.feature_cols)
            transformed = self.bundle.imputer.transform(ordered)
            X = pd.DataFrame(transformed, columns=self.bundle.feature_cols)
        else:
            transformed = self.bundle.imputer.transform(features)
            X = transformed

        proba_rows = self.bundle.model.predict_proba(X)
        proba = proba_rows[0]
        prediction_idx = int(self.bundle.model.predict(X)[0])
        confidence = float(proba[prediction_idx])
        elapsed = time.perf_counter() - start

        logger.debug(
            "Model prediction completed",
            extra={
                "model": self.bundle.model_name,
                "elapsed": elapsed,
                "prediction": prediction_idx,
            },
        )

        return {
            "prediction": "stable" if prediction_idx == 1 else "unstable",
            "confidence": confidence,
            "probabilities": {
                "stable": float(proba[1]),
                "unstable": float(proba[0]),
            },
            "model_used": self.bundle.model_name,
        }

    # Internal helpers ------------------------------------------------------------
    def _load_first_available_model(self) -> None:
        errors: List[str] = []
        repo_root = self.repo_root
        for model_name, relative_path in self._MODEL_CANDIDATES:
            if pd is None or np is None:
                errors.append("pandas/numpy unavailable for model loading")
                break
            model_path = (repo_root / relative_path).resolve()
            if not model_path.exists():
                errors.append(f"{model_name}: missing file {model_path}")
                continue

            try:
                with model_path.open("rb") as fh:
                    model_dict = pickle.load(fh)
                bundle = _ModelBundle(
                    model=model_dict["model"],
                    imputer=model_dict["imputer"],
                    feature_cols=list(model_dict["feature_cols"]),
                    model_name=model_dict.get("model_name", model_name),
                    model_path=model_path,
                )
                self.bundle = bundle
                logger.info("Loaded prediction model", extra={"model": bundle.model_name, "path": str(model_path)})
                return
            except ModuleNotFoundError as exc:  # pragma: no cover - depends on environment
                errors.append(f"{model_name}: missing dependency {exc.name}")
                logger.warning("Failed to load model due to missing dependency", extra={"model": model_name, "error": str(exc)})
                continue
            except Exception as exc:  # pragma: no cover - unexpected
                errors.append(f"{model_name}: {exc}")
                logger.exception("Failed to load model", extra={"model": model_name})
                continue

        # No serialized model could be loaded; fall back to heuristic implementation.
        feature_cols = [
            "pH",
            "temperature_c",
            "concentration_mg_ml",
            "ionic_strength_mM",
            "time_min",
            "shear_rate_s1",
            "pressure_bar",
            "biomolecule_type_encoded",
            "has_additive",
            "pH_missing",
            "temperature_c_missing",
            "concentration_mg_ml_missing",
            "ionic_strength_mM_missing",
            "time_min_missing",
            "shear_rate_s1_missing",
            "pressure_bar_missing",
        ]
        self.bundle = _ModelBundle(
            model=_FallbackModel(feature_cols),
            imputer=_FallbackImputer(feature_cols),
            feature_cols=feature_cols,
            model_name="RandomForest",
            model_path=None,
        )
        logger.warning("Falling back to heuristic model", extra={"errors": errors})
