# System Architecture

## Overview

PublicData Compliance is a public data authorization operations compliance review system built on a layered architecture pattern. The system follows a pipeline approach where data flows through catalog registration, authorization verification, privacy risk detection, risk entropy scoring, and compliance report generation.

## Architecture Layers

```
+---------------------------------------------------------------+
|                    Frontend (Vue 3 SPA)                       |
|  index.html - Single-file Vue application with ECharts        |
+---------------------------------------------------------------+
                              |
                              | HTTP REST
                              v
+---------------------------------------------------------------+
|                    API Layer (FastAPI)                         |
|  routes.py - 8 core endpoints + 4 auxiliary endpoints         |
|  main.py   - App initialization, CORS, extra routers          |
+---------------------------------------------------------------+
                              |
                              v
+---------------------------------------------------------------+
|                    Service Layer                               |
|  +-------------------+  +---------------------+               |
|  | DataCatalogParser |  | AuthorizationChecker|               |
|  +-------------------+  +---------------------+               |
|  +---------------------+  +-------------------+               |
|  | PrivacyRiskDetector |  | DataLineageTracker|               |
|  +---------------------+  +-------------------+               |
|  +-------------------+  +--------------------+                |
|  | RiskEntropyScorer |  | ReportGenerator    |                |
|  +-------------------+  +--------------------+                |
+---------------------------------------------------------------+
                              |
                              v
+---------------------------------------------------------------+
|                    Data Layer                                  |
|  SQLite (database.py) + JSON Rules (data_compliance_rules.json)|
+---------------------------------------------------------------+
```

## Component Details

### 1. API Layer (`backend/app/api/routes.py`)

FastAPI router with 8 core endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/register_catalog` | POST | Register data catalog entries |
| `/create_authorization` | POST | Create authorization records |
| `/upload_data_product` | POST | Upload data products for review |
| `/check_authorization` | POST | Verify authorization scope |
| `/analyze_privacy_risk` | POST | Run privacy risk analysis |
| `/get_risk_report/{id}` | GET | Generate compliance reports |
| `/get_lineage/{id}` | GET | Retrieve data lineage graphs |
| `/audit_logs` | GET | Query audit trail |

### 2. Service Layer

#### DataCatalogParser
- Keyword-based field classification (personal, sensitive, public)
- Data type auto-detection from field metadata
- Sensitivity level recommendation engine
- Re-identification risk field combination detection

#### AuthorizationChecker
- Authorization scope validation with wildcard support
- Purpose compliance checking (authorized vs unauthorized uses)
- Cross-department sharing validation
- Over-authorization risk detection

#### PrivacyRiskDetector
- Regex-based PII field identification (12+ patterns)
- Sensitive personal data detection (12+ patterns)
- Re-identification risk combination analysis (8 combinations)
- Anonymization quality assessment

#### DataLineageTracker
- DAG-based data lineage graph management
- Node types: catalog, product, process
- Edge types: collection, processing, sharing
- Recursive upstream/downstream traversal
- Relational lineage for cross-catalog impact analysis

#### RiskEntropyScorer
- Four-dimensional risk model: openness, authorization, privacy, re-identification
- Cross-dimensional coupling analysis with configurable coefficients
- Risk fuse mechanism (extreme threshold triggers)
- Weighted entropy score with coupling penalty

#### ReportGenerator
- Multi-section compliance report generation
- Issue compilation across all dimensions
- Review opinion generation based on risk levels
- Rectification suggestion prioritization
- Markdown export capability

### 3. Data Layer

#### SQLite Database Tables
- `rules`: Configurable compliance rules with severity and penalty scores
- `data_catalogs`: Registered data catalog entries
- `authorization_records`: Authorization grants with scope and validity
- `data_lineage`: Source-target relationships for lineage tracking
- `analysis_results`: Risk scores per dimension with JSON details
- `audit_logs`: Time-stamped operational audit trail

#### JSON Rule Library
- 10 default compliance rules covering privacy, authorization, re-identification, data type, and lineage categories
- Configurable risk thresholds and coupling coefficients

## Data Flow

```
1. Catalog Registration
   User -> POST /register_catalog -> DataCatalogParser.parse_catalog()
   -> SQLite INSERT -> DataLineageTracker.add_catalog_node() -> Audit Log

2. Authorization Creation
   User -> POST /create_authorization -> SQLite INSERT
   -> AuthorizationChecker.add_authorization() -> Audit Log

3. Data Product Upload
   User -> POST /upload_data_product -> DataLineageTracker.add_product_node()
   -> DataLineageTracker.add_lineage_edge() -> DataCatalogParser.parse_catalog()
   -> Audit Log

4. Compliance Review
   User -> GET /get_risk_report/{id}
   -> PrivacyRiskDetector.detect_privacy_risk()
   -> AuthorizationChecker.check_authorization()
   -> DataLineageTracker.get_lineage_path()
   -> RiskEntropyScorer.score() -> ReportGenerator.generate_report()
   -> SQLite INSERT (analysis_results) -> Audit Log
```

## Design Patterns

1. **Singleton Pattern**: Each service module uses a module-level singleton (`get_*_instance()`) for state management
2. **Facade Pattern**: Each service exposes a convenience function (e.g., `parse_data_catalog()`) that wraps the class instantiation
3. **Pipeline Pattern**: Data flows through a series of processing stages (register -> authorize -> analyze -> report)
4. **Observer Pattern**: Audit logging is integrated at each pipeline stage

## Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Framework | FastAPI | Async support, automatic OpenAPI docs, Pydantic integration |
| Database | SQLite | Zero-config, file-based, suitable for single-instance deployment |
| Validation | Pydantic 2.x | Type safety, JSON schema generation, performance |
| Frontend | Vue 3 (CDN) | No build step, rapid prototyping, single-file deployment |
| Charts | ECharts 5 | Rich visualization, radar/graph chart support |
| Rules | JSON | Hot-reloadable, no code changes for rule updates |
