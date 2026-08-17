# Techonomy Event Deployment & Operator Guide

This guide describes how to deploy the complete **Techonomy Knowledge Intelligence Platform** on any laptop using Docker and ngrok.

> **Target Architecture**: Single-Port Production Deployment  
> **Host Requirements**: Only **Git**, **Docker Desktop**, and **ngrok** are required on the host. Node.js and Python are built automatically inside Docker.

---

## 📋 Prerequisites

Ensure the deployment laptop has the following three tools installed:
1. **Git**: [https://git-scm.com](https://git-scm.com)
2. **Docker Desktop** (or Docker Engine with Docker Compose v2): [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
3. **ngrok CLI**: [https://ngrok.com/download](https://ngrok.com/download)

---

## 🚀 Quick Start Deployment (6 Steps)

### Step 1: Clone the Repository
Open a terminal (macOS/Linux) or PowerShell (Windows) and clone the repository:
```bash
git clone https://github.com/Pawan-19012006/Techonomy-Application.git techonomy
cd techonomy
```

### Step 2: Create Environment Configuration
Copy the example environment configuration to `backend/.env`:
```bash
cp backend/.env.example backend/.env
```

### Step 3: Populate API Keys & Secrets
Open `backend/.env` in any text editor and fill in your event secrets:
```env
# 1. Google Gemini Primary LLM Key (obtain from https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=AIzaSyYourActualGeminiApiKeyHere

# 2. OpenRouter Fallback LLM Key (obtain from https://openrouter.ai/keys)
OPENROUTER_API_KEY=sk-or-v1-YourActualOpenRouterKeyHere

# 3. Qdrant Cloud Vector Database (obtain from Qdrant Cloud console)
QDRANT_URL=https://your-cluster-id.qdrant.tech
QDRANT_API_KEY=your_qdrant_cloud_api_key_here

# 4. Supabase / PostgreSQL Database URL
DATABASE_URL=postgresql://postgres:password@db.supabase.co:5432/postgres

# 5. JWT Secret Key (Any random secure string)
JWT_SECRET=event-techonomy-secure-jwt-key-2026
```

### Step 4: Build and Start Application with Docker
Run ONE command to build and launch the complete application:
```bash
docker compose up --build -d
```
*Note: The initial build will take ~2-3 minutes as it compiles the production frontend and downloads the CPU PyTorch dependencies. Subsequent starts take seconds.*

### Step 5: Verify Application Health
Check that the backend, local database, and vector indices are online:
```bash
curl http://localhost:8000/health
```
Expected output:
```json
{"status": "healthy", "backend": "healthy", "database": "healthy", "qdrant": "healthy", ...}
```
You can also open `http://localhost:8000` in your web browser to test the user interface locally.

### Step 6: Expose Application with ngrok
Run ngrok against host port 8000:
```bash
ngrok http 8000
```
ngrok will print a public HTTPS URL (e.g., `https://active-whole-operable.ngrok-free.dev`).

**Share this single HTTPS URL with all event participants.**  
*Participants can now access the full React application, SSE AI streaming, and RAG search from any phone or laptop on any network.*

---

## 🛠️ Operational Commands

- **View Live Application Logs**:
  ```bash
  docker compose logs -f backend
  ```
- **Stop Application**:
  ```bash
  docker compose down
  ```
- **Restart Application**:
  ```bash
  docker compose restart backend
  ```

---

## ❓ Troubleshooting & Common Solutions

### 1. Docker Daemon Not Running
- **Symptom**: `Cannot connect to the Docker daemon at unix:///var/run/docker.sock`
- **Solution**: Open Docker Desktop on your laptop and wait until the status indicator turns green ("Docker Engine running").

### 2. Port 8000 Already Occupied
- **Symptom**: `Bind for 0.0.0.0:8000 failed: port is already allocated`
- **Solution**: Find and stop the process using port 8000:
  - macOS/Linux: `lsof -i :8000` then `kill -9 <PID>`
  - Windows: `netstat -ano | findstr :8000` then `taskkill /F /PID <PID>`

### 3. Missing Environment Variables / Controlled Error
- **Symptom**: Logs show `LLMQuotaExhaustedError` or `API key is missing`.
- **Solution**: Ensure `GEMINI_API_KEY` and `OPENROUTER_API_KEY` in `backend/.env` have valid values with no surrounding quotes or extra spaces. Restart container with `docker compose restart backend`.

### 4. Qdrant Cloud Connection Failure
- **Symptom**: Logs show `Could not connect to Qdrant Cloud at ... Falling back to local/in-memory Qdrant`.
- **Solution**: Check internet connectivity or verify `QDRANT_URL` and `QDRANT_API_KEY`. If internet is down, Techonomy automatically falls back to local disk/memory storage without crashing.

### 5. Embedding Model Download Failure
- **Symptom**: Container logs show `HFHubHTTPError` downloading `BAAI/bge-small-en-v1.5`.
- **Solution**: Verify the deployment laptop is connected to the internet during the initial container startup. HuggingFace models are cached in Docker volume `hf_cache` after the first download.

### 6. ngrok Not Authenticated
- **Symptom**: ngrok exits with `ERR_NGROK_4018`.
- **Solution**: Create a free ngrok account at [https://dashboard.ngrok.com](https://dashboard.ngrok.com) and run:
  ```bash
  ngrok config add-authtoken <your-authtoken>
  ```
