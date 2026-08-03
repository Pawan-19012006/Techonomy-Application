# Techonomy: Enterprise Knowledge Intelligence Platform

Welcome to **Techonomy**, an Enterprise Knowledge Intelligence Platform built with FastAPI, designed to deliver high-performance, modular Retrieval-Augmented Generation (RAG) and administrative control for enterprise teams.

This repository is structured as a clean, production-ready backend project skeleton, designed to be implemented module by module.

---

## 🏗️ Architecture & Directory Structure

The project follows a modular, layer-separated architecture to ensure maximum maintainability, testability, and scalability.

```text
backend/
├── app/                        # Main FastAPI application package
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── config.py               # Pydantic Settings configuration loading from .env
│   │
│   ├── api/                    # API Route Handlers (Routers)
│   │   ├── auth.py             # User authentication, token exchange
│   │   ├── chat.py             # Interactive AI chat & QA endpoints
│   │   ├── documents.py        # Document upload, parsing, management
│   │   ├── teams.py            # Team registration, access controls
│   │   └── admin.py            # Platform metrics, prompt logs, resets
│   │
│   ├── auth/                   # Authentication logic & FastAPI dependencies
│   │   ├── jwt.py              # JWT encoding/decoding
│   │   ├── password.py         # Password hashing (bcrypt)
│   │   └── dependencies.py     # Dependency injection (e.g., current_user)
│   │
│   ├── database/               # Database adapters & connection pooling
│   │   ├── sqlite.py           # Relational SQLite helper
│   │   ├── qdrant.py           # Vector Database helper for semantic search
│   │   └── models.py           # SQL Alchemy/Relational DB Models
│   │
│   ├── models/                 # Domain / Business logic models
│   │   ├── team.py             # Team domain model
│   │   ├── document.py         # Document domain model
│   │   ├── prompt_log.py       # Prompt history domain model
│   │   └── event.py            # System events / audit logs
│   │
│   ├── schemas/                # Pydantic Data Validation & Serialization models
│   │   ├── auth.py             # Login, Token schemas
│   │   ├── chat.py             # Query, response payload schemas
│   │   ├── team.py             # Team schema definitions
│   │   ├── document.py         # Metadata, parsing state schemas
│   │   └── admin.py            # Admin settings & stats schemas
│   │
│   ├── knowledge/              # RAG (Retrieval-Augmented Generation) components
│   │   ├── parser.py           # Document ingestion & parsing (PDF, Markdown)
│   │   ├── chunker.py          # text splitting algorithms
│   │   ├── embeddings.py       # Vector generation models
│   │   ├── ingest.py           # Vector indexing pipelines
│   │   ├── retriever.py        # Vector database querying
│   │   ├── reranker.py         # Coherence & relevance ranking
│   │   ├── prompt_builder.py   # RAG Context assembly
│   │   ├── llm.py              # Generative Model interface (OpenRouter)
│   │   └── citation.py         # Source attribution & transparency
│   │
│   ├── services/               # Business logic / Service layer
│   │   ├── authentication.py   # Auth service logic
│   │   ├── logging_service.py  # System event logging
│   │   ├── rate_limit.py       # API Rate Limiter
│   │   ├── timer.py            # Request processing timer helper
│   │   ├── document_service.py # Doc operations orchestrator
│   │   ├── team_service.py     # Team operations orchestrator
│   │   └── analytics.py        # Log aggregation & system metrics
│   │
│   ├── middleware/             # HTTP Middlewares
│   │   ├── auth.py             # Auth header validation
│   │   ├── logging.py          # Structured request/response logger
│   │   └── exception_handler.py# Global error interception & cleanup
│   │
│   ├── utils/                  # Helper utilities
│   │   ├── constants.py        # Shared defaults
│   │   ├── helpers.py          # Text processing/parsing tools
│   │   └── security.py         # Crypto utilities
│   │
│   └── prompts/                # Raw text assets for model configuration
│       ├── system_prompt.txt   # System role instructions
│       └── refusal_prompt.txt  # Guardrail & safe fallback replies
│
├── scripts/                    # CLI Utilities & Maintenance scripts
│   ├── ingest_company.py       # Batch document ingestion runner
│   ├── create_team_accounts.py # Admin utility to bootstrap teams
│   ├── reset_event.py          # System cleaning script
│   └── export_logs.py          # Prompt log backup
│
├── data/                       # Local filesystem storage directories (Git ignored)
│   ├── documents/              # Stored PDFs/MD source files
│   ├── uploads/                # Temporary uploaded files
│   └── exports/                # Generated reports & backups
│
├── tests/                      # Pytest Suite
│   ├── test_auth.py
│   ├── test_chat.py
│   ├── test_rag.py
│   └── test_documents.py
│
├── .env                        # Local Environment Configuration (Ignored)
├── .env.example                # Configuration Blueprint
├── requirements.txt            # Python Dependencies
├── Dockerfile                  # API deployment configuration
├── docker-compose.yml          # Local multi-container stack (App + Qdrant)
└── .gitignore                  # Git patterns to ignore
```

---

## ⚡ Development Setup

### Prerequisites
- Python 3.10+
- Virtual Environment tool (`venv`)
- Qdrant Vector database (optional for base run, but required for RAG)

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

---

## 🛠️ Tech Stack & Dependencies
- **FastAPI**: Modern, high-performance web framework for APIs.
- **Uvicorn**: Lightning-fast ASGI web server.
- **Pydantic v2**: High-performance data validation.
- **Pydantic Settings**: Environment settings parser.
- **Python-dotenv**: Loads variables from `.env` files.
- **SQLite**: Local relational database support.
- **Qdrant**: High-performance vector database.
