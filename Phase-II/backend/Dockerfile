# Phase V: Main Backend API Dockerfile (T067)
# Runs the main FastAPI backend with task API, chat API, and Dapr integration

FROM python:3.11-slim

WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r ./requirements.txt

# Copy backend source code
COPY src ./src

# Set Python path (allows "from src.*" imports)
ENV PYTHONPATH=/app/backend

# Expose backend port
EXPOSE 8000

# Health check (main backend runs on port 8000)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run main backend app
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
