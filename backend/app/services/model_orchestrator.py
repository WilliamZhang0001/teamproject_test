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

# Optional literature service import
try:
    from backend.app.core.db import SessionLocal
    from backend.app.services.literature_service import LiteratureService
    LITERATURE_AVAILABLE = True
except ImportError:
    LITERATURE_AVAILABLE = False
    logger.warning("Literature service not available")

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
        # Use lazy loading by default to speed up startup
        self.predictor = predictor or ModelPredictorAdapter(lazy_load=True)
        self.iqr_repo = iqr_repo or IqrRepository(lazy_load=True)

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
        
        # Add literature information if available
        literature_info = self._get_literature_info(payload, result)
        if literature_info:
            response["literature"] = literature_info
        
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

        # Add literature information if available
        # Extract recommended values for similarity search
        target_params = {}
        for param_name, param_info in recommendations.items():
            if param_info and isinstance(param_info, dict):
                # Extract median value if available
                if "median" in param_info:
                    target_params[param_name] = param_info["median"]
                elif "value" in param_info:
                    target_params[param_name] = param_info["value"]
        
        literature_info = self._get_literature_info_for_recommendation(
            biomolecule_name=biomolecule_name,
            experiment_type=experiment_type,
            target_params=target_params
        )
        if literature_info:
            recommendations["literature"] = literature_info

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
                return "Experimental conditions are expected to be feasible, recommend experimental validation"
            return "Experimental conditions may be feasible, recommend proceeding cautiously and monitoring validation results"
        if confidence >= 0.8:
            return "Experimental conditions are expected to be unstable, recommend adjusting parameters"
        return "Prediction result is unstable with low confidence, recommend optimizing parameters or supplementing data"
    
    # ------------------------------------------------------------------
    def _get_literature_info(self, payload: Dict, result: Dict) -> Optional[Dict]:
        """Get literature information for prediction scenario"""
        if not LITERATURE_AVAILABLE:
            return None
        
        try:
            db = SessionLocal()
            try:
                literature_service = LiteratureService(db)
                
                # Build ML result dict for literature search
                ml_result = {
                    "prediction": result.get("prediction"),
                    "confidence": result.get("confidence"),
                    "property_type": payload.get("property", "stability"),
                    **{k: v for k, v in payload.items() 
                       if k in ["pH", "temperature_c", "concentration_mg_ml", 
                               "ionic_strength_mM", "additive", "time_min", 
                               "shear_rate_s1", "pressure_bar"] and v is not None}
                }
                
                # Get similar literature
                similar_literature = literature_service.find_similar_literature(
                    ml_result=ml_result,
                    biomolecule_name=payload.get("biomolecule_name"),
                    top_k=3
                )
                
                if similar_literature:
                    return {
                        "top_similar_literature": similar_literature,
                        "count": len(similar_literature)
                    }
                return None
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Failed to get literature information: {e}", exc_info=True)
            return None
    
    # ------------------------------------------------------------------
    def _get_literature_info_for_recommendation(
        self,
        biomolecule_name: Optional[str],
        experiment_type: Optional[str],
        target_params: Dict
    ) -> Optional[Dict]:
        """Get literature information for recommendation scenario"""
        if not LITERATURE_AVAILABLE:
            return None
        
        try:
            db = SessionLocal()
            try:
                from backend.app.repos import literature_repo
                
                # Search similar records
                similar_records = literature_repo.search_similar_records(
                    db,
                    target_params=target_params,
                    biomolecule_name=biomolecule_name,
                    property_type=experiment_type or "stability",
                    limit=3
                )
                
                if similar_records:
                    return {
                        "top_similar_literature": similar_records,
                        "count": len(similar_records)
                    }
                return None
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Failed to get literature information for recommendation: {e}", exc_info=True)
            return None


__all__ = ["ModelOrchestrator", "ModelNotAvailableError"]
