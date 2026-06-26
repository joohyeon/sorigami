from __future__ import annotations
import os
import subprocess
import sys
import threading
import traceback
from pathlib import Path

from tools.sg_supabase_write import update_job_status

SKILLS_DIR = Path(__file__).parent / "skills"

# Hermes' -s/--skills flag only registers a skill by *name* for progressive
# disclosure (a one-line catalog entry) and silently ignores a file path — it
# never injects the skill body into the model prompt. So we read the
# orchestrator instructions at import time and inline them into the -z prompt,
# guaranteeing the agent always receives the full pipeline procedure. Reading
# at module load also fails fast if the skill file is missing.
ORCHESTRATOR_SKILL = (SKILLS_DIR / "sg-orchestrator.md").read_text()


def _build_prompt(context_json: str) -> str:
    """Combine the orchestrator skill body with the job context into one prompt."""
    return (
        f"{ORCHESTRATOR_SKILL}\n\n"
        "---\n\n"
        "# Job Context\n\n"
        "Follow the sg-orchestrator instructions above to execute the full "
        "pipeline for the job described by this JSON:\n\n"
        f"{context_json}\n"
    )


def _monitor(proc: subprocess.Popen, job_id: str, log_file) -> None:
    """Wait for proc to exit, close the log fd, and update job status."""
    try:
        proc.wait()
        log_file.close()
        if proc.returncode == 0:
            # The orchestrator is responsible for setting the job to `complete`
            # itself (Stage 7). This is only a safety net: if Hermes exits 0 while
            # the job is still in any non-terminal state (analyzing, executing,
            # awaiting_*), it exited before finishing — treat that as a failure.
            from supabase_client import get_supabase
            client = get_supabase()
            row = client.table("sg_jobs").select("status").eq("id", job_id).maybe_single().execute()
            current_status = (row.data or {}).get("status", "")
            if current_status not in ("complete", "failed"):
                update_job_status(job_id, "failed", {"error": f"hermes exited 0 from unexpected state: {current_status}"})
        else:
            update_job_status(job_id, "failed", {"error": f"hermes exited {proc.returncode}"})
    except Exception as exc:
        print(f"[CRITICAL] _monitor thread failed for job {job_id}: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        try:
            update_job_status(job_id, "failed", {"error": f"monitor thread error: {exc}"})
        except Exception as inner:
            print(f"[CRITICAL] also failed to mark job {job_id} as failed: {inner}", file=sys.stderr)


def launch_hermes(job_id: str, context_json: str) -> None:
    """Spawn a Hermes session for one job. Non-blocking — runs in background.

    Secrets (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, GOOGLE_SERVICE_ACCOUNT_JSON)
    are NOT embedded in context_json — the subprocess inherits them as env vars
    from the parent process so they never appear in argv or ps output.
    """
    cmd = [
        "hermes",
        "-z", _build_prompt(context_json),
        "--provider", os.environ.get("HERMES_PROVIDER", "github-copilot"),
        "-m", os.environ.get("HERMES_MODEL", "gemini-2.5-pro"),
        "--yolo",
        "--accept-hooks",
    ]
    log_file = open(f"/tmp/sg-job-{job_id}.log", "w")
    try:
        proc = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT)
    except Exception:
        log_file.close()
        raise
    t = threading.Thread(target=_monitor, args=(proc, job_id, log_file), daemon=True)
    t.start()
