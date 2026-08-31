"""Strict Live Verification Script for Google Gemini AI Integration in CareAI SaaS."""
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import SessionLocal
from app.models.user import User, UserRole
from app.models.patient import PatientProfile
from app.models.medical_document import MedicalDocument, DocumentType
from app.services.medical_document_service import medical_document_service
from app.ai.client import ai_client, AIProviderUnavailableError
from app.core.security import create_access_token


def create_mock_pdf_with_text(text: str) -> bytes:
    """Generate minimal valid PDF bytes with extractable text."""
    clean_text = text.replace("(", "").replace(")", "")
    stream_data = f"BT\n/F1 12 Tf\n50 250 Td\n({clean_text}) Tj\nET\n".encode("latin-1")
    length = len(stream_data)
    pdf_template = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 400 400] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length " + str(length).encode("ascii") + b" >>\nstream\n"
        + stream_data +
        b"endstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n500\n%%EOF\n"
    )
    return pdf_template


def run_gemini_live_audit():
    print("=" * 80)
    print("CAREAI HEALTHCARE SAAS — LIVE GEMINI AI VERIFICATION AUDIT")
    print("=" * 80)

    client = TestClient(app)
    db: Session = SessionLocal()

    # 1. Inspect API Key Presence (Never print key)
    is_key_present = ai_client.is_configured()
    print(f"1. API Key Configured: {'YES' if is_key_present else 'NO (Empty in environment / .env)'}")

    # 2. Check Provider & Model Configuration
    provider_name = ai_client.provider
    configured_model = ai_client.model_name
    print(f"2. Configured AI Provider: {provider_name}")
    print(f"3. Configured AI Model: {configured_model}")

    available_models = []
    direct_gemini_passed = False
    ai_assistant_live_passed = False
    document_analysis_passed = False
    failure_reason = None

    if is_key_present:
        # Check actual available models via SDK
        try:
            from google import genai
            g_client = genai.Client(api_key=ai_client._get_gemini_key())
            print("\n[+] Querying live Gemini models via official SDK...")
            models_pager = g_client.models.list()
            for m in models_pager:
                m_name = getattr(m, "name", str(m))
                if "gemini" in m_name.lower():
                    available_models.append(m_name)
            print(f"   Found {len(available_models)} available Gemini models.")
            if available_models:
                print(f"   Sample available models: {available_models[:5]}")
        except Exception as e:
            print(f"   [WARN] Could not fetch model list: {e}")

        # Send minimal real request directly through AIClient
        print("\n[+] Testing Direct Real Gemini Completion...")
        try:
            raw_response = ai_client.generate_completion(
                system_prompt="You are a clinical test verification engine. Answer briefly.",
                user_prompt="Say 'CareAI Live Verification Succeeded'.",
                response_mime_type="text/plain",
            )
            print(f"   [SUCCESS] Live Gemini response received: {raw_response[:100]}...")
            direct_gemini_passed = True
        except Exception as e:
            print(f"   [FAIL] Direct Gemini API call failed: {e}")
            failure_reason = str(e)
    else:
        print("\n[!] No active API key detected in environment. Verifying controlled fallback...")

    # 3. Test Authenticated AI Assistant Route
    print("\n[+] Testing Authenticated AI Assistant API Route (/api/v1/ai-assistant/chat)...")
    patient = db.query(User).filter(User.role == UserRole.PATIENT).first()
    if patient:
        token = create_access_token(subject=str(patient.id), role=patient.role.value)
        headers = {"Authorization": f"Bearer {token}"}
        chat_res = client.post("/api/v1/ai-assistant/chat", json={
            "message": "Hello CareAI, what are standard normal resting heart rate ranges?",
        }, headers=headers)

        if chat_res.status_code == 200:
            resp_json = chat_res.json()
            print(f"   [PASS] AI Assistant HTTP 200 OK")
            print(f"   Model used: {resp_json.get('model_name')}")
            print(f"   Response snippet: {resp_json.get('assistant_response', '')[:120]}...")
            ai_assistant_live_passed = True
        elif chat_res.status_code == 503:
            print(f"   [CONTROLLED FALLBACK] AI Assistant HTTP 503 Service Unavailable")
            print(f"   Detail: {chat_res.json().get('detail')}")
            if not is_key_present:
                print("   -> Correct behavior when GEMINI_API_KEY is not configured.")
        else:
            print(f"   [FAIL] AI Assistant returned unexpected HTTP {chat_res.status_code}: {chat_res.text}")
            failure_reason = chat_res.text

    # 4. Test Medical Document AI Analysis Route
    print("\n[+] Testing Medical Document AI Analysis Flow (/api/v1/medical-documents/{id}/analyses)...")
    if patient:
        doc = medical_document_service.upload_document(
            db=db,
            patient_user=patient,
            file_content=create_mock_pdf_with_text("Fasting Glucose: 135 mg/dL. HbA1c: 7.2%. Daily Metformin 500mg."),
            original_filename="sample_panel_test.pdf",
            title="Sample Panel Test Report",
            document_type=DocumentType.LAB_REPORT,
        )

        token = create_access_token(subject=str(patient.id), role=patient.role.value)
        headers = {"Authorization": f"Bearer {token}"}
        analysis_res = client.post(f"/api/v1/medical-documents/{doc.id}/analyze", headers=headers)

        if analysis_res.status_code == 200:
            data = analysis_res.json()
            print(f"   [PASS] Medical Document Analysis HTTP 200 OK")
            print(f"   Category: {data.get('document_category')}")
            print(f"   Summary: {data.get('summary', '')[:120]}...")
            document_analysis_passed = True
        elif analysis_res.status_code == 503:
            print(f"   [CONTROLLED FALLBACK] Medical Document Analysis HTTP 503 Service Unavailable")
            print(f"   Detail: {analysis_res.json().get('detail')}")
            if not is_key_present:
                print("   -> Correct behavior when GEMINI_API_KEY is not configured.")
        else:
            print(f"   [FAIL] Document Analysis returned unexpected HTTP {analysis_res.status_code}: {analysis_res.text}")
            failure_reason = analysis_res.text

    db.close()

    print("\n" + "=" * 80)
    print("FINAL GEMINI AI RUNTIME VERIFICATION MATRIX:")
    print("=" * 80)
    print(f"• API Key Configured:              {'YES' if is_key_present else 'NO'}")
    print(f"• Provider Reachable:              {'YES' if is_key_present and direct_gemini_passed else ('NO (Key missing)' if not is_key_present else 'FAIL')}")
    print(f"• Actual Model Used:               {configured_model}")
    print(f"• Direct Real Gemini Request:      {'PASS' if direct_gemini_passed else ('SKIPPED (No Key)' if not is_key_present else 'FAIL')}")
    print(f"• AI Assistant Live Endpoint:      {'PASS (Live Gemini)' if ai_assistant_live_passed else ('CONTROLLED 503 (No Key)' if not is_key_present else 'FAIL')}")
    print(f"• Medical Document AI Call:        {'PASS (Live Gemini)' if document_analysis_passed else ('CONTROLLED 503 (No Key)' if not is_key_present else 'FAIL')}")
    if failure_reason:
        print(f"• Failure Details:                 {failure_reason}")
    print("=" * 80)


if __name__ == "__main__":
    run_gemini_live_audit()
