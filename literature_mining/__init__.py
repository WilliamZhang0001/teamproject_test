"""Top-level helpers for the Literature Mining engine.

Scope (phase 1):
- Focus on protein stability under pH, temperature, and concentration.
- Extract parameter–outcome pairs from free text and normalize units.

This package exposes a simple function `extract_protein_stability_from_text`
that returns normalized records which downstream ML can consume.
"""

from .schemas import ExtractionRecord
from .extractors.stability_extractor import extract_from_text

__all__ = [
    "ExtractionRecord",
    "extract_from_text",
]


def extract_protein_stability_from_text(text: str) -> list[ExtractionRecord]:
    """Convenience wrapper for protein stability extraction.

    Parameters
    ----------
    text: str
        Full text of a paper section, abstract, or paragraph.

    Returns
    -------
    list[ExtractionRecord]
        Normalized parameter–outcome records.
    """

    return extract_from_text(text=text, biomolecule_type="protein")