"""Administrator endpoints for system metrics and doctor profile approvals."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import require_role
from app.models.user import User, UserRole
from app.models.doctor import DoctorProfile
from app.schemas.doctor import DoctorProfileRead, DoctorApprovalUpdate
from app.schemas.user import UserRead
from app.services.doctor_service import doctor_service
from app.services.user_service import user_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/pending-doctors",
    response_model=List[DoctorProfileRead],
    summary="List doctor applications pending approval",
)
def get_pending_doctors(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> List[DoctorProfile]:
    """Retrieve all doctor profiles awaiting administrative credential review."""
    return doctor_service.list_pending_doctors(db=db, skip=skip, limit=limit)


@router.put(
    "/doctors/{doctor_id}/approval",
    response_model=DoctorProfileRead,
    summary="Approve or reject doctor credentials",
)
def update_doctor_approval_status(
    doctor_id: int,
    approval_data: DoctorApprovalUpdate,
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> DoctorProfile:
    """Approve or reject a doctor application with justification."""
    profile = doctor_service.get_by_id(db=db, doctor_id=doctor_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found.",
        )
    return doctor_service.review_approval(
        db=db, profile=profile, approval_data=approval_data
    )


@router.get(
    "/users",
    response_model=List[UserRead],
    summary="List all registered platform users",
)
def list_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> List[User]:
    """Administrator audit list of all platform user accounts."""
    return user_service.get_all(db=db, skip=skip, limit=limit)
