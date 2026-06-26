import json
from unittest.mock import patch, MagicMock
from uuid import uuid4


def test_build_context_includes_required_fields():
    from hermes.context import build_context
    job = {"id": str(uuid4()), "drive_file_id": "abc123"}
    mode = {"id": str(uuid4()), "name": "Team Meeting"}
    skills = [{"skill_name": "Summary", "ai_prompt": "Summarize this."}]
    env = {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-key",
    }
    with patch.dict("os.environ", env):
        ctx = json.loads(build_context(job, mode, skills))
    assert ctx["job_id"] == job["id"]
    assert ctx["drive_file_id"] == "abc123"
    assert ctx["mode_name"] == "Team Meeting"
    assert len(ctx["skills"]) == 1


def test_launch_hermes_spawns_subprocess():
    from hermes.runner import launch_hermes
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = MagicMock(pid=12345)
        launch_hermes("job-1", '{"job_id":"job-1"}')
    mock_popen.assert_called_once()
    cmd = mock_popen.call_args[0][0]
    assert "hermes" in cmd
    assert "-s" in cmd
    assert "sg-orchestrator" in cmd
