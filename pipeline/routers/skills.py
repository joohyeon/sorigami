from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from models import CreateSkillRequest, UpdateSkillRequest
from supabase_client import get_supabase

router = APIRouter(prefix="/skills", tags=["skills"])

@router.get("")
def list_skills(user_id: str | None = None, db=Depends(get_supabase)):
    if user_id:
        result = db.table("sg_skills").select("*").or_(f"is_default.eq.true,user_id.eq.{user_id}").execute()
    else:
        result = db.table("sg_skills").select("*").execute()
    return result.data

@router.post("", status_code=201)
def create_skill(body: CreateSkillRequest, user_id: str | None = None, db=Depends(get_supabase)):
    result = db.table("sg_skills").insert({
        "user_id": user_id,
        "name": body.name,
        "description": body.description,
        "ai_prompt": body.ai_prompt,
        "integration_actions": body.integration_actions,
        "is_default": False,
    }).execute()
    return result.data[0]

@router.put("/{skill_id}")
def update_skill(skill_id: str, body: UpdateSkillRequest, db=Depends(get_supabase)):
    check = db.table("sg_skills").select("id, is_default, user_id").eq("id", skill_id).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail="Skill not found")
    skill = check.data[0]
    if skill.get("is_default") or skill.get("user_id") is None:
        raise HTTPException(status_code=403, detail="Cannot modify default skills")
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    result = db.table("sg_skills").update(updates).eq("id", skill_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Skill not found")
    return result.data[0]

@router.delete("/{skill_id}", status_code=204)
def delete_skill(skill_id: str, db=Depends(get_supabase)):
    check = db.table("sg_skills").select("id, is_default, user_id").eq("id", skill_id).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail="Skill not found")
    skill = check.data[0]
    if skill.get("is_default") or skill.get("user_id") is None:
        raise HTTPException(status_code=403, detail="Cannot modify default skills")
    db.table("sg_skills").delete().eq("id", skill_id).execute()
