"""Repository responsible for querying IQR statistics."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IqrHit:
    level: str
    source_text: str


class IqrRepository:
    """Loads and queries IQR statistics with defined priority order."""

    def __init__(self, stats_path: Optional[Path] = None, lazy_load: bool = True) -> None:
        repo_root = Path(__file__).resolve()
        for _ in range(4):
            repo_root = repo_root.parent
        default_path = repo_root / "models" / "iqr_statistics.json"
        self.stats_path = stats_path or default_path
        self._lazy_load = lazy_load
        self._stats: Optional[Dict] = None
        if not lazy_load:
            self._stats = self._load()

    # ------------------------------------------------------------------
    def _load(self) -> Dict:
        if not self.stats_path.exists():
            raise FileNotFoundError(f"IQR statistics file not found: {self.stats_path}")
        with self.stats_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        logger.info("Loaded IQR statistics", extra={"path": str(self.stats_path)})
        return data

    # ------------------------------------------------------------------
    def get_recommendations(
        self,
        biomolecule_name: Optional[str],
        experiment_type: Optional[str],
        recommend_parameters: Iterable[str],
    ) -> Tuple[Dict[str, Optional[Dict]], Dict[str, IqrHit]]:
        # Lazy load statistics on first use
        if self._stats is None:
            self._stats = self._load()
        
        biomolecule_name = (biomolecule_name or "").strip() or None
        experiment_type = (experiment_type or "").strip() or None
        results: Dict[str, Optional[Dict]] = {}
        hits: Dict[str, IqrHit] = {}

        for parameter in recommend_parameters:
            stats, hit = self._resolve_parameter_stats(parameter, biomolecule_name, experiment_type)
            if stats is None:
                results[parameter] = None
                continue

            q1 = stats.get("q1")
            q3 = stats.get("q3")
            safe_range = [q1, q3] if q1 is not None and q3 is not None else None
            full_range = None
            if stats.get("min") is not None and stats.get("max") is not None:
                full_range = [stats.get("min"), stats.get("max")]

            results[parameter] = {
                "recommended_value": stats.get("median"),
                "safe_range": safe_range,
                "full_range": full_range,
                "sample_count": stats.get("count", 0),
                "source": hit.source_text,
            }
            hits[parameter] = hit

        return results, hits

    # ------------------------------------------------------------------
    def _resolve_parameter_stats(
        self,
        parameter: str,
        biomolecule_name: Optional[str],
        experiment_type: Optional[str],
    ) -> Tuple[Optional[Dict], IqrHit]:
        # Ensure stats are loaded
        if self._stats is None:
            self._stats = self._load()
        stats = self._stats
        # Level 1: experiment + biomolecule
        if biomolecule_name and experiment_type:
            combined = stats.get("by_experiment_and_biomolecule", {})
            exp_bucket = combined.get(experiment_type, {})
            bio_bucket = exp_bucket.get(biomolecule_name, {})
            param_stats = bio_bucket.get(parameter)
            if param_stats:
                return param_stats, IqrHit(
                    level="experiment_biomolecule",
                    source_text=f"Based on {experiment_type} data for {biomolecule_name}",
                )

        if experiment_type:
            exp_stats = stats.get("by_experiment_type", {}).get(experiment_type, {})
            param_stats = exp_stats.get(parameter)
            if param_stats:
                return param_stats, IqrHit(
                    level="experiment",
                    source_text=f"Based on all {experiment_type} experimental data",
                )

        if biomolecule_name:
            bio_stats = stats.get("by_biomolecule", {}).get(biomolecule_name, {})
            param_stats = bio_stats.get(parameter)
            if param_stats:
                return param_stats, IqrHit(
                    level="biomolecule",
                    source_text=f"Based on all experimental data for {biomolecule_name}",
                )

        global_stats = stats.get("global", {})
        param_stats = global_stats.get(parameter)
        if param_stats:
            return param_stats, IqrHit(level="global", source_text="Based on all experimental data")

        return None, IqrHit(level="not_found", source_text="No statistics available")
