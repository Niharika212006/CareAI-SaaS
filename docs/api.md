# CareAI Healthcare SaaS — API Architecture & Endpoint Reference

---

## 1. Authentication & Identity Management (`/api/v1/auth`)

| Endpoint | Method | Purpose | Role Authorization |
| :--- | :--- | :--- | :--- |
| `/api/v1/auth/login` | `POST` | Authenticates user via email & password, returns JWT token & role metadata. | Public (All users) |
| `/api/v1/auth/register` | `POST` | Self-registers a new `PATIENT` or `DOCTOR` (starts `PENDING`). Staff/Admin registration blocked. | Public |
| `/api/v1/auth/me` | `GET` | Returns currently authenticated user identity and profile summary. | Authenticated (Any role) |
| `/api/v1/auth/refresh` | `POST` | Issues fresh access token for unexpired sessions. | Authenticated |

---

## 2. Patient & Medical Profile (`/api/v1/patients`)

| Endpoint | Method | Purpose | Role Authorization |
| :--- | :--- | :--- | :--- |
| `/api/v1/patients/me` | `GET` | Retrieves current patient's clinical profile (allergies, chronic conditions, blood group). | `PATIENT` |
| `/api/v1/patients/me` | `PUT` | Updates personal medical history and emergency contacts. | `PATIENT` |
| `/api/v1/patients/{id}` | `GET` | Retrieves specific patient clinical profile for consultation preparation. | `DOCTOR`, `ADMIN` |

---

## 3. Doctor Discovery & Availability (`/api/v1/doctors`)

| Endpoint | Method | Purpose | Role Authorization |
| :--- | :--- | :--- | :--- |
| `/api/v1/doctors/directory` | `GET` | Search approved doctors by name, specialization, or hospital. | Public / `PATIENT` |
| `/api/v1/doctors/{id}/slots` | `GET` | Computes dynamic available booking slots for a specific doctor on a chosen date. | Public / `PATIENT` |
| `/api/v1/doctor/availability` | `GET` | Retrieves weekly consultation hours and recurring availability rules. | `DOCTOR` |
| `/api/v1/doctor/availability` | `POST` | Configures recurring weekly consultation time windows and slot durations. | `DOCTOR` |
| `/api/v1/doctor/unavailable-dates`| `POST` | Blocks specific holiday or emergency leave dates from the booking calendar. | `DOCTOR` |

---

## 4. Appointments & Consultations (`/api/v1/appointments`)

| Endpoint | Method | Purpose | Role Authorization |
| :--- | :--- | :--- | :--- |
| `/api/v1/appointments` | `POST` | Books a consultation appointment with an approved doctor. | `PATIENT` |
| `/api/v1/appointments/my` | `GET` | Retrieves all upcoming and past appointments for current patient. | `PATIENT` |
| `/api/v1/appointments/doctor/my` | `GET` | Retrieves clinical appointment schedule and patient consultation queue. | `DOCTOR` |
| `/api/v1/appointments/{id}/confirm`| `PATCH` | Confirms a pending patient appointment booking. | `DOCTOR` |
| `/api/v1/appointments/{id}/complete`| `PATCH`| Marks consultation as completed and unlocks prescription generation. | `DOCTOR` |
| `/api/v1/appointments/{id}/cancel` | `PATCH` | Cancels an appointment with a recorded reason. | `PATIENT`, `DOCTOR`, `ADMIN` |

---

## 5. Digital Prescriptions & Pharmacy Dispensary (`/api/v1/prescriptions`, `/api/v1/pharmacy`)

| Endpoint | Method | Purpose | Role Authorization |
| :--- | :--- | :--- | :--- |
| `/api/v1/prescriptions` | `POST` | Authors and issues a digital prescription for a completed consultation. | `DOCTOR`, `ADMIN` |
| `/api/v1/prescriptions/my` | `GET` | Retrieves active and historical prescriptions for current patient. | `PATIENT` |
| `/api/v1/prescriptions/{id}` | `GET` | Retrieves full prescription details, medication schedule, and AI safety report. | `PATIENT`, `DOCTOR`, `PHARMACY_STAFF`, `ADMIN` |
| `/api/v1/pharmacy/dashboard` | `GET` | Operational metrics for pharmacy (pending, review, ready, dispensed today). | `PHARMACY_STAFF` |
| `/api/v1/pharmacy/prescriptions` | `GET` | Pharmacy dispensary queue with status, patient, and risk filters. | `PHARMACY_STAFF` |
| `/api/v1/pharmacy/prescriptions/{id}/status` | `PATCH` | Transitions prescription status (`UNDER_REVIEW` $\rightarrow$ `READY`). | `PHARMACY_STAFF` |
| `/api/v1/pharmacy/prescriptions/{id}/dispense` | `POST` | Records final medication dispensation and alerts patient & doctor. | `PHARMACY_STAFF` |

---

## 6. Diagnostic Laboratory Management (`/api/v1/lab`)

| Endpoint | Method | Purpose | Role Authorization |
| :--- | :--- | :--- | :--- |
| `/api/v1/lab/stats` | `GET` | Laboratory dashboard metrics (pending specimens, in-progress runs, critical alerts).| `LAB_TECHNICIAN` |
| `/api/v1/lab/queue` | `GET` | Prioritized diagnostic work queue (filter by `STAT`, `URGENT`, `ROUTINE`). | `LAB_TECHNICIAN` |
| `/api/v1/lab/orders` | `POST` | Creates diagnostic lab requisition order with multiple test line items. | `DOCTOR`, `PATIENT`, `ADMIN` |
| `/api/v1/lab/orders/{id}/collect-sample` | `POST` | Logs specimen accessioning or flags compromised sample (`HEMOLYZED`/`CLOTTED`). | `LAB_TECHNICIAN` |
| `/api/v1/lab/orders/{id}/start-processing`| `POST` | Transitions order to `IN_PROGRESS` analytical run. | `LAB_TECHNICIAN` |
| `/api/v1/lab/orders/{id}/enter-results` | `POST` | Submits analyte results; triggers automatic panic threshold flagging (`CRITICAL`). | `LAB_TECHNICIAN` |
| `/api/v1/lab/orders/{id}/verify` | `POST` | Technologist verifies findings and attaches clinical validation notes. | `LAB_TECHNICIAN` |
| `/api/v1/lab/orders/{id}/release`| `POST` | Releases final report for patient and physician viewing. | `LAB_TECHNICIAN` |
| `/api/v1/lab/patient/my-reports` | `GET` | Patient portal endpoint listing all verified and released diagnostic reports. | `PATIENT` |
| `/api/v1/lab/patient/my-reports/{id}`| `GET` | Structured diagnostic report details with reference ranges and abnormal flags. | `PATIENT` |

---

## 7. AI Intelligence & Assistant (`/api/v1/ai`)

| Endpoint | Method | Purpose | Role Authorization |
| :--- | :--- | :--- | :--- |
| `/api/v1/ai/assistant/chat` | `POST` | Multi-turn conversational CareAI Assistant with role-aware system prompts. | Authenticated (All roles) |
| `/api/v1/ai/assistant/conversations` | `GET` | Lists user's saved multi-turn AI consultation threads. | Authenticated (All roles) |
| `/api/v1/ai/assistant/conversations/{id}` | `DELETE` | Deletes a conversational history thread. | Authenticated (All roles) |
| `/api/v1/ai/analyze-interactions` | `POST` | Ad-hoc drug-drug, drug-food, and allergy interaction risk analyzer. | Authenticated (`DOCTOR`, `PHARMACY_STAFF`, `PATIENT`) |
| `/api/v1/ai/prescriptions/{id}/analyze` | `POST` | Executes AI drug safety evaluation and binds persistent report to prescription. | `DOCTOR`, `PHARMACY_STAFF`, `ADMIN` |
| `/api/v1/ai/prescriptions/{id}/report` | `GET` | Retrieves bound AI drug safety audit report. | `DOCTOR`, `PHARMACY_STAFF`, `PATIENT`, `ADMIN` |
| `/api/v1/medical-documents/{id}/analyze`| `POST`| Performs AI extraction and clinical summary generation on uploaded documents. | `PATIENT`, `DOCTOR` |

---

## 8. Administration, Dashboards & Notifications

| Endpoint | Method | Purpose | Role Authorization |
| :--- | :--- | :--- | :--- |
| `/api/v1/dashboard/patient` | `GET` | Patient home dashboard (stats, upcoming appointments, prescriptions). | `PATIENT` |
| `/api/v1/dashboard/doctor` | `GET` | Doctor clinical dashboard (today's schedule, pending approvals, alerts).| `DOCTOR` |
| `/api/v1/dashboard/admin` | `GET` | Platform-wide metrics, doctor approval queue, system user counts. | `ADMIN` |
| `/api/v1/dashboard/lab-technician`| `GET` | Diagnostic overview, urgent specimen counts, turnaround metrics. | `LAB_TECHNICIAN` |
| `/api/v1/admin/pending-doctors` | `GET` | Lists unverified doctor credential applications. | `ADMIN` |
| `/api/v1/admin/doctors/{id}/approval`| `PATCH`| Approves or rejects doctor practice credentials. | `ADMIN` |
| `/api/v1/admin/staff/provision` | `POST` | Provisions staff accounts (`LAB_TECHNICIAN`, `PHARMACY_STAFF`, `ADMIN`). | `ADMIN` |
| `/api/v1/admin/lab-tests` | `POST`/`PUT` | Manages diagnostic test catalog, reference ranges, and panic levels. | `ADMIN` |
| `/api/v1/notifications` | `GET` | Retrieves unread and historical in-app notifications. | Authenticated (All roles) |
| `/api/v1/notifications/{id}/read`| `PATCH` | Marks an in-app notification as read. | Authenticated (All roles) |
