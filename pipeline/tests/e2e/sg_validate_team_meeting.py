import argparse
import json
import os
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import httpx
from supabase import create_client


BASE_ENV = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
SMTP_ENV = ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "EMAIL_FROM")
TEAM_MEETING_SKILLS = [
    {
        "name": "Meeting Summary",
        "description": "Concise summary of the meeting",
        "ai_prompt": (
            "Summarize the transcript into a clear, concise paragraph covering "
            "the main topics discussed."
        ),
        "is_default": True,
        "require_review": False,
        "integration_actions": [],
    },
    {
        "name": "Action Items",
        "description": "Extract tasks and owners",
        "ai_prompt": (
            "Extract all action items from the transcript. For each item return: "
            "text (the task), owner (speaker name if mentioned, else null). "
            'Return as JSON array: [{"text":"...","owner":"..."}]'
        ),
        "is_default": True,
        "require_review": True,
        "integration_actions": [],
    },
    {
        "name": "Decision Log",
        "description": "Key decisions made",
        "ai_prompt": (
            "List all decisions made during the conversation. Return as a JSON "
            'array of strings: ["Decision 1","Decision 2"]'
        ),
        "is_default": True,
        "require_review": False,
        "integration_actions": [],
    },
]


@dataclass
class ValidationConfig:
    file_id: str
    server_url: str
    attendees: list[str]
    send_email: bool
    speakers: list[str]
    out_path: Path | None


def load_dotenv(path: Path) -> dict[str, str]:
    loaded: dict[str, str] = {}
    if not path.exists():
        return loaded

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        os.environ[key] = value
        loaded[key] = value

    return loaded


def _missing_env(keys):
    return [key for key in keys if not os.environ.get(key)]


def preflight(config: ValidationConfig):
    response = httpx.get(f"{config.server_url}/health", timeout=10)
    response.raise_for_status()

    missing = _missing_env(BASE_ENV)
    if config.send_email:
        missing.extend(_missing_env(SMTP_ENV))
        if not config.attendees:
            missing.append("attendees")

    if missing:
        raise RuntimeError(f"Missing required preflight configuration: {', '.join(missing)}")


def _user_id(user) -> str | None:
    if isinstance(user, dict):
        return user.get("id")
    return getattr(user, "id", None)


def _users_from_response(response) -> list:
    if response is None:
        return []
    if isinstance(response, list):
        return response
    users = getattr(response, "users", None)
    if users is not None:
        return list(users)
    return []


def _first_or_create_user(db) -> str:
    users = _users_from_response(db.auth.admin.list_users())
    for user in users:
        user_id = _user_id(user)
        if user_id:
            return user_id

    created = db.auth.admin.create_user(
        {
            "email": f"sorigamis-e2e-{uuid4()}@example.com",
            "password": secrets.token_urlsafe(24),
            "email_confirm": True,
        }
    )
    created_user = getattr(created, "user", created)
    user_id = _user_id(created_user)
    if not user_id:
        raise RuntimeError("Supabase did not return a user id for the test user")
    return user_id


def _email_skill(attendees: list[str]) -> dict:
    return {
        "name": "Meeting Follow-up Email",
        "description": "Draft and send a meeting follow-up email to attendees",
        "ai_prompt": (
            "Write a concise follow-up email for the meeting. Include a summary, "
            "action items, decisions, and next steps."
        ),
        "is_default": True,
        "require_review": True,
        "integration_actions": [
            {
                "type": "email",
                "destination": "meeting_attendees",
                "config": {
                    "recipients": attendees,
                    "subject": "Team Meeting follow-up",
                },
            }
        ],
    }


def _ensure_skill(db, skill: dict) -> str:
    existing = db.table("sg_skills").select("id").eq("name", skill["name"]).execute().data
    if existing:
        skill_id = existing[0]["id"]
        db.table("sg_skills").update(skill).eq("id", skill_id).execute()
        return skill_id

    created = db.table("sg_skills").insert(skill).execute().data
    return created[0]["id"]


def ensure_team_meeting_mode(db, attendees: list[str]) -> tuple[str, str]:
    user_id = _first_or_create_user(db)
    skills = [*TEAM_MEETING_SKILLS, _email_skill(attendees)]
    skill_ids = [_ensure_skill(db, skill) for skill in skills]

    payload = {
        "name": "Team Meeting",
        "user_id": user_id,
        "skill_ids": skill_ids,
    }
    existing = db.table("sg_modes").select("id").eq("name", "Team Meeting").execute().data
    if existing:
        mode_id = existing[0]["id"]
        db.table("sg_modes").update(payload).eq("id", mode_id).execute()
        return mode_id, user_id

    created = db.table("sg_modes").insert(payload).execute().data
    return created[0]["id"], user_id
