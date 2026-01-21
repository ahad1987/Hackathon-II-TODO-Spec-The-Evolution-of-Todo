# Backend Dockerfile for TaskFlow AI Chatbot
# Base Image: python:3.11-slim (Debian-based for psycopg2 wheel compatibility)
# Constitutional Compliance: NO application code modifications

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy requirements.txt first for layer caching optimization
COPY requirements.txt .

# Install dependencies
# --no-cache-dir: Don't cache pip packages (reduces image size)
# --upgrade: Ensure latest compatible versions
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application code AS-IS (IMMUTABLE per Constitution)
# Copies entire src/ directory without modifications
COPY src/ ./src/

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port 8000 (IMMUTABLE per api-contracts.md)
EXPOSE 8000

# Health check (optional but recommended)
# Checks /health endpoint every 30s
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run FastAPI application
# --host 0.0.0.0: Listen on all interfaces (required for container networking)
# --port 8000: IMMUTABLE port per Constitution
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

