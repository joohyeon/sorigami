from __future__ import annotations
import os
from typing import Any

try:
    from supabase import create_client
except ImportError:  # pragma: no cover - exercised in test envs without supabase
    create_client = None  # type: ignore[assignment]

_client: Any | None = None

def get_supabase() -> Any:
    global _client
    if _client is None:
        if create_client is None:
            raise RuntimeError("supabase is not installed")
        _client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        )
    return _client
