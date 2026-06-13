# Deployment Guide

## Prerequisites

- Python 3.10+ (recommended 3.12)
- pip or uv package manager
- Docker (optional, for containerized deployment)

## Local Development

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Server

```bash
# Windows
cd backend && start.bat

# Linux/macOS
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8013 --reload
```

### 3. Access

- API: http://localhost:8013
- Swagger UI: http://localhost:8013/docs
- Frontend: Open `frontend/index.html` in a browser

## Docker Deployment

### Build and Run

```bash
# Build image
docker build -t public-data-compliance .

# Run container
docker run -d -p 8013:8013 --name pdc public-data-compliance
```

### Docker Compose

```bash
docker compose up -d
```

This starts the API server with persistent data volume and health checks.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHONDONTWRITEBYTECODE` | `1` | Prevent .pyc file creation |
| `PYTHONUNBUFFERED` | `1` | Enable unbuffered stdout |

## Database

The system uses SQLite with automatic initialization. The database file is created at:

```
backend/data/public_data_compliance.db
```

No manual migration is required. Tables and default rules are created on first startup.

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov httpx

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=backend --cov-report=term-missing

# Run specific test file
pytest tests/test_api.py -v
```

## CI/CD

The project includes GitHub Actions workflows:

1. **Lint**: Runs `ruff check .` for code quality
2. **Test**: Runs `pytest tests/ -v --tb=short`
3. **Docker**: Builds and verifies the Docker image

## Production Considerations

1. **Database**: For production, consider migrating from SQLite to PostgreSQL
2. **CORS**: Restrict `allow_origins` in `main.py` from `["*"]` to specific domains
3. **Authentication**: Add JWT/OAuth2 middleware for API authentication
4. **Logging**: Configure structured logging with log aggregation
5. **Monitoring**: Add Prometheus metrics endpoint
6. **Backup**: Implement regular database backup strategy
