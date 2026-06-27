import argparse
import json
import os
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import httpx


try:
    from supabase import create_client
except ImportError:  # pragma: no cover - only needed when running the future CLI
    create_client = None


BASE_ENV = (
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "HERMES_PROVIDER",
    "HERMES_MODEL",
)
SMTP_ENV = ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM")
EXPECTED_SKILLS = [
    "Meeting Summary",
    "Action Items",
    "Decision Log",
    "Meeting Follow-up Email",
]
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


def _users_from_response(value) -> list:
    if value is None:
        return []
    if isinstance(value, list | tuple):
        return list(value)
    if _user_id(value):
        return [value]
    if isinstance(value, dict):
        for key in ("users", "data"):
            if key in value:
                return _users_from_response(value[key])
        return []

    for attr in ("users", "data"):
        users = getattr(value, attr, None)
        if users is not None:
            return _users_from_response(users)

    try:
        return list(value)
    except TypeError:
        pass

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
    payload = {**skill, "user_id": None}
    query = (
        db.table("sg_skills")
        .select("id")
        .eq("name", skill["name"])
        .eq("is_default", True)
    )
    if hasattr(query, "is_"):
        query = query.is_("user_id", "null")
    existing = query.execute().data
    if existing:
        skill_id = existing[0]["id"]
        db.table("sg_skills").update(payload).eq("id", skill_id).execute()
        return skill_id

    created = db.table("sg_skills").insert(payload).execute().data
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
    existing = (
        db.table("sg_modes")
        .select("id")
        .eq("name", "Team Meeting")
        .eq("user_id", user_id)
        .execute()
        .data
    )
    if existing:
        mode_id = existing[0]["id"]
        db.table("sg_modes").update(payload).eq("id", mode_id).execute()
        return mode_id, user_id

    created = db.table("sg_modes").insert(payload).execute().data
    return created[0]["id"], user_id


def _speaker_mapping(speakers: dict[str, str] | list[str]) -> dict[str, str]:
    if isinstance(speakers, dict):
        return speakers

    mapping = {}
    for speaker in speakers:
        if "=" not in speaker:
            continue
        label, name = speaker.split("=", 1)
        label = label.strip()
        name = name.strip()
        if label and name:
            mapping[label] = name
    return mapping


def checkpoint_response(
    checkpoint: dict,
    speakers: dict[str, str] | list[str],
    send_email: bool,
) -> dict:
    checkpoint_type = checkpoint.get("type")
    speaker_names = _speaker_mapping(speakers)

    if checkpoint_type == "speaker_assignment":
        confirmed_speakers = []
        for index, speaker in enumerate(checkpoint.get("speakers") or []):
            label = speaker.get("label") or f"Speaker {index + 1}"
            confirmed_speakers.append(
                {
                    "id": speaker.get("id"),
                    "confirmed_name": speaker_names.get(label, f"Participant {label}"),
                }
            )
        return {"speakers": confirmed_speakers}

    if checkpoint_type == "action_confirmation":
        action = checkpoint.get("action") or {}
        action_type = checkpoint.get("action_type") or action.get("type")
        if action_type == "email" and send_email:
            return {"approved": True}
        return {"skipped": True}

    return {"approved": True}


def _result_output_is_present(result: dict) -> bool:
    for key in ("output", "output_markdown", "output_json"):
        output = result.get(key)
        if output:
            return True
    return False


def _email_action_status(action_logs: list[dict], send_email: bool) -> str:
    if not send_email:
        return "skipped"

    for action in action_logs:
        action_type = action.get("action_type") or action.get("type")
        status = action.get("status")
        if action_type == "email" and status == "fired":
            return "fired"
    return "missing"


def build_report(
    job_id: str,
    file_id: str,
    mode_id: str,
    timeline: list[dict],
    results: dict,
    send_email: bool,
) -> dict:
    skill_results = results.get("skill_results") or []
    action_logs = results.get("action_logs") or []
    results_by_name = {result.get("skill_name"): result for result in skill_results}
    missing_skills = [
        name
        for name in EXPECTED_SKILLS
        if name not in results_by_name or not _result_output_is_present(results_by_name[name])
    ]
    email_status = _email_action_status(action_logs, send_email)
    passed = not missing_skills and (not send_email or email_status == "fired")

    return {
        "passed": passed,
        "job_id": job_id,
        "drive_file_id": file_id,
        "mode_id": mode_id,
        "timeline": timeline,
        "skill_results": skill_results,
        "action_logs": action_logs,
        "email_action_status": email_status,
        "missing_skills": missing_skills,
    }


def _timeline_entry(job_info: dict) -> dict:
    return {
        "status": job_info.get("status"),
        "checkpoint": job_info.get("checkpoint"),
    }


def _approved_steps(plan: dict | None) -> list[str]:
    if plan and plan.get("approved_steps"):
        return plan["approved_steps"]
    return ["speaker_assignment", *EXPECTED_SKILLS]


def poll_job(config: ValidationConfig, job_id: str, mode_id: str) -> dict:
    timeline = []
    base_url = config.server_url.rstrip("/")
    speaker_names = _speaker_mapping(config.speakers)
    max_attempts = 40

    for attempt in range(max_attempts):
        response = httpx.get(f"{base_url}/jobs/{job_id}", timeout=30)
        response.raise_for_status()
        job_info = response.json()
        status = job_info.get("status")
        timeline.append(_timeline_entry(job_info))

        if status == "awaiting_plan_confirmation":
            confirm_response = httpx.post(
                f"{base_url}/jobs/{job_id}/confirm",
                json={
                    "approved_steps": _approved_steps(job_info.get("plan")),
                    "per_step_overrides": {},
                },
                timeout=30,
            )
            confirm_response.raise_for_status()
        elif status == "awaiting_checkpoint":
            checkpoint = job_info.get("checkpoint") or {}
            checkpoint_response_result = checkpoint_response(
                checkpoint,
                speakers=speaker_names,
                send_email=config.send_email,
            )
            checkpoint_response_http = httpx.post(
                f"{base_url}/jobs/{job_id}/checkpoint",
                json={"data": checkpoint_response_result},
                timeout=30,
            )
            checkpoint_response_http.raise_for_status()
        elif status == "awaiting_skill_review":
            review_response = httpx.post(
                f"{base_url}/jobs/{job_id}/checkpoint",
                json={"data": {"approved": True}},
                timeout=30,
            )
            review_response.raise_for_status()
        elif status == "complete":
            results_response = httpx.get(f"{base_url}/jobs/{job_id}/results", timeout=30)
            results_response.raise_for_status()
            return build_report(
                job_id=job_id,
                file_id=config.file_id,
                mode_id=mode_id,
                timeline=timeline,
                results=results_response.json(),
                send_email=config.send_email,
            )
        elif status == "failed":
            return {
                "passed": False,
                "job_id": job_id,
                "drive_file_id": config.file_id,
                "mode_id": mode_id,
                "timeline": timeline,
                "skill_results": [],
                "action_logs": [],
                "email_action_status": "skipped" if not config.send_email else "missing",
                "error": job_info.get("error") or "job failed",
            }

        if attempt < max_attempts - 1:
            time.sleep(15)

    return {
        "passed": False,
        "job_id": job_id,
        "drive_file_id": config.file_id,
        "mode_id": mode_id,
        "timeline": timeline,
        "skill_results": [],
        "action_logs": [],
        "email_action_status": "skipped" if not config.send_email else "missing",
        "error": "timeout",
    }
