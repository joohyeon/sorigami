from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, HTTPException
from models import CreateJobRequest, ConfirmJobRequest, CheckpointRequest
from supabase_client import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", status_code=201)
def create_job(body: CreateJobRequest, db=Depends(get_supabase)):
    # Create job row
    result = db.table("sg_jobs").insert({
        "drive_file_id": body.drive_file_id,
        "mode_id": str(body.mode_id),
        "user_id": str(body.user_id),
        "status": "submitted",
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Job insert returned no data")
    row = result.data[0]
    job_id = row["id"]

    # Resolve mode — use maybe_single so a missing mode_id returns None instead of raising
    try:
        mode_result = db.table("sg_modes").select("*").eq("id", str(body.mode_id)).maybe_single().execute()
    except Exception as exc:
        db.table("sg_jobs").update({"status": "failed", "error": str(exc)}).eq("id", job_id).execute()
        raise HTTPException(status_code=500, detail="Failed to resolve mode")

    if not mode_result.data:
        db.table("sg_jobs").update({"status": "failed", "error": "mode not found"}).eq("id", job_id).execute()
        raise HTTPException(status_code=404, detail=f"Mode {body.mode_id} not found")

    mode = mode_result.data
    skill_ids = mode.get("skill_ids", [])
    skills_data = []
    if skill_ids:
        try:
            skills_data = db.table("sg_skills").select("*").in_("id", skill_ids).execute().data or []
        except Exception as exc:
            db.table("sg_jobs").update({"status": "failed", "error": str(exc)}).eq("id", job_id).execute()
            raise HTTPException(status_code=500, detail="Failed to resolve skills")

    skills = [
        {
            "skill_name": s["name"],
            "ai_prompt": s["ai_prompt"],
            "integration_actions": s.get("integration_actions", []),
            "require_review": bool(s.get("require_review", False)),
        }
        for s in skills_data
    ]

    # Spawn Hermes (non-blocking)
    from hermes.context import build_context
    from hermes.runner import launch_hermes
    context_json = build_context(row, mode, skills)
    try:
        launch_hermes(job_id, context_json)
    except Exception as exc:
        logger.error("launch_hermes failed for job %s: %s", job_id, exc, exc_info=True)
        db.table("sg_jobs").update({"status": "failed", "error": f"pipeline failed to start: {exc}"}).eq("id", job_id).execute()
        raise HTTPException(status_code=500, detail="Failed to start pipeline")

    return {"job_id": job_id, "status": row["status"]}


@router.get("/{job_id}")
def get_job(job_id: str, db=Depends(get_supabase)):
    result = db.table("sg_jobs").select("*").eq("id", job_id).maybe_single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Job not found")
    row = result.data
    return {
        "job_id": row["id"],
        "status": row["status"],
        "plan": row.get("plan_json"),
        "checkpoint": row.get("checkpoint_json"),
        "quality": row.get("quality_json"),
        "error": row.get("error"),
    }


@router.get("/{job_id}/results")
def get_job_results(job_id: str, db=Depends(get_supabase)):
    result = (
        db.table("sg_skill_results")
        .select("*")
        .eq("job_id", job_id)
        .execute()
    )
    action_logs = (
        db.table("sg_action_logs")
        .select("*")
        .eq("job_id", job_id)
        .execute()
    )
    return {"skill_results": result.data, "action_logs": action_logs.data}


@router.post("/{job_id}/confirm")
def confirm_job(job_id: str, body: ConfirmJobRequest, db=Depends(get_supabase)):
    check = db.table("sg_jobs").select("id").eq("id", job_id).maybe_single().execute()
    if not check.data:
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        result = db.table("sg_jobs").update({
            "status": "executing",
            "plan_json": {"approved_steps": body.approved_steps, "overrides": body.per_step_overrides},
        }).eq("id", job_id).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Job update failed: no rows affected")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to confirm job")
    return {"job_id": job_id, "status": "executing"}


@router.post("/{job_id}/checkpoint")
def resolve_checkpoint(job_id: str, body: CheckpointRequest, db=Depends(get_supabase)):
    check = db.table("sg_jobs").select("id").eq("id", job_id).maybe_single().execute()
    if not check.data:
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        result = db.table("sg_jobs").update({
            "status": "executing",
            "checkpoint_json": body.data,
        }).eq("id", job_id).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Checkpoint update failed: no rows affected")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to resolve checkpoint")
    return {"job_id": job_id, "status": "executing"}
