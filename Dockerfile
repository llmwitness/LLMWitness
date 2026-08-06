# Multi-Stage Production Dockerfile for AgentTrace Microservices
FROM python:3.11-slim as base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy codebase
COPY agenttrace_sdk.py gateway.py ingest.py utils.py config.py ./

EXPOSE 8000 8011

CMD ["uvicorn", "gateway:app", "--host", "0.0.0.0", "--port", "8011"]
