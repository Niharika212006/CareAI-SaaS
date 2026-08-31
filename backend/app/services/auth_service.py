"""Authentication service handling registration, validation, and JWT generation."""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User, UserRole
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile, DoctorApprovalStatus
from app.schemas.user import UserCreate
from app.schemas.token import Token


class AuthService:
    """Business logic for user authentication and session tokens."""

    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> User:
        """Register a new user and initialize role-specific profile stub."""
        existing_user = db.query(User).filter(User.email == user_in.email.lower()).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )

        db_user = User(
            email=user_in.email.lower(),
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            phone_number=user_in.phone_number,
            role=user_in.role,
            is_active=True,
            is_verified=False,
        )
        db.add(db_user)
        db.flush()  # Populate db_user.id

        # Automatically create profile scaffold based on user role
        if user_in.role == UserRole.PATIENT:
            patient_profile = PatientProfile(user_id=db_user.id)
            db.add(patient_profile)
        elif user_in.role == UserRole.DOCTOR:
            doctor_profile = DoctorProfile(
                user_id=db_user.id,
                specialization="General Practice",
                license_number=f"LIC-PENDING-{db_user.id}",
                approval_status=DoctorApprovalStatus.PENDING,
            )
            db.add(doctor_profile)

        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user credentials."""
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def create_token_for_user(user: User) -> Token:
        """Generate a signed JWT token response for an authenticated user."""
        access_token = create_access_token(
            subject=str(user.id),
            role=user.role.value,
        )
        return Token(
            access_token=access_token,
            token_type="bearer",
            role=user.role.value,
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
        )


auth_service = AuthService()
