# Team Meeting E2E Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a manual E2E validator that drives the real Team Meeting FastAPI/Hermes/Supabase path and can approve a real SMTP email action.

**Architecture:** Add one runtime SMTP tool for Hermes, update the orchestrator instructions to support email actions, and add one manual validation runner under `pipeline/tests/e2e/`. The runner acts as the mobile app substitute: it seeds Team Meeting data, submits through FastAPI, polls checkpoints, approves or skips actions based on CLI flags, and writes a report.

**Tech Stack:** Python 3.12, FastAPI endpoints via `httpx`, Supabase Python client, Hermes prompt instructions, standard-library `smtplib` and `email.message.EmailMessage`, pytest with mocks.

---

## File Structure

- Create `pipeline/tools/sg_email_send.py`: SMTP sender used by Hermes Stage 6.
- Create `pipeline/tests/test_email_tool.py`: unit tests for SMTP env parsing, message construction, send success, and sanitized errors.
- Modify `pipeline/hermes/skills/sg-orchestrator.md`: document email action checkpoint and `sg_email_send` call.
- Modify `pipeline/tests/test_hermes_runner.py`: assert the inlined orchestrator prompt contains email action instructions.
- Create `pipeline/tests/e2e/__init__.py`: package marker for importing the validator in tests.
- Create `pipeline/tests/e2e/sg_validate_team_meeting.py`: manual E2E validation CLI.
- Create `pipeline/tests/test_team_meeting_validator.py`: unit tests for preflight, seeding, checkpoint decisions, polling, and report generation.
- Modify `RUNBOOK.md`: add a short pointer to the manual validator after the CLI is tested.

---

## Task 1: SMTP Email Runtime Tool

**Files:**
- Create: `pipeline/tools/sg_email_send.py`
- Test: `pipeline/tests/test_email_tool.py`

- [ ] **Step 1: Write failing tests for SMTP success and required env**

Create `pipeline/tests/test_email_tool.py`:

```python
import os
from unittest.mock import MagicMock, patch

import pytest


SMTP_ENV = {
    "SMTP_HOST": "smtp.example.com",
    "SMTP_PORT": "587",
    "SMTP_USERNAME": "user@example.com",
    "SMTP_PASSWORD": "secret-password",
    "SMTP_FROM": "noreply@example.com",
}


def test_send_email_uses_starttls_and_sends_message():
    smtp = MagicMock()
    with patch.dict(os.environ, {**SMTP_ENV, "SMTP_USE_TLS": "true"}, clear=True), \
         patch("tools.sg_email_send.smtplib.SMTP", return_value=smtp) as smtp_cls:
        from tools.sg_email_send import send_email

        result = send_email(
            recipients=["alice@example.com", "bob@example.com"],
            subject="Team Meeting follow-up",
            body_markdown="# Summary\n\nDone.",
        )

    smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=30)
    smtp.starttls.assert_called_once()
    smtp.login.assert_called_once_with("user@example.com", "secret-password")
    sent_message = smtp.send_message.call_args.args[0]
    assert sent_message["From"] == "noreply@example.com"
    assert sent_message["To"] == "alice@example.com, bob@example.com"
    assert sent_message["Subject"] == "Team Meeting follow-up"
    assert sent_message.get_content().strip() == "# Summary\n\nDone."
    smtp.quit.assert_called_once()
    assert result["recipients"] == ["alice@example.com", "bob@example.com"]
    assert result["subject"] == "Team Meeting follow-up"
    assert result["status"] == "sent"
    assert "secret-password" not in str(result)


def test_send_email_requires_smtp_env():
    with patch.dict(os.environ, {}, clear=True):
        from tools.sg_email_send import send_email

        with pytest.raises(RuntimeError, match="Missing SMTP env"):
            send_email(["alice@example.com"], "Subject", "Body")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd pipeline
uv run pytest tests/test_email_tool.py -v
```

Expected: FAIL during import with `ModuleNotFoundError: No module named 'tools.sg_email_send'`.

- [ ] **Step 3: Implement minimal SMTP tool**

Create `pipeline/tools/sg_email_send.py`:

```python
from __future__ import annotations

import os
import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage


_REQUIRED_ENV = [
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
    "SMTP_FROM",
]


def _smtp_config() -> dict[str, str | int | bool]:
    missing = [key for key in _REQUIRED_ENV if not os.environ.get(key)]
    if missing:
        raise RuntimeError(f"Missing SMTP env: {', '.join(missing)}")
    try:
        port = int(os.environ["SMTP_PORT"])
    except ValueError as exc:
        raise RuntimeError("SMTP_PORT must be an integer") from exc
    use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() not in {"0", "false", "no"}
    return {
        "host": os.environ["SMTP_HOST"],
        "port": port,
        "username": os.environ["SMTP_USERNAME"],
        "password": os.environ["SMTP_PASSWORD"],
        "from": os.environ["SMTP_FROM"],
        "use_tls": use_tls,
    }


def _sanitize_error(exc: Exception) -> str:
    message = str(exc)
    password = os.environ.get("SMTP_PASSWORD")
    if password:
        message = message.replace(password, "[redacted]")
    return message


def send_email(recipients: list[str], subject: str, body_markdown: str) -> dict:
    if not recipients:
        raise RuntimeError("At least one email recipient is required")
    config = _smtp_config()
    message = EmailMessage()
    message["From"] = str(config["from"])
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(body_markdown)

    smtp = None
    try:
        smtp = smtplib.SMTP(str(config["host"]), int(config["port"]), timeout=30)
        if bool(config["use_tls"]):
            smtp.starttls()
        smtp.login(str(config["username"]), str(config["password"]))
        smtp.send_message(message)
        smtp.quit()
    except Exception as exc:
        if smtp is not None:
            try:
                smtp.quit()
            except Exception:
                pass
        raise RuntimeError(f"SMTP send failed: {_sanitize_error(exc)}") from exc

    return {
        "status": "sent",
        "recipients": recipients,
        "subject": subject,
        "sent_at": datetime.now(UTC).isoformat(),
    }
```

- [ ] **Step 4: Run tests to verify success**

Run:

```bash
cd pipeline
uv run pytest tests/test_email_tool.py -v
```

Expected: PASS.

- [ ] **Step 5: Add failure sanitization tests**

Append to `pipeline/tests/test_email_tool.py`:

```python
def test_send_email_redacts_password_from_smtp_errors():
    smtp = MagicMock()
    smtp.login.side_effect = RuntimeError("bad password secret-password")
    with patch.dict(os.environ, SMTP_ENV, clear=True), \
         patch("tools.sg_email_send.smtplib.SMTP", return_value=smtp):
        from tools.sg_email_send import send_email

        with pytest.raises(RuntimeError) as err:
            send_email(["alice@example.com"], "Subject", "Body")

    assert "secret-password" not in str(err.value)
    assert "[redacted]" in str(err.value)


def test_send_email_can_disable_starttls_for_local_smtp():
    smtp = MagicMock()
    with patch.dict(os.environ, {**SMTP_ENV, "SMTP_USE_TLS": "false"}, clear=True), \
         patch("tools.sg_email_send.smtplib.SMTP", return_value=smtp):
        from tools.sg_email_send import send_email

        send_email(["alice@example.com"], "Subject", "Body")

    smtp.starttls.assert_not_called()
    smtp.send_message.assert_called_once()
```

- [ ] **Step 6: Run email tool tests**

Run:

```bash
cd pipeline
uv run pytest tests/test_email_tool.py -v
```

Expected: all tests PASS.

- [ ] **Step 7: Commit Task 1**

```bash
git add pipeline/tools/sg_email_send.py pipeline/tests/test_email_tool.py
git commit -m "Add SMTP email send tool"
```

---

## Task 2: Hermes Email Action Instructions

**Files:**
- Modify: `pipeline/hermes/skills/sg-orchestrator.md`
- Modify: `pipeline/tests/test_hermes_runner.py`

- [ ] **Step 1: Write failing prompt test**

Append to `pipeline/tests/test_hermes_runner.py`:

```python
def test_orchestrator_prompt_contains_email_action_instructions():
    """Stage 6 must explain how Hermes confirms and fires email actions."""
    from hermes.runner import _build_prompt

    prompt = _build_prompt('{"job_id":"job-1"}')

    assert "sg_email_send" in prompt
    assert "action_type\": \"email\"" in prompt
    assert "Meeting Follow-up Email" in prompt
    assert "SMTP" in prompt
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd pipeline
uv run pytest tests/test_hermes_runner.py::test_orchestrator_prompt_contains_email_action_instructions -v
```

Expected: FAIL because `sg_email_send` is not in the orchestrator prompt.

- [ ] **Step 3: Update Stage 6 instructions**

Modify `pipeline/hermes/skills/sg-orchestrator.md` Stage 6 to include this email-specific block after the existing external action instructions:

````markdown
### Email action handling

For a skill named "Meeting Follow-up Email" or any integration action with
`{"type": "email"}`, build the email body from the approved skill outputs and
the speaker-attributed transcript. The email should include:
- meeting summary
- action items with owners
- decisions

Before sending, write an action confirmation checkpoint:
```json
{
  "type": "action_confirmation",
  "action_type": "email",
  "destination": "meeting_attendees",
  "preview": {
    "to": ["alice@example.com"],
    "subject": "Team Meeting follow-up",
    "body_markdown": "<Hermes-generated meeting follow-up body>"
  }
}
```

After approval, call the SMTP helper:
```bash
.venv/bin/python -c "
from tools.sg_email_send import send_email
result = send_email(
    recipients=<recipients_from_integration_action_config>,
    subject=<subject_from_preview>,
    body_markdown=<body_markdown_from_preview>,
)
print(result)
"
```

Write `sg_action_logs` with `action_type='email'`, `destination='meeting_attendees'`,
`payload_json` containing the recipients, subject, body preview, and send result,
and `status='fired'` on success. If the SMTP helper raises, write `status='failed'`
with the sanitized error.
````

- [ ] **Step 4: Run prompt test**

Run:

```bash
cd pipeline
uv run pytest tests/test_hermes_runner.py::test_orchestrator_prompt_contains_email_action_instructions -v
```

Expected: PASS.

- [ ] **Step 5: Run full Hermes runner tests**

Run:

```bash
cd pipeline
uv run pytest tests/test_hermes_runner.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit Task 2**

```bash
git add pipeline/hermes/skills/sg-orchestrator.md pipeline/tests/test_hermes_runner.py
git commit -m "Document Hermes email action handling"
```

---

## Task 3: Validator Preflight And Team Meeting Setup

**Files:**
- Create: `pipeline/tests/e2e/__init__.py`
- Create: `pipeline/tests/e2e/sg_validate_team_meeting.py`
- Test: `pipeline/tests/test_team_meeting_validator.py`

- [ ] **Step 1: Write failing tests for env loading and preflight**

Create `pipeline/tests/test_team_meeting_validator.py`:

```python
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_load_dotenv_sets_values(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("SUPABASE_URL=https://example.supabase.co\nSMTP_PORT=587\n")

    from tests.e2e.sg_validate_team_meeting import load_dotenv

    values = load_dotenv(env_file)

    assert values["SUPABASE_URL"] == "https://example.supabase.co"
    assert values["SMTP_PORT"] == "587"


def test_preflight_requires_smtp_when_send_email():
    from tests.e2e.sg_validate_team_meeting import ValidationConfig, preflight

    cfg = ValidationConfig(
        file_id="drive-file",
        server_url="http://localhost:8080",
        attendees=["alice@example.com"],
        send_email=True,
        speakers={},
        out_path=Path("/tmp/report.json"),
    )

    with patch.dict("os.environ", {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "key",
        "GOOGLE_SERVICE_ACCOUNT_JSON": "{}",
        "HERMES_PROVIDER": "github-copilot",
        "HERMES_MODEL": "gemini-2.5-pro",
    }, clear=True), \
         patch("tests.e2e.sg_validate_team_meeting.httpx.get") as get:
        get.return_value.status_code = 200
        get.return_value.json.return_value = {"ok": True}
        with pytest.raises(RuntimeError, match="SMTP_HOST"):
            preflight(cfg)
```

- [ ] **Step 2: Run tests to verify import failure**

Run:

```bash
cd pipeline
uv run pytest tests/test_team_meeting_validator.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tests.e2e'`.

- [ ] **Step 3: Add package and minimal validator helpers**

Create `pipeline/tests/e2e/__init__.py` as an empty file.

Create `pipeline/tests/e2e/sg_validate_team_meeting.py`:

```python
from __future__ import annotations

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


BASE_ENV = [
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "HERMES_PROVIDER",
    "HERMES_MODEL",
]

SMTP_ENV = [
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
    "SMTP_FROM",
]


@dataclass
class ValidationConfig:
    file_id: str
    server_url: str
    attendees: list[str]
    send_email: bool
    speakers: dict[str, str]
    out_path: Path


def load_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        clean_value = value.strip().strip('"').strip("'")
        values[key.strip()] = clean_value
        os.environ[key.strip()] = clean_value
    return values


def _missing_env(keys: list[str]) -> list[str]:
    return [key for key in keys if not os.environ.get(key)]


def preflight(config: ValidationConfig) -> None:
    health = httpx.get(f"{config.server_url}/health", timeout=10)
    health.raise_for_status()
    missing = _missing_env(BASE_ENV)
    if config.send_email:
        missing.extend(_missing_env(SMTP_ENV))
        if not config.attendees:
            missing.append("--attendee")
    if missing:
        raise RuntimeError(f"Missing required validation inputs: {', '.join(missing)}")
```

- [ ] **Step 4: Run preflight tests**

Run:

```bash
cd pipeline
uv run pytest tests/test_team_meeting_validator.py -v
```

Expected: PASS for current tests.

- [ ] **Step 5: Add failing test for Team Meeting seeding**

Append to `pipeline/tests/test_team_meeting_validator.py`:

```python
def test_ensure_team_meeting_mode_seeds_email_skill():
    from tests.e2e.sg_validate_team_meeting import ensure_team_meeting_mode

    db = MagicMock()
    db.auth.admin.list_users.return_value = []
    created_user = MagicMock()
    created_user.user.id = "user-1"
    db.auth.admin.create_user.return_value = created_user

    db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    db.table.return_value.insert.return_value.execute.return_value.data = [{"id": "new-id"}]

    mode_id, user_id = ensure_team_meeting_mode(db, ["alice@example.com"])

    assert mode_id == "new-id"
    assert user_id == "user-1"
    inserted_payloads = [call.args[0] for call in db.table.return_value.insert.call_args_list]
    assert any(payload.get("name") == "Meeting Follow-up Email" for payload in inserted_payloads)
```

- [ ] **Step 6: Run new test to verify it fails**

Run:

```bash
cd pipeline
uv run pytest tests/test_team_meeting_validator.py::test_ensure_team_meeting_mode_seeds_email_skill -v
```

Expected: FAIL with `ImportError` for `ensure_team_meeting_mode`.

- [ ] **Step 7: Implement Team Meeting setup**

Append to `pipeline/tests/e2e/sg_validate_team_meeting.py`:

```python
TEAM_MEETING_SKILLS = [
    {
        "name": "Meeting Summary",
        "description": "Concise summary of the meeting",
        "ai_prompt": "Summarize the transcript into meeting notes covering the main topics discussed.",
        "is_default": True,
        "require_review": False,
        "integration_actions": [],
    },
    {
        "name": "Action Items",
        "description": "Extract tasks and owners",
        "ai_prompt": "Extract action items as JSON with text and owner fields.",
        "is_default": True,
        "require_review": True,
        "integration_actions": [],
    },
    {
        "name": "Decision Log",
        "description": "Extract decisions made",
        "ai_prompt": "List decisions made during the conversation as JSON strings.",
        "is_default": True,
        "require_review": True,
        "integration_actions": [],
    },
]


def _first_or_create_user(db) -> str:
    users = db.auth.admin.list_users()
    if users:
        return users[0].id
    created = db.auth.admin.create_user({
        "email": f"sorigamis-e2e-{uuid4()}@example.com",
        "password": secrets.token_urlsafe(24),
        "email_confirm": True,
    })
    return created.user.id


def ensure_team_meeting_mode(db, attendees: list[str]) -> tuple[str, str]:
    user_id = _first_or_create_user(db)
    skill_rows = []
    skills = [
        *TEAM_MEETING_SKILLS,
        {
            "name": "Meeting Follow-up Email",
            "description": "Send meeting summary, action items, and decisions by email",
            "ai_prompt": "Create a concise follow-up email from the meeting summary, action items, and decisions.",
            "is_default": True,
            "require_review": True,
            "integration_actions": [{
                "type": "email",
                "destination": "meeting_attendees",
                "config": {
                    "recipients": attendees,
                    "subject": "Team Meeting follow-up",
                },
            }],
        },
    ]
    for skill in skills:
        existing = db.table("sg_skills").select("id").eq("name", skill["name"]).execute()
        if existing.data:
            skill_id = existing.data[0]["id"]
            db.table("sg_skills").update(skill).eq("id", skill_id).execute()
        else:
            inserted = db.table("sg_skills").insert(skill).execute()
            skill_id = inserted.data[0]["id"]
        skill_rows.append(skill_id)

    existing_mode = db.table("sg_modes").select("id").eq("name", "Team Meeting").execute()
    payload = {"name": "Team Meeting", "user_id": user_id, "skill_ids": skill_rows}
    if existing_mode.data:
        mode_id = existing_mode.data[0]["id"]
        db.table("sg_modes").update(payload).eq("id", mode_id).execute()
        return mode_id, user_id
    inserted_mode = db.table("sg_modes").insert(payload).execute()
    return inserted_mode.data[0]["id"], user_id
```

- [ ] **Step 8: Run validator setup tests**

Run:

```bash
cd pipeline
uv run pytest tests/test_team_meeting_validator.py -v
```

Expected: PASS.

- [ ] **Step 9: Commit Task 3**

```bash
git add pipeline/tests/e2e/__init__.py pipeline/tests/e2e/sg_validate_team_meeting.py pipeline/tests/test_team_meeting_validator.py
git commit -m "Add Team Meeting validator setup"
```

---

## Task 4: Validator Polling, Checkpoints, And Report

**Files:**
- Modify: `pipeline/tests/e2e/sg_validate_team_meeting.py`
- Modify: `pipeline/tests/test_team_meeting_validator.py`

- [ ] **Step 1: Write failing tests for checkpoint handlers**

Append to `pipeline/tests/test_team_meeting_validator.py`:

```python
def test_checkpoint_response_assigns_speakers_from_mapping():
    from tests.e2e.sg_validate_team_meeting import checkpoint_response

    checkpoint = {
        "type": "speaker_assignment",
        "speakers": [{"id": "spk-1", "label": "A"}, {"id": "spk-2", "label": "B"}],
    }

    response = checkpoint_response(checkpoint, speakers={"A": "Alice"}, send_email=False)

    assert response == {
        "speakers": [
            {"id": "spk-1", "confirmed_name": "Alice"},
            {"id": "spk-2", "confirmed_name": "Participant B"},
        ]
    }


def test_checkpoint_response_approves_email_only_when_enabled():
    from tests.e2e.sg_validate_team_meeting import checkpoint_response

    checkpoint = {"type": "action_confirmation", "action_type": "email"}

    assert checkpoint_response(checkpoint, {}, send_email=True) == {"approved": True}
    assert checkpoint_response(checkpoint, {}, send_email=False) == {"skipped": True}
```

- [ ] **Step 2: Run checkpoint tests to verify failure**

Run:

```bash
cd pipeline
uv run pytest tests/test_team_meeting_validator.py::test_checkpoint_response_assigns_speakers_from_mapping tests/test_team_meeting_validator.py::test_checkpoint_response_approves_email_only_when_enabled -v
```

Expected: FAIL because `checkpoint_response` is missing.

- [ ] **Step 3: Implement checkpoint response helpers**

Append to `pipeline/tests/e2e/sg_validate_team_meeting.py`:

```python
def checkpoint_response(checkpoint: dict, speakers: dict[str, str], send_email: bool) -> dict:
    checkpoint_type = checkpoint.get("type")
    if checkpoint_type == "speaker_assignment":
        confirmed = []
        for speaker in checkpoint.get("speakers", []):
            label = speaker.get("label", "Unknown")
            confirmed.append({
                "id": speaker.get("id"),
                "confirmed_name": speakers.get(label, f"Participant {label}"),
            })
        return {"speakers": confirmed}
    if checkpoint_type == "action_confirmation":
        if checkpoint.get("action_type") == "email":
            return {"approved": bool(send_email)} if send_email else {"skipped": True}
        return {"skipped": True}
    return {"skipped": True}
```

- [ ] **Step 4: Run checkpoint tests**

Run:

```bash
cd pipeline
uv run pytest tests/test_team_meeting_validator.py::test_checkpoint_response_assigns_speakers_from_mapping tests/test_team_meeting_validator.py::test_checkpoint_response_approves_email_only_when_enabled -v
```

Expected: PASS.

- [ ] **Step 5: Write failing test for final report validation**

Append to `pipeline/tests/test_team_meeting_validator.py`:

```python
def test_build_report_marks_success_when_results_and_email_log_exist():
    from tests.e2e.sg_validate_team_meeting import build_report

    report = build_report(
        job_id="job-1",
        file_id="drive-1",
        mode_id="mode-1",
        timeline=[{"status": "complete"}],
        results={
            "skill_results": [
                {"skill_name": "Meeting Summary", "output_markdown": "Summary"},
                {"skill_name": "Action Items", "output_json": [{"text": "Send notes"}]},
                {"skill_name": "Decision Log", "output_json": ["Ship beta"]},
                {"skill_name": "Meeting Follow-up Email", "output_markdown": "Email body"},
            ],
            "action_logs": [{"action_type": "email", "status": "fired"}],
        },
        send_email=True,
    )

    assert report["passed"] is True
    assert report["job_id"] == "job-1"
    assert report["email_action_status"] == "fired"
```

- [ ] **Step 6: Run report test to verify failure**

Run:

```bash
cd pipeline
uv run pytest tests/test_team_meeting_validator.py::test_build_report_marks_success_when_results_and_email_log_exist -v
```

Expected: FAIL because `build_report` is missing.

- [ ] **Step 7: Implement report builder and polling loop**

Append to `pipeline/tests/e2e/sg_validate_team_meeting.py`:

```python
EXPECTED_SKILLS = {
    "Meeting Summary",
    "Action Items",
    "Decision Log",
    "Meeting Follow-up Email",
}


def build_report(
    job_id: str,
    file_id: str,
    mode_id: str,
    timeline: list[dict],
    results: dict,
    send_email: bool,
) -> dict:
    skill_results = results.get("skill_results", [])
    action_logs = results.get("action_logs", [])
    skill_names = {row.get("skill_name") for row in skill_results}
    email_logs = [row for row in action_logs if row.get("action_type") == "email"]
    email_status = email_logs[-1].get("status") if email_logs else None
    skills_present = EXPECTED_SKILLS.issubset(skill_names)
    non_empty_outputs = all(
        row.get("output_markdown") or row.get("output_json")
        for row in skill_results
        if row.get("skill_name") in EXPECTED_SKILLS
    )
    email_ok = email_status == "fired" if send_email else True
    return {
        "passed": bool(skills_present and non_empty_outputs and email_ok),
        "job_id": job_id,
        "drive_file_id": file_id,
        "mode_id": mode_id,
        "timeline": timeline,
        "skill_results": skill_results,
        "action_logs": action_logs,
        "email_action_status": email_status,
    }


def poll_job(config: ValidationConfig, job_id: str, mode_id: str) -> dict:
    timeline: list[dict] = []
    deadline = time.time() + 60 * 120
    while time.time() < deadline:
        job_resp = httpx.get(f"{config.server_url}/jobs/{job_id}", timeout=30)
        job_resp.raise_for_status()
        job = job_resp.json()
        status = job["status"]
        timeline.append({"status": status, "checkpoint": job.get("checkpoint")})
        if status == "awaiting_plan_confirmation":
            plan = job.get("plan") or {}
            approved_steps = plan.get("approved_steps") or [
                "speaker_assignment",
                "Meeting Summary",
                "Action Items",
                "Decision Log",
                "Meeting Follow-up Email",
                "email:meeting_attendees",
            ]
            confirm = httpx.post(
                f"{config.server_url}/jobs/{job_id}/confirm",
                json={"approved_steps": approved_steps, "per_step_overrides": {}},
                timeout=30,
            )
            confirm.raise_for_status()
        elif status in {"awaiting_checkpoint", "awaiting_skill_review"}:
            checkpoint = job.get("checkpoint") or {}
            data = {"approved": True} if status == "awaiting_skill_review" else checkpoint_response(
                checkpoint,
                speakers=config.speakers,
                send_email=config.send_email,
            )
            response = httpx.post(
                f"{config.server_url}/jobs/{job_id}/checkpoint",
                json={"data": data},
                timeout=30,
            )
            response.raise_for_status()
        elif status == "complete":
            results_resp = httpx.get(f"{config.server_url}/jobs/{job_id}/results", timeout=30)
            results_resp.raise_for_status()
            return build_report(job_id, config.file_id, mode_id, timeline, results_resp.json(), config.send_email)
        elif status == "failed":
            return {
                "passed": False,
                "job_id": job_id,
                "drive_file_id": config.file_id,
                "mode_id": mode_id,
                "timeline": timeline,
                "error": job.get("error"),
            }
        time.sleep(5)
    return {
        "passed": False,
        "job_id": job_id,
        "drive_file_id": config.file_id,
        "mode_id": mode_id,
        "timeline": timeline,
        "error": "Timed out waiting for job completion",
    }
```

- [ ] **Step 8: Run validator tests**

Run:

```bash
cd pipeline
uv run pytest tests/test_team_meeting_validator.py -v
```

Expected: PASS.

- [ ] **Step 9: Commit Task 4**

```bash
git add pipeline/tests/e2e/sg_validate_team_meeting.py pipeline/tests/test_team_meeting_validator.py
git commit -m "Add Team Meeting validator polling"
```

---

## Task 5: Validator CLI Entrypoint

**Files:**
- Modify: `pipeline/tests/e2e/sg_validate_team_meeting.py`
- Modify: `pipeline/tests/test_team_meeting_validator.py`

- [ ] **Step 1: Write failing test for argument parsing**

Append to `pipeline/tests/test_team_meeting_validator.py`:

```python
def test_parse_args_collects_attendees_and_speakers():
    from tests.e2e.sg_validate_team_meeting import parse_args

    cfg = parse_args([
        "--file-id", "drive-1",
        "--attendee", "alice@example.com",
        "--attendee", "bob@example.com",
        "--speaker", "A=Alice",
        "--send-email",
        "--out", "/tmp/report.json",
    ])

    assert cfg.file_id == "drive-1"
    assert cfg.attendees == ["alice@example.com", "bob@example.com"]
    assert cfg.speakers == {"A": "Alice"}
    assert cfg.send_email is True
    assert str(cfg.out_path) == "/tmp/report.json"
```

- [ ] **Step 2: Run parse test to verify failure**

Run:

```bash
cd pipeline
uv run pytest tests/test_team_meeting_validator.py::test_parse_args_collects_attendees_and_speakers -v
```

Expected: FAIL because `parse_args` is missing.

- [ ] **Step 3: Implement parse_args and main**

Append to `pipeline/tests/e2e/sg_validate_team_meeting.py`:

```python
def _parse_speaker(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--speaker must use LABEL=Name, for example A=Alice")
    label, name = value.split("=", 1)
    if not label.strip() or not name.strip():
        raise argparse.ArgumentTypeError("--speaker label and name must be non-empty")
    return label.strip(), name.strip()


def parse_args(argv: list[str] | None = None) -> ValidationConfig:
    parser = argparse.ArgumentParser(description="Validate the real Team Meeting Hermes pipeline locally.")
    parser.add_argument("--file-id", required=True)
    parser.add_argument("--server-url", default="http://localhost:8080")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--attendee", action="append", default=[])
    parser.add_argument("--send-email", action="store_true")
    parser.add_argument("--speaker", action="append", type=_parse_speaker, default=[])
    parser.add_argument("--out", default="/tmp/sg-team-meeting-e2e.json")
    args = parser.parse_args(argv)
    load_dotenv(Path(args.env_file))
    return ValidationConfig(
        file_id=args.file_id,
        server_url=args.server_url.rstrip("/"),
        attendees=args.attendee,
        send_email=args.send_email,
        speakers=dict(args.speaker),
        out_path=Path(args.out),
    )


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv)
    preflight(config)
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    mode_id, user_id = ensure_team_meeting_mode(db, config.attendees)
    create_resp = httpx.post(
        f"{config.server_url}/jobs",
        json={"drive_file_id": config.file_id, "mode_id": mode_id, "user_id": user_id},
        timeout=30,
    )
    create_resp.raise_for_status()
    job_id = create_resp.json()["job_id"]
    report = poll_job(config, job_id, mode_id)
    config.out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run parse and validator tests**

Run:

```bash
cd pipeline
uv run pytest tests/test_team_meeting_validator.py -v
```

Expected: PASS.

- [ ] **Step 5: Run all pipeline tests**

Run:

```bash
cd pipeline
uv run pytest tests -v
```

Expected: PASS.

- [ ] **Step 6: Commit Task 5**

```bash
git add pipeline/tests/e2e/sg_validate_team_meeting.py pipeline/tests/test_team_meeting_validator.py
git commit -m "Add Team Meeting validator CLI"
```

---

## Task 6: Manual Runbook Entry

**Files:**
- Modify: `RUNBOOK.md`

- [ ] **Step 1: Add a concise manual validation section**

Append to `RUNBOOK.md`:

````markdown
## Team Meeting Pipeline E2E Validation

This validation path runs outside the mobile app but exercises the real FastAPI,
Hermes, Supabase, Google Drive, and SMTP email path.

Prerequisites:

- `pipeline/.env` contains Supabase, Google, Hermes, and SMTP variables.
- The Google Drive audio file is shared with the service-account email.
- The local FastAPI server is running.

Start the server:

```bash
cd pipeline
uv run uvicorn main:app --port 8080
```

Run the validator:

```bash
uv run python tests/e2e/sg_validate_team_meeting.py \
  --file-id <drive_file_id> \
  --server-url http://localhost:8080 \
  --attendee your-test-email@example.com \
  --send-email \
  --out /tmp/sg-team-meeting-e2e.json
```

Expected success:

- the Supabase job reaches `complete`
- Team Meeting skill results are present
- the email action log is `fired`
- the test recipient receives the email
- `/tmp/sg-team-meeting-e2e.json` contains the status timeline and results
````

- [ ] **Step 2: Run docs check and pipeline tests**

Run:

```bash
cd pipeline
uv run pytest tests -v
```

Expected: PASS.

- [ ] **Step 3: Commit Task 6**

```bash
git add RUNBOOK.md
git commit -m "Document Team Meeting E2E validation"
```

---

## Final Verification

- [ ] **Step 1: Run full pipeline tests**

```bash
cd pipeline
uv run pytest tests
```

Expected: PASS.

- [ ] **Step 2: Run Flutter tests if this branch already includes Flutter changes**

```bash
flutter test
```

Expected: PASS. If Flutter tooling is unavailable, record the exact failure.

- [ ] **Step 3: Check worktree**

```bash
git status --short
```

Expected: no unstaged changes after final commits.

---

## Manual E2E Verification Command

Run only when real credentials and a shared Drive file are available:

```bash
cd pipeline
uv run uvicorn main:app --port 8080
uv run python tests/e2e/sg_validate_team_meeting.py \
  --file-id <drive_file_id> \
  --server-url http://localhost:8080 \
  --attendee your-test-email@example.com \
  --speaker A=Alice \
  --speaker B=Bob \
  --send-email \
  --out /tmp/sg-team-meeting-e2e.json
```

Expected: the command exits `0`, writes `/tmp/sg-team-meeting-e2e.json`, and the attendee inbox receives the Team Meeting follow-up email.
