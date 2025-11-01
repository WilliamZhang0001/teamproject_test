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

## 4. Frontend Input → API Gateway → Core Model → Unified Output

The platform implements a deterministic pipeline from user interaction in the frontend to the
unified response returned by the prediction endpoints. Each hop preserves the contracts documented
above while delegating responsibility to focused components.

### Stage 1 – Frontend Input Normalisation

* Frontend forms serialise their payloads exactly as shown in the Scenario 1/2 examples. Optional
  numeric fields may be omitted or sent as `null`; boolean flags such as additive usage are
  expressed through the presence of strings (e.g. any additive name implies `has_additive = 1`).
* The parameter specification loaded by `app.core.parameter_spec.ParameterSpecLoader` defines
  required/optional fields, numeric bounds and enumerations. When the request reaches the gateway,
  `_validation_payload` merges `known_parameters` into the body before running
  `validator.validate(...)`, ensuring that frontend-provided fields are canonicalised and enriched
  with derived values (e.g. converted units, trimmed strings) prior to model execution.

### Stage 2 – API Gateway Enforcement

* `/api/v1/predict` and `/api/v1/jobs` are implemented in `backend/app/api/v1_predict.py` and
  `backend/app/api/v1_jobs.py`. Both endpoints call `_require_auth` (JWT verification) and
  `_enforce_rate_limit` to gate access before any downstream work begins. Per-request metadata such
  as user id, token id and client IP compose the keys used by the in-memory `RateLimiter`.
* The gateway replays cached responses when an `Idempotency-Key` header is present, protecting the
  model layer from duplicate submissions. Errors with status `< 500` are also cached, enabling the
  frontend to surface deterministic validation feedback during retries.
* Once guardrails pass, the gateway feeds the normalised payload into `ModelOrchestrator.execute`.
  Success and failure paths are auditable through structured logging (`_audit_log`) and Prometheus
  metrics exposed by the orchestrator (`ml_prediction_latency_seconds`,
  `ml_model_selection_total`, `ml_model_degradation_total`, `ml_iqr_hit_level_total`).

### Stage 3 – Core Model Orchestration

* `ModelOrchestrator` (in `backend/app/services/model_orchestrator.py`) inspects the payload to
  branch between the stability prediction flow and the IQR recommendation flow. The same
  orchestrator instance is reused by synchronous calls and asynchronous jobs to guarantee identical
  business logic regardless of invocation mode.
* Prediction scenario:
  * Features are prepared by the `prepare_features` helper in the model adapter module, aligning
    runtime payloads with the training pipeline (feature ordering, missing-value flags, additive
    encoding).
  * `ModelPredictorAdapter` attempts to load LightGBM, then XGBoost, then RandomForest model bundles
    from `models/`. If all serialised artefacts are unavailable the adapter falls back to a heuristic
    `_FallbackModel`, ensuring the gateway never returns `model_unavailable` unless every candidate
    fails to load.
  * Latency and model selection statistics are recorded, and degradation events (when the best model
    is not LightGBM) increment `ml_model_degradation_total`.
* Recommendation scenario:
  * `IqrRepository.get_recommendations` resolves statistics from `models/iqr_statistics.json` using
    the documented priority order (`experiment+biomolecule` → `experiment` → `biomolecule` →
    `global`). Each parameter yields a payload matching the Scenario 2 response contract.
  * Hit provenance is surfaced via `source` strings and mirrored in the `ml_iqr_hit_level_total`
    metric for observability.

### Stage 4 – Unified Output Assembly

* For predictions, the orchestrator enriches the raw adapter output with rounded probabilities and a
  natural-language recommendation computed by `_build_recommendation`, producing the unified JSON
  structure consumed by the frontend result panels.
* For recommendations, the orchestrator returns a dictionary keyed by each requested parameter. The
  frontend can iterate this map without branching because every entry follows the same schema
  (`recommended_value`, `safe_range`, `full_range`, `sample_count`, `source`). Missing statistics are
  represented as `null`, signalling the UI to fall back to manual input guidance.
* Asynchronous jobs surface identical payloads under `result_json` once `status = SUCCEEDED`, so
  long-running workflows share the same rendering components as direct responses. Failures bubble up
  through `error_code` or job `error` fields, preserving the error-handling patterns described in the
  Error responses table.
