FROM python:3.13-slim

WORKDIR /app

# Install system dependencies required for native packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and helper scripts
COPY app ./app
COPY scripts ./scripts

# Create data, logs, and qdrant storage directories
RUN mkdir -p /app/data/uploads /app/data/documents /app/data/exports /app/logs /app/qdrant_storage

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
