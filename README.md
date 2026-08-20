<div align="center">

# 🏛️ Techonomy / Kairos

### *AI-Powered Enterprise Knowledge Intelligence & Analytical RAG Platform*

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Qdrant](https://img.shields.io/badge/Qdrant-v1.12-DC2626?style=for-the-badge&logo=qdrant&logoColor=white)](https://qdrant.tech)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<p align="center">
  <b>Techonomy (Kairos Intelligence System)</b> is an enterprise-grade, instruction-guided Knowledge Intelligence platform designed to transform multi-document company repositories into accurate, evidence-grounded analytical insights. Powered by a two-stage RAG pipeline, a 20-lane resilient LLM Gateway, and strict document security boundaries.
</p>

</div>

---

<p align="center">
  <img src="docs/images/login page.png" alt="Techonomy Platform Dashboard" width="900">
</p>
<p align="center"><i>Figure 1: Login Page</i></p>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Instruction-Guided RAG Pipeline](#-instruction-guided-rag-pipeline)
- [LLM Gateway & Multi-Key Load Balancer](#-llm-gateway--multi-key-load-balancer)
- [Document Security & Knowledge Isolation](#-document-security--knowledge-isolation)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Clone & Switch Branch](#2-clone--switch-branch)
  - [3. Configure Environment](#3-configure-environment)
  - [4. Launch Application Stack](#4-launch-application-stack)
  - [5. Ingest Knowledge Base](#5-ingest-knowledge-base)
  - [6. Verify Application Health](#6-verify-application-health)
- [Environment Configuration](#-environment-configuration)
- [Knowledge Base Management](#-knowledge-base-management)
- [Usage & Verification Walkthrough](#-usage--verification-walkthrough)
- [Event & Remote Deployment](#-event--remote-deployment)
- [Testing & Validation Matrix](#-testing--validation-matrix)
- [Screenshots & Visuals](#-screenshots--visuals)
- [Roadmap](#-roadmap)
- [License](#-license)

---

## 💡 Overview

Modern corporate operations generate vast volumes of complex unstructured documentation — financial audit reports, customer experience metrics, B2B sales funnels, and operational playbooks. Standard RAG architectures frequently fail on complex multi-document questions, yielding non-committal responses like *"The provided context does not contain sufficient information"* even when the underlying data is present.

**Techonomy** solves this challenge through an **Instruction-Guided Two-Stage RAG Architecture**:

1. **Stage 1 (Instruction-Guided Analytical Planning)**: Queries an internal, isolated `instruction_knowledge` vector base containing analytical frameworks, financial metrics guidance, and query playbooks to generate a structured `RetrievalPlan`.
2. **Stage 2 (Factual Evidence Retrieval & Grounding)**: Executes targeted multi-domain retrieval against official company documents in `company_knowledge`, reranks candidates, and enforces a hard evidence boundary before passing retrieved snippets to the LLM.

The platform guarantees that every answer is **100% grounded in retrieved company evidence**, with interactive citations pointing directly to exact PDF pages (`DS09_Customer_Experience_VoC.pdf — Page 3`) for instant verification in an embedded canvas document viewer.

---

## ✨ Key Features

### 🧠 Instruction-Guided Two-Stage RAG Architecture
- **Stage 1 Planning**: Leverages internal analytical instructions to formulate multi-step retrieval strategies without polluting participant evidence context.
- **Stage 2 Retrieval**: Retrieves, expands, and synthesizes evidence from official company reports using temporal reasoning and concept expansion.

### 🛡️ Hard Evidence Boundary & Knowledge Isolation
- **Dataset Separation**: Complete physical and logical isolation between `company_knowledge` (user-visible evidence) and `instruction_knowledge` (internal analytical guidance).
- **Zero Instruction Exposure**: Internal instruction PDFs are strictly invisible to participants, barred from API document endpoints (`403 Forbidden`), and never cited.

### 🚀 20-Lane Resilient LLM Gateway & Load Balancer
- **Multi-Key Pool**: Manages **10 Gemini Primary Lanes (`G01`–`G10`)** and **10 OpenRouter/Nemotron Fallback Lanes (`N01`–`N10`)**.
- **Per-Lane Quota Control**: Enforces an application-level **50 requests per lane** (1,000 total platform requests) and **1 concurrent request per lane**.
- **Automatic Failover & Auto-Recovery**: Atomically tracks usage in PostgreSQL. Automatically routes to OpenRouter fallback when Gemini lanes are blocked, and seamlessly returns to Gemini as soon as capacity recovers.

### 📊 Adaptive Response Depth
- **Query Archetype Classification**: Classifies queries into `SIMPLE_FACTUAL`, `ANALYTICAL`, `COMPARATIVE`, or `STRATEGIC_DIAGNOSTIC`.
- **Dynamic Token Budget Scaling**: Dynamically allocates token budgets from 2,000 to 4,500 max tokens to deliver comprehensive multi-period financial breakdowns without truncated prose.

### 📄 Embedded Document Viewer & Citation Deep-Linking
- **Location-Aware Page Navigation**: Clicking citation badges (`3.pdf — Page 12`) opens the built-in PDF viewer and automatically scrolls to the target page element (`pdf-page-12`).
- **Security Shields**: Prevents path traversal (`400 Bad Request`) and restricts file serving strictly to `backend/data/documents/company/`.

### 🛡️ Enterprise Arena & Admin Control Dashboard
- **Team Quota & Event Timers**: Configurable 2-hour event session timers (`02:00:00`) and per-team question quotas (10 questions).
- **Admin Dashboard**: Real-time overview of active teams, prompt execution logs, and system metrics.

---

## 🏗️ System Architecture

<p align="center">
  <img src="docs/images/architecture.png" alt="Techonomy Architecture Diagram" width="900">
</p>
<p align="center"><i>Figure 2: Techonomy End-to-End System Architecture & Data Flow</i></p>

### End-to-End Data Processing Pipeline

```text
               ┌────────────────────────────────────────────────────────┐
               │                  User Query / Prompt                   │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │               Stage 1: Instruction RAG                 │
               │   Queries instruction_knowledge -> Retrieves Playbook  │
               │   Generates RetrievalPlan & Domain Concepts            │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │                 Stage 2: Company RAG                   │
               │   Vector Search (Qdrant) -> Cross-Encoder Reranking    │
               │   Candidate Diversity & Evidence Selection             │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │                20-Lane LLM Gateway Pool                │
               │   Gemini Primary (G01-G10) ──Fallback──> OpenRouter (N01-N10) │
               │   PostgreSQL Atomic Locks & 60s Rate-Limit Cooldown    │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │        Grounded Answer + Page-Level Citations          │
               │   Interactive PDF Document Viewer Navigation           │
               └────────────────────────────────────────────────────────┘
```

---

## 🔬 Instruction-Guided RAG Pipeline

```text
PDF Documents  ──> PyMuPDF Parser ──> Text Cleaner ──> Semantic Chunker
                                                            │
  Qdrant Collections <── L2 Normalized Embeddings <── BAAI/bge-small-en-v1.5
```

1. **Document Ingestion & Parsing**: Documents are ingested via PyMuPDF (`fitz`), clean-parsed, and cataloged into hierarchical sections.
2. **Semantic Chunking & Optimization**: Text is split into optimal token windows (min 30, max 512 tokens) preserving heading headers and tabular alignment.
3. **Dense Vector Indexing**: Chunks are embedded using `BAAI/bge-small-en-v1.5` (384 dimensions) with L2 normalization and stored in Qdrant collections.
4. **Query Expansion & Temporal Resolution**: Relative dates (*"last quarter"*, *"FY 2024-25"*) and domain concepts (*"EBITDA"*, *"VoC metrics"*) are resolved dynamically.
5. **Cross-Encoder Reranking**: Candidate chunks are scored and reranked for semantic density, diversity, and numerical table presence.
6. **Prompt Assembly & Evidence Framing**: Retrieved company snippets are injected into a strict system prompt prohibiting external knowledge hallucination.

---

## ⚡ LLM Gateway & Multi-Key Load Balancer

To prevent single API-key rate limits (HTTP 429) from causing downtime during competitive events, Techonomy implements a **20-Lane Distributed LLM Scheduler**:

### Pool Allocation & Credentials

- **Gemini Primary Pool (`G01`–`G10`)**: 10 primary lanes mapped to `GEMINI_API_KEY_1` ... `GEMINI_API_KEY_10`.
- **OpenRouter Fallback Pool (`N01`–`N10`)**: 10 fallback lanes mapped to `OPENROUTER_API_KEY_1` ... `OPENROUTER_API_KEY_10`.
- **Per-Lane Application Quota**: `daily_limit = 50` requests per lane (**1,000 total platform requests**).
- **Per-Lane Concurrency**: `max_concurrent_requests = 1` per lane.
- **PostgreSQL Atomic Reservations**: Lanes are reserved via SQL updates to table `llm_lanes` using least-loaded selection (`active_requests`, `requests_used`, `lane_id`).
- **Cooldown & Failover**: An HTTP 429 on any single lane puts ONLY that lane into a 60-second cooldown. If all 10 Gemini lanes are blocked, traffic seamlessly routes to OpenRouter, returning to Gemini as soon as capacity recovers.

---

## 🔒 Document Security & Knowledge Isolation

Techonomy enforces strict document boundaries between analytical system instructions and participant-facing company evidence:

| Knowledge Collection | Document Type | Visibility | Exposed to Users? | Appears in Citations? | Viewable via PDF Endpoint? |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `company_knowledge` | `company` | `user_visible` | **YES** | **YES** | **YES** (`/api/documents/{id}/file`) |
| `instruction_knowledge` | `instruction` | `internal` | **NO** | **NO** | **NO** (`403 Forbidden`) |

### Security Protections:
- **Path Traversal Shields**: Rejects URLs containing `..` or illegal characters with `400 Bad Request`.
- **Instruction Access Block**: Attempts to download internal instruction PDFs return `403 Forbidden`.
- **Isolated Storage**: Official company PDFs are stored in `backend/data/documents/company/`; internal instruction PDFs reside in `backend/data/documents/instructions/`.

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend Framework** | React 18 + Vite | SPA User Interface |
| **Frontend Language** | TypeScript | Type Safety & Component Interfaces |
| **Styling** | Tailwind CSS + Lucide Icons | Responsive Modern UI Design |
| **PDF Renderer** | PDF.js | Canvas PDF Viewer & Page Scrolling |
| **Backend Framework** | FastAPI + Uvicorn | Async REST API & SSE Streaming |
| **Backend Language** | Python 3.13 | Core RAG Execution & Pipeline Logic |
| **Relational Database** | PostgreSQL 16 + SQLAlchemy | Persistent State, Quota & Lane Records |
| **Vector Database** | Qdrant (v1.12.0) | High-Performance Vector Similarity Search |
| **Embedding Engine** | PyTorch + SentenceTransformers | `BAAI/bge-small-en-v1.5` Embedding Generation |
| **Primary LLM Engine** | Google Gemini API | `gemini-flash-lite-latest` Primary Inference |
| **Fallback LLM Engine** | OpenRouter / NVIDIA Nemotron | `nvidia/nemotron-3.5-lightning:free` Fallback |
| **Containerization** | Docker + Docker Compose | Single-Port Single-Command Stack Deployment |

---

## 📁 Project Structure

```text
techonomy/
├── backend/
│   ├── app/
│   │   ├── api/                  # FastAPI REST endpoints (auth, teams, documents, chat, admin)
│   │   ├── database/             # SQLAlchemy ORM models & PostgreSQL connection engine
│   │   ├── knowledge/            # Core RAG Architecture
│   │   │   ├── indexing/         # PDF parser, semantic chunker & Qdrant client
│   │   │   ├── rag/              # 20-Lane LLM Gateway, Scheduler, & Adapters
│   │   │   └── retrieval/        # Instruction Planner, Vector Search & Reranker
│   │   ├── prompts/              # System prompts & instruction guidelines
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   └── services/             # ChatService, TeamService, AdminService
│   ├── data/
│   │   └── documents/
│   │       ├── company/          # Official company evidence PDFs (1.pdf - 7.pdf, DS01 - DS09)
│   │       └── instructions/     # Internal analytical playbooks (Company_Blueprint.pdf, etc.)
│   ├── scripts/                  # Dataset ingestion, benchmarks, & verification scripts
│   ├── tests/                    # Pytest test suites (RAG isolation, scheduler, security)
│   ├── Dockerfile                # Multi-stage Backend container build
│   └── requirements.txt          # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── api/                  # API client services
│   │   ├── components/           # UI components (Chat, DocumentViewer, Admin, Common)
│   │   ├── contexts/             # AuthContext & Session Timer State
│   │   └── pages/                # Page views (Dashboard, Chat, Documents, Rules, Admin)
│   ├── Dockerfile                # Frontend build image
│   └── package.json              # React dependencies
├── docs/
│   └── images/                   # Screenshot placeholders for README
├── docker-compose.yml            # Complete application orchestration manifest
├── README.md                     # Master Repository Operator Guide
└── EVENT_DEPLOYMENT.md           # Quick Event Deployment Guide
```

---

## 🚀 Getting Started

### 1. Prerequisites

The host deployment machine requires **ONLY**:
1. **Git**: To clone the repository.
2. **Docker Desktop** (or Docker Engine + Docker Compose): To build and run all services inside containers.
3. **ngrok CLI**: To expose host port `8000` to the internet.

> [!NOTE]
> You **do NOT need** Python, Node.js, PostgreSQL, or Qdrant installed locally on your host machine. Everything runs automatically inside Docker containers.

---

### 2. Clone & Switch Branch

```bash
# 1. Clone the repository
git clone https://github.com/Pawan-19012006/Techonomy-Application.git techonomy
cd techonomy

# 2. Switch to the release branch
git switch finetune

# 3. Verify active branch
git branch
```

---

### 3. Configure Environment

Copy the backend environment template:

```bash
cp backend/.env.example backend/.env
```

> [!CAUTION]
> **NEVER commit `backend/.env` to source control.**

Edit `backend/.env` and add your API credentials:

```env
PROJECT_NAME="Techonomy Knowledge Intelligence Platform"
VERSION=1.0.0
PORT=8000
DATABASE_URL=postgresql://techonomy:techonomy_pass@postgres:5432/techonomy_db
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Gemini Primary API Keys (G01 - G10)
GEMINI_API_KEY_1=your_gemini_key_1
GEMINI_API_KEY_2=your_gemini_key_2
GEMINI_MODEL=gemini-flash-lite-latest
GEMINI_REQUEST_LIMIT=50
GEMINI_MAX_CONCURRENT_REQUESTS=1

# OpenRouter Fallback API Keys (N01 - N10)
OPENROUTER_API_KEY_1=your_openrouter_key_1
OPENROUTER_API_KEY_2=your_openrouter_key_2
OPENROUTER_MODEL=nvidia/nemotron-3.5-lightning:free
NEMOTRON_REQUEST_LIMIT=50
NEMOTRON_MAX_CONCURRENT_REQUESTS=1
```

---

### 4. Launch Application Stack

Launch the complete single-port application stack (Frontend + FastAPI + PostgreSQL + Qdrant):

```bash
# 1. Build and start containers in detached mode
docker compose up --build -d

# 2. Verify container health status
docker compose ps

# 3. Check backend startup logs
docker compose logs backend --tail=100
```

---

### 5. Ingest Knowledge Base

Ingest the PDF documents into vector collections inside the running container:

```bash
# A. Ingest COMPANY Documents
docker compose exec backend python scripts/ingest_datasets.py --type reset-company
docker compose exec backend python scripts/ingest_datasets.py --type company

# B. Ingest INSTRUCTION Documents
docker compose exec backend python scripts/ingest_datasets.py --type reset-instruction
docker compose exec backend python scripts/ingest_datasets.py --type instruction
```

---

### 6. Verify Application Health

Confirm all services are online:

```bash
curl http://localhost:8000/health
```

*Expected JSON Response:*
`{"status":"healthy","backend":"healthy","database":"healthy","qdrant":"healthy", ...}`

---

## ⚙️ Environment Configuration

The application uses `backend/.env` for system configuration:

| Variable | Default / Format | Description |
| :--- | :--- | :--- |
| `PROJECT_NAME` | `"Techonomy Knowledge Intelligence Platform"` | Application title |
| `DATABASE_URL` | `postgresql://techonomy:...@postgres:5432/techonomy_db` | PostgreSQL database connection string |
| `QDRANT_HOST` | `qdrant` | Qdrant vector database hostname |
| `QDRANT_PORT` | `6333` | Qdrant vector database HTTP port |
| `GEMINI_API_KEY_1..10` | `your_gemini_key_1` | 10 independent Gemini API key slots |
| `OPENROUTER_API_KEY_1..10` | `your_openrouter_key_1` | 10 independent OpenRouter API key slots |
| `GEMINI_REQUEST_LIMIT` | `50` | Per-lane request quota limit for Gemini |
| `NEMOTRON_REQUEST_LIMIT` | `50` | Per-lane request quota limit for OpenRouter |
| `GEMINI_MAX_CONCURRENT_REQUESTS` | `1` | Max active concurrent requests per Gemini lane |
| `QUESTION_LIMIT` | `10` | Maximum question quota allowed per event team |

---

## 📚 Knowledge Base Management

PDF documents are organized in two dedicated directories:

```text
techonomy/backend/data/documents/
├── company/        <-- Official Company Evidence (e.g. 1.pdf, 3.pdf, DS01.pdf...)
└── instructions/   <-- Internal Analytical Playbooks (e.g. Company_Blueprint.pdf)
```

### Collection Reset Commands:
- **Reset Company Collection**: `docker compose exec backend python scripts/ingest_datasets.py --type reset-company`
- **Reset Instruction Collection**: `docker compose exec backend python scripts/ingest_datasets.py --type reset-instruction`

---

## 🖥️ Usage & Verification Walkthrough

Open **[http://localhost:8000](http://localhost:8000)** in your web browser:

1. **Team Arena Entry**: Enter a team name and member names to join.
2. **Dashboard**: View the live event timer (`02:00:00`) and team question quota counter (`0 / 10`).
3. **Ask Analytical Questions**:
   - *"Compare the company's financial performance across available reporting periods and identify key areas of concern."*
   - *"Conduct a detailed risk assessment of the company across financial, operational, and customer dimensions."*
4. **Interactive Document Viewer**: Click any citation badge (`3.pdf — Page 12`) to open the canvas PDF viewer directly scrolled to page 12.
5. **Admin Dashboard**: Access `/login` (Select **ADMIN** tab; Credentials: `kairos@csbs` / `kairospass`).

---

## 🌐 Event & Remote Deployment

Expose port `8000` for event participants:

```bash
# 1. Launch ngrok tunnel on host machine
ngrok http 8000
```

ngrok will output a public HTTPS URL:
```text
Forwarding    https://xxxx.ngrok-free.app -> http://localhost:8000
```

- Share the single **HTTPS URL** with event participants.
- Participants can access the application from any mobile device or laptop without installing any software.

---

## 🧪 Testing & Validation Matrix

Run the automated test suites inside the backend container to verify platform stability:

```bash
# 1. RAG Dataset Isolation & Hard Evidence Boundary Test
docker compose exec backend python -m pytest tests/test_instruction_rag_isolation.py -v

# 2. 20-Lane LLM Gateway & Quota Scheduler Test
docker compose exec backend python -m pytest tests/test_llm_scheduler.py tests/test_multi_key_scheduler.py -v

# 3. Document Access Security & Path Traversal Shields Test
docker compose exec backend python -m pytest tests/test_document_serving_security.py -v

# 4. Full Release-Gate Pre-Event Audit Verification Suite
docker compose exec backend python scripts/run_release_gate_verification.py
```

*Verification Results*: All 60/60 tests pass with 100% compliance across isolation, quota, failover, and security layers.

---

## 🖼️ Screenshots & Visuals

<p align="center">
  <br>
  <img src="docs/images/Dashboard.png" alt="Techonomy Documents & Admin View" width="900">
</p>
<p align="center"><i>Figure 3: Participant Dashboard</i></p>

<p align="center">
  <br>
  <img src="docs/images/Chatbot.png" alt="Techonomy Documents & Admin View" width="900">
</p>
<p align="center"><i>Figure 4: Chatbot Page</i></p>

<p align="center">
  <br>
  <img src="docs/images/Documents.png" alt="Techonomy Documents & Admin View" width="900">
</p>
<p align="center"><i>Figure 5: Documents Viewing Page</i></p>

---

## 📜 License

This project is released under the [MIT License](LICENSE).

---

<div align="center">
  <b>Techonomy / Kairos Intelligence Platform</b> • Built for Enterprise Knowledge Retrieval & Competition Arenas
</div>
