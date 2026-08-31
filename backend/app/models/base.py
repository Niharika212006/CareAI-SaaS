"""Base model mixin with timestamps and common attributes."""
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer


class TimeStampedModel:
    """Mixin for models requiring an integer primary key and automatic timestamps."""
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
