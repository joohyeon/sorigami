
from __future__ import annotations

import importlib

_SUBMODULES = {
    "sg_drive_download",
    "sg_notify_fcm",
    "sg_slack_post",
    "sg_supabase_write",
    "sg_webhook_call",
    "sg_linear_create",
}


def __getattr__(name: str):
    if name in _SUBMODULES:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = sorted(_SUBMODULES)
