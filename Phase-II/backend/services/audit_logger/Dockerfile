# Phase V: Audit Logger Service Dockerfile (T064)
# Constitutional Compliance: Standalone service with Dapr sidecar for Pub/Sub

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend source code (needed for database models)
COPY backend/src /app/backend/src

# Copy audit logger service
COPY backend/services/audit_logger /app/backend/services/audit_logger

# Set Python path to include backend src
ENV PYTHONPATH=/app/backend/src:/app/backend/services/audit_logger

# Expose service port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8004/health/live')" || exit 1

# Run service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004", "--log-level", "info"]
