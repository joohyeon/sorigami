from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from models import CreateModeRequest, UpdateModeRequest
from supabase_client import get_supabase

router = APIRouter(prefix="/modes", tags=["modes"])

@router.get("")
def list_modes(user_id: str | None = None, db=Depends(get_supabase)):
    if user_id:
        result = db.table("sg_modes").select("*").eq("user_id", user_id).execute()
    else:
        result = db.table("sg_modes").select("*").execute()
    return result.data

@router.post("", status_code=201)
def create_mode(body: CreateModeRequest, user_id: str | None = None, db=Depends(get_supabase)):
    result = db.table("sg_modes").insert({
        "user_id": user_id,
        "name": body.name,
        "skill_ids": [str(s) for s in body.skill_ids],
    }).execute()
    return result.data[0]

@router.put("/{mode_id}")
def update_mode(mode_id: str, body: UpdateModeRequest, db=Depends(get_supabase)):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if "skill_ids" in updates:
        updates["skill_ids"] = [str(s) for s in updates["skill_ids"]]
    result = db.table("sg_modes").update(updates).eq("id", mode_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Mode not found")
    return result.data[0]

@router.delete("/{mode_id}", status_code=204)
def delete_mode(mode_id: str, db=Depends(get_supabase)):
    db.table("sg_modes").delete().eq("id", mode_id).execute()
