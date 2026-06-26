from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from models import CreateJobRequest, ConfirmJobRequest, CheckpointRequest
from supabase_client import get_supabase

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("", status_code=201)
def create_job(body: CreateJobRequest, db=Depends(get_supabase)):
    result = db.table("sg_jobs").insert({
        "drive_file_id": body.drive_file_id,
        "mode_id": str(body.mode_id),
        "user_id": str(body.user_id),
        "status": "submitted",
    }).execute()
    row = result.data[0]
    return {"job_id": row["id"], "status": row["status"]}

@router.get("/{job_id}")
def get_job(job_id: str, db=Depends(get_supabase)):
    result = db.table("sg_jobs").select("*").eq("id", job_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Job not found")
    row = result.data
    return {
        "job_id": row["id"],
        "status": row["status"],
        "plan": row.get("plan_json"),
        "checkpoint": row.get("checkpoint_json"),
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
    check = db.table("sg_jobs").select("id").eq("id", job_id).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail="Job not found")
    db.table("sg_jobs").update({
        "status": "executing",
        "plan_json": {"approved_steps": body.approved_steps, "overrides": body.per_step_overrides},
    }).eq("id", job_id).execute()
    return {"job_id": job_id, "status": "executing"}

@router.post("/{job_id}/checkpoint")
def resolve_checkpoint(job_id: str, body: CheckpointRequest, db=Depends(get_supabase)):
    check = db.table("sg_jobs").select("id").eq("id", job_id).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail="Job not found")
    db.table("sg_jobs").update({
        "status": "executing",
        "checkpoint_json": body.data,
    }).eq("id", job_id).execute()
    return {"job_id": job_id, "status": "executing"}
