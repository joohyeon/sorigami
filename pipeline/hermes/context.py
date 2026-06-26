from __future__ import annotations
import json
import os


def _require_env(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        raise RuntimeError(f"Required environment variable '{key}' is not set")
    return val


def build_context(job: dict, mode: dict, skills: list[dict]) -> str:
    # Validate required secrets are present before spawning Hermes.
    # We do NOT embed them in the context JSON — the subprocess inherits
    # SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and GOOGLE_SERVICE_ACCOUNT_JSON
    # directly from the environment (set as Fly.io secrets), so they never
    # appear in argv or ps output.
    _require_env("SUPABASE_URL")
    _require_env("SUPABASE_SERVICE_ROLE_KEY")

    return json.dumps({
        "job_id": job["id"],
        "drive_file_id": job["drive_file_id"],
        "mode_name": mode.get("name", ""),
        "skills": skills,
        # device_token populated in Plan 2 when FCM registration is added
        "fcm_device_token": job.get("fcm_device_token", ""),
    })
