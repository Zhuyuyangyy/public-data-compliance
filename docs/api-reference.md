# API Reference

> Base URL: `http://localhost:8013/api/v1`
> Interactive docs: `http://localhost:8013/docs` (Swagger UI)

---

## Core Endpoints

### POST /register_catalog

Register a new data catalog entry with field-level sensitivity analysis.

**Request Body:**
```json
{
  "name": "string (required)",
  "department": "string (required)",
  "data_type": "public | sensitive | personal (required)",
  "fields": [
    {
      "name": "string (required)",
      "description": "string",
      "data_type": "string",
      "sensitivity": "low | medium | high | extreme",
      "is_personal_info": false,
      "is_sensitive_info": false,
      "can_reidentify": false
    }
  ],
  "source_info": "string",
  "auth_scope": "string",
  "sensitivity_level": "low | medium | high | extreme"
}
```

**Response:** `DataCatalogResponse` with detected data type, recommended sensitivity, and issue count.

---

### POST /create_authorization

Create an authorization record for a data catalog.

**Request Body:**
```json
{
  "catalog_id": 1,
  "authorized_party": "string (required)",
  "usage_scope": "string (required)",
  "valid_from": "YYYY-MM-DD",
  "valid_to": "YYYY-MM-DD"
}
```

**Response:** `AuthorizationResponse` with status and timestamps.

---

### POST /upload_data_product

Upload a data product linked to a catalog for compliance review.

**Request Body:**
```json
{
  "catalog_id": 1,
  "product_name": "string (required)",
  "product_description": "string",
  "fields": [{"name": "string", "description": "string"}],
  "process_description": "string"
}
```

**Response:** Product ID, parse results, and field analysis.

---

### POST /check_authorization

Verify whether a requester is authorized for specific fields and purposes.

**Request Body:**
```json
{
  "catalog_id": 1,
  "requester": "string",
  "intended_use": "string",
  "requested_fields": ["field1", "field2"]
}
```

**Response:** `AuthorizationCheckResponse` with authorized/unauthorized fields and issues.

---

### POST /analyze_privacy_risk

Run privacy risk analysis on a catalog or inline fields.

**Request Body:**
```json
{
  "catalog_id": 1,
  "fields": [{"name": "string", "description": "string"}]
}
```

**Response:** `PrivacyRiskResponse` with personal/sensitive counts, re-identification risks, and risk score.

---

### GET /get_risk_report/{catalog_id}

Generate a comprehensive compliance report for a catalog entry.

**Response:** `ReportResponse` with risk scores, issues, review opinions, and rectification suggestions.

---

### GET /get_lineage/{catalog_id}

Retrieve the data lineage graph for a catalog entry.

**Response:** `LineageResponse` with nodes, edges, and completeness flag.

---

### GET /audit_logs

Query the audit trail.

**Query Parameters:**
- `limit` (int, default 50): Maximum number of log entries.

**Response:** List of audit log entries with timestamps.

---

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "public-data-compliance",
  "version": "1.0.0"
}
```

---

## Auxiliary Endpoints

### POST /map_sensitivity

Map data items to sensitivity levels with multi-factor scoring.

### POST /assess_breach_risk

Assess data breach/exposure risk based on collection scale, authorization status, and security measures.

### POST /authorize_data_use

Process data use authorization requests with automatic decision logic.

### GET /check_compliance

Check overall compliance status for an organization's data operations.

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad request / invalid input |
| 404 | Resource not found |
| 422 | Validation error (Pydantic) |
| 500 | Internal server error |
