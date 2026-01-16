FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY backend/src ./src
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH PORT=7860
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f http://localhost:7860/health || exit 1
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "7860"]
