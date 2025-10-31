from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, List


@dataclass
class RangeWindow:
    param: str
    lower: float
    upper: float
    support: float  # fraction of grid points meeting the criterion


def merge_intervals(xs: List[float], mask: List[bool]) -> List[Tuple[float, float, float]]:
    """Merge consecutive True segments into intervals.

    Returns list of (start, end, support_fraction).
    """
    intervals = []
    n = len(xs)
    i = 0
    while i < n:
        if not mask[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and mask[j + 1]:
            j += 1
        start, end = xs[i], xs[j]
        support = sum(mask[i : j + 1]) / n
        intervals.append((start, end, support))
        i = j + 1
    return intervals


def merge_intervals_by_threshold(xs: List[float], values: List[float], threshold: float) -> List[Tuple[float, float, float]]:
    """Merge consecutive points where values >= threshold.

    Returns list of (start, end, support_mean), where support_mean is the mean of
    `values` across the interval. `values` typically represent coverage fractions in [0, 1].
    """
    intervals: List[Tuple[float, float, float]] = []
    n = len(xs)
    assert len(values) == n
    i = 0
    while i < n:
        if values[i] < threshold:
            i += 1
            continue
        j = i
        while j + 1 < n and values[j + 1] >= threshold:
            j += 1
        start, end = xs[i], xs[j]
        support_mean = float(sum(values[i : j + 1]) / (j - i + 1))
        intervals.append((start, end, support_mean))
        i = j + 1
    return intervals