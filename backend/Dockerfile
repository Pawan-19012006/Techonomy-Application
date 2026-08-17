FROM python:3.13-slim

WORKDIR /app

# Install system dependencies required for native packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install CPU-only PyTorch + python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code and helper scripts
COPY app ./app
COPY scripts ./scripts

# Create data, logs, and qdrant storage directories
RUN mkdir -p /app/data/uploads /app/data/documents /app/data/exports /app/logs /app/qdrant_storage

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
