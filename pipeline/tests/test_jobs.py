from uuid import uuid4
import pytest
from unittest.mock import patch, MagicMock

JOB_PAYLOAD = {
    "drive_file_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs",
    "mode_id": str(uuid4()),
    "user_id": str(uuid4()),
}


def test_create_job(client, mock_supabase):
    # Insert returns the new job row
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "abc-123", "status": "submitted", "drive_file_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"}
    ]
    # Mode lookup uses maybe_single() (changed from single())
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "id": JOB_PAYLOAD["mode_id"], "name": "Test Mode", "skill_ids": []
    }
    env = {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-key",
    }
    with patch.dict("os.environ", env), patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = MagicMock(pid=99999)
        response = client.post("/jobs", json=JOB_PAYLOAD)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "submitted"
    assert "job_id" in body


def test_get_job(client, mock_supabase):
    job_id = str(uuid4())
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "id": job_id,
        "status": "analyzing",
        "plan_json": None,
        "checkpoint_json": None,
    }
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == job_id
    assert body["status"] == "analyzing"
    assert body["plan"] is None
    assert body["checkpoint"] is None


def test_get_job_results(client, mock_supabase):
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    response = client.get("/jobs/test-job-id/results")
    assert response.status_code == 200
    body = response.json()
    assert "skill_results" in body
    assert "action_logs" in body


def test_confirm_job_not_found(client, mock_supabase):
    # confirm_job checks existence with maybe_single()
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = None
    response = client.post("/jobs/missing-id/confirm", json={"approved_steps": [], "per_step_overrides": {}})
    assert response.status_code == 404


def test_checkpoint_not_found(client, mock_supabase):
    # resolve_checkpoint checks existence with maybe_single()
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = None
    response = client.post("/jobs/missing-id/checkpoint", json={"data": {}})
    assert response.status_code == 404
