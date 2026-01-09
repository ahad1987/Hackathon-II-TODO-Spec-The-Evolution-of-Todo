# Root-level Dockerfile for Railway deployment
# Builds the Phase II backend from the monorepo structure

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files from Phase-II/backend
COPY Phase-II/backend/requirements.txt ./requirements.txt
COPY Phase-II/backend/pyproject.toml ./pyproject.toml

# Install Python dependencies using pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code from Phase-II/backend
COPY Phase-II/backend/src ./src
COPY Phase-II/backend/tests ./tests

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
