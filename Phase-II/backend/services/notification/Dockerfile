# Phase V: Notification Service Dockerfile (T055)
# Multi-stage build for optimized image size

FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy source code
COPY backend/src /app/backend/src
COPY backend/services/notification /app/backend/services/notification

# Set Python path
ENV PYTHONPATH=/app/backend

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8003/health/live').raise_for_status()" || exit 1

# Run service
CMD ["python", "-m", "uvicorn", "services.notification.main:app", "--host", "0.0.0.0", "--port", "8003"]
