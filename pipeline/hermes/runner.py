from __future__ import annotations
import os
import subprocess
from pathlib import Path

SKILLS_DIR = Path(__file__).parent / "skills"


def launch_hermes(job_id: str, context_json: str) -> None:
    """Spawn a Hermes session for one job. Non-blocking — runs in background."""
    cmd = [
        "hermes",
        "-z", context_json,
        "--provider", os.environ.get("HERMES_PROVIDER", "github-copilot"),
        "-m", os.environ.get("HERMES_MODEL", "gemini-2.5-pro"),
        "-s", "sg-orchestrator",
        "--skills", str(SKILLS_DIR / "sg-orchestrator.md"),
        "--yolo",
        "--accept-hooks",
    ]
    subprocess.Popen(
        cmd,
        stdout=open(f"/tmp/sg-job-{job_id}.log", "w"),
        stderr=subprocess.STDOUT,
    )
