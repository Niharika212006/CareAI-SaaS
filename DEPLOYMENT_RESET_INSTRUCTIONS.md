# Render PostgreSQL Database Reset & Deployment Guide

This guide explains how to perform a clean database reset on Render if your existing PostgreSQL instance is contaminated with partial or failed migration state.

---

## Why Reset May Be Needed
If a previous migration run failed halfway (e.g. creating some custom types or tables before erroring out), the PostgreSQL database state may have orphaned objects. A clean database or table wipe allows Alembic to run the entire linear chain from zero (`000000000001` $\rightarrow$ `e1f2a3b4c5d6`) cleanly.

---

## Option 1: Recreate the PostgreSQL Instance on Render (Recommended)

1. Log in to your **[Render Dashboard](https://dashboard.render.com)**.
2. Navigate to your PostgreSQL database service: **`careai-postgres`** (or `careai_db`).
3. If you want a fresh database:
   - Click **Settings** $\rightarrow$ scroll to the bottom $\rightarrow$ click **Delete Database**.
   - Click **New +** $\rightarrow$ select **PostgreSQL**.
   - Name: `careai-postgres`
   - Database: `careai_db`
   - User: `careai_user`
   - Plan: **Free**
   - Click **Create Database**.
4. Copy the **Internal Database URL** from the new database.
5. Go to your Web Service **`careai-backend`** $\rightarrow$ **Environment**.
6. Ensure the `DATABASE_URL` matches the new Internal Database URL.
7. Click **Manual Deploy** $\rightarrow$ **Clear build cache & deploy**.

---

## Option 2: Drop and Recreate Public Schema via Render Web Shell or psql

If you prefer not to delete the entire database service, connect to your PostgreSQL database via Render's **psql** / **Connect** / Web Shell and run:

```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO public;
```

Then trigger a manual deploy on the Web Service:
- Click **Manual Deploy** $\rightarrow$ **Deploy latest commit**.

---

## Verification After Deployment
Once deployed, verify:
1. **Health Check:** `GET https://careai-backend.onrender.com/health` returns `{"status":"healthy","database":"connected"}`.
2. **Seed Initial Demo Data (Optional / Automatic):**
   In your Web Service Shell on Render, run:
   ```bash
   python seed.py
   ```
   This populates the fresh PostgreSQL database with all 5 role accounts and sample data.
