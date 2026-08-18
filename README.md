# Techonomy

**Techonomy** is a production-grade, RAG-based (Retrieval-Augmented Generation) knowledge intelligence platform built for hackathons and technical competition events. It provides automated, verified, and context-aware responses to participant questions based on official event documentation.

### Production Architecture Summary

- **Backend**: FastAPI (Python 3.13) serving REST endpoints, SSE streams, and production React SPA assets.
- **Frontend**: React 19 + TailwindCSS v4 SPA (built via Node 20 multi-stage Docker build).
- **Embeddings**: Local `BAAI/bge-small-en-v1.5` (384-dimensional dense vectors, CPU-optimized).
- **Vector Database**: Qdrant Cloud cluster (or local Qdrant container fallback).
- **Relational Database**: PostgreSQL (Supabase Cloud or local Docker PostgreSQL container fallback).
- **LLM Load Balancing**: 20-Lane Priority Scheduler with 10 Gemini primary keys (`G01–G10`) and 10 OpenRouter / Nemotron 3.5 fallback keys (`N01–N10`).
- **Containerization**: Single-command container deployment via Docker Compose.
- **Public Tunneling**: Single-port public ingress via `ngrok`.

---

## 1. Prerequisites

The host machine running the Techonomy platform requires ONLY:

1. **Git**: To clone the repository.
2. **Docker Desktop** (or Docker Engine + Docker Compose): To build and run all services in isolated containers.
3. **ngrok CLI**: To expose the host's single port (`8000`) securely to the internet.
4. **Active Internet Connection**: Required to connect to Qdrant Cloud, Gemini / OpenRouter APIs, and download the embedding model on first run.

> [!NOTE]
> The host machine **does NOT require** Python, Node.js, npm, PostgreSQL, Qdrant, CUDA, or PyTorch installed locally. All build tools, runtime environments, native dependencies, and PyTorch (CPU-only build) are handled automatically inside Docker containers.

---

## 2. Clone the Project

Open a terminal on your host machine and run:

```bash
git clone <repository-url>
cd techonomy
```

---

## 3. Environment Configuration

All application configuration is managed via `backend/.env`.

### Step 1: Copy the Canonical Template

Run the following command from the repository root:

```bash
cp backend/.env.example backend/.env
```

> [!CAUTION]
> **NEVER commit `backend/.env` to Git.** It contains sensitive API keys and database credentials.

### Step 2: Configure Environment Variables

Edit `backend/.env` using any standard text editor. Below is a breakdown of all required configuration categories:

#### A. Application & Server Configuration
```env
PROJECT_NAME="Techonomy Knowledge Intelligence Platform"
VERSION=1.0.0
DEBUG=False
HOST=0.0.0.0
PORT=8000
JWT_SECRET=replace_with_a_secure_random_jwt_secret_key_here
JWT_ALGORITHM=HS256
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

#### B. Event & Team Quota Configuration
```env
QUESTION_LIMIT=10
```
- `QUESTION_LIMIT`: Maximum allowed query limit per team across the entire event.

#### C. Persistent Database Configuration
```env
DATABASE_URL=postgresql://techonomy:techonomy_pass@postgres:5432/techonomy_db
```
- Default uses the local PostgreSQL Docker container.
- For Cloud PostgreSQL (Supabase), replace with your Supabase pooler connection string:
  `postgresql://user:password@aws-0-region.pooler.supabase.com:5432/postgres?sslmode=require`

#### D. Vector Database Configuration (Qdrant Cloud)
```env
QDRANT_URL=https://your-cluster-id.qdrant.tech
QDRANT_API_KEY=your_qdrant_cloud_api_key_here
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=company_knowledge
```
- When `QDRANT_URL` and `QDRANT_API_KEY` are provided, Techonomy connects directly to your Qdrant Cloud cluster. If left empty, it falls back to the local `qdrant` container.

#### E. 20 LLM Provider API Keys (10 Gemini + 10 OpenRouter / Nemotron)
```env
# Primary LLM Keys (Gemini 2.0 Flash)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_API_KEY_1=your_gemini_key_1
GEMINI_API_KEY_2=your_gemini_key_2
GEMINI_API_KEY_3=your_gemini_key_3
GEMINI_API_KEY_4=your_gemini_key_4
GEMINI_API_KEY_5=your_gemini_key_5
GEMINI_API_KEY_6=your_gemini_key_6
GEMINI_API_KEY_7=your_gemini_key_7
GEMINI_API_KEY_8=your_gemini_key_8
GEMINI_API_KEY_9=your_gemini_key_9
GEMINI_API_KEY_10=your_gemini_key_10
GEMINI_MODEL=gemini-flash-lite-latest

# Fallback LLM Keys (OpenRouter / Nemotron 3.5)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_API_KEY_1=your_openrouter_key_1
OPENROUTER_API_KEY_2=your_openrouter_key_2
OPENROUTER_API_KEY_3=your_openrouter_key_3
OPENROUTER_API_KEY_4=your_openrouter_key_4
OPENROUTER_API_KEY_5=your_openrouter_key_5
OPENROUTER_API_KEY_6=your_openrouter_key_6
OPENROUTER_API_KEY_7=your_openrouter_key_7
OPENROUTER_API_KEY_8=your_openrouter_key_8
OPENROUTER_API_KEY_9=your_openrouter_key_9
OPENROUTER_API_KEY_10=your_openrouter_key_10
OPENROUTER_MODEL=nvidia/nemotron-3.5-lightning:free
MODEL_NAME=nvidia/nemotron-3.5-lightning:free
```
- **Provider Routing**: The scheduler routes queries across Gemini primary lanes (`G01–G10`). If Gemini lanes enter rate-limiting or exhaust capacity, queries automatically failover to OpenRouter / Nemotron fallback lanes (`N01–N10`).

#### F. Embedding & Retrieval Configuration
```env
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5
RETRIEVAL_TOP_K=10
TOP_K=10
```

---

## 4. Docker Startup

Start the complete application stack with a single command from the repository root:

```bash
docker compose up --build -d
```

### What Docker Does Automatically:
1. **Stage 1 (Frontend)**: Compiles the React 19 static production build inside a Node 20 container.
2. **Stage 2 (Backend)**: Pre-installs CPU-only PyTorch and Python backend dependencies.
3. **Database & Storage**: Launches local PostgreSQL and local Qdrant containers (if fallbacks are used).
4. **FastAPI Server**: Copies frontend static build artifacts to `/app/frontend/dist` and starts Uvicorn on port `8000`.
5. **Model Initialization**: Downloads the `BAAI/bge-small-en-v1.5` model (~133 MB) into a persistent Docker volume (`hf_cache`).

> [!NOTE]
> The initial `docker compose up --build` command may take 2–4 minutes depending on your internet speed as Docker pulls container base images and downloads the embedding model. Subsequent startups complete in seconds.

---

## 5. Verify Startup

### Check Container Status
```bash
docker compose ps
```
All containers (`techonomy_backend`, `techonomy_postgres`, `techonomy_qdrant`) should show status `Up` or `healthy`.

### Inspect Backend Logs
```bash
docker compose logs backend --tail=50
```

### Verify System Health Endpoint
Run this command from your terminal:

```bash
curl http://localhost:8000/health
```

**Expected JSON Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "qdrant": "connected",
  "embedding_model": "loaded"
}
```

### Check System Metrics & Status
```bash
curl http://localhost:8000/api/status
```

> [!TIP]
> If `embedding_model` displays `"loading"`, wait 30 seconds for Hugging Face model initialization to complete.

---

## 6. Event PDF / Knowledge Base Setup

> [!IMPORTANT]
> The repository includes sample mock PDFs in `backend/data/documents/`. **Do NOT use sample PDFs for the actual event.**

### Why Normal Ingestion Must NOT Be Repeated Without Reset
Techonomy chunks PDF content and assigns unique `uuid4` identifiers to each vector payload. Simply copying new files and re-running ingestion without clearing Qdrant creates duplicate chunks and causes vector retrieval pollution.

### Safe Event Knowledge Base Replacement Workflow

1. **Clean Host Data Directory**:
   Remove mock PDFs from `backend/data/documents/`:
   ```bash
   rm -f backend/data/documents/*.pdf
   ```

2. **Add Real Event PDFs**:
   Copy your official event PDF files into `backend/data/documents/`:
   ```bash
   cp /path/to/your/event_handbook.pdf backend/data/documents/
   ```

3. **Execute Event Knowledge Reset**:
   Run the safe event reset CLI script inside the running backend container:
   ```bash
   docker compose exec -it backend python scripts/reset_event.py
   ```

4. **Review Confirmation Prompt**:
   The script scans `backend/data/documents/`, displays discovered PDFs, and asks for confirmation:
   ```text
   ==================================================
   TECHONOMY KNOWLEDGE BASE RESET
   ==================================================

   This operation will DELETE the existing Qdrant collection:
   company_knowledge

   PDF files found:
     1. event_handbook.pdf

   Continue? [y/N]: y
   ```
   Type `y` and press **Enter**.

   *For non-interactive execution (e.g. automated scripts)*:
   ```bash
   docker compose exec backend python scripts/reset_event.py --yes
   ```

5. **Script Execution Actions**:
   - Recreates the Qdrant `company_knowledge` collection (384 dimensions, Cosine distance).
   - Extracts text and structure using PyMuPDF.
   - Chunks content with `SemanticChunker` (512 max tokens, 50 overlap).
   - Generates normalized BGE embeddings.
   - Uploads vectors to Qdrant Cloud.
   - Executes post-ingestion verification confirming vector count and indexed document names.

---

## 7. Knowledge Base Verification

Verify that only official event documents exist in your vector database:

```bash
docker compose exec backend python scripts/debug_qdrant.py
```

**Expected Output:**
```text
================================================================================
 🛠️ TECHONOMY QDRANT VECTOR DATABASE DEBUG UTILITY
================================================================================
 • Collection Name:         company_knowledge
 • Total Vector Points:     127
--------------------------------------------------------------------------------

 📄 INDEXED DOCUMENTS IN COLLECTION:
   [ 1] event_handbook.pdf

================================================================================
```

Ensure:
- `Total Vector Points` is greater than 0.
- Only your official event PDF filenames appear under `INDEXED DOCUMENTS`.

---

## 8. Starting ngrok

Techonomy serves both the React user interface and FastAPI endpoints through a single port (`8000`).

To expose the application to the internet, run ngrok on your host machine:

```bash
ngrok http 8000
```

**Terminal Output:**
```text
Session Status                online
Account                       Event Operator (Plan: Free)
Forwarding                    https://a1b2-c3d4-e5f6.ngrok-free.dev -> http://localhost:8000
```

Copy the generated **HTTPS URL** (e.g., `https://a1b2-c3d4-e5f6.ngrok-free.dev`). This is the **ONLY** URL required for the entire event.

---

## 9. Remote Device / Network Independence

- **Participant Experience**: Participants open the single HTTPS ngrok URL on their smartphones, laptops, or tablets.
- **Network Agnostic**: Participants can be connected to cellular hotspots, college Wi-Fi, home networks, or separate ISPs.
- **Zero Client Setup**: Participants do **NOT** need Docker, Python, backend access, or API keys.
- **Host Laptop Requirements**: The hosting operator laptop must remain:
  1. Powered on and awake (disable sleep mode).
  2. Connected to an active internet connection.
  3. Running Docker Desktop and the `backend` container.
  4. Running the `ngrok http 8000` process.

---

## 10. Event-Day Quick Start Checklist

Copy and execute these steps on event day:

```bash
# 1. Clone & enter repository
git clone <repository_url>
cd techonomy

# 2. Setup environment credentials
cp backend/.env.example backend/.env
# EDIT backend/.env with API keys & Qdrant Cloud credentials

# 3. Launch Docker stack
docker compose up --build -d

# 4. Check backend status
curl http://localhost:8000/health

# 5. Load real event PDFs
rm -f backend/data/documents/*.pdf
cp /path/to/official_event_docs/*.pdf backend/data/documents/

# 6. Reset & ingest vector database
docker compose exec -it backend python scripts/reset_event.py

# 7. Verify vector database
docker compose exec backend python scripts/debug_qdrant.py

# 8. Start public HTTPS tunnel
ngrok http 8000
```

---

## 11. Troubleshooting

| Symptom / Error | Cause | Solution / Diagnostic Command |
|---|---|---|
| `docker: command not found` | Docker Desktop is not installed or not added to PATH. | Install Docker Desktop for macOS/Windows/Linux. |
| `Cannot connect to Docker daemon` | Docker Desktop application is closed. | Launch Docker Desktop and wait until status shows "Engine Running". |
| `backend` container status `unhealthy` | Embedding model download or DB connection pending. | Check logs: `docker compose logs backend --tail=100` |
| Health check shows `"embedding_model": "loading"` | Hugging Face model download in progress. | Wait 30s and re-test: `curl http://localhost:8000/health` |
| `qdrant_client.http.exceptions.UnexpectedResponse: 401` | Incorrect `QDRANT_API_KEY` or `QDRANT_URL`. | Verify cluster URL and API key in `backend/.env`. |
| `psycopg2.OperationalError: Connection refused` | Database container initializing or invalid `DATABASE_URL`. | Test Postgres health: `docker compose exec postgres pg_isready -U techonomy -d techonomy_db` |
| `No LLM API keys configured` | `GEMINI_API_KEY_1..10` and fallback keys empty in `.env`. | Open `backend/.env` and paste at least one valid Gemini or OpenRouter key. |
| `reset_event.py` fails with `0 PDFs found` | `backend/data/documents/` has no `.pdf` files. | Copy event PDF files into `backend/data/documents/` before running script. |
| `PyMuPDF` or PDF extraction error | Corrupted or password-protected PDF. | Re-save PDF without password protection or export as standard PDF/A. |
| `ngrok: command not found` | ngrok CLI not installed. | Download ngrok from [ngrok.com](https://ngrok.com/download) or `brew install ngrok`. |
| `ngrok` error `ERR_NGROK_4018` | Authtoken not configured on host machine. | Run `ngrok config add-authtoken <your-token>` |
| Participants see `502 Bad Gateway` on ngrok | Docker container or backend process crashed. | Check backend logs: `docker compose logs backend --tail=50` |
| Browser displays old UI layout | Browser cached static assets. | Perform hard refresh (`Cmd+Shift+R` or `Ctrl+F5`) in participant browser. |

---

## 12. Stopping & Restarting

### Stop Containers (Preserving Volumes & Data)
```bash
docker compose down
```

### Restart Containers
```bash
docker compose up -d
```

### Reset All Local Container Volumes (Full Fresh State)
```bash
docker compose down -v
```

> [!NOTE]
> Restarting or stopping Docker containers does **NOT** delete vectors in your Qdrant Cloud database. Qdrant Cloud data persists until `scripts/reset_event.py` is explicitly executed.

---

## 13. Security Warnings

1. **Keep Secrets Private**: NEVER commit `backend/.env` or share `JWT_SECRET`, `QDRANT_API_KEY`, or LLM API keys.
2. **No Keys in Frontend**: All API key rotation and LLM invocations occur strictly on the backend. No credentials exist in the React bundle.
3. **Public Tunnel Awareness**: The ngrok HTTPS URL is accessible to anyone with the link. Keep host machine secure.
4. **Destructive Reset Protection**: `scripts/reset_event.py` wipes the target collection before re-indexing. Only event operators should execute this script.

---

## 14. Architecture Diagram

```text
  [ Participant Laptop / Phone ]
               │
               ▼ (Public Internet)
    https://xxxx.ngrok-free.dev
               │
               ▼ (ngrok Tunnel Ingress)
     [ Host Laptop : Port 8000 ]
               │
               ▼
     ┌────────────────────────────────────────────────────────┐
     │                FastAPI Application Container           │
     │                                                        │
     │  ┌────────────────────────┐  ┌──────────────────────┐  │
     │  │  React 19 SPA Static   │  │  /api/* REST & SSE   │  │
     │  │  Distribution Asset    │  │  Streaming Handlers  │  │
     │  └────────────────────────┘  └──────────┬───────────┘  │
     │                                         │              │
     │  ┌────────────────────────┐  ┌──────────▼───────────┐  │
     │  │ BGE-Small Embedding    │  │ 20-Lane Priority     │  │
     │  │ Model (CPU PyTorch)    │  │ LLM Quota Scheduler  │  │
     │  └───────────┬────────────┘  └──────────┬───────────┘  │
     └──────────────┼──────────────────────────┼──────────────┘
                    │                          │
        ┌───────────▼───────────┐  ┌───────────▼───────────┐
        │  Qdrant Cloud Cluster │  │  PostgreSQL Database  │
        │  (384-Dim Vector DB)  │  │  (Team Quota Records) │
        └───────────────────────┘  └───────────────────────┘
```

---

## 15. Important Operator Rules

1. **Keep Docker Running**: Keep Docker Desktop active throughout the event.
2. **Keep ngrok Running**: Keep the terminal running `ngrok http 8000` open.
3. **Keep Internet Active**: Ensure the host laptop maintains an active internet connection.
4. **Do Not Share Keys**: Keep `backend/.env` secure.
5. **Always Reset On PDF Change**: Do not copy new PDFs into `data/documents/` without running `scripts/reset_event.py`.
6. **Verify Qdrant**: Run `scripts/debug_qdrant.py` after indexing to confirm vector count and document names.
7. **Do Not Change Embedding Models**: Keep `EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5` consistent across ingestion and retrieval.
8. **Participants Only Need the Link**: Participants do not require backend setups or local tools.
