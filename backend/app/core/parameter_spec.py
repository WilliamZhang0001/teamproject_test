"""Parameter specification parsing and validation utilities."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .config import settings


LOGGER = logging.getLogger(__name__)


@dataclass
class FieldConstraint:
    """Represents validation constraints for a single field."""

    name: str
    field_type: str
    required: bool
    description: str = ""
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    enum_values: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a serialisable view of the constraint."""

        payload: Dict[str, Any] = {
            "name": self.name,
            "type": self.field_type,
            "required": self.required,
        }
        if self.description:
            payload["description"] = self.description
        if self.unit:
            payload["unit"] = self.unit
        if self.enum_values:
            payload["enum_values"] = list(self.enum_values)
        if self.min_value is not None or self.max_value is not None:
            payload["numeric_range"] = {
                "min": self.min_value,
                "max": self.max_value,
            }
        if self.min_length is not None or self.max_length is not None:
            payload["length_range"] = {
                "min": self.min_length,
                "max": self.max_length,
            }
        return payload


@dataclass
class ParameterSpec:
    """Container holding all parsed parameter constraints."""

    required_fields: Dict[str, FieldConstraint]
    optional_fields: Dict[str, FieldConstraint]
    optional_min_required: int = 1

    def optional_field_names(self) -> List[str]:
        return list(self.optional_fields.keys())


@dataclass
class ParameterError:
    """Single validation error."""

    field: str
    code: str
    message: str
    expected: Optional[Dict[str, Any]] = None
    actual: Any = None

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "field": self.field,
            "code": self.code,
            "message": self.message,
        }
        if self.expected is not None:
            payload["expected"] = self.expected
        if self.actual is not None:
            payload["actual"] = self.actual
        return payload


@dataclass
class ParameterValidationResult:
    """Result returned from a validation run."""

    normalized_payload: Dict[str, Any]
    provided_optional_fields: List[str]
    errors: List[ParameterError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


class ParameterValidationError(Exception):
    """Raised when validation fails."""

    def __init__(self, errors: Iterable[ParameterError], context: Optional[str] = None):
        self.errors = list(errors)
        self.context = context
        super().__init__("Parameter validation failed")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": str(self),
            "context": self.context,
            "errors": [error.to_dict() for error in self.errors],
        }


class ParameterSpecLoader:
    """Load and parse parameter specifications from the Markdown source file."""

    def __init__(self, spec_path: Optional[Path] = None):
        project_root = Path(__file__).resolve().parents[3]
        default_path = Path(settings.parameter_spec_path)
        if not default_path.is_absolute():
            default_path = project_root / default_path
        self.spec_path = spec_path or default_path
        self._cache: Optional[ParameterSpec] = None
        self._cached_mtime: Optional[float] = None

    def load(self) -> ParameterSpec:
        """Return a parsed specification, reloading when the file changes."""

        if not self.spec_path.exists():
            raise FileNotFoundError(f"Parameter specification not found: {self.spec_path}")

        mtime = self.spec_path.stat().st_mtime
        if self._cache is not None and self._cached_mtime == mtime:
            return self._cache

        LOGGER.debug("Loading parameter specification from %s", self.spec_path)
        text = self.spec_path.read_text(encoding="utf-8")
        spec = self._parse(text)

        self._cache = spec
        self._cached_mtime = mtime
        return spec

    def _parse(self, text: str) -> ParameterSpec:
        """Parse markdown tables from specification text."""

        lines = [line.strip() for line in text.splitlines()]

        tables: List[List[str]] = []
        current: List[str] = []
        for line in lines:
            if line.startswith("<<<<<<<"):
                # Drop unresolved merge markers silently.
                continue
            if line.startswith("|"):
                if set(part.strip() for part in line.split("|") if part.strip()) == {"---"}:
                    continue
                current.append(line)
                continue
            if current:
                tables.append(current)
                current = []
        if current:
            tables.append(current)

        if len(tables) < 2:
            raise ValueError("Parameter specification must contain at least two tables")

        required_spec = self._parse_required_table(tables[0])
        optional_spec = self._parse_optional_table(tables[1])

        return ParameterSpec(required_fields=required_spec, optional_fields=optional_spec)

    def _parse_required_table(self, table_lines: List[str]) -> Dict[str, FieldConstraint]:
        required_fields: Dict[str, FieldConstraint] = {}

        for line in table_lines:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if not cells or cells[0] in {"字段名", "Field Name"}:
                continue

            name = self._normalize_identifier(cells[0])
            field_type = cells[1]
            description = cells[2]
            constraints = cells[4] if len(cells) > 4 else ""

            enum_values = self._extract_enum(constraints)
            min_length, max_length = self._extract_length_range(constraints)

            required_fields[name] = FieldConstraint(
                name=name,
                field_type=field_type,
                required=True,
                description=description,
                min_length=min_length,
                max_length=max_length,
                enum_values=enum_values,
            )

        return required_fields

    def _parse_optional_table(self, table_lines: List[str]) -> Dict[str, FieldConstraint]:
        optional_fields: Dict[str, FieldConstraint] = {}

        for line in table_lines:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if not cells or cells[0] in {"字段名", "Field Name"}:
                continue

            name = self._normalize_identifier(cells[0])
            field_type = cells[1]
            unit = cells[2] if len(cells) > 2 else None
            value_range = cells[3] if len(cells) > 3 else ""
            description = cells[5] if len(cells) > 5 else ""

            min_value, max_value = self._extract_numeric_range(value_range)

            optional_fields[name] = FieldConstraint(
                name=name,
                field_type=field_type,
                required=False,
                description=description,
                unit=unit if unit != "-" else None,
                min_value=min_value,
                max_value=max_value,
            )

        return optional_fields

    @staticmethod
    def _normalize_identifier(raw: str) -> str:
        return raw.strip().strip("`")

    @staticmethod
    def _extract_enum(text: str) -> List[str]:
        return re.findall(r'"([^\"]+)"', text)

    @staticmethod
    def _extract_length_range(text: str) -> (Optional[int], Optional[int]):
        match = re.search(r"(-?\d+)\s*-\s*(-?\d+)", text)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None

    @staticmethod
    def _extract_numeric_range(text: str) -> (Optional[float], Optional[float]):
        match = re.search(r"(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+(?:\.\d+)?)", text)
        if match:
            return float(match.group(1)), float(match.group(2))
        return None, None


class ParameterValidator:
    """Validate payloads against the loaded parameter specification."""

    def __init__(self, loader: ParameterSpecLoader):
        self.loader = loader

    def optional_field_names(self) -> List[str]:
        """Return the optional experimental parameter names from the spec."""

        return self.loader.load().optional_field_names()

    def validate(
        self,
        payload: Dict[str, Any],
        *,
        require_optional: Optional[bool] = None,
        context: Optional[str] = None,
    ) -> ParameterValidationResult:
        """Validate the provided payload."""

        spec = self.loader.load()
        normalized = dict(payload)

        # Normalise aliases for backwards compatibility.
        if "property" not in normalized and "experiment_type" in normalized:
            normalized["property"] = normalized["experiment_type"]
        if "experiment_type" not in normalized and "property" in normalized:
            normalized["experiment_type"] = normalized["property"]

        errors: List[ParameterError] = []

        for name, constraint in spec.required_fields.items():
            value = normalized.get(name)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(
                    ParameterError(
                        field=name,
                        code="missing_field",
                        message="Required field is missing",
                        expected={"required": True},
                        actual=value,
                    )
                )
                continue

            if constraint.enum_values and value not in constraint.enum_values:
                errors.append(
                    ParameterError(
                        field=name,
                        code="invalid_choice",
                        message="Value is not allowed",
                        expected={"allowed": constraint.enum_values},
                        actual=value,
                    )
                )

            if constraint.min_length is not None or constraint.max_length is not None:
                length = len(value) if isinstance(value, str) else None
                if length is None:
                    errors.append(
                        ParameterError(
                            field=name,
                            code="invalid_type",
                            message="Value must be a string",
                            expected={"type": "string"},
                            actual=value,
                        )
                    )
                else:
                    if constraint.min_length is not None and length < constraint.min_length:
                        errors.append(
                            ParameterError(
                                field=name,
                                code="too_short",
                                message="Value is shorter than allowed",
                                expected={"min_length": constraint.min_length},
                                actual=length,
                            )
                        )
                    if constraint.max_length is not None and length > constraint.max_length:
                        errors.append(
                            ParameterError(
                                field=name,
                                code="too_long",
                                message="Value is longer than allowed",
                                expected={"max_length": constraint.max_length},
                                actual=length,
                            )
                        )

        provided_optional: List[str] = []
        for name, constraint in spec.optional_fields.items():
            value = normalized.get(name)
            if value is None or (isinstance(value, str) and not value.strip()):
                continue

            provided_optional.append(name)

            if constraint.enum_values and value not in constraint.enum_values:
                errors.append(
                    ParameterError(
                        field=name,
                        code="invalid_choice",
                        message="Value is not allowed",
                        expected={"allowed": constraint.enum_values},
                        actual=value,
                    )
                )

            if isinstance(value, (int, float)):
                numeric_value = float(value)
            else:
                try:
                    numeric_value = float(value)
                except (TypeError, ValueError):
                    numeric_value = None

            if constraint.min_value is not None or constraint.max_value is not None:
                if numeric_value is None:
                    errors.append(
                        ParameterError(
                            field=name,
                            code="invalid_type",
                            message="Value must be numeric",
                            expected={"type": "number"},
                            actual=value,
                        )
                    )
                else:
                    if constraint.min_value is not None and numeric_value < constraint.min_value:
                        errors.append(
                            ParameterError(
                                field=name,
                                code="below_minimum",
                                message="Value is below the minimum allowed",
                                expected={"min": constraint.min_value},
                                actual=numeric_value,
                            )
                        )
                    if constraint.max_value is not None and numeric_value > constraint.max_value:
                        errors.append(
                            ParameterError(
                                field=name,
                                code="above_maximum",
                                message="Value is above the maximum allowed",
                                expected={"max": constraint.max_value},
                                actual=numeric_value,
                            )
                        )

        if require_optional is None:
            require_optional = settings.parameter_validation_require_optional

        if require_optional and len(provided_optional) < settings.parameter_validation_optional_min_count:
            errors.append(
                ParameterError(
                    field="*experimental_parameters",
                    code="insufficient_parameters",
                    message="At least one experimental parameter must be provided",
                    expected={"min_provided": settings.parameter_validation_optional_min_count},
                    actual=len(provided_optional),
                )
            )

        result = ParameterValidationResult(
            normalized_payload=normalized,
            provided_optional_fields=provided_optional,
            errors=errors,
        )

        if result.is_valid:
            LOGGER.debug(
                "Parameter validation succeeded with optional fields: %s", provided_optional
            )
            return result

        LOGGER.warning(
            "Parameter validation failed in context '%s' with %d error(s)",
            context,
            len(errors),
        )
        raise ParameterValidationError(errors, context=context)


@lru_cache(maxsize=1)
def get_parameter_validator() -> ParameterValidator:
    """Return a cached validator instance."""

    loader = ParameterSpecLoader()
    return ParameterValidator(loader)

