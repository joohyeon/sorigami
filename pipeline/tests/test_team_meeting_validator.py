import importlib
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest


PIPELINE_ROOT = Path(__file__).resolve().parents[1]


def test_load_dotenv_sets_environment_and_returns_loaded_values(tmp_path, monkeypatch):
    from tests.e2e.sg_validate_team_meeting import load_dotenv

    env_file = tmp_path / ".env"
    env_file.write_text(
        """
        # comment
        SUPABASE_URL=https://example.supabase.co
        SUPABASE_SERVICE_ROLE_KEY='service-role'
        SMTP_HOST="smtp.example.com"

        NO_EQUALS
        SMTP_PORT=2525
        """,
        encoding="utf-8",
    )
    for key in [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SMTP_HOST",
        "SMTP_PORT",
    ]:
        monkeypatch.delenv(key, raising=False)

    loaded = load_dotenv(env_file)

    assert loaded == {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "service-role",
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "2525",
    }
    assert os.environ["SUPABASE_SERVICE_ROLE_KEY"] == "service-role"


def test_preflight_requires_full_base_environment(monkeypatch):
    from tests.e2e.sg_validate_team_meeting import ValidationConfig, preflight

    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role")
    for key in ["GOOGLE_SERVICE_ACCOUNT_JSON", "HERMES_PROVIDER", "HERMES_MODEL"]:
        monkeypatch.delenv(key, raising=False)

    config = ValidationConfig(
        file_id="drive-file",
        server_url="http://localhost:8080",
        attendees=[],
        user_email="sorigamis-e2e@example.com",
        send_email=False,
        speakers=[],
        out_path=None,
    )

    class HealthResponse:
        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        "tests.e2e.sg_validate_team_meeting.httpx.get",
        lambda url, timeout: HealthResponse(),
    )

    with pytest.raises(RuntimeError) as exc:
        preflight(config)

    message = str(exc.value)
    assert "GOOGLE_SERVICE_ACCOUNT_JSON" in message
    assert "HERMES_PROVIDER" in message
    assert "HERMES_MODEL" in message


def test_preflight_requires_smtp_settings_and_attendees_when_send_email(monkeypatch):
    from tests.e2e.sg_validate_team_meeting import ValidationConfig, preflight

    for key, value in {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "service-role",
        "GOOGLE_SERVICE_ACCOUNT_JSON": "{}",
        "HERMES_PROVIDER": "openai",
        "HERMES_MODEL": "gpt-4.1",
    }.items():
        monkeypatch.setenv(key, value)
    for key in ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM"]:
        monkeypatch.delenv(key, raising=False)

    config = ValidationConfig(
        file_id="drive-file",
        server_url="http://localhost:8080",
        attendees=[],
        user_email="sorigamis-e2e@example.com",
        send_email=True,
        speakers=[],
        out_path=None,
    )

    class HealthResponse:
        def raise_for_status(self):
            return None

    def fake_get(url, timeout):
        assert url == "http://localhost:8080/health"
        assert timeout == 10
        return HealthResponse()

    monkeypatch.setattr("tests.e2e.sg_validate_team_meeting.httpx.get", fake_get)

    with pytest.raises(RuntimeError) as exc:
        preflight(config)

    message = str(exc.value)
    assert "SMTP_HOST" in message
    assert "SMTP_PORT" in message
    assert "SMTP_USERNAME" in message
    assert "SMTP_PASSWORD" in message
    assert "SMTP_FROM" in message
    assert "EMAIL_FROM" not in message
    assert "attendee" in message


def test_validator_import_does_not_require_supabase_create_client(monkeypatch):
    monkeypatch.setitem(sys.modules, "supabase", SimpleNamespace())
    sys.modules.pop("tests.e2e.sg_validate_team_meeting", None)

    module = importlib.import_module("tests.e2e.sg_validate_team_meeting")

    assert module.BASE_ENV


def test_parse_args_collects_attendees_and_speaker_mappings(tmp_path, monkeypatch):
    from tests.e2e.sg_validate_team_meeting import parse_args

    env_file = tmp_path / ".env"
    out_path = tmp_path / "report.json"
    loaded_paths = []
    monkeypatch.setattr(
        "tests.e2e.sg_validate_team_meeting.load_dotenv",
        lambda path: loaded_paths.append(path),
    )

    config = parse_args(
        [
            "--file-id",
            "drive-1",
            "--env-file",
            str(env_file),
            "--attendee",
            "alice@example.com",
            "--attendee",
            "bob@example.com",
            "--user-email",
            "team-meeting-e2e@example.com",
            "--speaker",
            "A=Alice",
            "--send-email",
            "--out",
            str(out_path),
        ]
    )

    assert config.file_id == "drive-1"
    assert config.attendees == ["alice@example.com", "bob@example.com"]
    assert config.user_email == "team-meeting-e2e@example.com"
    assert config.speakers == [("A", "Alice")]
    assert config.send_email is True
    assert config.out_path == out_path
    assert loaded_paths == [env_file]


def test_parse_args_defaults_to_namespaced_e2e_user_email(monkeypatch):
    from tests.e2e.sg_validate_team_meeting import parse_args

    monkeypatch.setattr("tests.e2e.sg_validate_team_meeting.load_dotenv", lambda path: None)

    config = parse_args(["--file-id", "drive-1"])

    assert config.user_email == "sorigamis-e2e@example.com"


def test_parse_args_default_out_path_is_random_json(monkeypatch):
    from tests.e2e.sg_validate_team_meeting import parse_args

    monkeypatch.setattr("tests.e2e.sg_validate_team_meeting.load_dotenv", lambda path: None)

    first = parse_args(["--file-id", "drive-1"])
    second = parse_args(["--file-id", "drive-1"])

    assert first.out_path != Path("/tmp/sg-team-meeting-e2e.json")
    assert first.out_path != second.out_path
    assert first.out_path.suffix == ".json"
    assert second.out_path.suffix == ".json"


def test_write_report_uses_owner_only_permissions(tmp_path):
    from tests.e2e.sg_validate_team_meeting import write_report

    out_path = tmp_path / "report.json"

    write_report(out_path, {"passed": False, "error": "boom"})

    assert json.loads(out_path.read_text(encoding="utf-8")) == {
        "passed": False,
        "error": "boom",
    }
    if hasattr(os, "stat"):
        assert out_path.stat().st_mode & 0o777 == 0o600


def test_write_report_exclusive_refuses_to_overwrite_existing_file(tmp_path):
    from tests.e2e.sg_validate_team_meeting import write_report

    out_path = tmp_path / "report.json"
    out_path.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError):
        write_report(out_path, {"passed": False}, exclusive=True)

    assert out_path.read_text(encoding="utf-8") == "existing"


def test_main_writes_report_and_returns_zero_when_report_passed(
    tmp_path, monkeypatch, capsys
):
    from tests.e2e import sg_validate_team_meeting as validator

    out_path = tmp_path / "report.json"
    calls = []

    class FakeResponse:
        def raise_for_status(self):
            calls.append(("raise_for_status",))

        def json(self):
            return {"job_id": "job-1"}

    monkeypatch.setattr(validator, "load_dotenv", lambda path: calls.append(("env", path)))
    monkeypatch.setattr(validator, "preflight", lambda config: calls.append(("preflight", config)))
    monkeypatch.setattr(
        validator,
        "create_client",
        lambda url, key: calls.append(("create_client", url, key)) or "db",
    )
    monkeypatch.setattr(
        validator,
        "ensure_team_meeting_mode",
        lambda db, attendees, user_email: calls.append(("ensure_mode", db, attendees, user_email))
        or ("mode-1", "user-1"),
    )
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role")
    monkeypatch.setattr(
        validator.httpx,
        "post",
        lambda url, json, timeout: calls.append(("post", url, json, timeout))
        or FakeResponse(),
    )
    monkeypatch.setattr(
        validator,
        "poll_job",
        lambda config, job_id, mode_id: calls.append(("poll", job_id, mode_id))
        or {"passed": True, "job_id": job_id, "mode_id": mode_id},
    )

    result = validator.main(
        [
            "--file-id",
            "drive-1",
            "--server-url",
            "http://validator.test/",
            "--attendee",
            "alice@example.com",
            "--user-email",
            "team-meeting-e2e@example.com",
            "--out",
            str(out_path),
        ]
    )

    assert result == 0
    assert json.loads(out_path.read_text(encoding="utf-8")) == {
        "passed": True,
        "job_id": "job-1",
        "mode_id": "mode-1",
    }
    assert json.loads(capsys.readouterr().out) == {
        "passed": True,
        "job_id": "job-1",
        "mode_id": "mode-1",
    }
    assert (
        "post",
        "http://validator.test/jobs",
        {
            "drive_file_id": "drive-1",
            "mode_id": "mode-1",
            "user_id": "user-1",
        },
        30,
    ) in calls
    assert ("ensure_mode", "db", ["alice@example.com"], "team-meeting-e2e@example.com") in calls


def test_main_returns_one_when_report_failed(tmp_path, monkeypatch):
    from tests.e2e import sg_validate_team_meeting as validator

    out_path = tmp_path / "report.json"

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"job_id": "job-1"}

    monkeypatch.setattr(validator, "load_dotenv", lambda path: None)
    monkeypatch.setattr(validator, "preflight", lambda config: None)
    monkeypatch.setattr(validator, "create_client", lambda url, key: "db")
    monkeypatch.setattr(
        validator,
        "ensure_team_meeting_mode",
        lambda db, attendees, user_email: ("mode-1", "user-1"),
    )
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role")
    monkeypatch.setattr(validator.httpx, "post", lambda url, json, timeout: FakeResponse())
    monkeypatch.setattr(
        validator,
        "poll_job",
        lambda config, job_id, mode_id: {"passed": False, "job_id": job_id},
    )

    result = validator.main(["--file-id", "drive-1", "--out", str(out_path)])

    assert result == 1


def test_main_writes_failure_report_when_poll_job_raises(tmp_path, monkeypatch):
    from tests.e2e import sg_validate_team_meeting as validator

    out_path = tmp_path / "report.json"

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"job_id": "job-1"}

    monkeypatch.setattr(validator, "load_dotenv", lambda path: None)
    monkeypatch.setattr(validator, "preflight", lambda config: None)
    monkeypatch.setattr(validator, "create_client", lambda url, key: "db")
    monkeypatch.setattr(
        validator,
        "ensure_team_meeting_mode",
        lambda db, attendees, user_email: ("mode-1", "user-1"),
    )
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role")
    monkeypatch.setattr(validator.httpx, "post", lambda url, json, timeout: FakeResponse())

    def raise_poll_job(config, job_id, mode_id):
        raise RuntimeError("poll failed\nwith detail")

    monkeypatch.setattr(validator, "poll_job", raise_poll_job)

    result = validator.main(["--file-id", "drive-1", "--out", str(out_path)])

    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert result == 1
    assert report["passed"] is False
    assert report["drive_file_id"] == "drive-1"
    assert report["error"] == "RuntimeError: poll failed with detail"


def test_main_failure_report_redacts_secret_from_exception(
    tmp_path, monkeypatch, capsys
):
    from tests.e2e import sg_validate_team_meeting as validator

    out_path = tmp_path / "report.json"
    secret = "service-role-secret"

    monkeypatch.setattr(validator, "load_dotenv", lambda path: None)
    monkeypatch.setattr(validator, "preflight", lambda config: None)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", secret)

    def raise_create_client():
        raise RuntimeError(f"auth failed for {secret}\nretry denied")

    monkeypatch.setattr(validator, "_create_supabase_client", raise_create_client)

    result = validator.main(["--file-id", "drive-1", "--out", str(out_path)])

    report = json.loads(out_path.read_text(encoding="utf-8"))
    stdout_report = json.loads(capsys.readouterr().out)
    assert result == 1
    assert secret not in report["error"]
    assert secret not in stdout_report["error"]
    assert "[redacted]" in report["error"]
    assert "\n" not in report["error"]


class FakeTableQuery:
    def __init__(self, db, table_name):
        self.db = db
        self.table_name = table_name
        self.operation = None
        self.payload = None
        self.filters = []

    def select(self, columns):
        self.operation = "select"
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = payload
        return self

    def update(self, payload):
        self.operation = "update"
        self.payload = payload
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def is_(self, key, value):
        self.filters.append((key, None if value == "null" else value))
        return self

    def execute(self):
        rows = self.db.rows[self.table_name]
        if self.operation == "select":
            return SimpleNamespace(data=[row for row in rows if self._matches(row)])
        if self.operation == "insert":
            row = {"id": str(uuid4()), **self.payload}
            rows.append(row)
            self.db.inserts.append((self.table_name, row))
            return SimpleNamespace(data=[row])
        if self.operation == "update":
            updated = []
            for row in rows:
                if self._matches(row):
                    row.update(self.payload)
                    updated.append(row)
                    self.db.updates.append((self.table_name, row.copy()))
            return SimpleNamespace(data=updated)
        raise AssertionError(f"Unsupported operation {self.operation}")

    def _matches(self, row):
        return all(row.get(key) == value for key, value in self.filters)


class FakeSupabase:
    def __init__(self, skills=None, modes=None, admin=None):
        self.rows = {
            "sg_skills": skills if skills is not None else [],
            "sg_modes": modes if modes is not None else [],
        }
        self.inserts = []
        self.updates = []
        self.auth = SimpleNamespace(admin=admin or FakeAuthAdmin())

    def table(self, table_name):
        return FakeTableQuery(self, table_name)


class FakeAuthAdmin:
    def __init__(self, users=None):
        self.users = users if users is not None else []
        self.created_users = []

    def list_users(self):
        return self.users

    def create_user(self, payload):
        self.created_users.append(payload)
        return SimpleNamespace(user=SimpleNamespace(id=str(uuid4())))


def test_ensure_team_meeting_mode_seeds_user_owned_email_skill_with_attendees():
    from tests.e2e.sg_validate_team_meeting import ensure_team_meeting_mode

    selected_user_id = str(uuid4())
    db = FakeSupabase(
        skills=[
            {
                "id": str(uuid4()),
                "user_id": selected_user_id,
                "name": "Meeting Summary",
                "description": "stale",
                "ai_prompt": "stale",
                "integration_actions": [{"type": "webhook"}],
                "is_default": False,
                "require_review": True,
            }
        ],
        admin=FakeAuthAdmin(
            users=[
                SimpleNamespace(
                    id=selected_user_id,
                    email="sorigamis-e2e@example.com",
                )
            ]
        ),
    )
    attendees = ["alice@example.com", "bob@example.com"]

    mode_id, user_id = ensure_team_meeting_mode(db, attendees)

    assert mode_id
    assert user_id

    skills_by_name = {row["name"]: row for row in db.rows["sg_skills"]}
    assert list(skills_by_name) == [
        "Meeting Summary",
        "Action Items",
        "Decision Log",
        "Meeting Follow-up Email",
    ]

    for name in ["Meeting Summary", "Action Items", "Decision Log"]:
        assert skills_by_name[name]["user_id"] == selected_user_id
        assert skills_by_name[name]["is_default"] is False
        assert skills_by_name[name]["integration_actions"] == []

    assert skills_by_name["Meeting Summary"]["description"] != "stale"
    assert any(
        table == "sg_skills" and row["name"] == "Meeting Summary"
        for table, row in db.updates
    )

    email_skill = skills_by_name["Meeting Follow-up Email"]
    assert email_skill["user_id"] == selected_user_id
    assert email_skill["is_default"] is False
    assert email_skill["require_review"] is True
    assert email_skill["integration_actions"] == [
        {
            "type": "email",
            "destination": "meeting_attendees",
            "config": {
                "recipients": attendees,
                "subject": "Team Meeting follow-up",
            },
        }
    ]

    mode = db.rows["sg_modes"][0]
    assert mode["name"] == "Team Meeting"
    assert mode["user_id"] == user_id
    assert mode["skill_ids"] == [skills_by_name[name]["id"] for name in skills_by_name]


def test_ensure_team_meeting_mode_ignores_arbitrary_admin_users_when_email_does_not_match():
    from tests.e2e.sg_validate_team_meeting import ensure_team_meeting_mode

    arbitrary_user_id = str(uuid4())
    db = FakeSupabase()
    db.auth.admin = FakeAuthAdmin(
        users=SimpleNamespace(
            data=[SimpleNamespace(id=arbitrary_user_id, email="real-user@example.com")]
        )
    )

    mode_id, user_id = ensure_team_meeting_mode(
        db,
        attendees=[],
        user_email="sorigamis-e2e@example.com",
    )

    assert mode_id
    assert user_id != arbitrary_user_id
    assert db.auth.admin.created_users == [
        {
            "email": "sorigamis-e2e@example.com",
            "password": db.auth.admin.created_users[0]["password"],
            "email_confirm": True,
        }
    ]


def test_ensure_team_meeting_mode_reuses_matching_e2e_user_from_nested_wrapper():
    from tests.e2e.sg_validate_team_meeting import ensure_team_meeting_mode

    arbitrary_user_id = str(uuid4())
    e2e_user_id = str(uuid4())
    db = FakeSupabase()
    db.auth.admin = FakeAuthAdmin(
        users=SimpleNamespace(
            data=SimpleNamespace(
                users=[
                    {"id": arbitrary_user_id, "email": "real-user@example.com"},
                    {"id": e2e_user_id, "email": "sorigamis-e2e@example.com"},
                ]
            )
        )
    )

    mode_id, user_id = ensure_team_meeting_mode(
        db,
        attendees=[],
        user_email="sorigamis-e2e@example.com",
    )

    assert mode_id
    assert user_id == e2e_user_id
    assert db.auth.admin.created_users == []


def test_ensure_team_meeting_mode_ignores_same_name_skill_for_another_user():
    from tests.e2e.sg_validate_team_meeting import ensure_team_meeting_mode

    selected_user_id = str(uuid4())
    other_user_id = str(uuid4())
    other_user_action_items_id = str(uuid4())
    db = FakeSupabase(
        skills=[
            {
                "id": other_user_action_items_id,
                "user_id": other_user_id,
                "name": "Action Items",
                "description": "user-owned",
                "ai_prompt": "do not touch",
                "integration_actions": [{"type": "slack"}],
                "is_default": False,
                "require_review": False,
            }
        ],
        admin=FakeAuthAdmin(
            users=[
                SimpleNamespace(
                    id=selected_user_id,
                    email="sorigamis-e2e@example.com",
                )
            ]
        ),
    )

    _, user_id = ensure_team_meeting_mode(db, attendees=[])

    assert user_id == selected_user_id
    action_items = [
        row for row in db.rows["sg_skills"] if row["name"] == "Action Items"
    ]
    assert len(action_items) == 2
    other_user_owned = next(
        row for row in action_items if row["id"] == other_user_action_items_id
    )
    selected_user_seeded = next(
        row for row in action_items if row["id"] != other_user_action_items_id
    )
    assert other_user_owned["user_id"] == other_user_id
    assert other_user_owned["is_default"] is False
    assert other_user_owned["ai_prompt"] == "do not touch"
    assert selected_user_seeded["user_id"] == selected_user_id
    assert selected_user_seeded["is_default"] is False


def test_ensure_team_meeting_mode_scopes_mode_lookup_to_selected_user():
    from tests.e2e.sg_validate_team_meeting import ensure_team_meeting_mode

    selected_user_id = str(uuid4())
    other_user_id = str(uuid4())
    other_mode_id = str(uuid4())
    db = FakeSupabase(
        modes=[
            {
                "id": other_mode_id,
                "name": "Team Meeting",
                "user_id": other_user_id,
                "skill_ids": ["existing-skill"],
            }
        ],
        admin=FakeAuthAdmin(
            users=[
                SimpleNamespace(
                    id=selected_user_id,
                    email="sorigamis-e2e@example.com",
                )
            ]
        ),
    )

    mode_id, user_id = ensure_team_meeting_mode(db, attendees=[])

    assert user_id == selected_user_id
    assert mode_id != other_mode_id
    other_mode = next(row for row in db.rows["sg_modes"] if row["id"] == other_mode_id)
    selected_mode = next(row for row in db.rows["sg_modes"] if row["id"] == mode_id)
    assert other_mode["skill_ids"] == ["existing-skill"]
    assert selected_mode["user_id"] == selected_user_id


def test_pipeline_migration_adds_require_review_column():
    migration = (
        PIPELINE_ROOT
        / "supabase"
        / "migrations"
        / "20260627000000_require_review.sql"
    )

    assert migration.exists()
    sql = migration.read_text(encoding="utf-8").lower()
    assert "alter table sg_skills" in sql
    assert "require_review" in sql


def test_checkpoint_response_maps_speaker_labels_with_participant_fallback():
    from tests.e2e.sg_validate_team_meeting import checkpoint_response

    response = checkpoint_response(
        {
            "type": "speaker_assignment",
            "speakers": [
                {"id": "speaker-1", "label": "SPEAKER_00"},
                {"id": "speaker-2", "label": "SPEAKER_01"},
                {"id": "speaker-3", "label": "SPEAKER_02"},
            ],
        },
        speakers={"SPEAKER_00": "Alice", "SPEAKER_02": "Carol"},
        send_email=False,
    )

    assert response == {
        "speakers": [
            {"id": "speaker-1", "confirmed_name": "Alice"},
            {"id": "speaker-2", "confirmed_name": "Participant SPEAKER_01"},
            {"id": "speaker-3", "confirmed_name": "Carol"},
        ]
    }


def test_checkpoint_response_only_approves_email_action_when_send_email_enabled():
    from tests.e2e.sg_validate_team_meeting import checkpoint_response

    email_checkpoint = {"type": "action_confirmation", "action": {"type": "email"}}
    flat_email_checkpoint = {"type": "action_confirmation", "action_type": "email"}
    webhook_checkpoint = {"type": "action_confirmation", "action": {"type": "webhook"}}

    assert checkpoint_response(email_checkpoint, speakers={}, send_email=True) == {
        "approved": True
    }
    assert checkpoint_response(flat_email_checkpoint, speakers={}, send_email=True) == {
        "approved": True
    }
    assert checkpoint_response(email_checkpoint, speakers={}, send_email=False) == {
        "skipped": True
    }
    assert checkpoint_response(flat_email_checkpoint, speakers={}, send_email=False) == {
        "skipped": True
    }
    assert checkpoint_response(webhook_checkpoint, speakers={}, send_email=True) == {
        "skipped": True
    }


def test_checkpoint_response_skips_unknown_checkpoint_types():
    from tests.e2e.sg_validate_team_meeting import checkpoint_response

    assert checkpoint_response(
        {"type": "new_unknown_checkpoint"},
        speakers={},
        send_email=True,
    ) == {"skipped": True}


def _skill_result(name, output="done"):
    return {"skill_name": name, "output_markdown": output}


def test_build_report_passes_when_expected_skills_exist_and_email_action_fired():
    from tests.e2e.sg_validate_team_meeting import EXPECTED_SKILLS, build_report

    results = {
        "skill_results": [_skill_result(name) for name in EXPECTED_SKILLS],
        "action_logs": [
            {
                "action_type": "email",
                "status": "fired",
                "destination": "meeting_attendees",
            }
        ],
    }

    report = build_report(
        job_id="job-1",
        file_id="drive-file",
        mode_id="mode-1",
        timeline=[{"status": "submitted"}],
        results=results,
        send_email=True,
    )

    assert report["passed"] is True
    assert report["job_id"] == "job-1"
    assert report["drive_file_id"] == "drive-file"
    assert report["mode_id"] == "mode-1"
    assert report["timeline"] == [{"status": "submitted"}]
    assert report["skill_results"] == results["skill_results"]
    assert report["action_logs"] == results["action_logs"]
    assert report["email_action_status"] == "fired"


def test_poll_job_completes_after_confirming_plan_and_checkpoints(monkeypatch):
    from tests.e2e.sg_validate_team_meeting import (
        EXPECTED_SKILLS,
        ValidationConfig,
        poll_job,
    )

    config = ValidationConfig(
        file_id="drive-file",
        server_url="http://validator.test",
        attendees=[],
        user_email="sorigamis-e2e@example.com",
        send_email=True,
        speakers=["SPEAKER_00=Alice"],
        out_path=None,
    )
    responses = [
        {
            "job_id": "job-1",
            "status": "awaiting_plan_confirmation",
            "plan": {"approved_steps": ["speaker_assignment", "Meeting Summary"]},
        },
        {
            "job_id": "job-1",
            "status": "awaiting_checkpoint",
            "checkpoint": {
                "type": "speaker_assignment",
                "speakers": [{"id": "s1", "label": "SPEAKER_00"}],
            },
        },
        {
            "job_id": "job-1",
            "status": "awaiting_skill_review",
            "checkpoint": {"type": "skill_review"},
        },
        {"job_id": "job-1", "status": "complete"},
    ]
    calls = []

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            calls.append(("raise", self.payload))

        def json(self):
            return self.payload

    def fake_get(url, timeout):
        calls.append(("get", url, timeout))
        if url.endswith("/results"):
            return FakeResponse(
                {
                    "skill_results": [_skill_result(name) for name in EXPECTED_SKILLS],
                    "action_logs": [{"action_type": "email", "status": "fired"}],
                }
            )
        return FakeResponse(responses.pop(0))

    def fake_post(url, json, timeout):
        calls.append(("post", url, json, timeout))
        return FakeResponse({"ok": True})

    monkeypatch.setattr("tests.e2e.sg_validate_team_meeting.httpx.get", fake_get)
    monkeypatch.setattr("tests.e2e.sg_validate_team_meeting.httpx.post", fake_post)
    monkeypatch.setattr("tests.e2e.sg_validate_team_meeting.time.sleep", lambda _: None)

    report = poll_job(config, job_id="job-1", mode_id="mode-1")

    assert report["passed"] is True
    assert [entry["status"] for entry in report["timeline"]] == [
        "awaiting_plan_confirmation",
        "awaiting_checkpoint",
        "awaiting_skill_review",
        "complete",
    ]
    assert (
        "post",
        "http://validator.test/jobs/job-1/confirm",
        {"approved_steps": ["speaker_assignment", "Meeting Summary"], "per_step_overrides": {}},
        30,
    ) in calls
    assert (
        "post",
        "http://validator.test/jobs/job-1/checkpoint",
        {"data": {"speakers": [{"id": "s1", "confirmed_name": "Alice"}]}},
        30,
    ) in calls
    assert (
        "post",
        "http://validator.test/jobs/job-1/checkpoint",
        {"data": {"approved": True}},
        30,
    ) in calls


def test_poll_job_returns_failed_report_on_job_failure(monkeypatch):
    from tests.e2e.sg_validate_team_meeting import ValidationConfig, poll_job

    config = ValidationConfig(
        file_id="drive-file",
        server_url="http://validator.test",
        attendees=[],
        user_email="sorigamis-e2e@example.com",
        send_email=False,
        speakers=[],
        out_path=None,
    )

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"job_id": "job-1", "status": "failed", "error": "boom"}

    monkeypatch.setattr(
        "tests.e2e.sg_validate_team_meeting.httpx.get",
        lambda url, timeout: FakeResponse(),
    )

    report = poll_job(config, job_id="job-1", mode_id="mode-1")

    assert report["passed"] is False
    assert report["error"] == "boom"
    assert report["timeline"] == [{"status": "failed", "checkpoint": None}]


def test_poll_job_redacts_secret_from_failed_job_error(monkeypatch):
    from tests.e2e.sg_validate_team_meeting import ValidationConfig, poll_job

    secret = "super-secret"
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", secret)

    config = ValidationConfig(
        file_id="drive-file",
        server_url="http://validator.test",
        attendees=[],
        user_email="sorigamis-e2e@example.com",
        send_email=False,
        speakers=[],
        out_path=None,
    )

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "job_id": "job-1",
                "status": "failed",
                "error": f"pipeline failed with {secret}",
            }

    monkeypatch.setattr(
        "tests.e2e.sg_validate_team_meeting.httpx.get",
        lambda url, timeout: FakeResponse(),
    )

    report = poll_job(config, job_id="job-1", mode_id="mode-1")

    assert report["passed"] is False
    assert secret not in report["error"]
    assert "[redacted]" in report["error"]


def test_poll_job_does_not_sleep_after_final_timeout_attempt(monkeypatch):
    from tests.e2e.sg_validate_team_meeting import ValidationConfig, poll_job

    config = ValidationConfig(
        file_id="drive-file",
        server_url="http://validator.test",
        attendees=[],
        user_email="sorigamis-e2e@example.com",
        send_email=False,
        speakers=[],
        out_path=None,
    )
    sleeps = []
    poll_count = 0

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            nonlocal poll_count
            poll_count += 1
            return {"job_id": "job-1", "status": "executing"}

    monkeypatch.setattr(
        "tests.e2e.sg_validate_team_meeting.httpx.get",
        lambda url, timeout: FakeResponse(),
    )
    monkeypatch.setattr(
        "tests.e2e.sg_validate_team_meeting.time.sleep",
        lambda seconds: sleeps.append(seconds),
    )

    report = poll_job(
        config,
        job_id="job-1",
        mode_id="mode-1",
        max_attempts=3,
        poll_interval=2,
    )

    assert report["passed"] is False
    assert report["error"] == "timeout"
    assert poll_count == 3
    assert sleeps == [2, 2]


def test_poll_job_default_polling_budget_is_120_minutes(monkeypatch):
    from tests.e2e.sg_validate_team_meeting import ValidationConfig, poll_job

    config = ValidationConfig(
        file_id="drive-file",
        server_url="http://validator.test",
        attendees=[],
        user_email="sorigamis-e2e@example.com",
        send_email=False,
        speakers=[],
        out_path=None,
    )
    poll_count = 0
    sleeps = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            nonlocal poll_count
            poll_count += 1
            return {"job_id": "job-1", "status": "executing"}

    monkeypatch.setattr(
        "tests.e2e.sg_validate_team_meeting.httpx.get",
        lambda url, timeout: FakeResponse(),
    )
    monkeypatch.setattr(
        "tests.e2e.sg_validate_team_meeting.time.sleep",
        lambda seconds: sleeps.append(seconds),
    )

    report = poll_job(config, job_id="job-1", mode_id="mode-1")

    assert report["passed"] is False
    assert report["error"] == "timeout"
    assert poll_count * 15 == 120 * 60
    assert sleeps == [15] * (poll_count - 1)
