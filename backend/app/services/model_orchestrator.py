"""Business orchestration for model predictions and recommendations."""
from __future__ import annotations

import logging
import time
from typing import Dict, Iterable, Optional

try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter, Histogram
except ModuleNotFoundError:  # pragma: no cover - fallback for environments without Prometheus
    class _NoopMetric:
        def __init__(self, *args, **kwargs) -> None:  # noqa: D401 - simple no-op
            pass

        def labels(self, **kwargs):  # type: ignore[override]
            return self

        def observe(self, *args, **kwargs) -> None:
            return None

        def inc(self, *args, **kwargs) -> None:
            return None

    Counter = Histogram = _NoopMetric

from backend.app.adapters import ModelNotAvailableError, ModelPredictorAdapter
from backend.app.services.iqr_repo import IqrRepository

logger = logging.getLogger(__name__)

PREDICTION_LATENCY = Histogram(
    "ml_prediction_latency_seconds",
    "Latency of model predictions",
    labelnames=("model",),
)
MODEL_SELECTION_COUNTER = Counter(
    "ml_model_selection_total",
    "Number of predictions served by each model",
    labelnames=("model",),
)
MODEL_DEGRADATION_COUNTER = Counter(
    "ml_model_degradation_total",
    "Number of times the platform served a fallback model",
    labelnames=("model",),
)
IQR_HIT_LEVEL_COUNTER = Counter(
    "ml_iqr_hit_level_total",
    "IQR hit counts by priority level",
    labelnames=("level",),
)


class ModelOrchestrator:
    """Determines scenario and coordinates prediction/iqr lookups."""

    def __init__(
        self,
        predictor: Optional[ModelPredictorAdapter] = None,
        iqr_repo: Optional[IqrRepository] = None,
    ) -> None:
        self.predictor = predictor or ModelPredictorAdapter()
        self.iqr_repo = iqr_repo or IqrRepository()

    # ------------------------------------------------------------------
    def execute(self, payload: Dict) -> Dict:
        """Route request to appropriate scenario handler."""
        if payload.get("known_parameters") is not None:
            recommend_params = payload.get("recommend_parameters") or []
            return self._handle_recommendation(
                biomolecule_name=payload.get("biomolecule_name"),
                experiment_type=payload.get("property") or payload.get("experiment_type"),
                recommend_parameters=recommend_params,
            )

        return self._handle_prediction(payload)

    # ------------------------------------------------------------------
    def _handle_prediction(self, payload: Dict) -> Dict:
        logger.info(
            "Handling stability prediction request",
            extra={"biomolecule_name": payload.get("biomolecule_name"), "property": payload.get("property")},
        )

        started = time.perf_counter()
        result = self.predictor.predict(payload)
        elapsed = time.perf_counter() - started

        model_name = result["model_used"]
        PREDICTION_LATENCY.labels(model=model_name).observe(elapsed)
        MODEL_SELECTION_COUNTER.labels(model=model_name).inc()
        if model_name != "LightGBM":
            MODEL_DEGRADATION_COUNTER.labels(model=model_name).inc()

        recommendation = self._build_recommendation(result["prediction"], result["confidence"])

        response = {
            "prediction": result["prediction"],
            "confidence": round(result["confidence"], 4),
            "probabilities": {
                "stable": round(result["probabilities"]["stable"], 4),
                "unstable": round(result["probabilities"]["unstable"], 4),
            },
            "model_used": model_name,
            "recommendation": recommendation,
        }
        logger.info(
            "Prediction completed",
            extra={
                "model": model_name,
                "prediction": result["prediction"],
                "confidence": result["confidence"],
                "latency_ms": elapsed * 1000,
            },
        )
        return response

    # ------------------------------------------------------------------
    def _handle_recommendation(
        self,
        biomolecule_name: Optional[str],
        experiment_type: Optional[str],
        recommend_parameters: Iterable[str],
    ) -> Dict:
        logger.info(
            "Handling IQR recommendation request",
            extra={
                "biomolecule_name": biomolecule_name,
                "experiment_type": experiment_type,
                "targets": list(recommend_parameters),
            },
        )
        recommendations, hit_levels = self.iqr_repo.get_recommendations(
            biomolecule_name=biomolecule_name,
            experiment_type=experiment_type,
            recommend_parameters=recommend_parameters,
        )

        for hit in hit_levels.values():
            IQR_HIT_LEVEL_COUNTER.labels(level=hit.level).inc()

        logger.info(
            "IQR recommendation completed",
            extra={
                "biomolecule_name": biomolecule_name,
                "experiment_type": experiment_type,
                "levels": {k: v.level for k, v in hit_levels.items()},
            },
        )
        return recommendations

    # ------------------------------------------------------------------
    @staticmethod
    def _build_recommendation(prediction: str, confidence: float) -> str:
        if prediction == "stable":
            if confidence >= 0.8:
                return "该实验条件预计可行，建议进行实验验证"
            return "实验条件可能可行，建议谨慎推进并关注验证结果"
        if confidence >= 0.8:
            return "该实验条件预计不稳定，建议调整参数"
        return "预测结果不稳定，置信度较低，建议优化参数或补充数据"


__all__ = ["ModelOrchestrator", "ModelNotAvailableError"]
