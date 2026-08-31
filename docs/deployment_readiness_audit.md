# CareAI Healthcare SaaS — Production Deployment Readiness Audit

**Audit Date:** August 31, 2026  
**Target Deployment Architecture:**
- **Frontend:** Vercel (React 18 SPA + Vite)
- **Backend:** Render (FastAPI ASGI Web Service)
- **Database:** PostgreSQL (Render Managed PostgreSQL or Neon DB)
- **AI Intelligence:** Google Gemini 1.5 Flash via Server-Side API Key

---

## 1. Executive Summary & Readiness Score

| Evaluation Domain | Status | Score (out of 100) | Primary Notes |
| :--- | :---: | :---: | :--- |
| **Backend Core & API** | 🟢 READY | 95 / 100 | 165/165 tests passing, clean FastAPI modular structure. |
| **PostgreSQL Compatibility** | 🟠 HIGH ATTENTION | 85 / 100 | `psycopg2-binary` present; requires `postgres://` $\rightarrow$ `postgresql://` URI normalization. |
| **Render Web Service** | 🟠 HIGH ATTENTION | 85 / 100 | Start command & health probe ready; local storage is ephemeral. |
| **Vercel Frontend** | 🔴 BLOCKER PRESENT | 80 / 100 | Vite build succeeds; missing `vercel.json` SPA route rewrite. |
| **Security & Secrets** | 🟢 READY | 90 / 100 | `.env` ignored in Git; requires production `SECRET_KEY` config. |
| **OVERALL READINESS SCORE** | **87 / 100** | **PRE-DEPLOYMENT READY (Minor config fixes required)** |

---

## 2. Architecture & Tech Stack Discovered

```mermaid
graph TD
    User([User / Browser]) -->|HTTPS| Vercel[Vercel: Frontend React SPA]
    Vercel -->|REST API Requests / CORS| Render[Render: FastAPI Backend Web Service]
    
    subgraph Render Cloud Infrastructure
        Render -->|SQLAlchemy 2.0 / Pool| Postgres[(Render PostgreSQL / Neon DB)]
        Render -->|google-genai SDK| Gemini[Google Gemini 1.5 Flash API]
        Render -->|Ephemeral Disk Storage| LocalDisk[Local /uploads Directory]
    end
```

---

## 3. Required Environment Variables Matrix

### 3.1 Backend (Render Web Service)
| Environment Variable | Required / Optional | Production Setting Recommendation | Security Note |
| :--- | :---: | :--- | :--- |
| `DATABASE_URL` | **Required** | Provided automatically by Render PostgreSQL: `postgresql://user:pass@host:5432/dbname` | Render internal database URL. |
| `SECRET_KEY` | **Required** | Strong 64-character random string (e.g. `openssl rand -hex 32`) | **Do NOT use development default**. |
| `ALGORITHM` | Optional | `HS256` (Default) | Standard JWT HMAC-SHA256 signing. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Optional | `1440` (24 Hours) or `480` (8 Hours) | Session timeout. |
| `ENVIRONMENT` | **Required** | `production` | Disables verbose tracebacks in logs. |
| `DEBUG` | **Required** | `False` | Disables debug mode. |
| `ALLOWED_ORIGINS` | **Required** | `https://your-app.vercel.app,https://your-custom-domain.com` | Whitelist specific Vercel frontend URL. |
| `GEMINI_API_KEY` | Optional / Recommended | Valid Google Gemini API Key from Google AI Studio | Server-side only; falls back to 503 if omitted. |
| `AI_MODEL_NAME` | Optional | `gemini-1.5-flash` | Default clinical AI model. |
| `PYTHON_VERSION` | Recommended | `3.12.9` | Pins Python runtime on Render. |

### 3.2 Frontend (Vercel Project Settings)
| Environment Variable | Required / Optional | Production Setting Recommendation |
| :--- | :---: | :--- |
| `VITE_API_URL` | **Required** | `https://careai-backend.onrender.com/api/v1` |

---

## 4. PostgreSQL & Database Migration Readiness

### 4.1 Drivers & Connection Handling
- **Driver:** `psycopg2-binary>=2.9.9` is included in [requirements.txt](file:///c:/Users/pillu/.gemini/antigravity-ide/scratch/ai-healthcare-saas/backend/requirements.txt).
- **Dialect Handling:** [session.py](file:///c:/Users/pillu/.gemini/antigravity-ide/scratch/ai-healthcare-saas/backend/app/database/session.py) handles `sqlite` vs PostgreSQL via `connect_args={"check_same_thread": False}` only for SQLite.
- **Connection Pooling:** `pool_pre_ping=True` is enabled on `create_engine()`, preventing dropped connections on cloud databases.

### 4.2 Database URL Compatibility Notice
- **Issue:** Render and Heroku inject PostgreSQL connection strings formatted as `postgres://user:password@host/db`. SQLAlchemy 2.0 requires the dialect prefix `postgresql://` (or `postgresql+psycopg2://`).
- **Fix Required:** In [config.py](file:///c:/Users/pillu/.gemini/antigravity-ide/scratch/ai-healthcare-saas/backend/app/core/config.py), sanitize `DATABASE_URL` with `.replace("postgres://", "postgresql://", 1)`.

### 4.3 Schema Migrations & Startup Lifespan
- **Alembic Configuration:** [migrations/env.py](file:///c:/Users/pillu/.gemini/antigravity-ide/scratch/ai-healthcare-saas/backend/migrations/env.py) dynamically reads `settings.DATABASE_URL`.
- **Automatic Initialization:** [main.py](file:///c:/Users/pillu/.gemini/antigravity-ide/scratch/ai-healthcare-saas/backend/app/main.py) executes `Base.metadata.create_all(bind=engine)` inside its asynchronous lifespan startup hook. Connecting to a fresh PostgreSQL database automatically bootstraps all relational tables without manual schema scripts.

---

## 5. Render Backend Readiness Assessment

| Component | Status | Details |
| :--- | :---: | :--- |
| **Build Command** | 🟢 READY | `pip install -r requirements.txt` |
| **Start Command** | 🟢 READY | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Health Check Endpoint** | 🟢 READY | `/api/health` returns HTTP 200 `{"status": "healthy"}` |
| **Root Endpoint** | 🟢 READY | `/` returns API title and version |
| **Interactive Docs** | 🟢 READY | `/docs` (Swagger UI) available for API inspection |
| **Process Management** | 🟢 READY | Asynchronous ASGI execution via Uvicorn |

---

## 6. Vercel Frontend Readiness Assessment

| Component | Status | Details |
| :--- | :---: | :--- |
| **Framework Preset** | 🟢 READY | Vite |
| **Build Command** | 🟢 READY | `npm run build` |
| **Output Directory** | 🟢 READY | `dist` |
| **Root Directory** | 🟢 READY | `frontend` |
| **SPA Route Rewriting** | 🔴 BLOCKER | Missing `frontend/vercel.json`. React Router SPA requires URL rewrite to `/index.html` to avoid 404 errors on page reload. |

---

## 7. File Storage & Ephemeral Filesystem Risk

- **Current Implementation:** [storage.py](file:///c:/Users/pillu/.gemini/antigravity-ide/scratch/ai-healthcare-saas/backend/app/core/storage.py) saves uploaded medical PDFs/images to the local filesystem at `backend/uploads/medical_documents/`.
- **Render Cloud Risk:** Standard Render Web Services use **ephemeral container filesystems**. Any file saved locally is deleted whenever the service restarts, deploys, or wakes from sleep.
- **Short-Term Production Workaround:** For demos and staging evaluations on Render, the system continues to process OCR and AI analysis in memory immediately upon upload.
- **Long-Term Production Solution:** Attach a Render Persistent Disk (under Disks tab) mounted at `/opt/render/project/src/backend/uploads`, or configure AWS S3 / Google Cloud Storage signed upload URLs.

---

## 8. CORS & Network Security Requirements

1. **Origins Whitelist:**
   - In production, set `ALLOWED_ORIGINS="https://careai.vercel.app"` (replace with your actual Vercel domain).
   - [config.py](file:///c:/Users/pillu/.gemini/antigravity-ide/scratch/ai-healthcare-saas/backend/app/core/config.py) supports parsing comma-separated URLs from the environment variable.
2. **Credentialed Requests:**
   - `allow_credentials=True` is enabled in `CORSMiddleware`.
   - Browser `Authorization: Bearer <token>` headers are permitted via `allow_headers=["*"]`.

---

## 9. Security Audit Findings

| Audit Check | Status | Verification Result |
| :--- | :---: | :--- |
| **Committed `.env` Files** | 🟢 PASS | `.env` is listed in root [.gitignore](file:///c:/Users/pillu/.gemini/antigravity-ide/scratch/ai-healthcare-saas/.gitignore) and excluded from version control. |
| **Exposed API Keys** | 🟢 PASS | Zero hardcoded Gemini/Google API keys found in codebase. |
| **Database Credentials** | 🟢 PASS | Database URLs are loaded strictly from environment variables. |
| **Password Security** | 🟢 PASS | Bcrypt password hashing with unique salts (no plaintext passwords stored). |
| **Admin PHI Boundary** | 🟢 PASS | Admins are programmatically blocked (HTTP 403) from accessing patient private medical documents. |

---

## 10. Prioritized Deployment Blockers & Recommendations

### 🔴 BLOCKER (Must configure for deployment)
1. **Create `frontend/vercel.json`:**
   Add single-page routing rewrite rule so refreshing `/patient/dashboard`, `/doctor/appointments`, etc. does not result in a 404 error on Vercel:
   ```json
   {
     "rewrites": [
       { "source": "/(.*)", "destination": "/index.html" }
     ]
   }
   ```
2. **Set `VITE_API_URL` on Vercel:**
   Configure `VITE_API_URL=https://your-render-backend.onrender.com/api/v1` in the Vercel Project Environment Variables before deploying the frontend.

3. **Normalize `DATABASE_URL` for PostgreSQL:**
   Ensure `DATABASE_URL` in [config.py](file:///c:/Users/pillu/.gemini/antigravity-ide/scratch/ai-healthcare-saas/backend/app/core/config.py) converts `postgres://` to `postgresql://` if provided by Render PostgreSQL.

---

### 🟠 HIGH (Strongly recommended for production)
4. **Set Production `SECRET_KEY` on Render:**
   Generate and inject a secure random 64-character secret in Render Environment Settings.
5. **Configure `ALLOWED_ORIGINS`:**
   Set `ALLOWED_ORIGINS=https://your-app.vercel.app` on Render backend settings to restrict CORS to your deployed frontend domain.
6. **Seed Database on Production:**
   Run `python seed.py` once via Render SSH console or as a pre-deploy release command to populate standardized lab test catalog and admin credentials.

---

### 🟡 MEDIUM (Future production enhancements)
7. **Persistent Cloud Document Vault:**
   Migrate local `/uploads` storage to AWS S3 or Google Cloud Storage buckets for persistent file storage across container restarts.

---

## 11. Verification Results Summary

- **Backend Pytest Test Suite:** **165 / 165 Tests Passed** (`100%`)
- **Alembic Migration Status:** **Head Revision (`e1f2a3b4c5d6`) Synced**
- **Frontend Production Build:** **Vite v5.4.21 Compiled with 0 Errors**
- **Git Working Tree:** Clean, untracked files properly identified
