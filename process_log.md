# Process & Change Log

This file records the development process, code changes, and rationale for all modifications made to the Techonomy workspace.

---

## 🛠️ Step 1: Initial Skeleton Creation
**Action:** Generated the FastAPI directory skeleton.
- **Created Files:** All `.py` and package `__init__.py` files, configuration, tests, and deployment manifests.
- **Rationale:** Standardizing the application layout before coding prevents dependency cycles and ensures team alignment on package scopes.

---

## 🔧 Step 2: VS Code Python Environment Configuration
**Action:** Created `.vscode/settings.json` at the root workspace level.
- **Created File:** [.vscode/settings.json](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/.vscode/settings.json)
- **Rationale:** Configures VS Code to use `backend/.venv/bin/python` for syntax analysis and linting.

---

## 🔒 Step 3: Application Configuration (Pydantic Settings)
**Action:** Enhanced `backend/app/config.py` with comprehensive production parameters.
- **Modified File:** [config.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/config.py)
- **Rationale:** Added application settings, database configuration, JWT secret/expiration parameters, question rate limits, and log/upload filesystem paths.

---

## 📝 Step 4: Environment Variables Setup
**Action:** Created `.env` and `.env.example`.
- **Created Files:** [.env](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/.env) and [.env.example](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/.env.example).
- **Rationale:** Standardized local environment blueprint for development and deployment environments.

---

## 📚 Step 5: Root Documentation & Architecture
**Action:** Created `README.md` at project root.
- **Created File:** [README.md](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/README.md)
- **Rationale:** Overview of project structure, technology choices, setup commands, and architectural layer separation rules.

---

## ⚙️ Step 6: Backend Foundation Implementation

### 1. Requirements & Dependencies
- **Modified File:** [requirements.txt](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/requirements.txt)
- **Rationale:** Added `sqlalchemy>=2.0`, `pyjwt>=2.8.0`, `bcrypt>=4.0.1`, `python-multipart`, `email-validator`, and `httpx` to support relational DB ORM, JWT security, password hashing, file uploads, and API testing.

### 2. Central Logging Utility
- **Created File:** [logging.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/utils/logging.py)
- **Rationale:** Configured structured logging with console output and persistent file logging (`logs/app.log`) replacing standard `print()` statements.

### 3. Database Layer (SQLAlchemy 2.0 & SQLite)
- **Created Files:**
  - [sqlite.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/database/sqlite.py)
  - [models.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/database/models.py)
- **Rationale:** Built database engine, session factory (`SessionLocal`), `get_db` dependency, and ORM models for `Team`, `Document`, `PromptLog`, and `Event` using SQLAlchemy 2.0 mapped columns.

### 4. Pydantic Schemas Layer
- **Created Files:**
  - [auth.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/schemas/auth.py)
  - [team.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/schemas/team.py)
  - [document.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/schemas/document.py)
  - [admin.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/schemas/admin.py)
  - [chat.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/schemas/chat.py)
- **Rationale:** Enforced strict data validation and response contracts for auth tokens, team profile/usage, document metadata, prompt logs, and system analytics.

### 5. Security & Authentication Layer
- **Created Files:**
  - [password.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/auth/password.py)
  - [jwt.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/auth/jwt.py)
  - [dependencies.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/auth/dependencies.py)
- **Rationale:** Standardized password hashing (bcrypt), JWT token encoding/decoding, and FastAPI dependencies (`get_current_team`, `get_current_admin`).

### 6. Service Layer (Business Logic)
- **Created Files:**
  - [authentication.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/services/authentication.py)
  - [team_service.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/services/team_service.py)
  - [document_service.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/services/document_service.py)
  - [rate_limit.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/services/rate_limit.py)
  - [analytics.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/services/analytics.py)
- **Rationale:** Placed all business logic (quota consumption, team retrieval, auth validation, document saving, prompt logging) strictly inside service modules.

### 7. Middleware Layer
- **Created Files:**
  - [logging.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/middleware/logging.py)
  - [exception_handler.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/middleware/exception_handler.py)
- **Rationale:** Added HTTP request duration/status logging and global uncaught exception handling returning JSON errors.

### 8. API Layer (Routers)
- **Created Files:**
  - [auth.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/api/auth.py)
  - [teams.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/api/teams.py)
  - [documents.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/api/documents.py)
  - [admin.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/api/admin.py)
  - [chat.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/api/chat.py)
- **Rationale:** Exposed modular API endpoints for login, team info/usage, document upload/list, admin metrics/logs, and placeholder chat query (without AI).

### 9. Main Application & Health Probe
- **Modified File:** [main.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/main.py)
- **Rationale:** Wired FastAPI application with lifespan DB table initialization, registered middleware, included all routers, and implemented `/` and `/health` endpoints.

### 10. Containerization
- **Created Files:**
  - [Dockerfile](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/Dockerfile)
  - [docker-compose.yml](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/docker-compose.yml)
- **Rationale:** Multi-stage production container setup running Uvicorn server on port 8000 with mounted volumes for data and logs.

---

## 🧹 Step 7: Gitignore Update
**Action:** Updated `.gitignore` to match runtime data directory changes.
- **Modified File:** [.gitignore](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/.gitignore)
- **Rationale:** Replaced the legacy `storage/` directory paths with the current `data/` subdirectory paths (`data/uploads/`, `data/exports/`, `data/documents/`) to keep local files, logs, and database files untracked.

---

## 🏆 Step 8: Competition Platform Layer Implementation

### 1. Database Schema Enhancements
- **Modified File:** [models.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/database/models.py)
- **Rationale:** Enhanced `EventModel` to support Competition Events (`name`, `description`, `business_objective`, `rules`, `start_time`, `end_time`, `question_limit`, `is_active`). Added `pages` and `status` to `DocumentModel`. Added `response_time_ms` to `PromptLogModel`. Created `AuditLogModel` for system event activity.

### 2. Competition Pydantic V2 Schemas
- **Created/Modified Files:**
  - [event.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/schemas/event.py) (`EventCreate`, `EventUpdate`, `EventResponse`, `EventStatusResponse`)
  - [dashboard.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/schemas/dashboard.py) (`DashboardResponse` unified payload)
  - [team.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/schemas/team.py) (`TeamQuestionMetricsResponse`, `TeamHistoryResponse`)
  - [document.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/schemas/document.py) (`DocumentDeleteResponse`, updated metadata with pages/status)
  - [admin.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/schemas/admin.py) (Updated analytics summary & prompt log response)
- **Rationale:** Established input validation and OpenAPI document serialization schemas for competition management.

### 3. Business Logic Services
- **Created/Modified Files:**
  - [timer_service.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/services/timer_service.py): Calculates event remaining seconds, started, and finished flags dynamically from UTC server time.
  - [event_service.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/services/event_service.py): Handles event CRUD, activation, deactivation, and dynamic state evaluation (`UPCOMING`, `ACTIVE`, `PAUSED`, `COMPLETED`, `NO_EVENT`).
  - [dashboard_service.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/services/dashboard_service.py): Aggregates team, event, timer, question, and document metrics for `GET /dashboard`.
  - [team_service.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/services/team_service.py): Retreives question metrics and execution prompt history.
  - [document_service.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/services/document_service.py): Implements document deletion, count, and listing logic without file parsing/AI.
  - [analytics.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/services/analytics.py): Calculates total/active teams, question usage/remaining, prompt counts, and average response times.
  - [rate_limit.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/services/rate_limit.py): Exposes question quota metrics and enforces quota exhaustion rejection.
- **Rationale:** Strict adherence to business logic layer encapsulation.

### 4. Competition API Routers
- **Created/Modified Files:**
  - [event.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/api/event.py): `GET /event`, `GET /event/status`, Admin create, update, activate, deactivate endpoints.
  - [dashboard.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/api/dashboard.py): `GET /dashboard` single unified call.
  - [history.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/api/history.py): `GET /history` prompt history endpoint.
  - [teams.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/api/teams.py): `GET /teams/me`, `GET /teams/questions`, `GET /teams/history`.
  - [documents.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/api/documents.py): Metadata upload, listing, downloading, and deletion endpoints (`DELETE /{doc_id}`).
  - [admin.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/api/admin.py): Admin views for teams, prompt log filtering, documents, analytics, and event status.
  - [main.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/main.py): Registered all competition routers.
- **Rationale:** Clean, RESTful, documented OpenAPI endpoints.

---

## 📝 Step 9: Documentation Update
**Action:** Updated the root documentation to align with competition engine features.
- **Modified File:** [README.md](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/README.md)
- **Rationale:** Aligned the directory structure, endpoint descriptions, dependencies list, local setup steps (Python 3.13+), and added instructions on executing the test suites using `pytest`.

---

## 🧹 Step 10: Root Gitignore Setup
**Action:** Created workspace root `.gitignore`.
- **Created File:** [.gitignore](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/.gitignore)
- **Rationale:** Configured workspace root-level git patterns to ignore virtual environments, databases (e.g. `techonomy.db`), build caches, logs, and IDE settings globally across the repo.

---

## 🎨 Step 11: Enterprise React 19 Frontend Implementation
**Action:** Built the production-ready React 19 + TypeScript + Vite + Tailwind CSS frontend application inside `frontend/`.
- **Created Package:** `frontend/`
- **Created Architecture:**
  - **API Layer (`frontend/src/api/`):** [axios.ts](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/api/axios.ts) (Axios with JWT request/401 response interceptors), [auth.ts](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/api/auth.ts), [dashboard.ts](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/api/dashboard.ts), [documents.ts](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/api/documents.ts), [teams.ts](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/api/teams.ts), [chat.ts](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/api/chat.ts), [event.ts](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/api/event.ts).
  - **Contexts (`frontend/src/contexts/`):** [AuthContext.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/contexts/AuthContext.tsx) (JWT authentication state), [ThemeContext.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/contexts/ThemeContext.tsx) (Dark/Light mode toggle).
  - **Hooks (`frontend/src/hooks/`):** Custom TanStack Query hooks (`useAuth`, `useDashboard`, `useDocuments`, `useTeams`, `useChat`, `useEvent`).
  - **Components (`frontend/src/components/`):** Enterprise layout components ([Sidebar.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/components/layouts/Sidebar.tsx), [Navbar.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/components/layouts/Navbar.tsx)), common widgets ([MetricCard.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/components/common/MetricCard.tsx), [TimerBadge.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/components/common/TimerBadge.tsx), [QuestionCounter.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/components/common/QuestionCounter.tsx), [ProtectedRoute.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/components/common/ProtectedRoute.tsx)), dashboard widgets ([ActivityFeed.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/components/dashboard/ActivityFeed.tsx), [RecentDocuments.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/components/dashboard/RecentDocuments.tsx)), document widgets ([DocumentCard.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/components/documents/DocumentCard.tsx), [DocumentModal.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/components/documents/DocumentModal.tsx), [UploadModal.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/components/documents/UploadModal.tsx)), chat widgets ([ChatMessage.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/components/chat/ChatMessage.tsx), [ChatInput.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/components/chat/ChatInput.tsx)).
  - **Pages (`frontend/src/pages/`):** [LoginPage.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/pages/LoginPage.tsx), [DashboardPage.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/pages/DashboardPage.tsx), [DocumentsPage.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/pages/DocumentsPage.tsx), [KnowledgeAssistantPage.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/pages/KnowledgeAssistantPage.tsx), [RulesPage.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/pages/RulesPage.tsx), [TeamPage.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/pages/TeamPage.tsx), [NotFoundPage.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/pages/NotFoundPage.tsx).
- **Rationale:** Delivered an enterprise-grade UI matching Fortune 500 design guidelines (Microsoft/Linear/Atlassian style, `#111827` dark sidebar, `#4F46E5` indigo primary accents, `#F8FAFC` background) consuming live FastAPI endpoints.

---

## 🔑 Step 12: Automatic Database Seeding & Auth Fix
**Action:** Added `seed_initial_data()` to [sqlite.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/database/sqlite.py).
- **Modified File:** [sqlite.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/database/sqlite.py)
- **Rationale:** Automatically populates the SQLite database on startup with default demo team credentials (`devs@acme.com` / `SecretPassword123!`), admin team (`admin@techonomy.com` / `AdminPassword123!`), and an active competition event (`ABC Retail Pvt Ltd.`). Fixed login failures caused by unseeded empty databases.

---

## 🎨 Step 13: Color Grading Fix & Gitignore Update
**Action:** Fixed Tailwind CSS v4 `@variant dark` definition in [index.css](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/index.css) and updated workspace [.gitignore](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/.gitignore).
- **Modified Files:** [index.css](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/index.css), [.gitignore](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/.gitignore)
- **Rationale:** Resolved text contrast mismatch where white card background rendered low-contrast pale text in dark mode. Defined `@variant dark (&:where(.dark, .dark *));` to ensure dark mode card backgrounds (`#1E293B`) and inputs (`#0F172A`) apply high-contrast white text (`#F8FAFC`). Updated root `.gitignore` to track frontend `node_modules/`, build `dist/`, and environment configuration.

---

## ⚙️ Step 14: Enterprise Knowledge Engine Phase 1 (PDF -> Parser -> Cleaner -> Document)
**Action:** Implemented Phase 1 document ingestion foundation converting raw PDF files into clean `Document` objects.
- **Created/Updated Files:**
  - [exceptions.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/exceptions.py): Custom exceptions hierarchy (`PDFLoaderError`, `DocumentParserError`, `TextCleanerError`).
  - [page.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/models/page.py): `Page` Pydantic v2 domain model (`page_number`, `text`, `metadata`, `char_count`).
  - [document.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/models/document.py): `Document` Pydantic v2 domain model (`id`, `filename`, `title`, `file_type`, `total_pages`, `pages`, `metadata`, `total_characters`).
  - [chunk.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/models/chunk.py): `Chunk` Pydantic v2 domain model definition (no chunking logic implemented).
  - [pdf_loader.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/loaders/pdf_loader.py): `PDFLoader` using PyMuPDF (`fitz`) for raw page text extraction.
  - [parser.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/ingestion/parser.py): `DocumentParser` orchestrating loader selection and `Document` object creation.
  - [cleaner.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/ingestion/cleaner.py): `TextCleaner` normalizing whitespace, collapsing consecutive newlines, and stripping repeated headers/footers across pages while preserving page structure and order.
  - [ingest.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/ingestion/ingest.py): `IngestionPipeline` and `ingest_pdf()` coordinator (`PDF -> Parser -> Cleaner -> Clean Document`).
  - [test_parser.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/scripts/test_parser.py): Terminal test script for standalone execution without DB/Qdrant/API dependencies.
  - [test_knowledge_phase1.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/tests/test_knowledge_phase1.py): Pytest unit test suite (**11/11 tests passed**).
- **Rationale:** Strict adherence to Phase 1 boundaries without embeddings, vector search, Qdrant, retrieval, LLMs, or prompt engineering.

---

## 🌳 Step 15: Enterprise Knowledge Structuring Engine (Phase 2)
**Action:** Implemented Phase 2 Knowledge Structuring Engine converting clean `Document` objects into hierarchical, typed `StructuredDocument` objects.
- **Created/Updated Files:**
  - [exceptions.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/exceptions.py): Added `StructureAnalyzerError`, `HierarchyBuilderError`, `MetadataBuilderError`, and `StatisticsGeneratorError`.
  - [section.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/models/section.py): `Section` Pydantic v2 domain model (`id`, `title`, `section_type`, `level`, `content`, `page_number`, `reading_order`, `parent_id`, `children_ids`, `metadata`).
  - [structured_document.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/models/structured_document.py): `StructuredDocument` and `DocumentStatistics` domain models.
  - [structure_analyzer.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/analysis/structure_analyzer.py): Detects headings (H1-H6), bullet lists, numbered lists, basic tables, and paragraphs while preserving 0-indexed reading order.
  - [hierarchy_builder.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/analysis/hierarchy_builder.py): Assembles parent-child hierarchy tree (`H1 -> H2 -> H3 -> Paragraph/List/Table`).
  - [metadata_builder.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/metadata/metadata_builder.py): Enriches sections with document ID, page number, section type, hierarchy level, reading order, and character counts.
  - [statistics.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/analysis/statistics.py): Calculates page, section, heading, paragraph, list, table, character counts, and average section length.
  - [ingest.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/ingestion/ingest.py): `IngestionPipeline` updated with `structure_document()` and `structure_pdf()` pipeline methods.
  - [test_structure.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/scripts/test_structure.py): Terminal test script printing document hierarchy tree, element counts, metadata, and reading order.
  - [test_knowledge_phase2.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/tests/test_knowledge_phase2.py): Pytest unit test suite (**17/17 tests passed**).
- **Rationale:** Strict adherence to Phase 2 boundaries without embeddings, vector search, Qdrant, retrieval, LLMs, prompt engineering, or chunking.

---

## ⚡ Step 16: Enterprise Knowledge Optimization Engine (Phase 3 Chunking)
**Action:** Implemented Phase 3 Knowledge Optimization Engine converting `StructuredDocument` objects into optimized semantic `KnowledgeChunk` objects.
- **Created/Updated Files:**
  - [exceptions.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/exceptions.py): Added `SemanticChunkerError`, `ChunkOptimizerError`, `ChunkValidatorError`, and `TokenEstimatorError`.
  - [knowledge_chunk.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/models/knowledge_chunk.py): `KnowledgeChunk` Pydantic v2 domain model (`chunk_id`, `document_id`, `page_numbers`, `section_title`, `section_type`, `hierarchy_level`, `reading_order`, `content`, `estimated_tokens`, `metadata`).
  - [chunk_statistics.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/models/chunk_statistics.py): `ChunkStatistics` Pydantic v2 domain model (`total_chunks`, `average_chunk_size`, `largest_chunk`, `smallest_chunk`, `average_tokens`, `total_tokens`).
  - [token_estimator.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/optimization/token_estimator.py): Fast character-ratio heuristic estimator (`estimated_tokens ≈ chars / 4.0`).
  - [semantic_chunker.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/optimization/semantic_chunker.py): Groups document sections by semantic boundaries (heading + content, lists, tables) with configurable `max_tokens` (512) and `overlap_tokens` (50).
  - [chunk_optimizer.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/optimization/chunk_optimizer.py): Merges tiny fragments (< 30 tokens) and splits oversized chunks (> 512 tokens) along natural paragraph breaks while preserving reading order.
  - [chunk_validator.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/optimization/chunk_validator.py): Audits chunks for non-emptiness, token budget compliance, metadata, document ID, page numbers, and section titles.
  - [ingest.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/ingestion/ingest.py): Updated `IngestionPipeline` with `optimize_chunks()` and `chunk_pdf()` methods.
  - [test_chunking.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/scripts/test_chunking.py): Terminal test script printing chunk statistics, validation summary, metadata, and content previews.
  - [test_knowledge_phase3.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/tests/test_knowledge_phase3.py): Pytest unit test suite (**22/22 tests passed**).
- **Rationale:** Strict adherence to Phase 3 boundaries without embeddings, vector databases, Qdrant, retrieval, LLMs, OpenRouter, or prompt engineering.

---

## 🔍 Step 17: Enterprise Knowledge Indexing Engine (Phase 4 Indexing)
**Action:** Implemented Phase 4 Knowledge Indexing Engine generating local dense embeddings, L2 normalizing vectors, constructing Qdrant payloads, and uploading to Qdrant vector database.
- **Created/Updated Files:**
  - [config.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/config.py): Added `EMBEDDING_MODEL_NAME` (`BAAI/bge-small-en-v1.5`), `EMBEDDING_BATCH_SIZE` (`32`), `QDRANT_HOST` (`localhost`), `QDRANT_PORT` (`6333`), `QDRANT_COLLECTION_NAME` (`company_knowledge`), and `QDRANT_DISTANCE_METRIC` (`Cosine`).
  - [requirements.txt](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/requirements.txt): Added `sentence-transformers>=3.0.0`, `qdrant-client>=1.10.0`, `numpy>=1.26.0`.
  - [exceptions.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/exceptions.py): Added `EmbeddingGeneratorError`, `EmbeddingBatcherError`, `EmbeddingNormalizerError`, `PayloadBuilderError`, `QdrantClientWrapperError`, `CollectionManagerError`, and `IndexManagerError`.
  - [embedding.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/models/embedding.py): `Embedding` domain model (`chunk_id`, `vector`, `dimension`, `normalized`).
  - [indexed_chunk.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/models/indexed_chunk.py): `IndexedChunk` model combining `Embedding` and Qdrant payload dictionary.
  - [index_result.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/models/index_result.py): `IndexResult` model (`documents_indexed`, `chunks_indexed`, `vectors_uploaded`, `collection_name`, `embedding_dimension`, `processing_time`).
  - [embedder.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/indexing/embedder.py): `EmbeddingGenerator` using SentenceTransformers (`BAAI/bge-small-en-v1.5`) loaded as a singleton for fast local batch vector inference.
  - [embedding_batcher.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/indexing/embedding_batcher.py): `EmbeddingBatcher` grouping chunks into configurable batches (default 32).
  - [embedding_normalizer.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/indexing/embedding_normalizer.py): `EmbeddingNormalizer` computing L2 unit-length vector normalization using NumPy.
  - [payload_builder.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/indexing/payload_builder.py): `PayloadBuilder` constructing comprehensive Qdrant payloads with all chunk, section, and document metadata.
  - [qdrant_client.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/indexing/qdrant_client.py): `QdrantClientWrapper` handling Qdrant connection, fallback local storage engine, collection creation, point upserting, deletion, and collection statistics.
  - [collection_manager.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/indexing/collection_manager.py): `CollectionManager` managing collection creation and schema/dimension validation for `company_knowledge`.
  - [index_manager.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/indexing/index_manager.py): `IndexManager` orchestrating full indexing pipeline and returning `IndexResult`.
  - [ingest.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/ingestion/ingest.py): Updated `IngestionPipeline` with `index_document_chunks()` and `index_pdf()` methods.
  - [test_indexing.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/scripts/test_indexing.py): Terminal test script printing embedding model, dimension, batch count, embedding time, collection status, uploaded vectors, and sample payload.
  - [test_knowledge_phase4.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/tests/test_knowledge_phase4.py): Pytest unit test suite (**27/27 tests passed**).
- **Rationale:** Strict adherence to Phase 4 boundaries without retrieval, RAG, question answering, prompt engineering, OpenRouter, FastAPI endpoints, or search APIs.

---

## 🔎 Step 18: Enterprise Knowledge Retrieval Engine (Phase 5 Retrieval)
**Action:** Implemented Phase 5 Knowledge Retrieval Engine processing user queries, embedding questions with local `BAAI/bge-small-en-v1.5`, executing vector search against Qdrant, reranking matches with hybrid heuristics, and building synthesized context packages.
- **Created/Updated Files:**
  - [config.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/config.py): Added `RETRIEVAL_TOP_K` (`10`), `RETRIEVAL_RERANK_TOP_N` (`5`), `RETRIEVAL_CONTEXT_TOKEN_BUDGET` (`2000`), and `RETRIEVAL_MINIMUM_SIMILARITY` (`0.3`).
  - [exceptions.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/exceptions.py): Added `QueryProcessorError`, `QueryEmbedderError`, `VectorSearchError`, `SearchFilterError`, `RerankerError`, `ContextBuilderError`, and `RetrievalPipelineError`.
  - [processed_query.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/models/processed_query.py): `ProcessedQuery` domain model (`original_query`, `normalized_query`, `character_count`, `word_count`, `is_valid`, `metadata`).
  - [search_result.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/models/search_result.py): `SearchResult` domain model (`chunk_id`, `document_id`, `document_name`, `score`, `content`, `page_numbers`, `section_title`, `section_type`, `hierarchy_level`, `reading_order`, `estimated_tokens`, `payload`).
  - [context_package.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/models/context_package.py): `ContextPackage` domain model (`context_text`, `estimated_tokens`, `chunks_used`, `sources`, `source_chunks`, `metadata`).
  - [retrieval_result.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/models/retrieval_result.py): `RetrievalResult` model (`processed_query`, `embedding_dimension`, `top_k_searched`, `top_n_reranked`, `raw_search_results`, `reranked_results`, `context_package`, `processing_time`).
  - [query_processor.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/retrieval/query_processor.py): `QueryProcessor` validating and normalizing raw input questions.
  - [query_embedder.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/retrieval/query_embedder.py): `QueryEmbedder` generating L2-normalized dense vector embeddings using shared `EmbeddingGenerator`.
  - [search_filters.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/retrieval/search_filters.py): `SearchFilters` building reusable Qdrant payload filters (`document_id`, `page_numbers`, `section_type`, `minimum_similarity`).
  - [vector_search.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/retrieval/vector_search.py): `VectorSearch` executing semantic similarity queries against Qdrant collection.
  - [reranker.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/retrieval/reranker.py): `Reranker` performing hybrid scoring (cosine similarity + keyword overlap + section title boost + heading boost).
  - [context_builder.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/retrieval/context_builder.py): `ContextBuilder` deduplicating chunks, generating source citations, and enforcing token budget limits.
  - [retrieval_pipeline.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/retrieval/retrieval_pipeline.py): `RetrievalPipeline` and `retrieve_context()` pipeline coordinator.
  - [test_retrieval.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/scripts/test_retrieval.py): Terminal test script printing formatted query metrics, vector search top K, reranked top N, context token estimates, and citations.
  - [test_knowledge_phase5.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/tests/test_knowledge_phase5.py): Pytest unit test suite (**33/33 tests passed**).
- **Rationale:** Strict adherence to Phase 5 boundaries without LLM calls, OpenRouter, prompt engineering, chatbot, FastAPI endpoints, or frontend integration.

---

## 🛠️ Step 19: Phase 5 Debugging Sprint – Qdrant Persistence & Retrieval Audit
**Action:** Audited and resolved Qdrant database persistence inconsistency between indexing and retrieval pipelines.
- **Created/Updated Files:**
  - [qdrant_client.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/indexing/qdrant_client.py): Enhanced `count_vectors()` to use `client.count(exact=True)`. Added `get_indexed_documents()` and `get_sample_points()` inspection methods.
  - [debug_qdrant.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/scripts/debug_qdrant.py): Created new CLI debug utility displaying Collection Name, Storage Path, Total Points, First 10 Document Names, and First 10 Chunk IDs.
  - [test_knowledge_phase4.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/tests/test_knowledge_phase4.py) & [test_knowledge_phase5.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/tests/test_knowledge_phase5.py): Updated unit tests to run against an isolated collection (`pytest_unit_test_collection`), preventing unit tests from wiping the local production `./qdrant_storage` database.
  - [test_retrieval.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/scripts/test_retrieval.py): Enforced indexing of `annual_report.pdf` when `company_knowledge` is empty or lacks production vectors. Added audit logging for storage path, collection name, total vectors, indexed document names, and retrieved document names.
- **Rationale:** Guaranteed that Retrieval searches the exact same vector database (`annual_report.pdf`, 442 vectors) produced by Phase 4 without sample document interference.

---

## 🚀 Step 20: Enterprise RAG Serving Pipeline (Phase 6 RAG Engine)
**Action:** Implemented the production RAG serving pipeline consisting of `PromptBuilder`, `LLMService`, `ChatService`, `ChatResponse` schemas, and `POST /chat` API endpoint.
- **Created/Updated Files:**
  - [config.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/config.py): Added `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `OPENROUTER_BASE_URL`, `LLM_TIMEOUT_SECONDS` (`30.0`), and `LLM_MAX_RETRIES` (`1`).
  - [exceptions.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/exceptions.py): Added `PromptBuilderError`, `LLMServiceError`, `OpenRouterAPIError`, `LLMTimeoutError`, and `ChatServiceError`.
  - [system_prompt.txt](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/prompts/system_prompt.txt): Populated system prompt text file.
  - [prompt_builder.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/rag/prompt_builder.py): `PromptBuilder` assembling system message, retrieved context chunks, and user question. Re-exported in `app/prompts/prompt_builder.py`.
  - [llm_service.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/rag/llm_service.py): `LLMService` handling OpenRouter API generation calls, 30s timeout enforcement, 1 retry resilience, and custom error raising.
  - [chat_service.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/rag/chat_service.py): `ChatService` orchestrating end-to-end RAG question answering: `RetrievalPipeline` -> `PromptBuilder` -> `LLMService` -> `ChatServiceResult` (never accessing Qdrant, generating embeddings, or performing auth directly).
  - [chat.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/schemas/chat.py): Pydantic schemas (`SourceItem`, `ChatRequest`, `ChatResponse`, `ChatQueryRequest`, `ChatQueryResponse`).
  - [chat.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/api/chat.py): Implemented 6-step `POST /chat` and `POST /chat/query` endpoint pipeline (Authenticate -> Check Quota -> `ChatService.ask()` -> Log Prompt -> Consume Quota -> Return JSON).
  - [test_rag.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/scripts/test_rag.py): Terminal test script verifying `PromptBuilder`, `LLMService`, and `ChatService`.
  - [test_rag_pipeline.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/tests/test_rag_pipeline.py): Automated Pytest unit test suite (**40/40 tests passed**).
- **Rationale:** Strict adherence to single-responsibility RAG architecture reusing existing components without modifying ingestion, indexing, retrieval, auth, or quota modules.

---

## ⚡ Step 21: Event Backend Simplification & Auth Removal
**Action:** Drastically simplified Techonomy backend for event execution by removing all enterprise auth, user accounts, JWT, password hashing, admin roles, and rate limiting while keeping the full RAG pipeline intact.
- **Removed Obsolete Modules:**
  - Deleted `app/auth/` directory (`jwt.py`, `password.py`, `dependencies.py`).
  - Deleted obsolete routers (`admin.py`, `auth.py`, `dashboard.py`, `documents.py`, `event.py`, `history.py`).
  - Deleted obsolete services (`authentication.py`, `rate_limit.py`, `dashboard_service.py`, `event_service.py`, `timer_service.py`, `analytics.py`, `document_service.py`).
  - Deleted obsolete schemas (`admin.py`, `auth.py`, `dashboard.py`, `document.py`, `event.py`).
- **Database Simplification:**
  - Reduced SQLite database schema to **ONLY 2 tables**:
    1. `teams` (`team_name` PK, `member_names` JSON, `started_at` DateTime).
    2. `prompt_logs` (`id` PK, `team_name` FK $\rightarrow$ `teams.team_name`, `prompt`, `response`, `created_at`).
- **APIs Implemented:**
  - `POST /api/teams/join`: Joins or re-enters arena (`team_name`, `member_names`), setting `started_at` for new teams or returning existing team record.
  - `GET /api/teams/{team_name}`: Returns team name, member names, and `started_at` timestamp.
  - `POST /api/chat`: Receives `team_name` and `question`, delegates RAG generation to `ChatService`, stores prompt log in `prompt_logs`, and returns answer JSON.
  - `GET /api/teams/{team_name}/prompts`: Returns prompt history list for a team.
- **Verification:**
  - Updated Pytest suite in `tests/test_event_backend.py` (**43/43 tests passed 100%**).

---

## ⚡ Step 22: Frontend Integration to FastAPI Backend
**Action:** Connected existing React 19 + TypeScript frontend to the simplified FastAPI backend without changing the approved UI visual design.
- **Created Centralized API Service ([src/services/api.ts](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/services/api.ts)):**
  - Configured `API_BASE_URL` from `import.meta.env.VITE_API_BASE_URL`.
  - Implemented `joinTeam(team_name, member_names)` (`POST /api/teams/join`).
  - Implemented `sendChatMessage(team_name, question)` (`POST /api/chat`).
  - Implemented `getTeam(team_name)` (`GET /api/teams/{team_name}`).
  - Implemented `getTeamPrompts(team_name)` (`GET /api/teams/{team_name}/prompts`).
- **Team Entry & Arena Access ([LoginPage.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/pages/LoginPage.tsx)):**
  - Connected team entry form to `POST /api/teams/join`.
  - Persisted team information in `localStorage` under `techonomy_team` (`{ team_name, member_names, started_at }`).
- **Knowledge Assistant Chat & Citations ([KnowledgeAssistantPage.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/pages/KnowledgeAssistantPage.tsx) & [ChatMessage.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/components/chat/ChatMessage.tsx)):**
  - Connected chat form to `POST /api/chat` passing `team_name` and `question`.
  - Dynamically rendered RAG answer text and source citations (document name and page number).
  - Implemented submit button disabling and loading spinner state to prevent duplicate submissions.
  - Persisted visible conversation in `localStorage` under `techonomy_chat_history`.
- **Team State Restoration ([AuthContext.tsx](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/contexts/AuthContext.tsx)):**
  - Restored `techonomy_team` from `localStorage` on application startup.
- **Verification:**
  - Executed `npm run build` with **0 TypeScript or Vite build errors**.

---

## ⚡ Step 23: FastAPI CORS Middleware Configuration
**Action:** Configured production-friendly, environment-driven CORS in the Techonomy FastAPI backend to allow requests from frontend dev origins (`http://localhost:3001`, `http://127.0.0.1:3001`, `http://localhost:5173`, `http://127.0.0.1:5173`).
- **Configured Environment Setting ([app/config.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/config.py) & [.env](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/.env)):**
  - Added `CORS_ORIGINS` setting supporting comma-separated strings, JSON lists, or python arrays via custom property `settings.cors_origins_list`.
- **Attached CORSMiddleware ([app/main.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/main.py)):**
  - Mounted `CORSMiddleware` with `allow_origins=settings.cors_origins_list`, `allow_credentials=True`, `allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]`, and `allow_headers=["Content-Type", "Authorization", "Accept", "*"]`.
- **Verification:**
  - Added automated Pytest CORS preflight and header test (`test_cors_preflight_and_headers`) in `tests/test_event_backend.py`.
  - Executed Pytest suite (**44/44 tests passed 100%**).
  - Executed `npm run build` (**0 errors**).

---

## ⚡ Step 24: RAG Latency Instrumentation & Bottleneck Profiling
**Action:** Instrument the complete RAG serving pipeline with high-resolution timing (`time.perf_counter()`) across all 13 pipeline stages without altering RAG retrieval architecture or quality.
- **Instrumented Components:**
  - [retrieval_result.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/models/retrieval_result.py): Added `timing: Dict[str, float]` field to hold stage timings.
  - [retrieval_pipeline.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/retrieval/retrieval_pipeline.py): Measured `query_processing`, `embedding`, `vector_search`, `reranking`, and `context_building`.
  - [llm_service.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/rag/llm_service.py): Measured individual attempt start times, durations, HTTP statuses, retries, model name, and timeouts.
  - [chat_service.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/rag/chat_service.py): Measured `prompt_building`, `llm_generation`, `chat_service_total`, and returned `timing` dict in `ChatServiceResult`.
  - [chat.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/api/chat.py): Measured request validation, `TeamService.log_prompt()`, and emitted structured `[RAG TIMING]` breakdown logs. Warns if database write exceeds 100ms.
- **Empirical Diagnostics:**
  - Identified **LLM API Response Time** (`cohere/north-mini-code:free` taking 13s–53s) as the primary bottleneck for warm queries.
  - Identified **Cold-Start Embedding Model Loading** (`BAAI/bge-small-en-v1.5` taking 87s–107s on first query initialization) as the initial request bottleneck.
  - Verified **Database Logging** (`PromptLog`) is extremely fast (5ms–23ms) and contributes zero meaningful latency.
- **Verification:**
  - Executed Pytest test suite (**44/44 tests passed 100%**).
  - Benchmark scripts ([scripts/test_rag.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/scripts/test_rag.py), [scripts/measure_chat_latency.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/scripts/measure_chat_latency.py)) executed successfully.

---

## ⚡ Step 25: Diagnosis & Reliability Fix for Frontend Chat Timeout
**Action:** Diagnosed and resolved the root cause of the frontend `AxiosError: timeout of 45000ms exceeded` error on `POST /api/chat` requests.
- **Root Cause Identified:**
  - Frontend Axios client in `frontend/src/api/axios.ts` was hardcoded to a 45-second timeout (`timeout: 45000`).
  - Backend LLM configuration has `LLM_TIMEOUT_SECONDS = 30.0s` with `LLM_MAX_RETRIES = 1` (allowing a worst-case execution time of 61 seconds).
  - On queries where LLM generation took >45 seconds (or during cold-start model initialization), Axios prematurely aborted the HTTP request at 45 seconds before the backend could return its HTTP 200 response, causing the frontend to report *"Unable to connect to the Techonomy server."*
- **Step Milestones & Reliability Instrumentation:**
  - [app/api/chat.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/api/chat.py) & [app/knowledge/rag/chat_service.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/knowledge/rag/chat_service.py): Added step milestones (`[RAG STEP] CHAT REQUEST START`, `RETRIEVAL START/END`, `PROMPT BUILD START/END`, `LLM REQUEST START`, `LLM RESPONSE RECEIVED`, `PROMPT LOG START/END`, `CHAT REQUEST END`).
  - Extracted `active_team_name` string safely before async operations to prevent SQLAlchemy `ObjectDeletedError` session detachment.
- **Timeout Policy Alignment:**
  - [frontend/src/api/axios.ts](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/frontend/src/api/axios.ts): Updated Axios timeout to `75000` (75 seconds) ensuring `Frontend Timeout (75s) > Backend Maximum Execution Time (61s)`.
- **Verification:**
  - Tested `"What is the company's annual revenue?"` 3 times end-to-end ([scripts/measure_target_question.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/scripts/measure_target_question.py)): All 3 requests returned `HTTP 200 OK` with valid answers, source citations, and team names.
  - Executed Pytest suite (**44/44 tests passed 100%**).
  - Executed `npm run build` (**0 errors**).

---

## ⚡ Step 26: RAG Quality Diagnosis & System Prompt Enhancement
**Action:** Diagnosed compound query failures and evaluated evidence coverage for multi-part questions versus single-vector retrieval.
- **System Prompt Rules Expanded:**
  - Updated [app/prompts/system_prompt.txt](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/app/prompts/system_prompt.txt) to explicitly mandate structured sectioning for multi-part questions, strict prohibition of empty/fabricated tables, and claim-level citation association.
- **Retrieval vs. Generation Diagnosis:**
  - Evaluated compound query: *"Who are the current owners of the company? tell me more about the ownership details and marketing strategies of the company"*.
  - Identified **RETRIEVAL** as the primary bottleneck for compound queries: A single dense query vector embeddings search retrieves chunks dominated by one topic (e.g., Shareholding/Ownership) while leaving secondary topics (Marketing Strategy) unretrieved.
  - Identified **SYSTEM INSTRUCTION IMPROVEMENT** as effective for single-intent queries, ensuring missing evidence is explicitly stated without empty tables or false claims.
- **Verification:**
  - Ran diagnostic suite across 5 target queries ([scripts/diagnose_retrieval_and_generation.py](file:///Users/pawaneswaran/Desktop/Work/PROJECTS/techonomy/backend/scripts/diagnose_retrieval_and_generation.py)).
  - Pytest test suite executed (**44/44 tests passed 100%**).




















