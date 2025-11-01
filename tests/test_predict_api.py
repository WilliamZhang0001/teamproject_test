import asyncio
import json
import sys
from pathlib import Path

import pytest
from starlette.requests import Request

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.app.api.v1_predict import (  # noqa: E402
    PredictRequest,
    idempotency_cache,
    predict,
)
from backend.app.core.security import create_access_token  # noqa: E402


def _make_request() -> Request:
    async def receive() -> dict:
        return {"type": "http.request", "body": b"", "more_body": False}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/predict",
        "headers": [],
        "client": ("test", 1234),
    }
    return Request(scope, receive)


@pytest.fixture(autouse=True)
def clear_idempotency_cache():
    idempotency_cache._store.clear()  # type: ignore[attr-defined]
    yield
    idempotency_cache._store.clear()  # type: ignore[attr-defined]


@pytest.fixture(scope="module")
def auth_header() -> str:
    return f"Bearer {create_access_token('1')}"


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_predict_scenario1_success(auth_header: str):
    payload = PredictRequest(
        biomolecule_name="lysozyme",
        biomolecule_type="protein",
        property="stability",
        pH=7.0,
        temperature_c=25.0,
        concentration_mg_ml=10.0,
    )
    response = _run(predict(payload, _make_request(), authorization=auth_header, idempotency_key=None))
    assert response.status_code == 200
    data = json.loads(response.body)
    assert set(data.keys()) == {"prediction", "confidence", "probabilities", "model_used", "recommendation"}
    assert data["model_used"] == "RandomForest"


def test_predict_scenario2_recommendation(auth_header: str):
    payload = PredictRequest(
        biomolecule_name="lysozyme",
        property="stability",
        known_parameters={"pH": 7.0, "temperature_c": 25.0},
        recommend_parameters=["concentration_mg_ml", "ionic_strength_mM"],
    )
    response = _run(predict(payload, _make_request(), authorization=auth_header, idempotency_key=None))
    assert response.status_code == 200
    data = json.loads(response.body)
    assert "concentration_mg_ml" in data
    assert set(data["concentration_mg_ml"].keys()) == {
        "recommended_value",
        "safe_range",
        "full_range",
        "sample_count",
        "source",
    }


def test_predict_idempotency(auth_header: str):
    payload = PredictRequest(
        biomolecule_name="lysozyme",
        biomolecule_type="protein",
        property="stability",
        pH=6.5,
    )
    response1 = _run(predict(payload, _make_request(), authorization=auth_header, idempotency_key="dup-key"))
    response2 = _run(predict(payload, _make_request(), authorization=auth_header, idempotency_key="dup-key"))
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert json.loads(response1.body) == json.loads(response2.body)


def test_predict_authentication_failure():
    payload = PredictRequest(biomolecule_name="lysozyme", property="stability", pH=7.0)
    response = _run(predict(payload, _make_request(), authorization=None, idempotency_key=None))
    assert response.status_code == 401
    data = json.loads(response.body)
    assert data["error_code"] == "unauthorized"
