"""/api/v1/predict endpoint implementation."""
from __future__ import annotations

import logging
import time
from builtins import property as builtin_property
from collections import defaultdict, deque
from pathlib import Path
from threading import Lock
from typing import Any, Deque, Dict, Iterable, List, Optional, Tuple
from uuid import uuid4

import base64

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from backend.app.core.parameter_spec import ParameterValidationError, get_parameter_validator
from backend.app.core.security import verify_token
from backend.app.services.model_orchestrator import ModelNotAvailableError, ModelOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["ml-predict"])
_UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class ApiError(Exception):
    def __init__(self, status_code: int, error_code: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}


class PredictRequest(BaseModel):
    biomolecule_name: str = Field(..., description="Substance name")
    biomolecule_type: Optional[str] = Field(default="protein", description="Biomolecule type")
    property: str = Field(..., validation_alias=AliasChoices("property", "experiment_type"))
    pH: Optional[float] = Field(default=None)
    temperature_c: Optional[float] = Field(default=None)
    concentration_mg_ml: Optional[float] = Field(default=None)
    ionic_strength_mM: Optional[float] = Field(default=None)
    additive: Optional[str] = Field(default=None)
    time_min: Optional[float] = Field(default=None)
    shear_rate_s1: Optional[float] = Field(default=None)
    pressure_bar: Optional[float] = Field(default=None)
    known_parameters: Optional[Dict[str, float]] = Field(default=None)
    recommend_parameters: Optional[List[str]] = Field(default=None)

    model_config = ConfigDict(extra="forbid")

    @builtin_property
    def scenario(self) -> str:
        return "recommendation" if self.known_parameters is not None else "prediction"


class IdempotencyCache:
    def __init__(self) -> None:
        self._store: Dict[str, Tuple[int, Dict[str, Any]]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Tuple[int, Dict[str, Any]]]:
        with self._lock:
            return self._store.get(key)

    def set(self, key: str, status: int, payload: Dict[str, Any]) -> None:
        with self._lock:
            self._store[key] = (status, payload)


class RateLimiter:
    def __init__(self, limit: int = 60, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window = window_seconds
        self._counters: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            bucket = self._counters[key]
            while bucket and now - bucket[0] > self.window:
                bucket.popleft()
            if len(bucket) >= self.limit:
                retry_in = max(0.0, self.window - (now - bucket[0]))
                raise ApiError(
                    status_code=429,
                    error_code="rate_limited",
                    message="Rate limit exceeded",
                    details={"retry_in_seconds": round(retry_in, 2)},
                )
            bucket.append(now)


orchestrator = ModelOrchestrator()
validator = get_parameter_validator()
idempotency_cache = IdempotencyCache()
rate_limiter = RateLimiter(limit=120, window_seconds=60)


class UploadPayload(BaseModel):
    filename: str
    content: str


def _require_auth(authorization: Optional[str]) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise ApiError(status_code=401, error_code="unauthorized", message="Authorization header required")
    token = authorization.split(" ", 1)[1]
    try:
        payload = verify_token(token)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Token verification failed", extra={"error": str(exc)})
        raise ApiError(status_code=401, error_code="unauthorized", message="Invalid token") from exc
    return payload or {}


def _enforce_rate_limit(auth_payload: Dict[str, Any], request: Request) -> None:
    user_id = str(auth_payload.get("sub", "anonymous"))
    token_id = auth_payload.get("jti") or auth_payload.get("sub") or "anonymous"
    client_ip = request.client.host if request.client else "unknown"

    keys = {f"user:{user_id}", f"token:{token_id}", f"ip:{client_ip}"}
    for key in keys:
        rate_limiter.check(key)


def _validation_payload(body: PredictRequest) -> Dict[str, Any]:
    payload = body.model_dump(exclude_none=True)
    if body.known_parameters:
        payload.update(body.known_parameters)
    return payload


def _audit_log(user: Dict[str, Any], request: PredictRequest, response: Dict[str, Any], duration: float) -> None:
    logger.info(
        "Prediction request processed",
        extra={
            "user_id": user.get("sub"),
            "scenario": request.scenario,
            "biomolecule_name": request.biomolecule_name,
            "property": request.property,
            "duration_ms": round(duration * 1000, 2),
            "status": "success",
        },
    )


@router.post("/predict")
async def predict(
    payload: PredictRequest,
    request: Request,
    authorization: Optional[str] = Header(default=None, convert_underscores=False),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key", convert_underscores=False),
) -> JSONResponse:
    start = time.perf_counter()
    try:
        auth_payload = _require_auth(authorization)
        _enforce_rate_limit(auth_payload, request)

        if idempotency_key:
            cached = idempotency_cache.get(idempotency_key)
            if cached:
                status, body = cached
                logger.info(
                    "Idempotency cache hit",
                    extra={"key": idempotency_key, "scenario": payload.scenario},
                )
                return JSONResponse(status_code=status, content=body)

        body_dict = payload.model_dump(exclude_none=True)
        if payload.scenario == "prediction":
            to_validate = _validation_payload(payload)
            try:
                validation_result = validator.validate(to_validate)
            except ParameterValidationError as exc:
                raise ApiError(
                    status_code=422,
                    error_code="validation_failed",
                    message="Parameter validation failed",
                    details=exc.to_dict(),
                ) from exc
            body_dict.update(validation_result.normalized_payload)

        result = orchestrator.execute(body_dict)
        response_body = result
        status_code = 200

        duration = time.perf_counter() - start
        _audit_log(auth_payload, payload, response_body, duration)

        if idempotency_key:
            idempotency_cache.set(idempotency_key, status_code, response_body)

        return JSONResponse(status_code=status_code, content=response_body)
    except ApiError as exc:
        logger.warning(
            "API error encountered",
            extra={"error_code": exc.error_code, "error_message": exc.message, "details": exc.details},
        )
        response = {"error_code": exc.error_code, "message": exc.message, "details": exc.details}
        if idempotency_key and exc.status_code < 500:
            idempotency_cache.set(idempotency_key, exc.status_code, response)
        return JSONResponse(status_code=exc.status_code, content=response)
    except ModelNotAvailableError as exc:
        logger.error("Model not available", extra={"error": str(exc)})
        response = {
            "error_code": "model_unavailable",
            "message": "No prediction model is currently available",
            "details": {"reason": str(exc)},
        }
        return JSONResponse(status_code=503, content=response)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error in /predict endpoint")
        response = {
            "error_code": "internal_error",
            "message": "Internal server error",
            "details": {"reason": str(exc)},
        }
        return JSONResponse(status_code=500, content=response)


@router.post("/upload")
async def upload(
    request: Request,
    payload: UploadPayload,
    authorization: Optional[str] = Header(default=None, convert_underscores=False),
) -> JSONResponse:
    auth_payload = _require_auth(authorization)
    _enforce_rate_limit(auth_payload, request)

    file_id = str(uuid4())
    destination = _UPLOAD_DIR / f"{file_id}_{payload.filename}"
    try:
        content_bytes = base64.b64decode(payload.content)
    except Exception as exc:  # noqa: BLE001
        raise ApiError(
            status_code=400,
            error_code="invalid_upload",
            message="Invalid base64 content",
            details={"reason": str(exc)},
        ) from exc

    destination.write_bytes(content_bytes)

    logger.info(
        "Upload received",
        extra={"file_id": file_id, "filename": payload.filename, "user_id": auth_payload.get("sub")},
    )

    return JSONResponse(status_code=201, content={"file_id": file_id, "filename": payload.filename})
