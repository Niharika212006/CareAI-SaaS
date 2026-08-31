# AI Healthcare SaaS Platform

A production-grade, full-stack, role-based AI Healthcare SaaS platform engineered for intelligent clinical workflow management, interactive consultations, automated prescription safety analysis, and clinical decision support.

---

## 📌 1. Project Purpose & Vision

Modern healthcare ecosystems often suffer from fragmented patient records, delayed doctor discovery, communication bottlenecks, and preventable adverse drug events (ADEs).

The **AI Healthcare SaaS Platform** bridges these gaps by providing:
- **Centralized Clinical Workspace**: Streamlined portals tailored specifically for **Patients**, **Doctors**, and **System Administrators**.
- **AI-Powered Clinical Safety**: Real-time multi-dimensional drug analysis (drug-drug, drug-food, and drug-allergy interactions).
- **Intelligent Medical Records**: Structured prescription generation and historical health profile tracking.
- **Audited Role-Based Security**: Strict JWT-based RBAC (Role-Based Access Control) with end-to-end data validation.

---

## 👥 2. User Roles & Permissions Matrix

| Feature / Domain | Patient | Doctor | Admin |
| :--- | :---: | :---: | :---: |
| **Authentication & Profile Management** | ✅ Self | ✅ Self | ✅ Self |
| **Doctor Profile Verification** | ❌ | 📝 Submits Details | 🛡️ Approves / Rejects |
| **Doctor Discovery & Booking** | 🔍 Search & Book | 📅 Manage Schedule | 📊 Platform Oversight |
| **Consultations & Appointments** | 🕒 View & Join | 🩺 Accept & Conduct | 📋 All Records |
| **Prescription Generation** | 📖 View & Download | ✍️ Create & Issue | 🔍 Audit Log |
| **AI Prescription Interaction Analysis**| 📊 View Safety Summary | 🤖 Real-time AI Analysis | ⚙️ Model/Prompt Config |
| **System Metrics & User Management** | ❌ | ❌ | 📈 Full Admin Dashboard |

---

## 🛠️ 3. Technology Stack

### Backend
- **Language & Framework**: Python 3.12+ | [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous REST API)
- **Database & ORM**: PostgreSQL | [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Database Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **Data Validation & Settings**: [Pydantic v2](https://docs.pydantic.dev/) & `pydantic-settings`
- **Authentication & Security**: OAuth2 Bearer with JWT (`python-jose` / `pyjwt`), Passlib / Bcrypt password hashing
- **AI / LLM Integration**: Modular LLM Interface (Gemini / Claude / OpenAI API compatibility) for structured clinical safety analysis
- **Testing**: `pytest`, `httpx` (Async / sync TestClient)

### Frontend
- **Framework & Build**: [React 19 / 18](https://react.dev/) + [Vite](https://vitejs.dev/)
- **Routing**: [React Router DOM v6/v7](https://reactrouter.com/) (with Protected Route RBAC guards)
- **State & Context**: React Context API (`AuthContext`, `ThemeContext`)
- **Icons & UI**: [Lucide React](https://lucide.dev/), Modern Glassmorphic CSS design system with CSS custom properties
- **HTTP Client**: Interceptor-enabled Fetch/Axios API client with auto-refresh and bearer token injection

---

## 🏛️ 4. High-Level Modular Architecture

The repository enforces **Clean Architecture** principles, strictly decoupling business logic, data persistence, and API presentation layers.

```
ai-healthcare-saas/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/              # Modular API controllers
│   │   │   │   ├── auth.py          # Authentication (Register, Login, Token Refresh)
│   │   │   │   ├── users.py         # User account operations
│   │   │   │   ├── patients.py      # Patient profile & history
│   │   │   │   ├── doctors.py       # Doctor profiles & discovery
│   │   │   │   ├── admin.py         # Admin moderation & metrics
│   │   │   │   ├── appointments.py  # Consultation bookings
│   │   │   │   ├── prescriptions.py # Prescription creation & viewing
│   │   │   │   └── ai.py            # AI interaction checks & safety reports
│   │   │   └── api.py               # Aggregated APIRouter
│   │   ├── core/                    # Core configuration, security, JWT helpers
│   │   ├── database/                # Engine, SessionLocal, DeclarativeBase
│   │   ├── models/                  # SQLAlchemy ORM database models
│   │   ├── schemas/                 # Pydantic validation schemas
│   │   ├── services/                # Encapsulated business logic layer
│   │   ├── dependencies/            # FastAPI Dependency Injection (DB, RBAC)
│   │   ├── ai/                      # AI Interaction engine & prompt templates
│   │   ├── utils/                   # Structured logging & utility functions
│   │   └── main.py                  # FastAPI application entry point & CORS
│   ├── migrations/                  # Alembic migration scripts
│   ├── tests/                       # Automated backend test suite
│   ├── alembic.ini                  # Alembic configuration
│   ├── requirements.txt             # Python dependencies
│   └── .env.example                 # Backend environment variable template
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── common/              # Reusable UI primitives (Button, Card, Badge, Modal, Navbar, Sidebar)
│   │   ├── pages/
│   │   │   ├── auth/                # Login, Registration, Password Recovery
│   │   │   ├── patient/             # Patient dashboard & health records
│   │   │   ├── doctor/              # Doctor dashboard, appointments, prescription writer
│   │   │   ├── admin/               # Admin dashboard, doctor verification, user management
│   │   │   └── public/              # Landing page, doctor discovery directory, 404
│   │   ├── layouts/                 # DashboardLayout, AuthLayout, PublicLayout
│   │   ├── contexts/                # AuthContext (JWT, session persistence, role state)
│   │   ├── hooks/                   # Custom hooks (useAuth, useApi)
│   │   ├── services/                # Typed REST API service methods
│   │   ├── routes/                  # Central AppRoutes with ProtectedRoute role guards
│   │   ├── utils/                   # Constants, formatters, storage helpers
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css                # Premium modern healthcare design system
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
│
└── README.md                        # Master architectural documentation
```

---

## 🚀 5. Getting Started & Local Development

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
copy .env.example .env

# Run FastAPI development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- **API Documentation (Swagger UI)**: `http://127.0.0.1:8000/docs`
- **Alternative Docs (ReDoc)**: `http://127.0.0.1:8000/redoc`
- **Health Check**: `http://127.0.0.1:8000/api/health`

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
- **Web Application URL**: `http://localhost:5173/`

---

## 🗺️ 6. Implementation Roadmap

- [x] **Phase 1: Project Foundation & Architecture** (Current)
  - Modular folder structure establishment
  - Clean architecture separation (API, Core, DB, Models, Schemas, Services, Dependencies, AI)
  - Unified design system & responsive layout foundation
- [ ] **Phase 2: Authentication & Role-Based Access Control (RBAC)**
  - Registration, Login, Token Refresh for Patient, Doctor, Admin
  - Password hashing & JWT verification
  - Role-protected routes & session hydration
- [ ] **Phase 3: Profiles & Doctor Verification Workflow**
  - Patient health profile setup (allergies, medical history, blood group)
  - Doctor credential submission (license, specialization, experience)
  - Admin approval/rejection moderation workflow
- [ ] **Phase 4: Doctor Discovery & Appointment Booking**
  - Search & filter doctors by specialization, rating, and fee
  - Appointment scheduling, status transitions, and calendar overview
- [ ] **Phase 5: Prescriptions & AI Interaction Engine**
  - Digital prescription authoring for doctors
  - Drug-drug, drug-food, and drug-allergy interaction detection
  - AI patient safety report generation
- [ ] **Phase 6: Admin Analytics & Final Polish**
  - Platform audit logging & metrics
  - End-to-end integration tests & production deployment readiness
