# ─── Build stage ────────────────────────────────────────────────────
FROM python:3.12-slim AS base

LABEL maintainer="ZYY Project"
LABEL description="Public Data Compliance - Data authorization compliance review system"
LABEL version="1.0.0"

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY tests/ ./tests/

# Create data directory with proper permissions
RUN mkdir -p /app/backend/data && chmod 755 /app/backend/data

# Expose API port
EXPOSE 8013

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8013/api/v1/health')" || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8013"]
