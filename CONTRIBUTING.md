# Contributing to Public Data Compliance System

Thank you for your interest in contributing to the Public Data Compliance System.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/public-data-compliance.git
cd public-data-compliance

# Install dependencies
cd backend
pip install -r requirements.txt

# Install development tools
pip install pytest ruff
```

## Running the Application

```bash
cd backend
start.bat
# Or: python -m uvicorn app.main:app --host 0.0.0.0 --port 8013
```

The API server starts at `http://localhost:8013`. API docs at `http://localhost:8013/docs`.

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=backend
```

## Code Quality

We use `ruff` for linting:

```bash
ruff check .
ruff check --fix .
```

## Project Structure

- `backend/app/services/` - Core services (catalog parser, privacy detector, auth checker, lineage tracker, risk scorer)
- `backend/app/api/` - FastAPI route definitions
- `backend/app/models/` - Pydantic data models
- `backend/app/rules/` - Compliance rule configurations
- `frontend/` - Vue3 single-file frontend
- `tests/` - Test suite

## Key Modules

1. **DataCatalogParser** - Parses data catalogs, detects personal/sensitive fields
2. **PrivacyRiskDetector** - Identifies privacy risks and re-identification threats
3. **AuthorizationChecker** - Validates authorization scope and purpose
4. **DataLineageTracker** - Tracks data flow from source to product
5. **RiskEntropyScorer** - Multi-dimensional risk entropy with coupling and fuse mechanisms
6. **ReportGenerator** - Generates compliance review reports

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes and add tests
4. Ensure all tests pass (`pytest tests/ -v`)
5. Run linting (`ruff check .`)
6. Commit with a clear message
7. Push and open a Pull Request

## Commit Message Convention

Use the format: `type(scope): description`

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring

## Reporting Issues

Please use GitHub Issues to report bugs or request features. Include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Python version and OS
