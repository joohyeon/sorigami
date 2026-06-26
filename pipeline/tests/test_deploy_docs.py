from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_runbook_documents_pipeline_fly_deploy_context() -> None:
    runbook = (ROOT / "RUNBOOK.md").read_text()

    assert "flyctl deploy pipeline --config fly.toml --remote-only" in runbook
    assert "Do not run `flyctl deploy --config pipeline/fly.toml` from the repo root" in runbook
