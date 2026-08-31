# CareAI Healthcare SaaS — Limitations & Future Scope Analysis

An honest and objective assessment of the current project state, distinguishing **Current Architectural & Functional Limitations** from **Future Production Enhancements**.

---

## 1. Current System Limitations

| Area | Current Implementation | Realistic Limitation |
| :--- | :--- | :--- |
| **Notification Transport** | Polling / In-app database table (`notifications`) | Real-time WebSockets, push notifications (FCM/APNs), and SMS/Email dispatch gateways (Twilio/SendGrid) are not yet integrated. |
| **File Storage Layer** | Local filesystem storage service (`app/core/storage.py`) | Suitable for local evaluation; enterprise production requires direct S3/GCS multipart signed uploads with antivirus/malware scanning. |
| **Tele-Consultation** | Scheduled appointment bookings with clinical complaint tracking | No native in-browser WebRTC audio/video tele-health stream or chat room. |
| **Pharmacy Inventory** | Order progression & dispensation status tracking | Does not maintain a live stock inventory table (stock counts do not decrement on dispense). |
| **Multi-Tenancy** | Single database with logical row-level tenant separation | Does not implement schema-per-tenant or database-per-hospital isolation for enterprise hospital networks. |
| **Regulatory Certification** | HIPAA-aligned architectural design and PHI privacy barriers | Has not undergone formal third-party regulatory HIPAA/GDPR compliance auditing or FDA/MDR Class II SaMD certification. |
| **AI Fallback Knowledge Base** | Mock fallback rules + HTTP 503 error handling | Offline fallback relies on structured templates rather than an embedded local offline clinical LLM (e.g. BioMistral / Llama-3-Med via ONNX). |

---

## 2. Future Enhancements & Production Roadmap

```mermaid
timeline
    title CareAI Production Roadmap
    section Phase 1: Real-Time & Communications
      WebSockets live updates : Push notifications : WebRTC Video Tele-health
    section Phase 2: Interoperability & Compliance
      HL7 / FHIR standard integration : HIPAA / GDPR 3rd-party audit : Audit log export
    section Phase 3: Mobile & Inventory
      React Native Mobile App : Real-time pharmacy inventory sync : Barcode/QR scanning
    section Phase 4: Advanced AI
      Offline edge clinical LLM : Multimodal DICOM X-Ray viewer : Continuous learning
```

### 2.1 Real-Time Infrastructure (WebSockets & WebRTC)
- **Live Event Streaming:** Integrate FastAPI WebSocket endpoints for instant notification delivery and live chat updates without HTTP polling.
- **In-Browser Video Calls:** Embed WebRTC peer-to-peer encrypted video rooms for virtual doctor-patient consultations.

### 2.2 Healthcare Interoperability Standards (FHIR / HL7)
- **Fast Healthcare Interoperability Resources (FHIR):** Implement standard FHIR JSON endpoints (`/Patient`, `/Encounter`, `/MedicationRequest`, `/DiagnosticReport`) for seamless interoperability with legacy Hospital Information Systems (Epic, Cerner).
- **DICOM Imaging Support:** Support viewing and analyzing DICOM radiographic images (CT/MRI/X-Ray) within the diagnostic workspace.

### 2.3 Mobile Applications & Biometrics
- **Cross-Platform Mobile Client:** Build React Native mobile applications for iOS and Android with push notifications.
- **Biometric Security:** FaceID / TouchID biometric login for rapid mobile patient authentication.

### 2.4 Enterprise Hospital Multi-Tenancy & Inventory
- **Schema-Based Multi-Tenancy:** Partition hospital database schemas dynamically to guarantee physical data isolation between healthcare providers.
- **Dispensary Stock & Barcode Scanning:** Automatic decrementing of drug inventory upon dispensing, with barcode/QR verification to prevent medication errors.
