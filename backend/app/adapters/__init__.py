"""Adapter layer for external model integrations."""

from .predictors import ModelPredictorAdapter, ModelNotAvailableError

__all__ = ["ModelPredictorAdapter", "ModelNotAvailableError"]
