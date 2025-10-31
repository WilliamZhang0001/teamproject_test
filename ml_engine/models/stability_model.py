from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression


@dataclass
class StabilityClassifier:
    """Binary classifier estimating probability of stability.

    Minimal, robust pipeline:
    - Impute missing features with median.
    - Standardize features.
    - Logistic regression with regularization for interpretability.
    """

    C: float = 1.0
    random_state: int = 42
    model: Optional[Pipeline] = None

    def fit(self, df: pd.DataFrame) -> "StabilityClassifier":
        X = df[["pH", "temperature_c", "concentration_mg_ml"]]
        y = df["label"].astype(int)

        self.model = Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(C=self.C, random_state=self.random_state, max_iter=1000)),
        ])

        self.model.fit(X, y)
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if not self.model:
            raise RuntimeError("Model not fitted")
        return self.model.predict_proba(X)[:, 1]