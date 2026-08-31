# CareAI — Enterprise AI-Powered Healthcare SaaS Platform

![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-18%2F19-61DAFB?logo=react)
![Vite](https://img.shields.io/badge/Vite-5.4%2B-646CFF?logo=vite)
![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini%201.5%20Flash-4285F4?logo=google)
![Tests](https://img.shields.io/badge/Tests-165%2F165%20Passing-success)
![Build](https://img.shields.io/badge/Production%20Build-Passing-success)

---

## 1. Project Title
**CareAI: Enterprise Multi-Role Healthcare SaaS Platform with Clinical Decision Support**

---

## 2. Project Overview
**CareAI** is an intelligent, multi-tenant clinical workflow and diagnostic healthcare platform. It provides role-tailored digital workspaces for **Patients**, **Doctors**, **Hospital Administrators**, **Laboratory Technicians**, and **Pharmacy Staff**. 

The platform integrates real-time doctor appointment booking, digital prescription authoring with multi-drug interaction safety analysis, end-to-end biological diagnostic specimen accessioning and panic threshold detection, dispensary queue tracking, and role-aware AI conversational assistants powered by Google Gemini 1.5 Flash.

---

## 3. Problem Statement
Modern healthcare operations suffer from several acute challenges:
- **Fragmented Clinical Records:** Disconnected systems between outpatient clinics, testing laboratories, and retail dispensaries result in lost patient history.
- **Preventable Adverse Drug Events (ADEs):** Prescribing physicians lack real-time, automated screening for drug-drug interactions, food timing warnings, and cross-reactive allergies.
- **Diagnostic Bottlenecks:** Manual custody tracking of laboratory specimens delays critical care decisions and risks missing panic-level biological markers.
- **Role & Security Vulnerabilities:** Inadequate Role-Based Access Control (RBAC) often exposes Protected Health Information (PHI) to unauthorized administrative personnel.

---

## 4. Solution
CareAI solves these issues through a unified SaaS architecture:
- **Unified 5-Role Platform:** Dedicated interfaces for Patient, Doctor, Admin, Lab Technician, and Pharmacy Staff.
- **AI Clinical Decision Support (CDS):** Multi-dimensional prescription drug interaction screening and medical document OCR analysis.
- **Rigorous Chain-of-Custody Diagnostic Lab Workflow:** Requisition $\rightarrow$ Specimen Collection $\rightarrow$ Analytical Run $\rightarrow$ Panic-Value Alerting $\rightarrow$ Tech Verification $\rightarrow$ Patient Report Release.
- **Controlled Dispensary Pipeline:** Doctor Prescription $\rightarrow$ Pharmacist Audit $\rightarrow$ Pickup Packaging $\rightarrow$ Dispensation with automated patient notifications.
- **Strict PHI Security Boundaries:** Zero administrative access to patient medical documents; strict tenant isolation.

---

## 5. Key Features
- **Dynamic Doctor Discovery & Scheduling:** Search by specialty, dynamic slot calculation, and appointment confirmations.
- **AI Prescription Safety Engine:** Analyzes drug-drug, drug-food, and drug-allergy interactions with high/moderate/low risk grading.
- **Medical Document AI Vault:** Upload medical files (PDFs, images) with automated clinical summary and abnormal findings extraction.
- **Diagnostic Lab Management:** Full specimen tracking (with hemolysis/clotting rejection criteria) and automated panic threshold flagging.
- **Pharmacy Dispensary System:** Status lifecycle tracking (`PRESCRIBED` $\rightarrow$ `UNDER_REVIEW` $\rightarrow$ `READY` $\rightarrow$ `DISPENSED`) with prescription immutability.
- **Multi-Turn CareAI Assistant:** Role-contextualized conversational intelligence with automatic emergency red-flag triage.
- **Real-Time Notification Pipeline:** Automated in-app notifications dispatched across all major clinical events.

---

## 6. User Roles Matrix

| Feature Domain | Patient | Doctor | Admin | Lab Tech | Pharmacy |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Self-Registration** | ✅ | ✅ (Pending) | ❌ | ❌ | ❌ |
| **Doctor Discovery & Booking** | ✅ | 📅 Manage Slots | 📊 Monitor | ❌ | ❌ |
| **Consultation & Prescriptions** | 📖 View Own | ✍️ Author & Issue | 📋 Audit | ❌ | 📦 Dispense |
| **AI Drug Safety Analysis** | 📊 View Summary | 🤖 Real-time CDS | ⚙️ Config | ❌ | 🔍 Audit |
| **Diagnostic Lab Processing** | 🧪 View Released | 🔬 Order Tests | 📑 Catalog | 🔬 Full Access | ❌ |
| **Staff Account Provisioning** | ❌ | ❌ | 🛡️ Full Admin | ❌ | ❌ |
| **Private PHI Access** | ✅ Own Only | 🩺 Consulted Only | 🚫 Blocked (403)| 🔬 Assigned Only| 📦 Prescriptions Only |

---

## 7. Technology Stack
- **Frontend:** React 18/19, Vite 5.4, React Router v6, Lucide React, Glassmorphic CSS Design System.
- **Backend:** Python 3.12+, FastAPI (ASGI), Pydantic v2, Pydantic-Settings.
- **Database & Migration:** SQLAlchemy 2.0 ORM, SQLite (Dev/Testing) / PostgreSQL (Production), Alembic.
- **Authentication & Security:** OAuth2 Bearer, Stateless JWT (HS256), Passlib (Bcrypt password hashing).
- **AI Intelligence:** Google Gemini 1.5 Flash (`google-genai`), custom prompt engineering, deterministic triage rules.
- **Testing:** Pytest 9.1+, HTTPX / Starlette TestClient (165 Automated Tests).

---

## 8. System Architecture
```
CareAI Platform
├── Client Layer (React 18 SPA + Vite)
│   ├── Public Portal (Doctor Search & Directory)
│   ├── Patient Portal (Appointments, Prescriptions, Lab Reports, AI Chat)
│   ├── Doctor Workspace (Consultation Queue, Availability, CDS Safety)
│   ├── Lab Diagnostics Console (STAT Queue, Specimen Accessioning, Panic Flags)
│   ├── Pharmacy Dispensary (Prescription Processing, Dispense Audit)
│   └── Admin Management Console (Doctor Vetting, Staff Provisioning)
│
├── API Gateway & Security Layer (FastAPI ASGI)
│   ├── CORS Middleware & Request Throttling
│   ├── JWT Authentication & Dependency Injection
│   └── 5-Role RBAC Authorization Gates
│
├── Business Logic & AI Layer
│   ├── Domain Services (Appointments, Prescriptions, Lab, Pharmacy)
│   ├── AI Assistant Service (Gemini 1.5 Flash)
│   └── Prescription Safety Engine & Document OCR
│
└── Persistence Layer
    ├── Relational Database (SQLAlchemy 2.0 / SQLite / PostgreSQL)
    └── Encrypted Document Vault (Storage Service)
```

---

## 9. Project Structure
```
ai-healthcare-saas/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # Modular API controllers (auth, patients, doctors, appointments, etc.)
│   │   ├── core/                # Config, security, JWT helpers, storage service
│   │   ├── database/            # Engine, session, Base model
│   │   ├── dependencies/        # DB, Auth, and RBAC dependency injection
│   │   ├── models/              # SQLAlchemy 2.0 database models
│   │   ├── schemas/             # Pydantic v2 validation schemas
│   │   ├── services/            # Pure business logic and transaction services
│   │   ├── ai/                  # AI safety engine and Gemini integration
│   │   └── main.py              # FastAPI application entry point
│   ├── migrations/              # Alembic migration scripts
│   ├── scripts/                 # Verification and live audit scripts
│   ├── tests/                   # 165 automated pytest unit and integration tests
│   ├── requirements.txt         # Python dependencies
│   └── seed.py                  # Demo database seeder
│
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI primitives (Card, Badge, Button, Navbar, Sidebar)
│   │   ├── contexts/            # AuthContext, ThemeContext
│   │   ├── pages/               # Role-specific views (patient, doctor, admin, lab, pharmacy, auth)
│   │   ├── services/            # REST API client services
│   │   └── utils/               # Constants, formatters, storage helpers
│   ├── package.json             # NPM dependencies & build scripts
│   └── vite.config.js           # Vite configuration & API proxy
│
└── docs/                        # Complete viva, architecture, workflow, and API documentation
```

---

## 10. Installation Instructions

### Prerequisites
- **Python 3.12+**
- **Node.js 18+ & npm**
- **Git**

### Clone Repository
```bash
git clone https://github.com/Niharika212006/CareAI-SaaS.git
cd CareAI-SaaS
```

---

## 11. Environment Variables Setup

### Backend (`backend/.env`)
Create `backend/.env` from the template:
```ini
PROJECT_NAME="CareAI Healthcare SaaS Platform"
ENVIRONMENT="development"
DEBUG=True
DATABASE_URL="sqlite:///./healthcare_dev.db"
SECRET_KEY="replace_with_a_secure_random_jwt_secret_in_production"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI Configuration (Optional for mock fallback, required for live Gemini)
AI_PROVIDER="gemini"
GEMINI_API_KEY="your_google_gemini_api_key_here"
AI_MODEL_NAME="gemini-1.5-flash"
```

### Frontend (`frontend/.env`)
Create `frontend/.env`:
```ini
VITE_API_URL=http://127.0.0.1:8000/api/v1
```

---

## 12. Database Setup & Seeding

```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed rich connected demo data
python seed.py
```

---

## 13. Running the Backend Server

```bash
cd backend
.venv\Scripts\activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Backend API:** `http://127.0.0.1:8000`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`
- **Health Probe:** `http://127.0.0.1:8000/api/health`

---

## 14. Running the Frontend Application

```bash
cd frontend
npm install
npm run dev
```
- **Frontend App:** `http://localhost:5173`

---

## 15. Running the Test Suite

```bash
cd backend
.venv\Scripts\activate

# Run complete 165 automated tests
python -m pytest

# Run live master integration audit (89 checks)
python -m scripts.final_verification_audit
```

---

## 16. Demo Credentials Matrix

| Role | Email Address | Password | Purpose in Demo |
| :--- | :--- | :--- | :--- |
| **Admin** | `pillu.212006@gmail.com` | `Neha@6328` | Doctor credential approval & staff provisioning |
| **Doctor** | `dr.sarah@careai.com` | `DoctorPass123!` | Appointments, prescriptions & AI safety analysis |
| **Patient** | `patient.john@example.com` | `PatientPass123!` | Booking, lab reports & CareAI assistant |
| **Lab Technician** | `lab.tech@careai.com` | `LabTechPass123!` | Specimen collection, result entry & report release |
| **Pharmacy Staff** | `pharmacy.staff@careai.com` | `PharmacyPass123!` | Dispensary queue & medication fulfillment |

*Note: The login page includes one-click demo fill buttons for all 5 roles for seamless presentation.*

---

## 17. AI Integration Setup
CareAI uses the Google Gemini 1.5 Flash API for conversational intelligence, prescription safety screening, and medical report summarization.
1. Obtain an API key from [Google AI Studio](https://aistudio.google.com/).
2. Set `GEMINI_API_KEY=your_key_here` in `backend/.env`.
3. If no key is supplied, CareAI operates in controlled fallback mode: clinical operations continue normally, while AI endpoints return a structured HTTP 503 service unavailable response with user-friendly notices.

---

## 18. Security Features
- **Stateless JWT Tokens with Expiration:** Signed with HMAC-SHA256.
- **Bcrypt Password Encryption:** Industry-standard salt-hashed credentials.
- **Role-Based Access Control (RBAC):** Backend dependency injection guards enforce 401/403 blocks.
- **Protected Health Information (PHI) Privacy Boundary:** Administrators are programmatically blocked from reading or downloading private patient medical records.
- **Prescription Immutability:** Pharmacy personnel cannot alter doctor clinical diagnoses or prescribed dosages.

---

## 19. Current Limitations
- **Notification Transport:** In-app database notification queue (live WebSockets and SMS gateways are not configured).
- **Storage Layer:** Local filesystem storage service for medical PDFs (cloud S3/GCS adapters ready for production config).
- **Single-Tenant Database Instance:** Uses logical tenant separation rather than separate database schemas per hospital organization.

---

## 20. Future Enhancements
- **Bi-directional WebSockets / WebRTC:** Real-time in-browser tele-health video consultations.
- **EHR Interoperability (FHIR / HL7):** Integration with hospital Fast Healthcare Interoperability Resources (FHIR) standard APIs.
- **Native Mobile Apps:** React Native iOS/Android client apps with biometric face/fingerprint authentication.
- **Automated Pharmacy Inventory Sync:** Real-time stock decrementing upon prescription dispensation.
