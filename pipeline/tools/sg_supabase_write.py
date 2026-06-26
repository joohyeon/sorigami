from __future__ import annotations
import os

try:
    from supabase import create_client
except ImportError:  # pragma: no cover - exercised in test envs without supabase
    create_client = None  # type: ignore[assignment]


def _client():
    if create_client is None:
        raise RuntimeError("supabase is not installed")
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])


def update_job_status(
    job_id: str,
    status: str,
    extra: dict | None = None,
) -> None:
    try:
        client = _client()
        data = {"status": status}
        if extra:
            data.update(extra)
        client.table("sg_jobs").update(data).eq("id", job_id).execute()
    except Exception as exc:
        raise RuntimeError(f"Supabase write failed (update_job_status {job_id}): {exc}") from exc


def write_utterances(job_id: str, utterances: list[dict]) -> None:
    try:
        client = _client()
        rows = [{"job_id": job_id, **u} for u in utterances]
        client.table("sg_utterances").insert(rows).execute()
    except Exception as exc:
        raise RuntimeError(f"Supabase write failed (write_utterances {job_id}): {exc}") from exc


def write_speakers(job_id: str, speakers: list[dict]) -> None:
    try:
        client = _client()
        rows = [{"job_id": job_id, **s} for s in speakers]
        client.table("sg_speakers").insert(rows).execute()
    except Exception as exc:
        raise RuntimeError(f"Supabase write failed (write_speakers {job_id}): {exc}") from exc


def write_skill_result(
    job_id: str, skill_id: str | None, skill_name: str,
    output_json: dict, output_markdown: str,
) -> None:
    try:
        client = _client()
        client.table("sg_skill_results").insert({
            "job_id": job_id, "skill_id": skill_id, "skill_name": skill_name,
            "output_json": output_json, "output_markdown": output_markdown,
            "status": "complete",
        }).execute()
    except Exception as exc:
        raise RuntimeError(f"Supabase write failed (write_skill_result {job_id}): {exc}") from exc


def write_action_log(
    job_id: str, skill_id: str | None, action_type: str,
    destination: str, payload: dict, status: str,
    fired_at: str | None = None, error: str | None = None,
) -> None:
    try:
        client = _client()
        client.table("sg_action_logs").insert({
            "job_id": job_id, "skill_id": skill_id, "action_type": action_type,
            "destination": destination, "payload_json": payload,
            "status": status, "fired_at": fired_at, "error": error,
        }).execute()
    except Exception as exc:
        raise RuntimeError(f"Supabase write failed (write_action_log {job_id}): {exc}") from exc
