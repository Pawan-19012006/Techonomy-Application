# Techonomy: Enterprise Knowledge Intelligence Platform

Welcome to **Techonomy**, an Enterprise Knowledge Intelligence Platform built with FastAPI, designed to deliver high-performance, modular Retrieval-Augmented Generation (RAG) and administrative control for enterprise teams.

This repository contains the production-ready **backend platform foundation** and the **competition platform engine** ready for RAG and AI model integration.

---

## 🏗️ Architecture & Directory Structure

The project follows a modular, layer-separated architecture to ensure maximum maintainability, testability, and scalability.

```text
backend/
├── app/                        # Main FastAPI application package
│   ├── __init__.py
│   ├── main.py                 # Application entry point & router definitions
│   ├── config.py               # Pydantic Settings configuration loading from .env
│   │
│   ├── api/                    # API Route Handlers (Routers)
│   │   ├── auth.py             # User authentication, token exchange
│   │   ├── chat.py             # Interactive AI chat & QA endpoints
│   │   ├── dashboard.py        # Unified team dashboard metric endpoint
│   │   ├── documents.py        # Document upload, listing, downloading, deletion
│   │   ├── event.py            # Event creation, status, activation/deactivation
│   │   ├── history.py          # Team query history logs
│   │   ├── teams.py            # Team registration & quota access checks
│   │   └── admin.py            # Platform metrics, prompt logs, analytics
│   │
│   ├── auth/                   # Authentication logic & FastAPI dependencies
│   │   ├── jwt.py              # JWT encoding/decoding (PyJWT)
│   │   ├── password.py         # Direct bcrypt password hashing
│   │   └── dependencies.py     # Auth dependencies (get_current_team, get_current_admin)
│   │
│   ├── database/               # Database adapters & connection pooling
│   │   ├── sqlite.py           # Relational SQLite sessionmaker & table reset helper
│   │   ├── qdrant.py           # Vector Database helper (stub/pending RAG)
│   │   └── models.py           # SQLAlchemy 2.0 ORM Models (Team, Event, Document, PromptLog, AuditLog)
│   │
│   ├── models/                 # Domain / Business logic models
│   │   ├── team.py             # Team domain model
│   │   ├── document.py         # Document domain model
│   │   ├── prompt_log.py       # Prompt history domain model
│   │   └── event.py            # System events / audit logs
│   │
│   ├── schemas/                # Pydantic Data Validation & Serialization models
│   │   ├── auth.py             # Login, Token schemas
│   │   ├── chat.py             # Chat query Pydantic schemas
│   │   ├── dashboard.py        # Unified dashboard response schema
│   │   ├── event.py            # Event payload Pydantic schemas
│   │   ├── team.py             # Team schema definitions & usage metrics
│   │   ├── document.py         # Document metadata & upload/delete schemas
│   │   └── admin.py            # Admin settings, logs & stats schemas
│   │
│   ├── services/               # Business logic / Service layer
│   │   ├── authentication.py   # Auth service logic
│   │   ├── team_service.py     # Team operations orchestrator
│   │   ├── document_service.py # Document metadata operations orchestrator
│   │   ├── event_service.py    # Competition event manager
│   │   ├── timer_service.py    # Event timer/remaining seconds calculator
│   │   ├── dashboard_service.py# Aggregates unified dashboard payload
│   │   ├── rate_limit.py       # API Rate Limiter
│   │   ├── logging_service.py  # System event logging
│   │   └── analytics.py        # Log aggregation & system metrics
│   │
│   ├── middleware/             # HTTP Middlewares
│   │   ├── auth.py             # Auth header validation
│   │   ├── logging.py          # Structured request/response logger (processing time)
│   │   └── exception_handler.py# Global error interception & cleanup
│   │
│   ├── utils/                  # Helper utilities
│   │   ├── logging.py          # Central structured log formatter (console + file)
│   │   ├── constants.py        # Shared defaults
│   │   ├── helpers.py          # Text processing/parsing tools
│   │   └── security.py         # Crypto utilities
│   │
│   └── prompts/                # Raw text assets for model configuration
│       ├── system_prompt.txt   # System role instructions
│       └── refusal_prompt.txt  # Guardrail & safe fallback replies
│
├── data/                       # Local filesystem storage directories (Git ignored)
│   ├── documents/              # Stored PDFs/MD source files
│   ├── uploads/                # Temporary uploaded files
│   └── exports/                # Generated reports & backups
│
├── logs/                       # Application logs directory
│   └── app.log                 # Output log file
│
├── tests/                      # Pytest Suite
│   ├── test_backend_foundation.py
│   └── test_competition_platform.py
│
├── .env                        # Local Environment Configuration (Ignored)
├── .env.example                # Configuration Blueprint
├── requirements.txt            # Python Dependencies
├── Dockerfile                  # API deployment configuration
├── docker-compose.yml          # Local multi-container stack (App + volumes)
└── .gitignore                  # Git patterns to ignore
```

---

## ⚡ Development Setup

### Prerequisites
- Python 3.13+
- Virtual Environment tool (`venv`)

### Installation
1. Clone the repository and navigate to the `backend/` directory:
   ```bash
   cd backend/
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

4. Create your local `.env` configuration:
   ```bash
   cp .env.example .env
   ```
   *(Note: The application has built-in safe defaults in `app/config.py` for local developer onboarding).*

### Running the Tests
To run the automated verification test suite:
```bash
python -m pytest tests/
```

### Running Locally
To launch the FastAPI development server:
```bash
uvicorn app.main:app --reload
```

---

## 🛠️ Tech Stack & Dependencies
- **FastAPI**: Modern, high-performance web framework for APIs.
- **Uvicorn**: Lightning-fast ASGI web server.
- **SQLAlchemy 2.0**: Relational Database ORM mapping.
- **Pydantic v2**: High-performance data validation.
- **Pydantic Settings**: Environment settings parser.
- **Python-dotenv**: Loads variables from `.env` files.
- **Bcrypt**: Modern password hashing.
- **PyJWT**: JSON Web Token security implementation.
- **SQLite**: Local relational database support.
