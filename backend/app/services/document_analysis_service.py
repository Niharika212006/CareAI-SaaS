"""Domain service managing responsible AI medical document analysis and RBAC verification."""
import logging
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.document_analysis import MedicalDocumentAnalysis, AnalysisStatus
from app.models.medical_document import MedicalDocument
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile
from app.models.appointment import Appointment
from app.models.user import User, UserRole
from app.core.storage import storage_service
from app.ai.document_extractor import document_extractor
from app.ai.document_analyzer import document_analyzer
from app.ai.client import AIProviderUnavailableError, AIInvalidResponseError
from app.services.notification_service import notification_service
from app.models.notification import NotificationType, NotificationPriority

logger = logging.getLogger("healthcare.ai.service")


class DocumentAnalysisService:
    """Orchestrates document retrieval, text extraction, AI clinical analysis, and RBAC authorization."""

    @staticmethod
    def analyze_document(
        db: Session,
        document_id: int,
        current_user: User,
        force_heuristic_fallback: bool = False,
    ) -> MedicalDocumentAnalysis:
        """
        Extract readable text from an owned medical document and run responsible AI clinical insight analysis.
        Strictly restricted to the owning patient.
        """
        if current_user.role != UserRole.PATIENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only registered patient document owners can request AI analysis.",
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

        doc = db.query(MedicalDocument).filter(MedicalDocument.id == document_id).first()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medical document #{document_id} not found.",
            )

        if doc.patient_id != patient_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to analyze this medical document.",
            )

        # Reuse existing completed analysis if available to avoid duplicate redundant processing
        existing = (
            db.query(MedicalDocumentAnalysis)
            .filter(
                MedicalDocumentAnalysis.document_id == doc.id,
                MedicalDocumentAnalysis.analysis_status == AnalysisStatus.COMPLETED,
            )
            .order_by(MedicalDocumentAnalysis.created_at.desc())
            .first()
        )
        if existing:
            return existing

        # Locate physical storage file
        file_path = storage_service.get_file_path(doc.storage_key)
        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Physical document file was not found in storage.",
            )

        # Extract text safely
        extracted_text, extract_error = document_extractor.extract_text(file_path, doc.mime_type)
        if extract_error or not extracted_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=extract_error or "Text could not be extracted from this document.",
            )

        # Run AI Clinical Insight Engine via real LLM pipeline
        try:
            analysis_result = document_analyzer.analyze_extracted_text(
                extracted_text=extracted_text,
                document_title=doc.title,
                document_type_hint=doc.document_type.value,
                force_heuristic_fallback=force_heuristic_fallback,
            )
        except AIProviderUnavailableError as prov_err:
            logger.warning(f"AI Provider unavailable during analysis: {prov_err}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI analysis service is temporarily unavailable. Please try again later.",
            )
        except AIInvalidResponseError as inv_err:
            logger.error(f"AI response format error: {inv_err}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI model returned an unparseable response. Please retry.",
            )
        except HTTPException:
            raise
        except Exception as err:
            logger.error(f"Unexpected AI analysis execution error: {err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during document processing.",
            )

        # Persist structured analysis
        db_analysis = MedicalDocumentAnalysis(
            document_id=doc.id,
            requested_by_user_id=current_user.id,
            extracted_text=extracted_text[:15000],
            summary=analysis_result.summary,
            document_category=analysis_result.document_category,
            key_findings=analysis_result.key_findings,
            detected_medications=[m.model_dump() for m in analysis_result.detected_medications],
            detected_test_values=[t.model_dump() for t in analysis_result.detected_test_values],
            potential_concerns=[c.model_dump() for c in analysis_result.potential_concerns],
            patient_friendly_explanation=analysis_result.patient_friendly_explanation,
            recommended_next_step=analysis_result.recommended_next_step,
            disclaimer=analysis_result.disclaimer,
            analysis_status=AnalysisStatus.COMPLETED,
            ai_model_name=analysis_result.ai_model_name,
        )
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)

        # Discreet in-app notification to patient
        notification_service.create_notification(
            db=db,
            user_id=current_user.id,
            title="Medical Document Analysis Ready",
            message=f"Your AI clinical analysis for '{doc.title}' is ready to review.",
            notification_type=NotificationType.AI_SAFETY,
            priority=NotificationPriority.NORMAL,
            metadata_json={
                "document_id": doc.id,
                "analysis_id": db_analysis.id,
            },
        )

        return db_analysis

    @staticmethod
    def get_document_analysis(
        db: Session,
        document_id: int,
        current_user: User,
    ) -> MedicalDocumentAnalysis:
        """Retrieve the latest completed analysis for a document with strict RBAC authorization."""
        doc = db.query(MedicalDocument).filter(MedicalDocument.id == document_id).first()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medical document #{document_id} not found.",
            )

        # RBAC Check: Patient Owner or Authorized Doctor
        if current_user.role == UserRole.PATIENT:
            patient_profile = (
                db.query(PatientProfile)
                .filter(PatientProfile.user_id == current_user.id)
                .first()
            )
            if not patient_profile or doc.patient_id != patient_profile.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to view analysis for this document.",
                )
        elif current_user.role == UserRole.DOCTOR:
            doctor_profile = (
                db.query(DoctorProfile)
                .filter(DoctorProfile.user_id == current_user.id)
                .first()
            )
            if not doctor_profile:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only registered doctors can view patient document analyses.",
                )
            has_appt = (
                db.query(Appointment)
                .filter(
                    Appointment.doctor_id == doctor_profile.id,
                    Appointment.patient_id == doc.patient_id,
                )
                .first()
            )
            if not has_appt:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have clinical authorization to view this patient's analysis.",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admins and unauthorized users cannot access patient medical document analyses.",
            )

        analysis = (
            db.query(MedicalDocumentAnalysis)
            .filter(
                MedicalDocumentAnalysis.document_id == doc.id,
                MedicalDocumentAnalysis.analysis_status == AnalysisStatus.COMPLETED,
            )
            .order_by(MedicalDocumentAnalysis.created_at.desc())
            .first()
        )

        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No AI analysis has been generated for this document yet.",
            )

        return analysis

    @staticmethod
    def get_analysis_by_id(
        db: Session,
        analysis_id: int,
        current_user: User,
    ) -> MedicalDocumentAnalysis:
        """Retrieve a specific analysis by its primary ID after verifying parent document authorization."""
        analysis = (
            db.query(MedicalDocumentAnalysis)
            .filter(MedicalDocumentAnalysis.id == analysis_id)
            .first()
        )
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document analysis #{analysis_id} not found.",
            )

        # Delegate authorization check to parent document
        DocumentAnalysisService.get_document_analysis(
            db=db,
            document_id=analysis.document_id,
            current_user=current_user,
        )
        return analysis


document_analysis_service = DocumentAnalysisService()
