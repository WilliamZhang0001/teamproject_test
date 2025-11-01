"""Minimal asynchronous job endpoints."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from threading import Lock
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.services.model_orchestrator import ModelOrchestrator

from .v1_predict import _enforce_rate_limit, _require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/jobs", tags=["ml-jobs"])


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass
class Job:
    job_id: str
    created_at: float
    task_type: str
    payload: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class JobCreateRequest(BaseModel):
    task_type: str = Field(default="predict")
    payload: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class JobStore:
    def __init__(self) -> None:
        self._jobs: Dict[str, Job] = {}
        self._lock = Lock()

    def create(self, task_type: str, payload: Dict[str, Any]) -> Job:
        job = Job(job_id=str(uuid4()), created_at=time.time(), task_type=task_type, payload=payload)
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **kwargs: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            for key, value in kwargs.items():
                setattr(job, key, value)


store = JobStore()
async_orchestrator = ModelOrchestrator()


def _process_job(job_id: str) -> None:
    job = store.get(job_id)
    if not job:
        return

    store.update(job_id, status=JobStatus.RUNNING)
    try:
        if job.task_type == "predict":
            payload = job.payload
            result = async_orchestrator.execute(payload)
            store.update(job_id, status=JobStatus.SUCCEEDED, result=result)
        else:
            raise ValueError(f"Unsupported task_type: {job.task_type}")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Background job failed", extra={"job_id": job_id})
        store.update(job_id, status=JobStatus.FAILED, error=str(exc))


@router.post("")
async def create_job(
    request: Request,
    background: BackgroundTasks,
    body: JobCreateRequest,
    authorization: Optional[str] = Header(default=None, convert_underscores=False),
) -> JSONResponse:
    auth_payload = _require_auth(authorization)
    _enforce_rate_limit(auth_payload, request)

    job = store.create(body.task_type, body.payload)
    background.add_task(_process_job, job.job_id)

    logger.info(
        "Created async job",
        extra={"job_id": job.job_id, "task_type": job.task_type, "user_id": auth_payload.get("sub")},
    )

    return JSONResponse(status_code=202, content={"job_id": job.job_id})


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    request: Request,
    authorization: Optional[str] = Header(default=None, convert_underscores=False),
) -> JSONResponse:
    auth_payload = _require_auth(authorization)
    _enforce_rate_limit(auth_payload, request)

    job = store.get(job_id)
    if not job:
        response = {"error_code": "not_found", "message": "Job not found", "details": {"job_id": job_id}}
        return JSONResponse(status_code=404, content=response)

    payload: Dict[str, Any] = {
        "job_id": job.job_id,
        "status": job.status.value,
        "result_json": job.result if job.status == JobStatus.SUCCEEDED else None,
        "result_url": None,
    }
    if job.status == JobStatus.FAILED:
        payload["error"] = job.error

    return JSONResponse(status_code=200, content=payload)
