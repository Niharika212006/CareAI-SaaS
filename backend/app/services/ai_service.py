"""AI Service coordinating clinical safety evaluation, DB persistence, and RBAC verification."""
import json
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.ai_report import AIAnalysisReport, InteractionSeverity
from app.models.prescription import Prescription
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile
from app.models.user import User, UserRole
from app.ai.interaction_checker import interaction_checker, DISCLAIMER_TEXT
from app.schemas.ai import (
    SafetyFinding,
    AIInteractionCheckRequest,
    AISafetyReportResponse,
)


class AIService:
    """Encapsulated domain service for AI prescription safety and drug interaction auditing."""

    @staticmethod
    def analyze_prescription(
        db: Session,
        prescription_id: int,
        current_user: User,
    ) -> AISafetyReportResponse:
        """
        Fetch digital prescription, extract medications and patient allergies,
        run multi-vector interaction check, persist AIAnalysisReport to DB, and return structured safety findings.
        """
        # Fetch prescription with patient and doctor details
        prescription = (
            db.query(Prescription)
            .options(
                joinedload(Prescription.patient).joinedload(PatientProfile.user),
                joinedload(Prescription.doctor).joinedload(DoctorProfile.user),
                joinedload(Prescription.items),
            )
            .filter(Prescription.id == prescription_id)
            .first()
        )

        if not prescription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prescription with ID #{prescription_id} not found.",
            )

        # RBAC Authorization Check
        if current_user.role != UserRole.ADMIN:
            is_patient_owner = prescription.patient and prescription.patient.user_id == current_user.id
            is_doctor_owner = prescription.doctor and prescription.doctor.user_id == current_user.id
            if not (is_patient_owner or is_doctor_owner):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to run AI safety analysis on this prescription.",
                )

        # Extract medications
        medication_names = [
            (item.medication_name or item.drug_name or "").strip()
            for item in (prescription.items or [])
            if (item.medication_name or item.drug_name or "").strip()
        ]

        if not medication_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prescription contains no medication items to analyze.",
            )

        # Extract patient allergies and chronic conditions safely
        allergies: List[str] = []
        conditions: List[str] = []
        if prescription.patient:
            allergies = prescription.patient.get_allergy_names()
            conditions = prescription.patient.get_condition_names()

        # Execute deterministic safety audit
        safety_response = interaction_checker.run_safety_analysis(
            medications=medication_names,
            patient_allergies=allergies,
            patient_conditions=conditions,
            prescription_id=prescription.id,
            patient_id=prescription.patient_id,
        )

        # Persist report in database
        db_report = AIAnalysisReport(
            prescription_id=prescription.id,
            patient_id=prescription.patient_id,
            analyzed_by_user_id=current_user.id,
            overall_risk_level=safety_response.overall_risk_level,
            total_findings=safety_response.total_findings,
            findings=[f.model_dump() for f in safety_response.findings],
            drug_drug_interactions=[f.model_dump() for f in safety_response.drug_drug_interactions],
            drug_food_interactions=[f.model_dump() for f in safety_response.drug_food_interactions],
            drug_allergy_interactions=[f.model_dump() for f in safety_response.drug_allergy_interactions],
            clinical_summary=safety_response.clinical_summary,
            summary=safety_response.summary,
            ai_recommendations="\n".join(safety_response.ai_recommendations),
            disclaimer=safety_response.disclaimer,
            analysis_status="COMPLETED",
        )
        db.add(db_report)
        db.commit()
        db.refresh(db_report)

        # Notify on High / Critical Risk detection
        if safety_response.overall_risk_level in [InteractionSeverity.HIGH, InteractionSeverity.CRITICAL]:
            from app.services.notification_service import notification_service
            from app.models.notification import NotificationType, NotificationPriority

            alert_priority = (
                NotificationPriority.CRITICAL
                if safety_response.overall_risk_level == InteractionSeverity.CRITICAL
                else NotificationPriority.HIGH
            )

            # Notify Patient
            if prescription.patient and prescription.patient.user_id:
                notification_service.create_notification(
                    db=db,
                    user_id=prescription.patient.user_id,
                    title="Prescription Safety Alert",
                    message=f"Potential medication safety concern detected for prescription #{prescription.id}. Please review the safety analysis and consult a qualified healthcare professional.",
                    notification_type=NotificationType.AI_SAFETY,
                    priority=alert_priority,
                    metadata_json={
                        "prescription_id": prescription.id,
                        "report_id": db_report.id,
                        "risk_level": safety_response.overall_risk_level.value,
                    },
                )

            # Notify Doctor
            if prescription.doctor and prescription.doctor.user_id:
                notification_service.create_notification(
                    db=db,
                    user_id=prescription.doctor.user_id,
                    title="Prescription Safety Alert",
                    message=f"Clinical safety check for prescription #{prescription.id} flagged potential interaction hazards ({safety_response.total_findings} finding(s)). Please review the full report.",
                    notification_type=NotificationType.AI_SAFETY,
                    priority=alert_priority,
                    metadata_json={
                        "prescription_id": prescription.id,
                        "report_id": db_report.id,
                        "risk_level": safety_response.overall_risk_level.value,
                    },
                )

        safety_response.id = db_report.id
        safety_response.analyzed_at = db_report.created_at
        return safety_response

    @staticmethod
    def get_latest_prescription_report(
        db: Session,
        prescription_id: int,
        current_user: User,
    ) -> Optional[AISafetyReportResponse]:
        """Retrieve the most recent AI safety report for a specific prescription with RBAC verification."""
        prescription = (
            db.query(Prescription)
            .options(
                joinedload(Prescription.patient),
                joinedload(Prescription.doctor),
            )
            .filter(Prescription.id == prescription_id)
            .first()
        )

        if not prescription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prescription #{prescription_id} not found.",
            )

        if current_user.role != UserRole.ADMIN:
            is_patient_owner = prescription.patient and prescription.patient.user_id == current_user.id
            is_doctor_owner = prescription.doctor and prescription.doctor.user_id == current_user.id
            if not (is_patient_owner or is_doctor_owner):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view AI safety reports for this prescription.",
                )

        report = (
            db.query(AIAnalysisReport)
            .filter(AIAnalysisReport.prescription_id == prescription_id)
            .order_by(AIAnalysisReport.created_at.desc())
            .first()
        )

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No AI safety analysis has been conducted yet for prescription #{prescription_id}.",
            )

        return AIService._serialize_report(report)

    @staticmethod
    def get_patient_reports(
        db: Session,
        patient_user: User,
        skip: int = 0,
        limit: int = 50,
    ) -> List[AISafetyReportResponse]:
        """List historical AI safety reports for the authenticated patient."""
        patient_profile = (
            db.query(PatientProfile)
            .filter(PatientProfile.user_id == patient_user.id)
            .first()
        )
        if not patient_profile:
            return []

        reports = (
            db.query(AIAnalysisReport)
            .filter(AIAnalysisReport.patient_id == patient_profile.id)
            .order_by(AIAnalysisReport.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [AIService._serialize_report(r) for r in reports]

    @staticmethod
    async def analyze_interactions(
        request: AIInteractionCheckRequest,
    ) -> AISafetyReportResponse:
        """Ad-hoc interaction checking for raw medication payload lists."""
        return interaction_checker.run_safety_analysis(
            medications=request.medications,
            patient_allergies=request.patient_allergies,
            patient_conditions=request.patient_conditions,
            prescription_id=request.prescription_id,
            patient_id=request.patient_id,
        )

    @staticmethod
    def _serialize_report(report: AIAnalysisReport) -> AISafetyReportResponse:
        """Helper to convert ORM model into AISafetyReportResponse."""
        raw_findings = report.findings or []
        findings = [SafetyFinding(**f) for f in raw_findings]
        ddi = [SafetyFinding(**f) for f in (report.drug_drug_interactions or [])]
        dfi = [SafetyFinding(**f) for f in (report.drug_food_interactions or [])]
        dai = [SafetyFinding(**f) for f in (report.drug_allergy_interactions or [])]

        recs = []
        if report.ai_recommendations:
            recs = [r.strip() for r in report.ai_recommendations.split("\n") if r.strip()]

        return AISafetyReportResponse(
            id=report.id,
            prescription_id=report.prescription_id,
            patient_id=report.patient_id,
            overall_risk_level=report.overall_risk_level,
            total_findings=report.total_findings or len(findings),
            findings=findings,
            drug_drug_interactions=ddi,
            drug_food_interactions=dfi,
            drug_allergy_interactions=dai,
            clinical_summary=report.clinical_summary,
            summary=report.summary or report.clinical_summary,
            ai_recommendations=recs,
            disclaimer=report.disclaimer or DISCLAIMER_TEXT,
            analyzed_at=report.created_at,
        )


ai_service = AIService()
