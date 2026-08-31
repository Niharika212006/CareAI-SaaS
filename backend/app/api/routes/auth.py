"""Authentication endpoints: Register, Login, Current User."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.schemas.token import Token
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (Patient or Doctor)",
)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> Token:
    """Register a new user account and return an access token."""
    user = auth_service.register_user(db=db, user_in=user_in)
    return auth_service.create_token_for_user(user)


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate user and obtain JWT token",
)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
) -> Token:
    """Authenticate user with email and password."""
    user = auth_service.authenticate_user(
        db=db, email=credentials.email, password=credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated",
        )
    return auth_service.create_token_for_user(user)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current authenticated user profile",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> User:
    """Return the profile data of the currently logged-in user."""
    return current_user
