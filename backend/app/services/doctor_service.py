"""Doctor profile and discovery service."""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.schemas.doctor import DoctorProfileUpdate, DoctorApprovalUpdate


class DoctorService:
    """Business logic for doctor profiles, verification, and discovery."""

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Optional[DoctorProfile]:
        """Fetch doctor profile by user ID."""
        return db.query(DoctorProfile).filter(DoctorProfile.user_id == user_id).first()

    @staticmethod
    def get_by_id(db: Session, doctor_id: int) -> Optional[DoctorProfile]:
        """Fetch doctor profile by profile ID."""
        return db.query(DoctorProfile).filter(DoctorProfile.id == doctor_id).first()

    @staticmethod
    def list_approved_doctors(
        db: Session,
        specialization: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[DoctorProfile]:
        """List approved doctors for discovery."""
        query = db.query(DoctorProfile).filter(
            DoctorProfile.approval_status == DoctorApprovalStatus.APPROVED
        )
        if specialization:
            query = query.filter(DoctorProfile.specialization.ilike(f"%{specialization}%"))
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def list_pending_doctors(db: Session, skip: int = 0, limit: int = 50) -> List[DoctorProfile]:
        """List doctors pending admin verification."""
        return (
            db.query(DoctorProfile)
            .filter(DoctorProfile.approval_status == DoctorApprovalStatus.PENDING)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def update_profile(
        db: Session, profile: DoctorProfile, update_data: DoctorProfileUpdate
    ) -> DoctorProfile:
        """Update doctor professional details."""
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(profile, key, value)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def review_approval(
        db: Session, profile: DoctorProfile, approval_data: DoctorApprovalUpdate
    ) -> DoctorProfile:
        """Admin review of doctor credentials (approve/reject)."""
        profile.approval_status = approval_data.approval_status
        profile.rejection_reason = approval_data.rejection_reason
        db.commit()
        db.refresh(profile)

        # Notify Doctor
        from app.services.notification_service import notification_service
        from app.models.notification import NotificationType, NotificationPriority

        if profile.user_id:
            if profile.approval_status == DoctorApprovalStatus.APPROVED:
                notification_service.create_notification(
                    db=db,
                    user_id=profile.user_id,
                    title="Doctor Profile Approved",
                    message="Your doctor profile has been approved and you can now accept appointments.",
                    notification_type=NotificationType.DOCTOR_APPROVAL,
                    priority=NotificationPriority.HIGH,
                    metadata_json={"doctor_id": profile.id},
                )
            elif profile.approval_status == DoctorApprovalStatus.REJECTED:
                reason = profile.rejection_reason or "Credentials could not be verified."
                notification_service.create_notification(
                    db=db,
                    user_id=profile.user_id,
                    title="Doctor Credentials Status Update",
                    message=f"Your credential submission was not approved: {reason}",
                    notification_type=NotificationType.DOCTOR_APPROVAL,
                    priority=NotificationPriority.HIGH,
                    metadata_json={"doctor_id": profile.id},
                )

        return profile


doctor_service = DoctorService()
