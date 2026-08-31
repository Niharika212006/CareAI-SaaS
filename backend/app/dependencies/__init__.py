"""FastAPI dependencies module."""
from app.dependencies.database import get_db
from app.dependencies.auth import (
    oauth2_scheme,
    get_current_user,
    get_current_active_user,
    require_role,
)

__all__ = [
    "get_db",
    "oauth2_scheme",
    "get_current_user",
    "get_current_active_user",
    "require_role",
]
