# API Gateway – Model Orchestration Interfaces

This document describes the unified API gateway endpoints that connect the frontend to the
model orchestration layer. The contracts below align with the official examples in
`DemoB模型部分QuickStart.md`.

## Authentication & Guardrails

* **Authentication** – All endpoints require a valid `Authorization: Bearer <JWT>` header.
* **Rate limiting** – Requests are throttled per user, token and IP (default: 120 requests/minute).
  Exceeding the limit returns HTTP 429 with `{"error_code": "rate_limited"}`.
* **Idempotency** – Provide `Idempotency-Key` for safe retries on `POST /api/v1/predict`.
  Cached responses are replayed for identical payloads.
* **Audit logging** – Every call records the scenario, latency and caller identifier.
* **Metrics** – Prometheus metrics are exported for prediction latency, model selection rate and
  IQR hit levels (`ml_prediction_latency_seconds`, `ml_model_selection_total`,
  `ml_model_degradation_total`, `ml_iqr_hit_level_total`).

## 1. POST `/api/v1/predict`

Gateway entry point for both business scenarios. The request body must follow the examples
below and field names/casing are fixed.

### Scenario 1 – 参数可行性验证

**Request**
```json
{
  "biomolecule_name": "lysozyme",
  "biomolecule_type": "protein",
  "property": "stability",
  "pH": 7.0,
  "temperature_c": 25.0,
  "concentration_mg_ml": 10.0,
  "ionic_strength_mM": 150.0,
  "additive": "glycerol"
}
```

**Success response**
```json
{
  "prediction": "stable",
  "confidence": 0.85,
  "probabilities": {
    "stable": 0.85,
    "unstable": 0.15
  },
  "model_used": "LightGBM",
  "recommendation": "该实验条件预计可行，建议进行实验验证"
}
```

* `model_used` reflects the best available model. Fallback order: LightGBM → XGBoost → RandomForest
  (heuristic guard model). Degradation events increment `ml_model_degradation_total`.

### Scenario 2 – 参数范围推荐

If `known_parameters` is present the gateway switches to IQR recommendation mode.

**Request**
```json
{
  "biomolecule_name": "lysozyme",
  "property": "stability",
  "known_parameters": {
    "pH": 7.0,
    "temperature_c": 25.0
  },
  "recommend_parameters": ["concentration_mg_ml", "ionic_strength_mM"]
}
```

**Success response**
```json
{
  "concentration_mg_ml": {
    "recommended_value": 10.0,
    "safe_range": [5.0, 20.0],
    "full_range": [0.1, 100.0],
    "sample_count": 1234,
    "source": "基于所有 stability 实验数据"
  },
  "ionic_strength_mM": {
    "recommended_value": 150.0,
    "safe_range": [100.0, 200.0],
    "full_range": [0.0, 500.0],
    "sample_count": 987,
    "source": "基于 lysozyme 的 stability 数据"
  }
}
```

* Priority levels for lookups: `物质+实验` → `实验` → `物质` → `全局`.
  The hit level is recorded via `ml_iqr_hit_level_total{level="..."}`.

### Error responses

All failures follow the structure below. `details` is optional.

```json
{
  "error_code": "validation_failed",
  "message": "Parameter validation failed",
  "details": {
    "errors": [
      {"field": "pH", "code": "below_minimum", "message": "Value below minimum"}
    ]
  }
}
```

Error codes in use:

| Error code            | HTTP status | Description                               |
|-----------------------|-------------|-------------------------------------------|
| `unauthorized`        | 401         | Missing/invalid JWT                       |
| `validation_failed`   | 422         | Parameter spec validation error           |
| `rate_limited`        | 429         | Rate limit exceeded                       |
| `model_unavailable`   | 503         | No model available after fallbacks        |
| `internal_error`      | 500         | Unexpected server error                   |

## 2. Asynchronous Jobs

### POST `/api/v1/jobs`
Creates a background task. Currently `task_type` supports `predict` and reuses the same
orchestration logic. Returns 202 with:

```json
{"job_id": "<uuid>"}
```

### GET `/api/v1/jobs/{job_id}`
Returns job status.

```json
{
  "job_id": "...",
  "status": "PENDING|RUNNING|SUCCEEDED|FAILED",
  "result_json": {...},
  "result_url": null,
  "error": "..." // only when FAILED
}
```

## 3. File Upload (placeholder)

`POST /api/v1/upload` accepts a JSON body with `filename` and base64 encoded `content`. Files are
persisted locally and the API returns `{ "file_id": "...", "filename": "..." }`. Until object
storage is integrated, clients should continue sending JSON payloads directly to `/api/v1/predict`.
