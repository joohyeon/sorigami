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
    with patch("subprocess.Popen") as mock_popen, \
         patch("builtins.open", MagicMock()), \
         patch("threading.Thread") as mock_thread:
        mock_proc = MagicMock(pid=12345)
        mock_popen.return_value = mock_proc
        mock_thread.return_value = MagicMock()
        launch_hermes("job-1", '{"job_id":"job-1"}')
    mock_popen.assert_called_once()
    cmd = mock_popen.call_args[0][0]
    assert "hermes" in cmd
    # Ensure daemon monitor thread was started
    mock_thread.assert_called_once()
    assert mock_thread.call_args.kwargs.get("daemon") is True


def test_launch_hermes_inlines_orchestrator_skill_into_prompt():
    """The orchestrator instructions must travel in the -z prompt itself.

    Hermes' -s/--skills flag only *catalogs* a skill by name (progressive
    disclosure) — it never injects the skill body into the model prompt, and it
    silently ignores a file path. So the full sg-orchestrator instructions and
    the job context must both be inlined into the -z prompt for the agent to
    actually run the pipeline.
    """
    from hermes.runner import launch_hermes
    context_json = '{"job_id":"job-1","drive_file_id":"abc123"}'
    with patch("subprocess.Popen") as mock_popen, \
         patch("builtins.open", MagicMock()), \
         patch("threading.Thread"):
        mock_popen.return_value = MagicMock(pid=12345)
        launch_hermes("job-1", context_json)
    cmd = mock_popen.call_args[0][0]
    assert "-z" in cmd
    prompt = cmd[cmd.index("-z") + 1]
    # Orchestrator skill body is present (not just the name catalog entry)
    assert "Sorigamis pipeline orchestrator" in prompt
    assert "Pipeline Stages" in prompt
    # Job context is carried in the same prompt
    assert context_json in prompt
