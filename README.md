# Techonomy / Kairos

**Techonomy (Kairos Intelligence System)** is an internal company-knowledge intelligence platform powered by an instruction-guided Retrieval-Augmented Generation (RAG) architecture. It provides grounded, multi-document analytical answers based on official company documentation.

---

## 1. Prerequisites

The host machine running the Techonomy platform requires **ONLY**:

1. **Git**: To clone the repository.
2. **Docker Desktop** (or Docker Engine + Docker Compose): To build and run all services inside containers.
3. **ngrok CLI**: To expose the single application port (`8000`) securely to the internet.
4. **Internet Connection**: Required to reach LLM APIs (Gemini / OpenRouter) and vector services.

> [!NOTE]
> You **do NOT need** Python, Node.js, npm, PostgreSQL, Qdrant, or PyTorch installed locally. All build tools, runtime environments, databases, and dependencies run automatically inside Docker containers.

---

## 2. Clone the Repository

Open a terminal on your host machine and run:

```bash
# 1. Clone the repository
git clone https://github.com/Pawan-19012006/Techonomy-Application.git
cd techonomy

# 2. Switch to the final implementation branch
git switch finetune

# 3. Verify you are on the 'finetune' branch
git branch
```

---

## 3. Environment Setup

Copy the backend environment template:

```bash
cp backend/.env.example backend/.env
```

> [!CAUTION]
> **NEVER commit `backend/.env` to Git.** It contains private API credentials.

Edit `backend/.env` using any text editor and fill in your actual credentials:

### A. Application & Server Configuration
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

### B. Persistent Database Configuration
```env
DATABASE_URL=postgresql://techonomy:techonomy_pass@postgres:5432/techonomy_db
```
*(Uses the local PostgreSQL Docker container by default. Replace with a Supabase connection string if using cloud PostgreSQL).*

### C. Vector Database Configuration (Qdrant)
```env
QDRANT_URL=YOUR_QDRANT_URL
QDRANT_API_KEY=YOUR_QDRANT_API_KEY
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=company_knowledge
```
*(If `QDRANT_URL` and `QDRANT_API_KEY` are left blank, Techonomy falls back to the local `qdrant` container).*

### D. Gemini API Credentials (Primary LLM)
```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_API_KEY_1=YOUR_GEMINI_KEY_1
GEMINI_API_KEY_2=YOUR_GEMINI_KEY_2
GEMINI_MODEL=gemini-flash-lite-latest
```

### E. OpenRouter API Credentials (Fallback LLM)
```env
OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
OPENROUTER_MODEL=nvidia/nemotron-3.5-lightning:free
```

### F. Embedding & Retrieval Configuration
```env
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5
RETRIEVAL_TOP_K=10
TOP_K=10
```

### G. Event & Team Quota Configuration
```env
QUESTION_LIMIT=10
```

---

## 4. Understand the Knowledge Base

The system operates across **TWO logically separate knowledge bases**:

### 1. Company Documents (`company_knowledge`)
- **What it contains**: Official company financial statements, annual reports, sales data, customer analytics, and operational metrics.
- **Usage**: Used to answer participant questions.
- **Participant Access**: **User-visible**. Appears in search, citations, and can be opened in the document viewer with exact page navigation (`3.pdf — Page 12`).

### 2. Instruction Documents (`instruction_knowledge`)
- **What it contains**: Internal analytical frameworks, evaluation principles, and query planning guides.
- **Usage**: Used internally by the Stage 1 Planner to understand *HOW* to analyze different types of questions.
- **Participant Access**: **STRICTLY INTERNAL**. Never exposed to participants, never cited, and never listed on the Documents page.

### 4-Step RAG Flow
```text
User Question
     │
     ▼
Instruction Knowledge (Determines HOW to analyze the question & plans queries)
     │
     ▼
Company Knowledge (Searched for actual factual evidence)
     │
     ▼
LLM Answer (Generated strictly from company evidence)
     │
     ▼
Company Citations (Points ONLY to official company document pages)
```

---

## 5. Knowledge Base Documents

Place your PDF documents in the correct backend directories:

```text
techonomy/backend/data/documents/
├── company/        <-- Place official COMPANY PDFs here (e.g. 1.pdf, 3.pdf, DS08...)
└── instructions/   <-- Place internal INSTRUCTION PDFs here (e.g. Playbooks, Frameworks)
```

> [!IMPORTANT]
> Keep the datasets strictly separated. Never place instruction PDFs inside `company/`.

---

## 6. Start Docker

Launch the complete application stack (Frontend SPA + FastAPI Backend + PostgreSQL + Qdrant) with a single command:

```bash
# 1. Start all containers in detached mode
docker compose up --build -d

# 2. Check container status
docker compose ps

# 3. View backend startup logs
docker compose logs backend --tail=100
```

---

## 7. Ingest the Knowledge Base

You must ingest the PDF documents into vector collections before asking questions.

> [!NOTE]
> Always run `reset` before ingesting a replaced dataset to clear stale vector chunks and avoid duplicate retrieval results. Collection resets are independent: resetting `company` does NOT delete `instruction` data.

Run the following commands inside the running backend container:

```bash
# A. Ingest COMPANY Documents
docker compose exec backend python scripts/ingest_datasets.py --type reset-company
docker compose exec backend python scripts/ingest_datasets.py --type company

# B. Ingest INSTRUCTION Documents
docker compose exec backend python scripts/ingest_datasets.py --type reset-instruction
docker compose exec backend python scripts/ingest_datasets.py --type instruction
```

---

## 8. Verify the RAG

Run the automated RAG isolation test suite to confirm dataset separation and evidence boundaries:

```bash
docker compose exec backend python -m pytest tests/test_instruction_rag_isolation.py -v
```

This verifies:
- `company_knowledge` and `instruction_knowledge` collection isolation
- Two-stage instruction-guided retrieval
- Hard evidence boundary (only company documents used as factual context)
- Company-only source citations
- Independent dataset collection resets

---

## 9. Run Locally

Open your browser and navigate to:

👉 **[http://localhost:8000](http://localhost:8000)**

### Quick Verification Walkthrough:
1. **Participant Login**: Register/Join a team.
2. **Dashboard**: View team session timer and question quota.
3. **Kairos Chatbot**: Ask an analytical question (e.g., *"How has profitability changed across reporting periods?"*).
4. **Citations & Document Viewer**: Click a citation card (`3.pdf — Page 12`). Verify it opens the PDF viewer and scrolls to page 12.
5. **Documents Page**: Verify only company PDFs appear.
6. **Admin Login**: Access `/login` (select **ADMIN** tab; credentials: `kairos@csbs` / `kairospass`).

---

## 10. ngrok Deployment

Expose the single application port (`8000`) securely to the internet:

```bash
ngrok http 8000
```

ngrok will output an HTTPS URL:

```text
Forwarding    https://xxxx.ngrok-free.app -> http://localhost:8000
```

Copy the **HTTPS URL** (`https://xxxx.ngrok-free.app`). This is the **ONLY** URL required for the entire event.

---

## 11. Remote Participant Usage

- **Participant Access**: Participants open the single HTTPS ngrok URL on their smartphones, laptops, or tablets.
- **Zero Client Requirements**: Participants do **NOT** need Git, Docker, Python, Node, databases, or API keys.
- **Host Laptop Requirements**: The hosting laptop must remain:
  1. Powered on and awake.
  2. Connected to an active internet connection.
  3. Running Docker Desktop (`techonomy_backend` active).
  4. Running `ngrok http 8000`.

---

## 12. Common Commands

| Task | Command |
| :--- | :--- |
| **Start Stack** | `docker compose up --build -d` |
| **Stop Stack** | `docker compose down` |
| **Container Status** | `docker compose ps` |
| **Backend Logs (Tail 100)** | `docker compose logs backend --tail=100` |
| **Follow Live Backend Logs** | `docker compose logs -f backend` |
| **Restart Stack** | `docker compose restart` |

---

## 13. Troubleshooting

### 1. Containers Not Starting or Unhealthy
Check container status and logs:
```bash
docker compose ps
docker compose logs backend --tail=100
```

### 2. Environment / API Key Errors
Ensure `backend/.env` exists and contains at least one valid `GEMINI_API_KEY` or `OPENROUTER_API_KEY`.

### 3. RAG Returning Stale / Duplicate Documents
Clear and re-ingest the target collection:
```bash
docker compose exec backend python scripts/ingest_datasets.py --type reset-company
docker compose exec backend python scripts/ingest_datasets.py --type company
```

### 4. ngrok Connection Issues
Verify the app is working locally first at `http://localhost:8000`, then confirm ngrok is targeting port `8000`:
```bash
ngrok http 8000
```

### 5. Port 8000 Conflict
If port 8000 is occupied on the host, stop existing processes using port 8000 before running `docker compose up`.
