# CareAI Healthcare SaaS — End-to-End System Workflows

---

## 1. Patient Journey Workflow

The patient journey covers self-registration, finding certified specialists, booking appointments, attending consultations, accessing digital prescriptions, reviewing released diagnostic lab reports, picking up medications from the pharmacy, and interacting with the CareAI Assistant.

```mermaid
sequenceDiagram
    autonumber
    actor Patient
    participant WebApp as Patient Portal (React)
    participant API as FastAPI Backend
    participant DB as Relational DB
    participant AI as CareAI Engine
    
    Patient->>WebApp: Self-registers with email, password, phone (+91)
    WebApp->>API: POST /api/v1/auth/register (Role: PATIENT)
    API->>DB: Save Patient user & Profile
    API-->>WebApp: 201 Created & JWT Token
    
    Patient->>WebApp: Searches Doctor Directory (Specialty / Search query)
    WebApp->>API: GET /api/v1/doctors/directory
    API->>DB: Query approved doctors with active schedules
    API-->>WebApp: List of verified doctors & slots
    
    Patient->>WebApp: Selects slot & Books Appointment
    WebApp->>API: POST /api/v1/appointments
    API->>DB: Insert Appointment (Status: PENDING)
    API->>DB: Trigger Notification to Doctor
    API-->>WebApp: Appointment Confirmed
    
    Note over Patient,WebApp: Consultation & Post-Consultation Phase
    
    Patient->>WebApp: Views Issued Prescription & AI Safety Summary
    WebApp->>API: GET /api/v1/prescriptions/my
    API-->>WebApp: Returns active medications & dosage schedule
    
    Patient->>WebApp: Checks Diagnostic Lab Reports
    WebApp->>API: GET /api/v1/lab/patient/my-reports
    API-->>WebApp: Returns only VERIFIED & RELEASED lab results
    
    Patient->>WebApp: Queries CareAI Health Assistant (e.g., dosage instructions)
    WebApp->>API: POST /api/v1/ai/assistant/chat
    API->>AI: Role-tailored health query evaluation
    AI-->>API: Evidence-based explanation with disclaimer
    API-->>WebApp: Structured assistant reply
```

---

## 2. Doctor Journey Workflow

The doctor journey encompasses credential registration, administrative vetting, dynamic consultation management, digital prescription drafting with automated drug-drug interaction screening, and STAT/routine lab ordering.

```mermaid
sequenceDiagram
    autonumber
    actor Doctor
    participant WebApp as Doctor Portal (React)
    participant API as FastAPI Backend
    participant Admin as System Administrator
    participant AI as AI Drug Safety Engine
    participant DB as Relational DB
    
    Doctor->>WebApp: Registers as Doctor (License, Specialization, Hospital)
    WebApp->>API: POST /api/v1/auth/register (Role: DOCTOR)
    API->>DB: Insert DoctorProfile (approval_status: PENDING)
    
    Note over Doctor,Admin: Admin Approval Gate
    Admin->>API: PATCH /api/v1/admin/doctors/{id}/approval (APPROVED)
    API->>DB: Update DoctorProfile to APPROVED
    
    Doctor->>WebApp: Logs into Doctor Dashboard & Sets Available Slots
    WebApp->>API: POST /api/v1/doctor/availability
    API->>DB: Save Weekly Consultation Schedule
    
    Doctor->>WebApp: Reviews Incoming Consultation Queue
    WebApp->>API: GET /api/v1/appointments/doctor/my
    Doctor->>WebApp: Confirms & Completes Consultation
    WebApp->>API: PATCH /api/v1/appointments/{id}/confirm
    WebApp->>API: PATCH /api/v1/appointments/{id}/complete
    
    Doctor->>WebApp: Drafts Digital Prescription with Multiple Medications
    WebApp->>API: POST /api/v1/ai/analyze-interactions
    API->>AI: Analyze Drug-Drug, Drug-Food, Allergy Interactions
    AI-->>WebApp: Returns Risk Level (HIGH / MODERATE / LOW) & Advisories
    
    Doctor->>WebApp: Issues Final Digital Prescription
    WebApp->>API: POST /api/v1/prescriptions
    API->>DB: Save Prescription & Items (Status: PRESCRIBED)
    
    Doctor->>WebApp: Orders Diagnostic Lab Panel (STAT / Routine)
    WebApp->>API: POST /api/v1/lab/orders
    API->>DB: Create LabOrder & Requisition Items (Status: SAMPLE_PENDING)
```

---

## 3. Laboratory Diagnostic Workflow

The diagnostic lab workflow enforces a rigorous clinical custody chain: order reception, biological specimen collection with rejection criteria for compromised draws (hemolyzed/clotted), processing, result parameter entry with automated panic threshold alerts, technologist verification, and final report release to the patient portal.

```mermaid
stateDiagram-v2
    [*] --> SAMPLE_PENDING: Doctor Creates Diagnostic Order (STAT / URGENT / ROUTINE)
    
    SAMPLE_PENDING --> SAMPLE_PENDING: Specimen Rejected (HEMOLYZED / CLOTTED)
    SAMPLE_PENDING --> SAMPLE_COLLECTED: Specimen Collected (ACCEPTABLE condition)
    
    SAMPLE_COLLECTED --> IN_PROGRESS: Technologist Starts Analytical Run
    
    IN_PROGRESS --> RESULTS_ENTERED: Results Entered & Critical Flags Evaluated (CRITICAL / ABNORMAL / NORMAL)
    
    RESULTS_ENTERED --> VERIFIED: Technologist Audits & Verifies Findings
    
    VERIFIED --> RELEASED: Final Report Released to Patient & Doctor
    
    RELEASED --> [*]
```

---

## 4. Pharmacy Dispensary Workflow

The dispensary lifecycle guarantees that pharmacy personnel can process orders through distinct stages while preventing any modification of doctor prescriptions.

```mermaid
stateDiagram-v2
    [*] --> PRESCRIBED: Doctor Issues Digital Prescription
    
    PRESCRIBED --> UNDER_REVIEW: Pharmacist Opens & Audits Medication Queue
    
    UNDER_REVIEW --> READY: Pharmacist Packages Medication & Marks Ready for Pickup
    note right of READY
        Automated in-app notification 
        dispatched to Patient: "Ready for Pickup"
    end note
    
    READY --> DISPENSED: Patient Receives Medication; Pharmacist Confirms Dispensation
    note right of DISPENSED
        Dispensation timestamp and pharmacist ID recorded.
        Notifications sent to Patient and Prescribing Doctor.
    end note
    
    DISPENSED --> [*]
```

---

## 5. System Administrator Workflow

Administrators manage the health, governance, and user safety of the CareAI ecosystem without violating patient medical privacy.

```mermaid
graph TD
    Admin[Platform Administrator] --> AdminDashboard[Admin Management Console]
    
    subgraph Administrative Operations
        AdminDashboard --> DoctorVetting[Doctor Credential Audit & Approval]
        AdminDashboard --> StaffProvisioning[Internal Staff Account Provisioning: Lab Tech / Pharmacy Staff]
        AdminDashboard --> LabCatalog[Diagnostic Test Catalog & Standard Reference Ranges]
        AdminDashboard --> Metrics[Platform Health, User Totals & Appointment Volumes]
    end

    subgraph Security Boundary
        AdminDashboard -.->|HTTP 403 Forbidden| PHI[Protected Health Information / Patient Medical Documents]
    end
```

---

## 6. AI Intelligence & Fault-Tolerant Processing Workflow

The AI subsystem processes conversational prompts, multi-drug interactions, and medical document OCR with deterministic rule filters, system prompt guardrails, and graceful service degradation.

```mermaid
sequenceDiagram
    autonumber
    actor User as Any Platform Role
    participant API as FastAPI Backend
    participant Triage as Emergency Triage Filter
    participant PromptEng as Role-Aware Prompt Engine
    participant Gemini as Google Gemini 1.5 Flash API
    
    User->>API: POST /api/v1/ai/assistant/chat (Message payload)
    API->>Triage: Deterministic Emergency Pattern Scan (Chest Pain, Anaphylaxis)
    
    alt Acute Emergency Detected
        Triage-->>API: Flag emergency_symptom_detected = True
        API-->>User: Immediate Emergency Alert + Hospital Helpline Prompt
    else Standard Health / Clinical Query
        API->>PromptEng: Attach Role Context & PHI Safety Constraints
        PromptEng->>Gemini: Stream/Call GenerateContent
        
        alt Gemini API Online
            Gemini-->>API: Formatted Markdown Explanation
            API->>API: Strip internal metadata / Sanitize response
            API-->>User: 200 OK with Clinical Explanation
        else Gemini Offline / Network Timeout / Key Exhausted
            Gemini--xAPI: Connection Reset / 500 / Rate Limit Error
            API->>API: Catch AIProviderUnavailableError
            API-->>User: 503 Service Unavailable ("CareAI Assistant temporarily offline. Clinical services remain operational.")
        end
    end
```
