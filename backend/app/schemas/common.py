"""Common and generic Pydantic response schemas."""
from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel

T = TypeVar("T")


class MessageResponse(BaseModel):
    """Standard message response schema."""
    message: str
    detail: Optional[str] = None


class BaseResponse(BaseModel, Generic[T]):
    """Standard API envelope for responses."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard pagination wrapper schema."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
