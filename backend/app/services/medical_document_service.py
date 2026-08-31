"""Domain service managing medical document uploads, privacy RBAC, and storage coordination."""
from pathlib import Path
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.medical_document import MedicalDocument, DocumentType
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile
from app.models.appointment import Appointment
from app.models.user import User, UserRole
from app.schemas.medical_document import MedicalDocumentUpdate
from app.core.storage import storage_service
from app.services.notification_service import notification_service
from app.models.notification import NotificationType, NotificationPriority


class MedicalDocumentService:
    """Encapsulated service managing patient health records and doctor access controls."""

    @staticmethod
    def upload_document(
        db: Session,
        patient_user: User,
        file_content: bytes,
        original_filename: str,
        title: str,
        document_type: DocumentType = DocumentType.OTHER,
        description: Optional[str] = None,
        declared_mime_type: Optional[str] = None,
    ) -> MedicalDocument:
        """Upload and persist a patient's medical document securely."""
        if patient_user.role != UserRole.PATIENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only registered patients can upload medical documents.",
            )

        patient_profile = (
            db.query(PatientProfile)
            .filter(PatientProfile.user_id == patient_user.id)
            .first()
        )
        if not patient_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient profile not found. Please complete your profile first.",
            )

        clean_title = (title or "").strip()
        if not clean_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document title cannot be blank.",
            )

        # Store file safely
        storage_key, sanitized_filename, file_size, mime_type = storage_service.save_file(
            file_content=file_content,
            original_filename=original_filename,
            declared_mime_type=declared_mime_type,
        )

        # Persist metadata
        doc = MedicalDocument(
            patient_id=patient_profile.id,
            uploaded_by_user_id=patient_user.id,
            title=clean_title,
            document_type=document_type,
            description=description,
            file_name=sanitized_filename,
            storage_key=storage_key,
            file_size=file_size,
            mime_type=mime_type,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Discreet in-app notification to patient
        notification_service.create_notification(
            db=db,
            user_id=patient_user.id,
            title="Medical Document Uploaded",
            message=f"Your medical document '{clean_title}' was uploaded successfully.",
            notification_type=NotificationType.SYSTEM,
            priority=NotificationPriority.LOW,
            metadata_json={"document_id": doc.id},
        )

        return doc

    @staticmethod
    def get_patient_documents(
        db: Session,
        patient_user: User,
        document_type: Optional[DocumentType] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[MedicalDocument], int]:
        """Retrieve paginated documents owned by the authenticated patient."""
        patient_profile = (
            db.query(PatientProfile)
            .filter(PatientProfile.user_id == patient_user.id)
            .first()
        )
        if not patient_profile:
            return [], 0

        query = db.query(MedicalDocument).filter(MedicalDocument.patient_id == patient_profile.id)

        if document_type:
            query = query.filter(MedicalDocument.document_type == document_type)

        total = query.count()
        items = (
            query.order_by(MedicalDocument.created_at.desc(), MedicalDocument.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def get_document_for_patient(
        db: Session,
        document_id: int,
        patient_user: User,
    ) -> MedicalDocument:
        """Retrieve single document verifying patient ownership."""
        patient_profile = (
            db.query(PatientProfile)
            .filter(PatientProfile.user_id == patient_user.id)
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
                detail="You are not authorized to access this medical document.",
            )

        return doc

    @staticmethod
    def get_document_for_doctor(
        db: Session,
        document_id: int,
        doctor_user: User,
    ) -> MedicalDocument:
        """Retrieve single document verifying doctor has an active clinical appointment relationship."""
        doctor_profile = (
            db.query(DoctorProfile)
            .filter(DoctorProfile.user_id == doctor_user.id)
            .first()
        )
        if not doctor_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only registered doctors can access patient clinical documents.",
            )

        doc = db.query(MedicalDocument).filter(MedicalDocument.id == document_id).first()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medical document #{document_id} not found.",
            )

        # Verify clinical appointment relationship exists
        has_relationship = (
            db.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor_profile.id,
                Appointment.patient_id == doc.patient_id,
            )
            .first()
        )
        if not has_relationship:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have clinical authorization to view this patient's medical records.",
            )

        return doc

    @staticmethod
    def get_document_metadata_authorized(
        db: Session,
        document_id: int,
        current_user: User,
    ) -> MedicalDocument:
        """Retrieve metadata checking patient ownership or doctor clinical authorization."""
        if current_user.role == UserRole.PATIENT:
            return MedicalDocumentService.get_document_for_patient(db, document_id, current_user)
        elif current_user.role == UserRole.DOCTOR:
            return MedicalDocumentService.get_document_for_doctor(db, document_id, current_user)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admins and unauthorized roles cannot access sensitive patient medical records.",
            )

    @staticmethod
    def get_document_file_for_download(
        db: Session,
        document_id: int,
        current_user: User,
    ) -> Tuple[MedicalDocument, Path]:
        """Verify authorization and return document entity and physical filesystem Path."""
        doc = MedicalDocumentService.get_document_metadata_authorized(db, document_id, current_user)
        file_path = storage_service.get_file_path(doc.storage_key)
        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Physical document file not found in storage.",
            )
        return doc, file_path

    @staticmethod
    def get_patient_documents_for_doctor(
        db: Session,
        patient_id: int,
        doctor_user: User,
        document_type: Optional[DocumentType] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[MedicalDocument], int]:
        """List patient documents for an authorized doctor with a clinical appointment relationship."""
        doctor_profile = (
            db.query(DoctorProfile)
            .filter(DoctorProfile.user_id == doctor_user.id)
            .first()
        )
        if not doctor_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only registered doctors can access patient clinical documents.",
            )

        # Verify clinical appointment relationship exists
        has_relationship = (
            db.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor_profile.id,
                Appointment.patient_id == patient_id,
            )
            .first()
        )
        if not has_relationship:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have clinical authorization to view this patient's medical records.",
            )

        query = db.query(MedicalDocument).filter(MedicalDocument.patient_id == patient_id)

        if document_type:
            query = query.filter(MedicalDocument.document_type == document_type)

        total = query.count()
        items = (
            query.order_by(MedicalDocument.created_at.desc(), MedicalDocument.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def update_document_metadata(
        db: Session,
        document_id: int,
        patient_user: User,
        update_in: MedicalDocumentUpdate,
    ) -> MedicalDocument:
        """Update document metadata by patient owner."""
        doc = MedicalDocumentService.get_document_for_patient(db, document_id, patient_user)

        if update_in.title is not None:
            clean_title = update_in.title.strip()
            if not clean_title:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Document title cannot be blank.",
                )
            doc.title = clean_title

        if update_in.document_type is not None:
            doc.document_type = update_in.document_type

        if update_in.description is not None:
            doc.description = update_in.description

        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def delete_document(
        db: Session,
        document_id: int,
        patient_user: User,
    ) -> bool:
        """Delete document record and physical file with safe error handling."""
        doc = MedicalDocumentService.get_document_for_patient(db, document_id, patient_user)

        # Delete physical file from storage
        storage_service.delete_file(doc.storage_key)

        # Delete DB entity
        db.delete(doc)
        db.commit()
        return True


medical_document_service = MedicalDocumentService()
