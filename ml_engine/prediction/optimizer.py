from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from ..models.stability_model import StabilityClassifier
from ..utils.ranges import merge_intervals
from ..utils.ranges import merge_intervals_by_threshold


def _grid(constraints: Dict[str, Tuple[float, float]], steps: Dict[str, int]) -> pd.DataFrame:
    grids = {}
    for k, (lo, hi) in constraints.items():
        n = steps.get(k, 25)
        grids[k] = np.linspace(lo, hi, n)
    mesh = np.array(np.meshgrid(*grids.values(), indexing="ij"))
    flat = mesh.reshape(len(grids), -1).T
    df = pd.DataFrame(flat, columns=list(grids.keys()))
    return df


def recommend_windows(
    model: StabilityClassifier,
    *,
    constraints: Dict[str, Tuple[float, float]] | None = None,
    prob_threshold: float = 0.7,
) -> Dict[str, List[Dict]]:
    """Sweep parameter grid and return recommended windows.

    Parameters
    ----------
    model: fitted `StabilityClassifier`.
    constraints: ranges for parameters, defaults to broad sensible bounds.
    prob_threshold: minimum predicted probability to mark as "recommended".
    """

    if constraints is None:
        constraints = {
            "pH": (2.0, 10.0),
            "temperature_c": (4.0, 80.0),
            "concentration_mg_ml": (0.5, 100.0),
        }

    grid_df = _grid(constraints, steps={"pH": 17, "temperature_c": 20, "concentration_mg_ml": 20})
    probs = model.predict_proba(grid_df[["pH", "temperature_c", "concentration_mg_ml"]])
    grid_df["prob"] = probs

    # Compute windows for each parameter by marginalizing others
    results: Dict[str, List[Dict]] = {}
    for param in ["pH", "temperature_c", "concentration_mg_ml"]:
        # Sort by param value and compute mask
        df_sorted = grid_df.sort_values(param)
        xs = df_sorted[param].values.tolist()
        mask = (df_sorted["prob"].values >= prob_threshold).tolist()
        intervals = merge_intervals(xs, mask)
        results[param] = [
            {"param": param, "lower": float(lo), "upper": float(hi), "support": float(sup)}
            for (lo, hi, sup) in intervals
        ]

    return results


def recommend_windows_consensus(
    model: StabilityClassifier,
    *,
    constraints: Dict[str, Tuple[float, float]] | None = None,
    prob_threshold: float = 0.7,
    coverage_threshold: float = 0.5,
) -> Dict[str, List[Dict]]:
    """Recommend windows using consensus coverage across other dimensions.

    For each parameter value, compute coverage = fraction of (other params) combinations
    with predicted probability >= prob_threshold. Merge consecutive values whose coverage
    >= coverage_threshold into intervals. The interval 'support' is the mean coverage.
    """
    if constraints is None:
        constraints = {
            "pH": (2.0, 10.0),
            "temperature_c": (4.0, 80.0),
            "concentration_mg_ml": (0.5, 100.0),
        }

    grid_df = _grid(constraints, steps={"pH": 17, "temperature_c": 20, "concentration_mg_ml": 20})
    probs = model.predict_proba(grid_df[["pH", "temperature_c", "concentration_mg_ml"]])
    grid_df["prob"] = probs

    results: Dict[str, List[Dict]] = {}
    for param in ["pH", "temperature_c", "concentration_mg_ml"]:
        values = sorted(grid_df[param].unique().tolist())
        coverages: List[float] = []
        for v in values:
            df_v = grid_df[grid_df[param] == v]
            coverage_v = float((df_v["prob"] >= prob_threshold).mean())
            coverages.append(coverage_v)

        intervals = merge_intervals_by_threshold(values, coverages, coverage_threshold)
        results[param] = [
            {"param": param, "lower": float(lo), "upper": float(hi), "support": float(sup)}
            for (lo, hi, sup) in intervals
        ]

    return results