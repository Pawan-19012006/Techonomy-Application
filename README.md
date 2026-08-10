# Techonomy: Event Knowledge Intelligence Platform

Welcome to **Techonomy**, an Enterprise Knowledge Intelligence Platform built with FastAPI and React 19 + TypeScript, designed for hackathons and university knowledge competitions with modular Retrieval-Augmented Generation (RAG).

---

## 🏗️ Architecture & Target Design

```text
                    FastAPI
                       │
             ┌─────────┴─────────┐
             │                   │
         Team API             Chat API
             │                   │
        Team Service        Chat Service
             │                   │
             ▼                   ▼
          SQLite             RAG Engine
             │                   │
             │              Retriever
             │                   ↓
             │            Prompt Builder
             │                   ↓
             │                  LLM
             │                   │
             └───────► Prompt Logs
```

---

## 🔌 API Endpoints

- `POST /api/teams/join` - Join or re-enter event arena (`team_name`, `member_names`).
- `GET  /api/teams/{team_name}` - Retrieve team details (`started_at`, `member_names`).
- `POST /api/chat` - Submit RAG question (`team_name`, `question`).
- `GET  /api/teams/{team_name}/prompts` - Retrieve team prompt history logs.
- `GET  /health` - System health probe.

---

## ⚡ Development Setup

### Backend Setup (FastAPI)
```bash
cd backend/
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run Tests
python -m pytest tests/

# Start Server (runs on http://localhost:8000)
uvicorn app.main:app --reload
```

---

## 🛠️ Tech Stack

### Backend
- **Python 3.13** & **FastAPI**
- **SQLAlchemy 2.0** & **SQLite**
- **PyMuPDF** & **SentenceTransformers** (`BAAI/bge-small-en-v1.5`)
- **Qdrant Vector DB**
- **Pydantic v2** & **Uvicorn**
