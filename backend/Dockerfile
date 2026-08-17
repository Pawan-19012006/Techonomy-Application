# =====================================================================
# MULTI-STAGE REPRODUCIBLE PRODUCTION DOCKERFILE
# =====================================================================

# ---------------------------------------------------------------------
# STAGE 1: Build Production React Frontend (Node.js)
# ---------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ---------------------------------------------------------------------
# STAGE 2: Python Production Backend (FastAPI + CPU PyTorch)
# ---------------------------------------------------------------------
FROM python:3.13-slim
WORKDIR /app

# Install system dependencies required for native packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and pre-install CPU-only PyTorch + python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application source code and helper scripts
COPY backend/app ./app
COPY backend/scripts ./scripts

# Copy production React frontend static build from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create required runtime data, logs, and storage directories
RUN mkdir -p /app/data/uploads /app/data/documents /app/data/exports /app/logs /app/qdrant_storage

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
