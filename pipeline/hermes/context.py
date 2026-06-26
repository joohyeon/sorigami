from __future__ import annotations
import json
import os


def build_context(job: dict, mode: dict, skills: list[dict]) -> str:
    return json.dumps({
        "job_id": job["id"],
        "drive_file_id": job["drive_file_id"],
        "mode_name": mode.get("name", ""),
        "skills": skills,
        "supabase_url": os.environ["SUPABASE_URL"],
        "supabase_service_role_key": os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        "fcm_server_key": os.environ.get("FCM_SERVER_KEY", ""),
        "google_service_account_json": os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "{}"),
    })
