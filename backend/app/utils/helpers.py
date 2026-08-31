"""General utility helper functions."""
from datetime import datetime, timezone
from typing import Any, Dict


def get_utc_now() -> datetime:
    """Return current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Strip None values and whitespace from dictionary keys and string values."""
    cleaned = {}
    for k, v in data.items():
        if v is not None:
            if isinstance(v, str):
                cleaned[k] = v.strip()
            else:
                cleaned[k] = v
    return cleaned
