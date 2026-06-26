from __future__ import annotations
import os
import subprocess
import threading
from pathlib import Path

from tools.sg_supabase_write import update_job_status

SKILLS_DIR = Path(__file__).parent / "skills"


def _monitor(proc: subprocess.Popen, job_id: str, log_file) -> None:
    """Wait for proc to exit, close the log fd, and update job status."""
    proc.wait()
    log_file.close()
    if proc.returncode == 0:
        # Only mark complete if not already in a terminal state
        from supabase_client import get_supabase
        client = get_supabase()
        row = client.table("sg_jobs").select("status").eq("id", job_id).maybe_single().execute()
        current_status = (row.data or {}).get("status", "")
        if current_status not in ("complete", "failed"):
            update_job_status(job_id, "complete")
    else:
        update_job_status(job_id, "failed", {"error": f"hermes exited {proc.returncode}"})


def launch_hermes(job_id: str, context_json: str) -> None:
    """Spawn a Hermes session for one job. Non-blocking — runs in background."""
    cmd = [
        "hermes",
        "-z", context_json,
        "--provider", os.environ.get("HERMES_PROVIDER", "github-copilot"),
        "-m", os.environ.get("HERMES_MODEL", "gemini-2.5-pro"),
        "-s", str(SKILLS_DIR / "sg-orchestrator.md"),
        "--yolo",
        "--accept-hooks",
    ]
    log_file = open(f"/tmp/sg-job-{job_id}.log", "w")
    proc = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT)
    t = threading.Thread(target=_monitor, args=(proc, job_id, log_file), daemon=True)
    t.start()
