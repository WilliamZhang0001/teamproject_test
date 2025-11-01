"""Tests for parameter validation utilities."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.app.core.parameter_spec import (  # noqa: E402
    ParameterValidationError,
    get_parameter_validator,
)


@pytest.fixture(scope="module")
def validator():
    return get_parameter_validator()


def test_valid_payload_passes_validation(validator):
    payload = {
        "biomolecule_name": "lysozyme",
        "biomolecule_type": "protein",
        "property": "stability",
        "pH": 7.0,
    }

    result = validator.validate(payload)

    assert result.is_valid
    assert result.normalized_payload["property"] == "stability"
    assert result.normalized_payload["experiment_type"] == "stability"
    assert result.provided_optional_fields == ["pH"]


def test_missing_required_field_raises(validator):
    payload = {
        "biomolecule_type": "protein",
        "property": "stability",
        "pH": 7.0,
    }

    with pytest.raises(ParameterValidationError) as exc_info:
        validator.validate(payload)

    error_fields = [err["field"] for err in exc_info.value.to_dict()["errors"]]
    assert "biomolecule_name" in error_fields


def test_optional_range_enforced(validator):
    payload = {
        "biomolecule_name": "lysozyme",
        "biomolecule_type": "protein",
        "property": "stability",
        "pH": -1.0,
    }

    with pytest.raises(ParameterValidationError) as exc_info:
        validator.validate(payload)

    error = exc_info.value.to_dict()["errors"][0]
    assert error["field"] == "pH"
    assert error["code"] == "below_minimum"


def test_at_least_one_optional_required(validator):
    payload = {
        "biomolecule_name": "lysozyme",
        "biomolecule_type": "protein",
        "property": "stability",
    }

    with pytest.raises(ParameterValidationError) as exc_info:
        validator.validate(payload)

    error_codes = [err["code"] for err in exc_info.value.to_dict()["errors"]]
    assert "insufficient_parameters" in error_codes


def test_invalid_enum_value_detected(validator):
    payload = {
        "biomolecule_name": "lysozyme",
        "biomolecule_type": "invalid",
        "property": "stability",
        "pH": 7.0,
    }

    with pytest.raises(ParameterValidationError) as exc_info:
        validator.validate(payload)

    error_codes = [err["code"] for err in exc_info.value.to_dict()["errors"]]
    assert "invalid_choice" in error_codes

