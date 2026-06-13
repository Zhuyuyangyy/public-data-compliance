# PublicData Compliance -- Public Data Authorization Operations Compliance Review System

[![CI](https://github.com/ZYY-Project/public-data-compliance/actions/workflows/ci.yml/badge.svg)](https://github.com/ZYY-Project/public-data-compliance/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> End-to-end compliance auditing for public data authorization operations, featuring data lineage graphs, privacy risk detection, and multi-dimensional risk entropy scoring.

---

## Overview

PublicData Compliance addresses the regulatory challenges of public data authorization and operations -- a rapidly growing domain in China's data factor market. The system provides a complete pipeline from data catalog registration to compliance report generation, ensuring that public data resources are authorized, tracked, and risk-assessed throughout their lifecycle.

The platform is built around four patented technologies: data lineage graph-based authorization verification, sensitive field risk entropy assessment, semantic-closure product auditing, and full-process audit tracing.

---

## Key Features

- **Data Catalog Registration and Parsing** -- Automatic identification of data types (public, sensitive, personal information), intelligent detection of sensitive fields, and sensitivity level assessment with recommendations.
- **Authorization Scope Verification** -- Data lineage graph-based validation that detects overreach in data usage, cross-department sharing violations, and unauthorized downstream processing.
- **Privacy Risk Detection** -- Automated detection of personal information fields, sensitive personal data, re-identification risks, and anonymization/de-identification quality assessment.
- **Data Lineage Graph** -- Full tracking of data origin, transformation pathways, and processing chains. Supports downstream impact analysis for breach containment.
- **Multi-Dimensional Risk Entropy Scoring** -- Four-dimensional risk model (openness, authorization, privacy, re-identification) with coupling analysis and risk fuse mechanism.
- **Compliance Report Generation** -- Automated reports with issue summaries, risk classifications, review opinions, and remediation recommendations.
- **Audit Trail** -- Complete operational logging for regulatory inspection readiness.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, uvicorn |
| Database | SQLite (local) |
| Validation | Pydantic 2.9.2 |
| Frontend | Vue 3 (single-file) |
| Charts | ECharts 5 |
| Rules Engine | JSON-based configurable rule library |
| Testing | pytest, pytest-cov, httpx |
| Linting | ruff |
| Deployment | Docker, Docker Compose |

---

## Quick Start

### Prerequisites

- Python 3.10+ (recommended 3.12)
- Docker (optional)

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start the backend server
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8013

# Or use the Windows batch script
start.bat
```

The API server starts at `http://localhost:8013`. Interactive docs at `http://localhost:8013/docs`.

### Frontend

Open `frontend/index.html` directly in a browser. No build step required.

### Docker

```bash
# Build and run with Docker
docker build -t public-data-compliance .
docker run -d -p 8013:8013 public-data-compliance

# Or use Docker Compose
docker compose up -d
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/register_catalog` | Register a new data catalog entry |
| `POST` | `/api/v1/create_authorization` | Create an authorization record |
| `POST` | `/api/v1/upload_data_product` | Upload a data product for review |
| `POST` | `/api/v1/check_authorization` | Verify authorization scope |
| `POST` | `/api/v1/analyze_privacy_risk` | Run privacy risk analysis |
| `GET` | `/api/v1/get_risk_report/{catalog_id}` | Retrieve risk assessment report |
| `GET` | `/api/v1/get_lineage/{catalog_id}` | Retrieve data lineage graph |
| `GET` | `/api/v1/audit_logs` | Query audit logs |
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/map_sensitivity` | Map data items to sensitivity levels |
| `POST` | `/api/v1/assess_breach_risk` | Assess data breach risk |
| `POST` | `/api/v1/authorize_data_use` | Process authorization requests |
| `GET` | `/api/v1/check_compliance` | Check organization compliance status |

Full OpenAPI documentation available at `/docs` when the server is running. See [docs/api-reference.md](docs/api-reference.md) for detailed documentation.

---

## Project Structure

```
public-data-compliance/
├── backend/
│   ├── app/
│   │   ├── main.py                          # FastAPI application entry
│   │   ├── api/
│   │   │   └── routes.py                    # API endpoints (8 core + 4 auxiliary)
│   │   ├── core/
│   │   │   └── database.py                  # SQLite initialization
│   │   ├── models/
│   │   │   └── schemas.py                   # Pydantic data models
│   │   ├── services/
│   │   │   ├── data_catalog_parser.py       # Catalog registration and parsing
│   │   │   ├── data_lineage_tracker.py      # Data lineage graph engine
│   │   │   ├── authorization_checker.py     # Authorization scope validation
│   │   │   ├── privacy_risk_detector.py     # Privacy risk detection
│   │   │   ├── data_risk_scorer.py          # Multi-dimensional risk entropy
│   │   │   └── report_generator.py          # Compliance report generation
│   │   └── rules/
│   │       └── data_compliance_rules.json   # Configurable rule library
│   ├── data/                                # SQLite database directory
│   └── requirements.txt
├── frontend/
│   └── index.html                           # Vue 3 single-file frontend
├── tests/
│   ├── conftest.py                          # Shared test fixtures
│   ├── test_smoke.py                        # Smoke tests (imports, basic flows)
│   ├── test_api.py                          # API endpoint tests (12 endpoints)
│   └── test_services.py                     # Service unit tests (80+ test cases)
├── docs/
│   ├── architecture.md                      # System architecture documentation
│   ├── api-reference.md                     # API reference documentation
│   └── deployment.md                        # Deployment guide
├── .github/workflows/ci.yml                 # CI/CD pipeline
├── docker-compose.yml                       # Docker Compose configuration
├── Dockerfile                               # Docker build configuration
├── pyproject.toml                           # Project configuration
├── requirements.txt                         # Root dependencies
├── TODO.md                                  # Innovation suggestions
├── INNOVATION_ROADMAP.md                    # Patent portfolio strategy
├── CONTRIBUTING.md                          # Contribution guidelines
├── LICENSE                                  # MIT License
└── OPTIMIZATION_REPORT.md                   # Project optimization report
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=backend --cov-report=term-missing

# Run specific test suite
pytest tests/test_api.py -v
pytest tests/test_services.py -v
```

---

## Risk Scoring Model

| Dimension | What It Measures |
|-----------|------------------|
| Openness Risk | Degree of data exposure and public accessibility |
| Authorization Risk | Scope compliance, overreach detection, expiry validation |
| Privacy Risk | PII density, sensitive field ratio, anonymization quality |
| Re-identification Risk | De-anonymization probability, linkage attack surface |

The system computes a coupled risk score using cross-dimensional amplification factors. A risk fuse triggers when any single dimension exceeds the critical threshold, forcing an overall "high risk" classification.

---

## Patent Portfolio

| Patent | Title | Core Innovation |
|--------|-------|-----------------|
| 1 | Data Lineage Graph-Based Authorization Scope Verification | Graph traversal for scope boundary enforcement |
| 2 | Sensitive Field Risk Entropy Assessment for Public Data Operations | Multi-dimensional privacy risk quantification |
| 3 | Semantic-Closure Data Product Compliance Review | Closed-loop semantic validation of data products |
| 4 | Full-Process Audit Tracing System for Public Data Authorization | End-to-end operational audit with tamper-proof logging |

See [INNOVATION_ROADMAP.md](INNOVATION_ROADMAP.md) for 5 additional patent proposals.

---

## Benchmarks

| Metric | Value |
|--------|-------|
| Sensitive field detection recall | 95%+ across standard PII patterns |
| Authorization scope verification latency | < 500ms per catalog entry |
| Lineage graph traversal depth | Supports 10+ hop chains |
| Risk scoring throughput | 100+ catalog entries per second |
| Rule library update | Hot-reload without service restart |

---

## Documentation

- [System Architecture](docs/architecture.md) -- Detailed architecture documentation
- [API Reference](docs/api-reference.md) -- Complete API endpoint documentation
- [Deployment Guide](docs/deployment.md) -- Installation and deployment instructions
- [Innovation Roadmap](INNOVATION_ROADMAP.md) -- Patent portfolio and innovation strategy
- [TODO](TODO.md) -- Innovation suggestions and technical debt

---

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

---

## Disclaimer

This system provides automated compliance analysis for reference purposes only. It does not constitute legal advice. Users should verify results against applicable data protection laws and regulations.

---

## Contact

For technical inquiries, collaboration proposals, or patent licensing:

- **Project Lead**: ZYY Project Team
- **Issues**: Please use GitHub Issues for bug reports and feature requests
