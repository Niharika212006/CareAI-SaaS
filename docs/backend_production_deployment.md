# CareAI Healthcare SaaS — Render Backend & PostgreSQL Production Deployment Guide

---

## 1. Deployment Overview & Cloud Architecture

The CareAI backend and database infrastructure are deployed on **Render Cloud Services**:

```mermaid
graph TD
    Client[Frontend Client / Vercel / API Consumer] -->|HTTPS / REST API| RenderWeb[Render Web Service: careai-backend]
    
    subgraph Render Cloud Infrastructure (Region: Oregon)
        RenderWeb -->|FastAPI ASGI Server| Uvicorn[Uvicorn Process on $PORT]
        Uvicorn -->|SQLAlchemy 2.0 Pool| Postgres[(Render PostgreSQL: careai-postgres)]
        Uvicorn -->|google-genai SDK| Gemini[Google Gemini 1.5 Flash API]
    end
```

---

## 2. Deployment Instructions (Two Supported Methods)

### Method A: One-Click Render Blueprint (Recommended)
Because [render.yaml](file:///c:/Users/pillu/.gemini/antigravity-ide/scratch/ai-healthcare-saas/render.yaml) is configured in the repository root:
1. Log in to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** $\rightarrow$ **Blueprint**.
3. Connect your GitHub repository: `Niharika212006/CareAI-SaaS`.
4. Render will automatically detect `render.yaml` and provision:
   - **PostgreSQL Database:** `careai-postgres` (Database: `careai_db`, User: `careai_user`).
   - **Web Service:** `careai-backend` (Root: `backend`, Runtime: `Python 3.12`).
5. In the environment prompt:
   - Enter your `GEMINI_API_KEY` (from [Google AI Studio](https://aistudio.google.com/)).
   - Set `ALLOWED_ORIGINS` to `https://careai.vercel.app` (or `*` temporarily until frontend domain is created).
6. Click **Apply**. Render will automatically build, run database migrations (`alembic upgrade head`), and launch the backend service.

---

### Method B: Manual Render Setup (Alternative)

#### Step 1: Create Render PostgreSQL Database
1. In Render Dashboard, click **New +** $\rightarrow$ **PostgreSQL**.
2. **Name:** `careai-postgres`
3. **Database:** `careai_db`
4. **User:** `careai_user`
5. **Region:** `Oregon (US West)` (or closest region)
6. **Plan:** `Free`
7. Click **Create Database**.
8. Once provisioned, copy the **Internal Database URL** (e.g. `postgresql://careai_user:password@dpg-...-a/careai_db`).

#### Step 2: Create Render Web Service
1. Click **New +** $\rightarrow$ **Web Service**.
2. Connect your repository: `Niharika212006/CareAI-SaaS`.
3. Configure the following service settings:
   - **Name:** `careai-backend`
   - **Region:** Same as database (e.g. `Oregon`)
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt && alembic upgrade head`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/health`
4. Add the following **Environment Variables**:

| Variable Name | Value Source | Purpose |
| :--- | :--- | :--- |
| `DATABASE_URL` | Copied from Render PostgreSQL Internal Database URL | Production database connection |
| `ENVIRONMENT` | `production` | Production mode |
| `DEBUG` | `False` | Disables debug mode |
| `SECRET_KEY` | Generate secure random 64-char string (e.g. `openssl rand -hex 32`) | JWT cryptographic signing |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | 24-hour token validity |
| `ALLOWED_ORIGINS` | `https://careai.vercel.app,http://localhost:5173` | Allowed CORS origins |
| `PYTHON_VERSION` | `3.12.9` | Pins Python version |
| `AI_PROVIDER` | `gemini` | Gemini AI provider |
| `AI_MODEL_NAME` | `gemini-1.5-flash` | Gemini model |
| `GEMINI_API_KEY` | Your Google Gemini API Key | Server-side AI intelligence |

5. Click **Create Web Service**.

---

## 3. Production Database Seeding

After the backend web service deploys successfully:
1. In the Render Dashboard, open the `careai-backend` service.
2. Click the **Shell** tab (opens a live SSH terminal in your browser).
3. Run the idempotent seeder script:
   ```bash
   python seed.py
   ```
4. Output will confirm:
   ```text
   [+] Seeding CareAI Healthcare SaaS platform with rich demo data...
     [OK] Admin created/updated: pillu.212006@gmail.com / Neha@6328
     [OK] Lab Test Catalog populated (8 standardized tests).
     [OK] In-app notifications seeded across all 5 roles.
   [SUCCESS] CareAI demo data seeded successfully with 100% role fidelity!
   ```

---

## 4. Live Backend Verification Protocol

Once the Render service status displays **Live**, run the following verification checks against your deployed URL:

### 1. Health Probe (`GET /health`)
```bash
curl -i https://<your-service-name>.onrender.com/health
```
**Expected Response:** HTTP 200 `{"status": "healthy", "service": "CareAI Healthcare SaaS Platform", "environment": "production", "version": "0.1.0"}`

### 2. Swagger Documentation (`GET /docs`)
Open in browser: `https://<your-service-name>.onrender.com/docs`  
**Expected:** Interactive FastAPI OpenAPI 3.0 documentation page loads cleanly.

### 3. Production Authentication (`POST /api/v1/auth/login`)
```bash
curl -X POST https://<your-service-name>.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "pillu.212006@gmail.com", "password": "Neha@6328"}'
```
**Expected Response:** HTTP 200 with `access_token`, `role: "ADMIN"`, and user metadata.

### 4. RBAC Protection (`GET /api/v1/dashboard/admin`)
```bash
curl -X GET https://<your-service-name>.onrender.com/api/v1/dashboard/admin \
  -H "Authorization: Bearer <TOKEN_FROM_STEP_3>"
```
**Expected Response:** HTTP 200 with platform metrics. Without token: HTTP 401 Unauthorized.
