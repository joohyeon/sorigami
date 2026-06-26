from __future__ import annotations
from pydantic import BaseModel
from uuid import UUID
from typing import Any

class CreateJobRequest(BaseModel):
    drive_file_id: str
    mode_id: UUID
    user_id: UUID

class ConfirmJobRequest(BaseModel):
    approved_steps: list[str]
    per_step_overrides: dict[str, Any] = {}

class CheckpointRequest(BaseModel):
    data: dict[str, Any]

class CreateSkillRequest(BaseModel):
    name: str
    description: str = ""
    ai_prompt: str
    integration_actions: list[dict[str, Any]] = []

class UpdateSkillRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    ai_prompt: str | None = None
    integration_actions: list[dict[str, Any]] | None = None

class CreateModeRequest(BaseModel):
    name: str
    skill_ids: list[UUID]

class UpdateModeRequest(BaseModel):
    name: str | None = None
    skill_ids: list[UUID] | None = None
