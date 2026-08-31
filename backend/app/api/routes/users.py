"""User account management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate
from app.services.user_service import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/profile", response_model=UserRead, summary="Get own account profile")
def get_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Retrieve current user account information."""
    return current_user


@router.put("/profile", response_model=UserRead, summary="Update own account profile")
def update_user_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> User:
    """Update profile details for the authenticated user."""
    return user_service.update_user(db=db, user=current_user, update_data=update_data)
