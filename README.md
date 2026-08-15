# Techonomy — Enterprise RAG Knowledge Intelligence Platform

Techonomy is a high-performance, quota-managed Retrieval-Augmented Generation (RAG) platform designed for enterprise knowledge retrieval and real-time team competition events.

---

## 1. What the Project Is

Techonomy provides an intelligent knowledge query portal powered by FastAPI, sentence-transformers, Qdrant vector retrieval, and persistent LLM quota scheduling. It orchestrates multi-lane Gemini 2.0 Flash generation with seamless Nemotron 3.5 fallback, backed by atomic PostgreSQL team prompt quotas.

---

## 2. Architecture

```
                  ┌─────────────────────────────────────────┐
                  │          Client Browser / SEB           │
                  └────────────────────┬────────────────────┘
                                       │ HTTP / SSE Token Stream
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │       Vite React Frontend (:3000)       │
                  └────────────────────┬────────────────────┘
                                       │ REST / API Requests
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │       FastAPI RAG Backend (:8000)       │
                  └──────┬─────────────┬─────────────┬──────┘
                         │             │             │
        ┌────────────────┴┐    ┌───────┴──────┐   ┌──┴──────────────────────┐
        │ PostgreSQL DB   │    │  Qdrant Vector│   │ External LLM APIs       │
        │ (Local/Supabase)│    │  Storage     │   │ (Gemini 2.0 / Nemotron) │
        └─────────────────┘    └──────────────┘   └─────────────────────────┘
```

- **Frontend**: React 18, TypeScript, TailwindCSS, Vite, Axios.
- **Backend**: FastAPI, PyTorch, SentenceTransformer (`BAAI/bge-small-en-v1.5`), SQLAlchemy.
- **Database**: PostgreSQL (Local Docker Container or Supabase Cloud Pooler).
- **Vector DB**: Qdrant Vector Engine (Local Container or Embedded Disk Fallback).
- **LLM Gateway**: Multi-lane QuotaScheduler supporting Gemini 2.0 Flash (Primary) and OpenRouter Nemotron 3.5 (Fallback).

---

## 3. Prerequisites

- **Git** (v2.30+)
- **Docker Desktop** / **Docker Engine** with Compose plugin
- **Internet Access**: Required during initial setup for Docker base image downloads, HuggingFace model weight caching, and external LLM API inference.

---

## 4. Clone

```bash
git clone https://github.com/Pawan-19012006/Techonomy-Application.git
cd Techonomy-Application
```

---

## 5. Environment Setup

Create your local `.env` file from the repository template:

```bash
cp .env.example .env
```

Open `.env` and fill in your LLM API keys:

```env
GEMINI_API_KEY="your-actual-gemini-api-key"
OPENROUTER_API_KEY="your-actual-openrouter-api-key"
JWT_SECRET="secure-random-jwt-secret"
```

> **IMPORTANT**: Never commit `.env` or credentials to Git history.

---

## 6. Local Docker Deployment

To launch the complete application stack (Frontend, Backend, Local PostgreSQL, Qdrant):

```bash
docker compose up --build
```

Docker Compose will automatically start:
1. `techonomy_postgres`: Local PostgreSQL 16 database.
2. `techonomy_qdrant`: Qdrant vector engine.
3. `techonomy_backend`: FastAPI backend server.
4. `techonomy_frontend`: Vite React web application.

---

## 7. Application URLs

- **Frontend Web Portal**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Backend Health Probe**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 8. Supabase / Event Deployment (Mode B)

To switch the backend from the local PostgreSQL container to an authoritative Supabase PostgreSQL instance:

1. Open `.env`.
2. Update `DATABASE_URL` to point to your Supabase Pooler URI:

```env
DATABASE_URL="postgresql://user:password@aws-0-region.pooler.supabase.com:5432/postgres?sslmode=require"
```

3. Re-launch Docker Compose:

```bash
docker compose up --build
```

---

## 9. College LAN Deployment Setup

To serve multiple student computers over a local network from one host laptop:

1. **Find Laptop LAN IP Address**:
   - macOS: `ipconfig getifaddr en0` (e.g. `192.168.1.50`).
   - Linux: `hostname -I | awk '{print $1}'`.
   - Windows: `ipconfig` (Look for IPv4 Address).
2. **Update `.env` Configuration**:
   ```env
   CORS_ORIGINS="http://localhost:3000,http://192.168.1.50:3000"
   VITE_API_BASE_URL="http://192.168.1.50:8000"
   ```
3. **Launch Docker Stack**:
   ```bash
   docker compose up --build
   ```
4. **Connect Client Computers**:
   On student computers connected to the same Wi-Fi/LAN, open:
   ```
   http://192.168.1.50:3000
   ```

---

## 10. Troubleshooting

- **Port 8000 or 3000 Conflict**: Stop existing services using the port or run `lsof -i :8000`.
- **Database Connection Failure**: Verify PostgreSQL status with `docker compose ps` or test credentials.
- **Model Download Issue**: Run `python3 backend/scripts/preload_models.py` while connected to the Internet to populate the HuggingFace cache volume.
- **CORS Error on LAN**: Ensure `CORS_ORIGINS` in `.env` includes `http://<LAPTOP_LAN_IP>:3000`.

---

## 11. Development Without Docker (Native Mode)

If you prefer running natively without Docker:

### Backend Native Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/preload_models.py
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Native Setup
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 3000
```

---

## 12. Running Automated Tests

To run the full backend unit and integration test suite:

```bash
cd backend
PYTHONPATH=. .venv/bin/python -m pytest tests/
```

Baseline: **127 / 127 tests passing**.

---

## 13. Real LLM Provider Credential Validation

To execute validation tests against live external APIs (Gemini 2.0 Flash & OpenRouter Nemotron 3.5):

1. Configure real API credentials in `.env`:
   ```env
   GEMINI_API_KEY="your-live-gemini-api-key"
   OPENROUTER_API_KEY="your-live-openrouter-api-key"
   ```
2. Run live validation via local Python virtual environment:
   ```bash
   cd backend
   PYTHONPATH=. .venv/bin/python -m pytest tests/test_real_providers.py -v
   ```
3. Or run live validation inside the active Docker Compose container stack:
   ```bash
   docker compose exec backend python -m pytest tests/test_real_providers.py -v
   ```

> **Note**: Real provider tests require active internet connectivity and valid API keys. If keys are missing, tests will cleanly skip without failing.

