FROM python:3.11-slim

WORKDIR /app/backend/services/audit_logger

# Make shared backend imports work
ENV PYTHONPATH=/app/backend:/app/backend/src

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy shared backend code
COPY backend/src /app/backend/src

# Copy audit logger service
COPY backend/services/audit_logger /app/backend/services/audit_logger

EXPOSE 8004

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8004/health/ready')" || exit 1



CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004", "--log-level", "info"]

