from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query, status, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User, UserRole
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.models.medical_document import MedicalDocument, DocumentType
from app.models.prescription import Prescription, PrescriptionItem, PrescriptionStatus
from app.core.storage import storage_service
from app.ai.document_extractor import document_extractor
from app.ai.client import ai_client
from app.schemas.ai_assistant import (
    AIChatRequest,
    AIChatResponse,
    AIConversationRead,
    AIConversationSummary,
    AIConfigRead,
    AIConfigUpdate,
)
from app.schemas.prescription_upload import (
    PrescriptionMedicationItem,
    PrescriptionExtractionDraft,
    PrescriptionConfirmRequest,
    PrescriptionConfirmResponse,
)
from app.services.ai_assistant_service import ai_assistant_service

router = APIRouter(prefix="/ai-assistant", tags=["CareAI Assistant"])


@router.post(
    "/chat",
    response_model=AIChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Interact with the role-aware CareAI Assistant",
)
def chat_with_assistant(
    request: AIChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AIChatResponse:
    """
    Execute a conversational interaction turn with the CareAI Assistant.
    
    Security & RBAC Enforcement:
    - User identity and role are derived strictly from the authenticated JWT token.
    - System prompts and clinical safety guardrails adapt dynamically to the user's role:
      - PATIENT: Health education, medication/lab explanation, emergency symptom triage.
      - DOCTOR: Clinical copilot, authorized patient data and document synthesis.
      - LAB_TECHNICIAN: Laboratory testing protocols, diagnostic terminology, workflow guidance.
      - PHARMACY_STAFF: Drug interaction analysis, medication safety, formulary guidance.
      - ADMIN: Operational intelligence and governance with strict privacy barrier.
    """
    return ai_assistant_service.send_chat_message(
        db=db,
        user=current_user,
        request=request,
    )


@router.get(
    "/conversations",
    response_model=List[AIConversationSummary],
    summary="List all assistant conversation threads for authenticated user",
)
def list_my_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[AIConversationSummary]:
    """Retrieve historical assistant conversation threads belonging to the authenticated user."""
    return ai_assistant_service.list_conversations(
        db=db,
        user=current_user,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=AIConversationRead,
    summary="Retrieve full conversation thread and message history",
)
def get_conversation_history(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AIConversationRead:
    """Retrieve complete message history for an authorized conversation thread."""
    return ai_assistant_service.get_conversation(
        db=db,
        user=current_user,
        conversation_id=conversation_id,
    )


@router.delete(
    "/conversations/{conversation_id}",
    response_model=Dict[str, Any],
    summary="Delete an assistant conversation thread",
)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Permanently delete an assistant conversation thread and its associated messages."""
    ai_assistant_service.delete_conversation(
        db=db,
        user=current_user,
        conversation_id=conversation_id,
    )
    return {
        "status": "success",
        "message": f"Conversation {conversation_id} deleted successfully.",
        "id": conversation_id,
    }


@router.get(
    "/config",
    response_model=AIConfigRead,
    summary="Retrieve current AI provider and engine status",
)
def get_ai_config(
    current_user: User = Depends(get_current_active_user),
) -> AIConfigRead:
    """Retrieve operational status and active engine (Gemini vs Clinical Knowledge Engine)."""
    status_data = ai_client.get_status()
    return AIConfigRead(**status_data)


@router.post(
    "/config",
    response_model=Dict[str, Any],
    summary="Configure or update Gemini API key at runtime",
)
def update_ai_config(
    payload: AIConfigUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Set or clear Gemini API key dynamically.
    Enables live Google Gemini foundation model processing.
    """
    key = payload.api_key.strip()
    ai_client.set_gemini_key(key)

    # Try updating backend/.env file so key persists across server restarts
    try:
        from pathlib import Path
        import re
        env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
        if env_path.exists():
            content = env_path.read_text(encoding="utf-8")
            if "GEMINI_API_KEY=" in content:
                new_content = re.sub(r'GEMINI_API_KEY="[^"]*"', f'GEMINI_API_KEY="{key}"', content)
                if new_content == content:
                    new_content = re.sub(r"GEMINI_API_KEY=.*", f'GEMINI_API_KEY="{key}"', content)
                env_path.write_text(new_content, encoding="utf-8")
    except Exception:
        pass

    status_data = ai_client.get_status()
    return {
        "status": "success",
        "message": "Gemini API key updated successfully." if key else "Reset to CareAI Clinical Intelligence Engine.",
        "config": status_data,
    }


@router.post(
    "/patient/upload-prescription",
    response_model=PrescriptionExtractionDraft,
    summary="Upload prescription or medical document for AI multimodal extraction and review",
)
async def upload_prescription_draft(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PrescriptionExtractionDraft:
    """
    Accepts PDF, JPG, JPEG, or PNG prescription documents.
    Extracts doctor details, diagnosis, and medications using multimodal AI.
    Returns structured draft for patient verification before saving to database.
    """
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can upload prescriptions for personal medical records.",
        )

    patient_profile = (
        db.query(PatientProfile)
        .filter(PatientProfile.user_id == current_user.id)
        .first()
    )
    if not patient_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found. Please complete your profile first.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file cannot be empty.",
        )

    # Validate and save to storage
    storage_key, sanitized_filename, file_size, mime_type = storage_service.save_file(
        file_content=content,
        original_filename=file.filename or "prescription.pdf",
        declared_mime_type=file.content_type,
    )
    file_path = storage_service.get_file_path(storage_key)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store uploaded prescription on server storage.",
        )

    # Perform multimodal extraction
    extracted = document_extractor.extract_prescription_details(file_path, mime_type)

    # Convert medications to Pydantic items
    med_items = []
    for med in extracted.get("medications", []):
        med_items.append(
            PrescriptionMedicationItem(
                medication_name=med.get("medication_name", "Medication"),
                dosage=med.get("dosage", "As directed"),
                frequency=med.get("frequency", "Once daily"),
                duration=med.get("duration", "30 days"),
                route_of_administration=med.get("route_of_administration", "Oral"),
                instructions=med.get("instructions"),
            )
        )

    return PrescriptionExtractionDraft(
        temp_file_token=storage_key,
        file_name=sanitized_filename,
        file_size=file_size,
        mime_type=mime_type,
        doctor_name=extracted.get("doctor_name"),
        patient_name=current_user.full_name or extracted.get("patient_name"),
        date=extracted.get("date"),
        diagnosis=extracted.get("diagnosis", "Prescription Review"),
        clinical_notes=extracted.get("clinical_notes"),
        medications=med_items,
        confidence_score=extracted.get("confidence_score", 0.95),
        raw_text_summary=extracted.get("raw_text_summary"),
    )


@router.post(
    "/patient/confirm-prescription",
    response_model=PrescriptionConfirmResponse,
    summary="Confirm and persist extracted prescription into patient medical records",
)
def confirm_prescription(
    request: PrescriptionConfirmRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PrescriptionConfirmResponse:
    """
    Commits patient-verified prescription and attached medical document into the database.
    Creates MedicalDocument and Prescription + PrescriptionItem entities.
    Returns medication schedule advice and drug interaction tips.
    """
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can confirm and save prescriptions.",
        )

    patient_profile = (
        db.query(PatientProfile)
        .filter(PatientProfile.user_id == current_user.id)
        .first()
    )
    if not patient_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found.",
        )

    file_path = storage_service.get_file_path(request.temp_file_token)
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded prescription file token is invalid or expired. Please upload again.",
        )

    file_size = file_path.stat().st_size
    import mimetypes
    guessed_mime, _ = mimetypes.guess_type(request.file_name)
    mime_type = guessed_mime or "application/pdf"

    # 1. Create MedicalDocument record
    medical_doc = MedicalDocument(
        patient_id=patient_profile.id,
        uploaded_by_user_id=current_user.id,
        title=f"Prescription - {request.diagnosis}",
        document_type=DocumentType.PRESCRIPTION,
        description=f"Prescribed by {request.doctor_name or 'Attending Physician'}. Verified by patient via CareAI Assistant.",
        file_name=request.file_name,
        storage_key=request.temp_file_token,
        file_size=file_size,
        mime_type=mime_type,
    )
    db.add(medical_doc)
    db.flush()

    # 2. Link or create Prescription entity
    # Find an approved doctor or fallback doctor
    doctor_profile = (
        db.query(DoctorProfile)
        .filter(DoctorProfile.approval_status == DoctorApprovalStatus.APPROVED)
        .first()
    ) or db.query(DoctorProfile).first()

    prescription_id = None
    if doctor_profile:
        presc = Prescription(
            patient_id=patient_profile.id,
            doctor_id=doctor_profile.id,
            diagnosis=request.diagnosis,
            clinical_notes=request.clinical_notes or f"External prescription issued by {request.doctor_name or 'Clinician'}",
            notes=f"Prescription verified and uploaded by patient {current_user.full_name}",
            status=PrescriptionStatus.PRESCRIBED,
        )
        db.add(presc)
        db.flush()
        prescription_id = presc.id

        # Add items
        for item in request.medications:
            p_item = PrescriptionItem(
                prescription_id=presc.id,
                medication_name=item.medication_name,
                drug_name=item.medication_name,
                dosage=item.dosage,
                frequency=item.frequency,
                duration=item.duration,
                route_of_administration=item.route_of_administration or "Oral",
                instructions=item.instructions,
            )
            db.add(p_item)

    db.commit()

    # 3. Create medication schedule and interaction tips
    schedule = []
    for item in request.medications:
        schedule.append(f"{item.medication_name} ({item.dosage}): {item.frequency} - {item.instructions or 'Take as prescribed.'}")

    interaction_warnings = [
        "Take medications with a full glass of water unless otherwise directed by your physician.",
        "Do not stop or adjust prescribed dosages without consulting your prescribing healthcare provider.",
        "Report any unusual dizziness, rash, or gastrointestinal discomfort to your physician immediately.",
    ]

    ai_explanation = (
        f"Your prescription for '{request.diagnosis}' with {len(request.medications)} medication(s) "
        f"has been securely added to your CareAI Health Records. The digital file is archived under Medical Documents."
    )

    from app.services.notification_service import notification_service
    from app.models.notification import NotificationType, NotificationPriority
    notification_service.create_notification(
        db=db,
        user_id=current_user.id,
        title="Prescription Saved",
        message=f"Prescription for {request.diagnosis} was saved to your medical records.",
        notification_type=NotificationType.PRESCRIPTION,
        priority=NotificationPriority.NORMAL,
        metadata_json={"document_id": medical_doc.id, "prescription_id": prescription_id},
    )

    return PrescriptionConfirmResponse(
        document_id=medical_doc.id,
        prescription_id=prescription_id,
        message="Prescription confirmed and securely saved to your medical records.",
        ai_explanation=ai_explanation,
        medication_schedule=schedule,
        interaction_warnings=interaction_warnings,
        disclaimer=(
            "CareAI provides schedule management and educational information only. "
            "Always follow your doctor's specific prescription guidance."
        ),
    )


