# Techonomy / Kairos

**Techonomy (Kairos Intelligence System)** is an enterprise-grade, instruction-guided Retrieval-Augmented Generation (RAG) platform. It provides automated, verified, grounded, and multi-document synthesized answers to complex financial, operational, sales, marketing, and strategic questions based on official company documentation.

### The Fundamental Dataset Distinction

The system enforces a strict architectural and security boundary between two isolated datasets:

- **COMPANY DATA (`company_knowledge`)**:
  - Contains official company annual reports, financial statements, sales reports, customer analytics, and operational metrics.
  - Marked as `document_type = "company"` and `visibility = "user_visible"`.
  - **The sole source of factual evidence** for participant answers. User-visible in citations, document lists, and the in-app PDF document viewer.
- **INSTRUCTION DATA (`instruction_knowledge`)**:
  - Contains internal analytical frameworks, evaluation guides, financial principles, and query planning playbooks.
  - Marked as `document_type = "instruction"` and `visibility = "internal"`.
  - **Used exclusively by the Stage 1 Planner** to determine *HOW* to analyze questions, extract required metrics, resolve temporal references, and formulate targeted search queries.
  - **STRICTLY INTERNAL**: Internal instruction content is NEVER exposed to users, NEVER cited, NEVER listed on the Documents page, and CANNOT be accessed via public document APIs.

---

## ⚡ Quick Start

Get the entire stack up and running locally in under 3 minutes:

```bash
# 1. Clone the repository
git clone https://github.com/Pawan-19012006/Techonomy-Application.git
cd techonomy

# 2. Configure Backend Environment
cp backend/.env.example backend/.env
# (Edit backend/.env to paste your GEMINI_API_KEY or OPENROUTER_API_KEY)

# 3. Setup Python Virtual Environment & Dependencies
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Ingest Official Datasets
PYTHONPATH=. .venv/bin/python scripts/ingest_datasets.py --type all

# 5. Start Backend API Server (Terminal 1)
PYTHONPATH=. .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 6. Setup & Start Frontend Development Server (Terminal 2)
cd ../frontend
npm install
npm run dev
```

- **Frontend Application UI**: [http://localhost:5173](http://localhost:5173) (or [http://localhost:3000](http://localhost:3000))
- **Backend API & Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 1. Features

- **Instruction-Guided RAG**: Stage 1 queries internal instruction guidance to decompose questions before searching company evidence.
- **Two-Stage Vector Retrieval**: Hard separation between `instruction_knowledge` (internal planning) and `company_knowledge` (user-visible evidence).
- **Domain-Specific Query Expansion**: Dynamically expands broad concepts (`"profitability"`, `"working capital"`, `"sales"`) into targeted metric terms (`PAT`, `EBITDA`, `inventory days`, `receivable days`, `turnover`).
- **Temporal Resolution Layer**: Resolves relative time phrases (`"last year"`, `"previous period"`, `"latest quarter"`, `"last month"`) against reporting period anchors in official company reports (`FY 2024-25`, `FY 2025-26`, `9M FY26`).
- **Multi-Document Synthesis**: Combines evidence across multiple company reports (`1.pdf`, `3.pdf`, `7.pdf`, `DS01`, `DS04`, `DS08`) for comprehensive analytical coverage.
- **Adaptive Response Depth**: Dynamically scales answer depth, reranker targets (`top_n = 5..12`), and context token ceilings (`2,000..4,500` tokens) based on question archetypes (`SIMPLE_FACTUAL`, `ANALYTICAL`, `COMPARATIVE`, `STRATEGIC_DIAGNOSTIC`).
- **Evidence Coverage & Iterative Second-Pass Retrieval**: Inspects candidate evidence against required metrics; automatically executes targeted fallback queries if evidence is incomplete.
- **Company-Only Source Citations**: Strictly attributes factual claims to company PDFs with exact page numbers (`3.pdf — Page 12`). Suppresses citations on explicit refusal answers.
- **High-DPI PDF Document Viewer**: In-app PDF viewer rendered with `pdfjs-dist` supporting zoom, page jumping, and automatic smooth scrolling to exact cited page numbers.
- **Quota-Aware Multi-Lane LLM Gateway**: 20-Lane Priority Scheduler with 10 Gemini primary lanes (`G01–G10`) and 10 OpenRouter/Nemotron fallback lanes (`N01–N10`) with automatic rate-limit failover.
- **Team Management & Prompt Logging**: Per-team prompt usage tracking, quota enforcement, and persistent PostgreSQL audit logging.
- **Admin Control Panel**: Operator dashboard for monitoring registered teams, session activity, query logs, and system metrics.

---

## 2. High-Level Architecture

```text
                           ┌───────────────────────────┐
                           │    Participant / Admin    │
                           └─────────────┬─────────────┘
                                         │
                                         ▼
                           ┌───────────────────────────┐
                           │   React 19 / Vite SPA     │
                           └─────────────┬─────────────┘
                                         │  (HTTP / SSE Stream)
                                         ▼
                           ┌───────────────────────────┐
                           │   FastAPI Backend API     │
                           └─────────────┬─────────────┘
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │ STAGE 1: INSTRUCTION GUIDANCE RAG     │
                     │ (Collection: instruction_knowledge)   │
                     └───────────────────┬───────────────────┘
                                         │ Internal Guidance Chunks
                                         ▼
                     ┌───────────────────────────────────────┐
                     │         INSTRUCTION PLANNER           │
                     │  • Query Archetype & Adaptive Depth   │
                     │  • Temporal Resolution Engine        │
                     │  • Concept & Synonym Expansion        │
                     │  • Multi-Query Company Search Batch   │
                     └───────────────────┬───────────────────┘
                                         │ Multi-Query Batch
                                         ▼
                     ┌───────────────────────────────────────┐
                     │  STAGE 2: COMPANY EVIDENCE RETRIEVAL  │
                     │  (Collection: company_knowledge ONLY) │
                     │  • Strict Evidence Boundary Filter    │
                     │  • Per-Doc Saturation Cap (Max 3/doc) │
                     │  • Evidence Coverage Checker          │
                     │  • Iterative Second-Pass Retrieval    │
                     └───────────────────┬───────────────────┘
                                         │ Raw Company Candidate Chunks
                                         ▼
                     ┌───────────────────────────────────────┐
                     │          ADAPTIVE RERANKER            │
                     │  • Structured Financial Table Boost   │
                     │  • Metric & Numerical Density Boost   │
                     │  • Document Diversity Selection       │
                     └───────────────────┬───────────────────┘
                                         │ Top Reranked Matches (top_n = 5..12)
                                         ▼
                     ┌───────────────────────────────────────┐
                     │           CONTEXT BUILDER             │
                     │  • Adaptive Ceiling (2,000..4,500T)   │
                     └───────────────────┬───────────────────┘
                                         │ Curated Context Package
                                         ▼
                     ┌───────────────────────────────────────┐
                     │        PROMPT BUILDER & GATEWAY       │
                     │  • Response Guidance Directive        │
                     │  • 20-Lane LLM Priority Scheduler     │
                     └───────────────────┬───────────────────┘
                                         │ Generated Response + Citations
                                         ▼
                     ┌───────────────────────────────────────┐
                     │        USER-FACING RESPONSE           │
                     │  • Grounded Answer                    │
                     │  • Company-Only Page Citations        │
                     └───────────────────┬───────────────────┘
                                         │ Citation Click (e.g. ?page=68)
                                         ▼
                     ┌───────────────────────────────────────┐
                     │      IN-APP PDF DOCUMENT VIEWER       │
                     │  • High-DPI Canvas Rendering          │
                     │  • Auto-Scroll to Exact Cited Page    │
                     └───────────────────────────────────────┘
```

### Architecture Stage Breakdown

1. **Stage 1 (Instruction Guidance RAG)**: Queries `instruction_knowledge` to retrieve internal analytical playbooks. This stage does NOT produce user-visible text.
2. **Instruction Planning**: Parses temporal phrases (`"last year"` -> `FY 2024-25`), expands business concepts into metric terms, classifies the question archetype (`SIMPLE_FACTUAL`, `ANALYTICAL`, `COMPARATIVE`, `STRATEGIC_DIAGNOSTIC`), and builds a multi-query search batch.
3. **Stage 2 (Company Evidence Retrieval)**: Executes multi-query vector searches strictly against `company_knowledge` (`document_type = "company"`, `visibility = "user_visible"`). Performs evidence coverage checking and triggers targeted fallback searches for missing metrics.
4. **Adaptive Reranking & Context Assembly**: Reranks company candidates by boosting structured numerical tables, metric density, and document diversity. Assembles context within an adaptive token budget (up to 4,500 tokens).
5. **LLM Generation & Gateway**: Routes the grounded prompt through the 20-Lane LLM Gateway (Gemini primary with OpenRouter failover).
6. **Company-Only Citations & PDF Viewing**: Extracts company document page references (`3.pdf — Page 12`). Clicking a citation navigates to the PDF viewer and scrolls smoothly to the target page.

---

## 3. Dataset Separation

The platform enforces strict separation between internal instructions and factual company evidence:

| Dataset Category | Qdrant Collection | Document Type | Visibility | Permitted Usage | User Visibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Company Evidence** | `company_knowledge` | `company` | `user_visible` | Factual Evidence, LLM Context, Citations | **YES** (Search, List, View, Cite) |
| **Instruction Guidance** | `instruction_knowledge` | `instruction` | `internal` | Stage 1 Query Decomposition & Strategy Planning | **NO** (Strictly Hidden & Prohibited) |

### Security Boundary Enforcement

1. **Vector Search Gate**: `RetrievalPipeline` applies `document_type = "company"` and `visibility = "user_visible"` filters to all Stage 2 searches. Any instruction chunk erroneously returned is dropped before reranking.
2. **Prompt Context Isolation**: `PromptBuilder.format_context_chunks()` filters candidate chunks and formats ONLY company evidence.
3. **Citation Extraction Isolation**: `ChatService._extract_sources()` ignores any source where `document_type != "company"`.
4. **Server-Side API Guard**: `backend/app/api/documents.py` restricts file serving to `backend/data/documents/company/`. Requests attempting to access instruction filenames or perform path traversal return **HTTP 403 Forbidden** or **HTTP 400 Bad Request**.

---

## 4. Directory Structure

```text
techonomy/
├── backend/
│   ├── app/
│   │   ├── api/                     # FastAPI route handlers (chat, documents, teams, admin)
│   │   ├── database/                # SQLAlchemy database engine, models, and sessions
│   │   ├── knowledge/               # Core Knowledge & RAG Architecture
│   │   │   ├── exceptions.py        # Knowledge domain exceptions
│   │   │   ├── indexing/            # Document chunking, embedding, vector DB client
│   │   │   ├── ingestion/           # PDF text extraction and ingestion pipeline
│   │   │   ├── models/              # SearchResult, RetrievalResult, RetrievalPlan
│   │   │   ├── optimization/        # Token estimator and caching modules
│   │   │   ├── rag/                 # ChatService, PromptBuilder, LLMGateway, AnswerCache
│   │   │   └── retrieval/           # RetrievalPipeline, InstructionPlanner, Reranker,
│   │   │                            # TemporalResolver, ConceptExpander, EvidenceChecker
│   │   ├── middleware/              # Logging, CORS, and Exception Handler middlewares
│   │   ├── prompts/                 # System prompt templates (system_prompt.txt)
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── utils/                   # Logging and utility functions
│   │   ├── config.py                # Central Pydantic settings
│   │   └── main.py                  # FastAPI entrypoint & lifespan pre-warming
│   ├── data/
│   │   └── documents/
│   │       ├── company/             # OFFICIAL COMPANY PDFS (User-Visible Evidence)
│   │       └── instructions/        # INTERNAL INSTRUCTION PDFS (Internal Guidance Only)
│   ├── qdrant_storage/              # Local Qdrant persistent file storage fallback
│   ├── scripts/                     # Ingestion, diagnostic, and administrative scripts
│   │   ├── ingest_datasets.py       # Main Dataset Ingestion & Reset CLI
│   │   ├── inspect_qdrant_collections.py
│   │   ├── test_live_financial_answer.py
│   │   └── test_live_adaptive_depth.py
│   ├── tests/                       # Comprehensive Pytest test suite
│   │   ├── test_instruction_rag_isolation.py  # 7-Test Isolation Suite
│   │   ├── test_advanced_rag_matrix.py        # 7-Test Analytical Matrix Suite
│   │   ├── test_adaptive_response_depth.py    # 7-Test Adaptive Depth Suite
│   │   ├── test_document_serving_security.py  # 5-Test Document Access Security Suite
│   │   └── test_real_providers.py             # 6-Test LLM Gateway & Provider Suite
│   ├── .env.example                 # Backend environment variable template
│   ├── Dockerfile                   # Production Python backend Docker container
│   ├── pyproject.toml               # Python project configuration
│   └── requirements.txt             # Backend Python dependencies
├── frontend/
│   ├── src/
│   │   ├── api/                     # Axios client configuration
│   │   ├── components/              # UI components (chat, layout, skeletons)
│   │   ├── contexts/                # AuthContext and ThemeContext
│   │   ├── hooks/                   # React Query custom hooks (useDocuments, useChat)
│   │   ├── pages/                   # App Pages (Dashboard, Documents, DocumentViewer, Admin)
│   │   ├── services/                # API service functions (REST & SSE streaming)
│   │   ├── types/                   # TypeScript interfaces
│   │   ├── App.tsx                  # React Router routes definition
│   │   └── main.tsx                 # React DOM entrypoint
│   ├── public/                      # Static public web assets
│   ├── .env.example                 # Frontend environment variable template
│   ├── package.json                 # Frontend Node dependencies and scripts
│   ├── tsconfig.json                # TypeScript compiler configuration
│   └── vite.config.ts               # Vite bundler configuration
├── docker-compose.yml               # Multi-service Docker orchestration
├── .gitignore                       # Git exclusion rules
└── README.md                        # Master Repository Documentation
```

---

## 5. Requirements & Prerequisites

### System Requirements

- **Python**: `3.13` (or `3.10+`)
- **Node.js**: `v20.x` or higher
- **npm**: `v10.x` or higher
- **Relational Database**: PostgreSQL (Supabase Cloud recommended; SQLite `sqlite:///./techonomy.db` supported for local development)
- **Vector Database**: Qdrant Cloud cluster (or local filesystem storage fallback `./qdrant_storage`)
- **LLM API Keys**: At least 1 valid Google Gemini API key or OpenRouter API key

---

## 6. Environment Variables

All configuration settings are managed via environment variables.

### Backend Environment Variables (`backend/.env`)

| Variable | Purpose | Required? | Default / Example Value |
| :--- | :--- | :---: | :--- |
| `PROJECT_NAME` | Name of the platform application | Optional | `"Techonomy Knowledge Intelligence Platform"` |
| `VERSION` | Backend API version string | Optional | `1.0.0` |
| `DEBUG` | Enables verbose debug logging | Optional | `False` |
| `HOST` | Backend server bind address | Optional | `0.0.0.0` |
| `PORT` | Backend server bind port | Optional | `8000` |
| `JWT_SECRET` | Secret key for signing JWT tokens | **REQUIRED** | `replace_with_a_secure_random_key` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | Optional | `http://localhost:5173,http://localhost:3000` |
| `QUESTION_LIMIT` | Event prompt limit per team | Optional | `10` |
| `DATABASE_URL` | PostgreSQL or SQLite connection string | **REQUIRED** | `postgresql://user:pass@host:5432/db` |
| `QDRANT_URL` | Qdrant Cloud cluster URL | Optional | `https://your-cluster-id.qdrant.tech` |
| `QDRANT_API_KEY` | Qdrant Cloud API Key | Optional | `your_qdrant_api_key_here` |
| `QDRANT_COMPANY_COLLECTION_NAME` | Target collection for company evidence | Optional | `company_knowledge` |
| `QDRANT_INSTRUCTION_COLLECTION_NAME` | Target collection for instructions | Optional | `instruction_knowledge` |
| `EMBEDDING_MODEL_NAME` | HuggingFace embedding model | Optional | `BAAI/bge-small-en-v1.5` |
| `GEMINI_API_KEY` | Primary Gemini API Key | **REQUIRED** | `your_gemini_api_key_here` |
| `GEMINI_API_KEY_1`..`10` | Multi-lane Gemini API Keys (G01–G10) | Optional | `your_gemini_key_1` |
| `GEMINI_MODEL` | Target Gemini model identifier | Optional | `gemini-flash-lite-latest` |
| `OPENROUTER_API_KEY` | Fallback OpenRouter API Key | Optional | `your_openrouter_api_key_here` |
| `OPENROUTER_API_KEY_1`..`10` | Multi-lane OpenRouter Keys (N01–N10) | Optional | `your_openrouter_key_1` |
| `OPENROUTER_MODEL` | Target OpenRouter fallback model | Optional | `nvidia/nemotron-3.5-lightning:free` |
| `RETRIEVAL_TOP_K` | Vector search top K candidates | Optional | `10` |
| `RETRIEVAL_RERANK_TOP_N` | Reranker output target | Optional | `5` |
| `RETRIEVAL_CONTEXT_TOKEN_BUDGET` | Base context token ceiling | Optional | `2000` |

### Frontend Environment Variables (`frontend/.env`)

| Variable | Purpose | Required? | Default / Example Value |
| :--- | :--- | :---: | :--- |
| `VITE_API_BASE_URL` | Backend API URL for standalone frontend dev | Optional | `http://127.0.0.1:8000` (Leave empty in production) |

---

## 7. First-Time Setup

Follow these steps for a complete local setup from scratch:

### 1. Environment File Creation

```bash
# Copy Backend Environment Template
cp backend/.env.example backend/.env

# Copy Frontend Environment Template
cp frontend/.env.example frontend/.env
```

Open `backend/.env` and paste your API keys:
```env
GEMINI_API_KEY=AIzaSy...
```

### 2. Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd ../frontend
npm install
```

---

## 8. Dataset Ingestion

The repository uses `backend/scripts/ingest_datasets.py` to manage vector indexing and resets for both datasets.

### Step 1: Add PDF Files

Place official PDF documents into their respective directories:
- **Company Evidence PDFs** -> `backend/data/documents/company/`
  - Example: `1.pdf`, `2.pdf`, `3.pdf`, `4.pdf`, `6 - revised.pdf`, `7.pdf`, `DS01_Consumer_Sales_Transactions.pdf`, `DS08_Finance_Commercial_Economics.pdf`
- **Internal Instruction PDFs** -> `backend/data/documents/instructions/`
  - Example: `Company_Blueprint.pdf`, `Marketing_Strategy_Playbook.pdf`, `Strategy_Evidence_Data_Architecture.pdf`

### Step 2: Run Ingestion Commands

Execute ingestion from the `backend/` directory with the virtual environment activated:

```bash
cd backend
source .venv/bin/activate

# Ingest BOTH datasets (Company + Instructions)
PYTHONPATH=. .venv/bin/python scripts/ingest_datasets.py --type all

# Ingest ONLY Company Evidence PDFs
PYTHONPATH=. .venv/bin/python scripts/ingest_datasets.py --type company

# Ingest ONLY Instruction Guidance PDFs
PYTHONPATH=. .venv/bin/python scripts/ingest_datasets.py --type instruction
```

### Step 3: Independent Collection Resets

You can reset either dataset independently without affecting the other:

```bash
# Reset ONLY Company Knowledge collection (company_knowledge)
PYTHONPATH=. .venv/bin/python scripts/ingest_datasets.py --type reset-company

# Reset ONLY Instruction Knowledge collection (instruction_knowledge)
PYTHONPATH=. .venv/bin/python scripts/ingest_datasets.py --type reset-instruction
```

> [!CAUTION]
> **NEVER mix instruction PDFs into `backend/data/documents/company/`.** Placing instruction files in the company directory will pollute participant evidence and expose internal playbooks in citations.

---

## 9. Qdrant Vector Database

The application manages two isolated Qdrant vector collections:

| Property | `company_knowledge` | `instruction_knowledge` |
| :--- | :--- | :--- |
| **Vector Dimension** | `384` (`BAAI/bge-small-en-v1.5`) | `384` (`BAAI/bge-small-en-v1.5`) |
| **Distance Metric** | `Cosine` | `Cosine` |
| **Target Document Type** | `company` | `instruction` |
| **Target Visibility** | `user_visible` | `internal` |
| **Ingested Documents** | 15 Company Reports & Data Sheets | 15 Internal Playbooks & Guides |
| **Point Count (Ingested)** | ~274 Vectors | ~107 Vectors |

### Storage Fallback Mode

- **Qdrant Cloud Mode**: Set `QDRANT_URL` and `QDRANT_API_KEY` in `backend/.env`.
- **Local Filesystem Fallback**: If `QDRANT_URL` is omitted or empty, Qdrant operates in embedded local storage mode persisting vector files to `./backend/qdrant_storage/`.

### Inspect Vector Collections

```bash
cd backend
PYTHONPATH=. .venv/bin/python scripts/inspect_qdrant_collections.py
```

---

## 10. Database Architecture & Persistence

Techonomy uses SQLAlchemy with support for PostgreSQL (Supabase Cloud) and SQLite (`sqlite:///./techonomy.db`).

### Persistent Database Tables

1. **`teams`**:
   - `team_name` (PK, String): Unique team name identifier.
   - `member_names` (JSON): Array of team member names.
   - `started_at` (DateTime): Team registration timestamp.
2. **`prompt_logs`**:
   - `id` (PK, Integer): Log identifier.
   - `team_name` (FK): Foreign key to `teams.team_name`.
   - `prompt` (Text): User query string.
   - `response` (Text): Generated RAG answer.
   - `sources` (JSON): Citation sources array (`[{document: "3.pdf", page: 12}]`).
   - `created_at` (DateTime): Query timestamp.
3. **`llm_lanes`**:
   - Tracks operational status, request counts, error counts, and cooldown timestamps for all 20 LLM Gateway lanes (`G01–G10` and `N01–N10`).
4. **`team_quotas`**:
   - `team_name` (FK), `questions_used`, `question_limit` (Default: 10).

Database tables are initialized automatically on server boot via `init_db()`.

---

## 11. Running the Application

### Local Development (Dual Terminals)

#### Terminal 1: Backend API Server
```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 2: Frontend Vite Development Server
```bash
cd frontend
npm run dev
```

- Access Frontend: [http://localhost:5173](http://localhost:5173)
- Access Backend API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Docker Production Deployment (Single Port `8000`)

To build and run the full stack (Frontend SPA + Backend API) inside a single container on port `8000`:

```bash
docker compose up --build -d
```

Access the application at [http://localhost:8000](http://localhost:8000).

---

## 12. API Reference

### Core Endpoints

| Method | Endpoint | Description | Auth Required? |
| :--- | :--- | :--- | :---: |
| `GET` | `/health` | Application, DB, Qdrant, and Model health probe | No |
| `GET` | `/api/status` | Backend API status string | No |
| `POST` | `/api/teams/join` | Register or join an event team | No |
| `GET` | `/api/teams/{team_name}` | Get team status, members, and quota | No |
| `GET` | `/api/teams/{team_name}/prompts` | Get prompt execution history for a team | No |
| `POST` | `/api/chat` | Submit RAG query (Synchronous REST) | No |
| `POST` | `/api/chat/stream` | Submit RAG query (SSE Token Streaming) | No |
| `GET` | `/api/documents` | List available official **company** documents | No |
| `GET` | `/api/documents/{id}` | Get metadata for a company document | No |
| `GET` | `/api/documents/{id}/file` | Stream raw company PDF file for document viewer | No |
| `POST` | `/api/admin/login` | Event organizer authentication | Admin |
| `GET` | `/api/admin/overview` | Admin dashboard event metrics | Admin Token |
| `GET` | `/api/admin/teams` | Admin list of all registered teams | Admin Token |
| `GET` | `/api/admin/teams/{team_name}` | Admin team detail & prompt history | Admin Token |

---

## 13. How the RAG Works

```text
User Question ──► Stage 1 (Instruction RAG) ──► Planner ──► Stage 2 (Company RAG) ──► Reranker ──► PromptBuilder ──► LLM ──► Grounded Response
```

### Stage 1: Instruction Guidance & Planning
1. Queries `instruction_knowledge` (`top_k=4`, `minimum_similarity=0.15`).
2. `InstructionPlanner` extracts guidance terms and passes the query through `TemporalResolver` and `ConceptExpander`.
3. Constructs a structured `RetrievalPlan` containing:
   - `question_archetype` (`SIMPLE_FACTUAL`, `ANALYTICAL`, `COMPARATIVE`, `STRATEGIC_DIAGNOSTIC`)
   - `response_depth_target` (`CONCISE`, `DETAILED_ANALYSIS`, `STRUCTURED_COMPARISON`, `MULTI_SECTION_DEEP_DIVE`)
   - `adaptive_token_budget` (`2,000` to `4,500` tokens)
   - `target_top_n` (`5` to `12` reranked chunks)
   - Multi-query search batch (temporal queries + expanded concept queries)

### Stage 2: Company Evidence Retrieval & Reranking
1. Executes vector searches strictly in `company_knowledge` (`document_type = "company"`, `visibility = "user_visible"`).
2. Deduplicates candidates and caps saturation at max 3 chunks per document.
3. `EvidenceChecker` evaluates coverage against required metrics. If evidence is incomplete, it executes **targeted second-pass fallback queries**.
4. `Reranker` applies table structure boosts (+0.18 for financial tables), numerical density scoring, and document diversity selection.
5. `ContextBuilder` synthesizes context blocks within the adaptive token ceiling.

### LLM Answer Generation
1. Injects `RESPONSE GUIDANCE DIRECTIVE` to ensure answer depth matches information complexity rather than prompt length.
2. The LLM generates a structured response using numbers and facts strictly from company context.
3. `ChatService` extracts company citations (`3.pdf — Page 12`) and suppresses citations if the response is an explicit refusal.

---

## 14. Citations and Document Viewing

1. **Citation Card Format**: Kairos responses display citations for company documents used (`3.pdf — Page 12`).
2. **Exact Page Jump**: Clicking a citation card navigates to `/documents/3.pdf?page=12` (or `/admin/documents/3.pdf?page=12`).
3. **In-App PDF Viewer**:
   - Renders PDF pages using `pdfjs-dist` on high-DPI HTML5 canvases.
   - Reactively reads `searchParams.get('page')` and automatically scrolls smoothly to `pdf-page-12`.
   - Displays a `CITATION SOURCE` badge on the target page.
4. **Security Isolation**: If a user attempts to manually request an instruction PDF (e.g., `/documents/Financial_Analysis_Instruction.pdf`), the backend blocks access with **HTTP 403 Forbidden**.

---

## 15. Security & Visibility Model

The system implements multi-layer defense-in-depth:

```text
               ┌─────────────────────────────────────────┐
               │          User Request Ingress           │
               └────────────────────┬────────────────────┘
                                    │
                                    ▼
               ┌─────────────────────────────────────────┐
               │    Backend API Security Guard           │
               │    (find_document_file)                 │
               │    • Path Traversal Check (HTTP 400)    │
               │    • Instruction Check (HTTP 403)       │
               │    • Company Dir Scoping (HTTP 404)     │
               └────────────────────┬────────────────────┘
                                    │ Authorized Company File
                                    ▼
               ┌─────────────────────────────────────────┐
               │   Vector Search & RAG Isolation         │
               │   • document_type = "company"           │
               │   • visibility = "user_visible"         │
               │   • Instruction Chunks Dropped          │
               └────────────────────┬────────────────────┘
                                    │ Factual Company Evidence
                                    ▼
               ┌─────────────────────────────────────────┐
               │         Client Citation Navigation      │
               │         • Company PDFs Only             │
               │         • Exact Page Jump Navigation    │
               └─────────────────────────────────────────┘
```

---

## 16. Testing

The repository contains a comprehensive suite of automated tests.

### Run All Backend Tests

```bash
cd backend
source .venv/bin/activate

# Run full backend test suite
PYTHONPATH=. .venv/bin/python -m pytest -v
```

### Individual Test Suites

```bash
# 1. Dataset Isolation Test Suite (7 Tests)
PYTHONPATH=. .venv/bin/python -m pytest tests/test_instruction_rag_isolation.py -v

# 2. Advanced RAG Matrix Test Suite (7 Tests)
PYTHONPATH=. .venv/bin/python -m pytest tests/test_advanced_rag_matrix.py -v

# 3. Adaptive Response Depth Test Suite (7 Tests)
PYTHONPATH=. .venv/bin/python -m pytest tests/test_adaptive_response_depth.py -v

# 4. Document Access Security Test Suite (5 Tests)
PYTHONPATH=. .venv/bin/python -m pytest tests/test_document_serving_security.py -v

# 5. LLM Gateway & Real Provider Test Suite (6 Tests)
PYTHONPATH=. .venv/bin/python -m pytest tests/test_real_providers.py -v
```

All 32 test cases across the suites verify 100% pass rates.

---

## 17. Frontend Production Build

Validate TypeScript compilation and build the static distribution bundle:

```bash
cd frontend
npm run build
```

- **Build Output**: Saved to `frontend/dist/`.
- **Validation**: Ensures zero TypeScript compilation or bundler errors.

---

## 18. Troubleshooting

### `ModuleNotFoundError: No module named 'app'`
- **Cause**: Python command executed without setting `PYTHONPATH`.
- **Fix**: Run commands from `backend/` directory with `PYTHONPATH=.`:
  ```bash
  cd backend
  PYTHONPATH=. .venv/bin/python scripts/ingest_datasets.py --type all
  ```

### `ValueError: Collection company_knowledge not found`
- **Cause**: Qdrant collections have not been initialized or ingested.
- **Fix**: Run dataset ingestion script:
  ```bash
  PYTHONPATH=. .venv/bin/python scripts/ingest_datasets.py --type all
  ```

### `403 Forbidden` on Document Viewer
- **Cause**: Attempted to access an internal instruction document or path traversal.
- **Fix**: Verify that the document requested is located in `backend/data/documents/company/` and is marked `visibility = "user_visible"`.

### Frontend Cannot Reach Backend API
- **Cause**: Backend server is not running on port 8000 or CORS origin is blocked.
- **Fix**: Ensure Uvicorn is running on `http://127.0.0.1:8000` and check `CORS_ORIGINS` in `backend/.env`.

---

## 19. Development Workflow

1. **Clone Branch**: `git clone https://github.com/Pawan-19012006/Techonomy-Application.git`
2. **Environment**: Copy `.env.example` to `.env` in `backend/` and `frontend/`.
3. **Backend Setup**: Create `.venv`, run `pip install -r requirements.txt`.
4. **Frontend Setup**: Run `npm install` inside `frontend/`.
5. **Populate Datasets**: Add company PDFs to `backend/data/documents/company/` and instruction PDFs to `backend/data/documents/instructions/`.
6. **Ingest Data**: Run `PYTHONPATH=. .venv/bin/python scripts/ingest_datasets.py --type all`.
7. **Start Backend**: Run Uvicorn on port 8000.
8. **Start Frontend**: Run `npm run dev`.
9. **Run Tests**: Execute `PYTHONPATH=. .venv/bin/python -m pytest -v`.

---

## 20. Important Developer Rules

1. **Instruction Documents Are Strictly Internal**: Never modify code to expose `instruction_knowledge` chunks or filenames to users or frontend components.
2. **Company Documents Are Sole Factual Evidence**: Never use instruction documents as factual evidence in LLM answers or citations.
3. **Preserve Dataset Isolation**: Keep `company_knowledge` and `instruction_knowledge` Qdrant collections completely isolated.
4. **Server-Side Security First**: Document access authorization MUST be enforced in `backend/app/api/documents.py`, never relying solely on frontend UI filtering.
5. **Preserve Citation Page Parameters**: Ensure exact page numbers (`?page=N`) are passed from search results to citation cards and viewer components.
6. **Do Not Alter RAG Analytical Architecture**: Keep `InstructionPlanner`, `RetrievalPipeline`, `Reranker`, and `PromptBuilder` working in sync.
7. **Always Run Isolation Tests**: Execute `pytest tests/test_instruction_rag_isolation.py` after modifying any retrieval or indexing logic.

---

## 21. Version Information

- **Platform**: Techonomy / Kairos Knowledge Intelligence Platform
- **Version**: `v1.0.0`
- **Architecture**: Two-Stage Instruction-Guided RAG with Adaptive Response Depth
