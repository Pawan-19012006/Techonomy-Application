# Techonomy: Enterprise Knowledge Intelligence Platform

Welcome to **Techonomy**, an Enterprise Knowledge Intelligence Platform built with FastAPI and React 19 + TypeScript, designed to deliver high-performance, modular Retrieval-Augmented Generation (RAG) and administrative control for enterprise teams.

---

## 🏗️ Architecture & Directory Structure

```text
techonomy/
├── backend/                    # FastAPI Backend Application
│   ├── app/                    # Main FastAPI application package
│   │   ├── main.py             # Application entry point & router definitions
│   │   ├── config.py           # Pydantic Settings configuration loading
│   │   ├── api/                # API Routers (auth, chat, dashboard, documents, event, history, teams, admin)
│   │   ├── auth/               # JWT security & bcrypt password hashing
│   │   ├── database/           # SQLite sessionmaker & SQLAlchemy 2.0 ORM models
│   │   ├── schemas/            # Pydantic data validation schemas
│   │   ├── services/           # Encapsulated business logic layer
│   │   └── middleware/         # HTTP request duration timing & exception handler
│   ├── tests/                  # Pytest test suite
│   ├── Dockerfile              # Backend container configuration
│   └── requirements.txt        # Python 3.13 dependencies
│
├── frontend/                   # React 19 + TypeScript + Vite Frontend Application
│   ├── src/
│   │   ├── api/                # Axios client & JWT interceptors
│   │   ├── components/         # Layouts, MetricCards, DocumentCards, ChatMessages
│   │   ├── contexts/           # AuthContext (JWT state) & ThemeContext
│   │   ├── hooks/              # Custom TanStack Query hooks
│   │   ├── pages/              # Login, Dashboard, Documents, Assistant, Rules, Team, 404
│   │   ├── types/              # TypeScript interfaces matching backend schemas
│   │   └── index.css           # Tailwind CSS theme & enterprise styling
│   ├── package.json            # Node.js dependencies
│   └── vite.config.ts          # Vite build & proxy settings
│
└── process_log.md              # Complete development step tracker
```

---

## ⚡ Development Setup

### 1. Backend Setup (FastAPI)
```bash
cd backend/
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Run Tests
python -m pytest tests/

# Start Server (runs on http://localhost:8000)
uvicorn app.main:app --reload
```

### 2. Frontend Setup (React 19 + Vite)
```bash
cd frontend/
npm install

# Start Dev Server (runs on http://localhost:3000)
npm run dev

# Build Production Bundle
npm run build
```

---

## 🛠️ Tech Stack

### Backend
- **Python 3.13** & **FastAPI**
- **SQLAlchemy 2.0** & **SQLite**
- **PyJWT** & **Bcrypt**
- **Pydantic v2** & **Uvicorn**

### Frontend
- **React 19** & **TypeScript**
- **Vite** & **Tailwind CSS**
- **TanStack Query (React Query)**
- **Axios** (with JWT request/response interceptors)
- **React Hook Form** & **Zod**
- **Lucide Icons** & **Sonner Toasts**
