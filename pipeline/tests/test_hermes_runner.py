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


def _monitor_with_status(job_status: str):
    """Run runner._monitor for a process that exited 0, with the job currently in
    `job_status`, and return the list of statuses written via update_job_status."""
    from hermes import runner
    proc = MagicMock(returncode=0)
    log = MagicMock()
    client = MagicMock()
    (client.table.return_value.select.return_value.eq.return_value
     .maybe_single.return_value.execute.return_value) = MagicMock(data={"status": job_status})
    with patch("supabase_client.get_supabase", return_value=client), \
         patch("hermes.runner.update_job_status") as mock_update:
        runner._monitor(proc, "job-1", log)
    return [c.args[1] for c in mock_update.call_args_list]


def test_monitor_marks_failed_when_hermes_exits_zero_before_completion():
    # Hermes exited 0 but the orchestrator never reached `complete` → safety net fails it.
    assert "failed" in _monitor_with_status("analyzing")


def test_monitor_leaves_completed_job_untouched():
    # Orchestrator already set `complete`; the monitor must not touch it.
    assert _monitor_with_status("complete") == []


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


def test_orchestrator_prompt_contains_quality_computation():
    """The -z prompt must instruct Hermes to compute and write quality after transcription."""
    from hermes.runner import _build_prompt
    prompt = _build_prompt('{"job_id":"job-1"}')
    assert "sg_quality" in prompt
    assert "quality_json" in prompt


def test_orchestrator_prompt_contains_stage_55_skill_review():
    """The -z prompt must contain the Stage 5.5 skill review checkpoint instructions."""
    from hermes.runner import _build_prompt
    prompt = _build_prompt('{"job_id":"job-1"}')
    assert "awaiting_skill_review" in prompt
    assert "require_review" in prompt
    assert "Stage 5.5" in prompt


def test_orchestrator_prompt_contains_email_action_instructions():
    """Stage 6 must explain how Hermes confirms and fires email actions."""
    from hermes.runner import _build_prompt

    prompt = _build_prompt('{"job_id":"job-1"}')

    assert "sg_email_send" in prompt
    assert "recipients=" in prompt
    assert "send_email(to=" not in prompt
    assert "action_type\": \"email\"" in prompt
    assert "Meeting Follow-up Email" in prompt
    assert "SMTP" in prompt
    assert "plan_json.overrides" in prompt
    assert "per_step_overrides" not in prompt
    assert "send_fcm(device_token, title, body, creds_json)" in prompt
    assert "subject from the integration action config" in prompt
    assert "fallback to \"Team Meeting follow-up\"" in prompt
    assert "<subject_from_integration_action_config_or_default>" in prompt
    assert "\"subject\": \"Team Meeting follow-up\"" not in prompt
    assert 'subject=\\"Team Meeting follow-up\\"' not in prompt
