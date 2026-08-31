"""Authentication Token schemas."""
from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """JWT Access Token response payload."""
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    email: str
    full_name: str


class TokenPayload(BaseModel):
    """Decoded JWT payload structure."""
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None
