import os
from types import SimpleNamespace
from uuid import uuid4

import pytest

from tests.e2e.sg_validate_team_meeting import ValidationConfig, load_dotenv, preflight


def test_load_dotenv_sets_environment_and_returns_loaded_values(tmp_path, monkeypatch):
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


def test_preflight_requires_smtp_settings_and_attendees_when_send_email(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role")
    for key in ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "EMAIL_FROM"]:
        monkeypatch.delenv(key, raising=False)

    config = ValidationConfig(
        file_id="drive-file",
        server_url="http://localhost:8080",
        attendees=[],
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
    assert "EMAIL_FROM" in message
    assert "attendee" in message


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
    def __init__(self):
        self.rows = {
            "sg_skills": [
                {
                    "id": str(uuid4()),
                    "name": "Meeting Summary",
                    "description": "stale",
                    "ai_prompt": "stale",
                    "integration_actions": [{"type": "webhook"}],
                    "is_default": False,
                    "require_review": True,
                }
            ],
            "sg_modes": [],
        }
        self.inserts = []
        self.updates = []
        self.auth = SimpleNamespace(admin=FakeAuthAdmin())

    def table(self, table_name):
        return FakeTableQuery(self, table_name)


class FakeAuthAdmin:
    def __init__(self):
        self.created_users = []

    def list_users(self):
        return []

    def create_user(self, payload):
        self.created_users.append(payload)
        return SimpleNamespace(user=SimpleNamespace(id=str(uuid4())))


def test_ensure_team_meeting_mode_seeds_email_skill_with_attendees():
    from tests.e2e.sg_validate_team_meeting import ensure_team_meeting_mode

    db = FakeSupabase()
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
        assert skills_by_name[name]["is_default"] is True
        assert skills_by_name[name]["integration_actions"] == []

    assert skills_by_name["Meeting Summary"]["description"] != "stale"
    assert any(
        table == "sg_skills" and row["name"] == "Meeting Summary"
        for table, row in db.updates
    )

    email_skill = skills_by_name["Meeting Follow-up Email"]
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
