"""Machine Learning engine for phase-1 parameter window recommendation.

Narrow scope:
- Use extracted protein stability records (pH, temperature, concentration).
- Train a simple classifier to estimate stability probability.
- Sweep a parameter grid to produce recommended ranges/windows.
"""

from .features.preprocess import records_to_dataframe
from .models.stability_model import StabilityClassifier
from .prediction.optimizer import recommend_windows, recommend_windows_consensus

__all__ = [
    "records_to_dataframe",
    "StabilityClassifier",
    "recommend_windows",
    "recommend_windows_consensus",
]