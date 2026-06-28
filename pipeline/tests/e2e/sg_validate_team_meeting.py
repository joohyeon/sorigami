import argparse
import json
import os
import secrets
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import httpx


create_client = None


BASE_ENV = (
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "HERMES_PROVIDER",
    "HERMES_MODEL",
)
SMTP_ENV = ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM")
SECRET_ENV = (
    "SUPABASE_SERVICE_ROLE_KEY",
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "SMTP_PASSWORD",
    "SMTP_USERNAME",
)
EXPECTED_SKILLS = [
    "Meeting Summary",
    "Action Items",
    "Decision Log",
    "Meeting Follow-up Email",
]
DEFAULT_E2E_USER_EMAIL = "sorigamis-e2e@example.com"
TEAM_MEETING_SKILLS = [
    {
        "name": "Meeting Summary",
        "description": "Concise summary of the meeting",
        "ai_prompt": (
            "Summarize the transcript into a clear, concise paragraph covering "
            "the main topics discussed."
        ),
        "is_default": False,
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
        "is_default": False,
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
        "is_default": False,
        "require_review": False,
        "integration_actions": [],
    },
]


@dataclass
class ValidationConfig:
    file_id: str
    server_url: str
    attendees: list[str]
    user_email: str
    send_email: bool
    speakers: list[tuple[str, str]] | list[str]
    out_path: Path | None
    out_path_explicit: bool = False


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


def _parse_speaker(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("speaker must be LABEL=Name")

    label, name = value.split("=", 1)
    label = label.strip()
    name = name.strip()
    if not label or not name:
        raise argparse.ArgumentTypeError("speaker must include non-empty LABEL and Name")
    return label, name


def _default_out_path() -> Path:
    return Path(f"/tmp/sg-team-meeting-e2e-{uuid4()}.json")


def _has_explicit_out(argv: list[str]) -> bool:
    return any(arg == "--out" or arg.startswith("--out=") for arg in argv)


def parse_args(argv=None) -> ValidationConfig:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description="Run the Sorigamis Team Meeting E2E validator")
    parser.add_argument("--file-id", required=True)
    parser.add_argument("--server-url", default="http://localhost:8080")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--attendee", action="append", default=[])
    parser.add_argument("--user-email", default=DEFAULT_E2E_USER_EMAIL)
    parser.add_argument("--send-email", action="store_true")
    parser.add_argument("--speaker", action="append", type=_parse_speaker, default=[])
    parser.add_argument("--out", default=str(_default_out_path()))
    args = parser.parse_args(raw_args)

    load_dotenv(Path(args.env_file))

    return ValidationConfig(
        file_id=args.file_id,
        server_url=args.server_url.rstrip("/"),
        attendees=args.attendee,
        user_email=args.user_email,
        send_email=args.send_email,
        speakers=args.speaker,
        out_path=Path(args.out),
        out_path_explicit=_has_explicit_out(raw_args),
    )


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


def _user_email(user) -> str | None:
    if isinstance(user, dict):
        return user.get("email")
    return getattr(user, "email", None)


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

    print(
        f"Warning: could not extract user list from Supabase response "
        f"type {type(value).__name__!r}; treating as empty",
        file=sys.stderr,
    )
    return []


def _get_or_create_e2e_user(db, email: str) -> str:
    users = _users_from_response(db.auth.admin.list_users())
    for user in users:
        user_id = _user_id(user)
        if user_id and _user_email(user) == email:
            return user_id

    created = db.auth.admin.create_user(
        {
            "email": email,
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
        "is_default": False,
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


def _ensure_skill(db, skill: dict, user_id: str) -> str:
    payload = {**skill, "user_id": user_id, "is_default": False}
    query = (
        db.table("sg_skills")
        .select("id")
        .eq("name", skill["name"])
        .eq("user_id", user_id)
    )
    existing = query.execute().data
    if existing:
        skill_id = existing[0]["id"]
        db.table("sg_skills").update(payload).eq("id", skill_id).execute()
        return skill_id

    created = db.table("sg_skills").insert(payload).execute().data
    return created[0]["id"]


def ensure_team_meeting_mode(
    db,
    attendees: list[str],
    user_email: str = DEFAULT_E2E_USER_EMAIL,
) -> tuple[str, str]:
    user_id = _get_or_create_e2e_user(db, user_email)
    skills = [*TEAM_MEETING_SKILLS, _email_skill(attendees)]
    skill_ids = [_ensure_skill(db, skill, user_id) for skill in skills]

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


def _speaker_mapping(speakers: dict[str, str] | list[tuple[str, str]] | list[str]) -> dict[str, str]:
    if isinstance(speakers, dict):
        return speakers

    mapping = {}
    for speaker in speakers:
        if isinstance(speaker, tuple):
            label, name = speaker
            mapping[label] = name
            continue
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
    speakers: dict[str, str] | list[tuple[str, str]] | list[str],
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

    return {"skipped": True}


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


def poll_job(
    config: ValidationConfig,
    job_id: str,
    mode_id: str,
    *,
    max_attempts: int | None = None,
    poll_interval: int = 15,
) -> dict:
    timeline = []
    base_url = config.server_url.rstrip("/")
    speaker_names = _speaker_mapping(config.speakers)
    if max_attempts is None:
        max_attempts = (120 * 60) // poll_interval

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
            error = job_info.get("error") or "job failed"
            return {
                "passed": False,
                "job_id": job_id,
                "drive_file_id": config.file_id,
                "mode_id": mode_id,
                "timeline": timeline,
                "skill_results": [],
                "action_logs": [],
                "email_action_status": "skipped" if not config.send_email else "missing",
                "error": _sanitize_error_message(str(error)),
            }

        if attempt < max_attempts - 1:
            time.sleep(poll_interval)

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


def _create_supabase_client():
    client_factory = create_client
    if client_factory is None:
        try:
            from supabase import create_client as imported_create_client
        except ImportError as exc:
            raise RuntimeError("supabase create_client is unavailable") from exc
        client_factory = imported_create_client

    return client_factory(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )


def _sanitize_error_message(message: str) -> str:
    secret_values = [
        os.environ[key]
        for key in SECRET_ENV
        if os.environ.get(key)
    ]
    for value in sorted(secret_values, key=len, reverse=True):
        message = message.replace(value, "[redacted]")
    message = message.replace("\r", " ").replace("\n", " ")
    return message[:1000]


def _sanitize_error(exc: Exception) -> str:
    message = _sanitize_error_message(str(exc))
    return f"{type(exc).__name__}: {message}"[:1000]


def write_report(path: Path, report: dict, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT
    flags |= os.O_EXCL if exclusive else os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    fd = os.open(path, flags, 0o600)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as report_file:
            fd = -1  # fdopen took ownership; finally must not close it
            json.dump(report, report_file, ensure_ascii=False, indent=2)
            report_file.write("\n")
    finally:
        if fd >= 0:
            os.close(fd)


def _print_report(report: dict) -> None:
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main(argv=None) -> int:
    config = parse_args(argv)
    job_id = None
    mode_id = None
    try:
        preflight(config)
        db = _create_supabase_client()
        mode_id, user_id = ensure_team_meeting_mode(
            db,
            config.attendees,
            config.user_email,
        )

        response = httpx.post(
            f"{config.server_url}/jobs",
            json={
                "drive_file_id": config.file_id,
                "mode_id": mode_id,
                "user_id": user_id,
            },
            timeout=30,
        )
        response.raise_for_status()
        job_id = response.json()["job_id"]

        report = poll_job(config, job_id, mode_id)
    except Exception as exc:
        report = {
            "passed": False,
            "drive_file_id": config.file_id,
            "error": _sanitize_error(exc),
        }
        if job_id is not None:
            report["job_id"] = job_id
        if mode_id is not None:
            report["mode_id"] = mode_id

    _print_report(report)
    if config.out_path is not None:
        try:
            write_report(config.out_path, report, exclusive=not config.out_path_explicit)
        except OSError as exc:
            print(
                f"Warning: could not write report to {config.out_path}: {exc}",
                file=sys.stderr,
            )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
