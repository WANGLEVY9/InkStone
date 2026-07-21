"""Skill CRUD API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.skill import SkillService

router = APIRouter(prefix="/skills", tags=["skills"])
skill_service = SkillService()


class SkillCreate(BaseModel):
    """Request body for creating a new skill."""

    name: str
    description: str
    content: str
    domain: str | None = None
    tags: list[str] | None = None


class SkillUpdate(BaseModel):
    """Request body for updating an existing skill."""

    description: str | None = None
    content: str | None = None
    domain: str | None = None
    tags: list[str] | None = None


class SkillResponse(BaseModel):
    """Response model for skill list items (no content)."""

    name: str
    description: str
    domain: str | None = None
    tags: list[str] = []


class SkillDetailResponse(SkillResponse):
    """Response model for a single skill (includes content)."""

    content: str


@router.get("/", response_model=list[SkillResponse])
async def list_skills(domain: str | None = None) -> list[dict[str, Any]]:
    """List skills, optionally filtered by domain.

    Args:
        domain: Optional domain filter. If ``None``, returns global skills.

    Returns:
        List of skill metadata dicts.
    """
    return skill_service.list_skills(domain=domain)


@router.get("/{skill_name}", response_model=SkillDetailResponse)
async def get_skill(skill_name: str) -> dict[str, Any]:
    """Get a single skill by name.

    Args:
        skill_name: The skill identifier.

    Returns:
        Skill dict with content.

    Raises:
        HTTPException: 404 if the skill does not exist.
    """
    skill = skill_service.get_skill(skill_name)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
    return skill


@router.post("/", response_model=SkillDetailResponse, status_code=201)
async def create_skill(request: SkillCreate) -> dict[str, Any]:
    """Create a new skill.

    Args:
        request: Skill creation payload.

    Returns:
        The created skill dict with content.

    Raises:
        HTTPException: 409 if a skill with the same name already exists.
    """
    try:
        return skill_service.create_skill(
            name=request.name,
            description=request.description,
            content=request.content,
            domain=request.domain,
            tags=request.tags,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{skill_name}/update", response_model=SkillDetailResponse)
async def update_skill(skill_name: str, request: SkillUpdate) -> dict[str, Any]:
    """Update an existing skill.

    Args:
        skill_name: The skill identifier.
        request: Skill update payload.

    Returns:
        The updated skill dict.

    Raises:
        HTTPException: 404 if the skill does not exist.
    """
    update_data: dict[str, Any] = {}
    if "description" in request.model_fields_set:
        update_data["description"] = request.description
    if "content" in request.model_fields_set:
        update_data["content"] = request.content
    if "domain" in request.model_fields_set:
        update_data["domain"] = request.domain
    if "tags" in request.model_fields_set:
        update_data["tags"] = request.tags

    try:
        result = skill_service.update_skill(skill_name, **update_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if result is None:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
    return result


@router.post("/{skill_name}/delete")
async def delete_skill(skill_name: str) -> dict[str, bool]:
    """Delete a skill.

    Args:
        skill_name: The skill identifier.

    Returns:
        A dict confirming deletion.

    Raises:
        HTTPException: 404 if the skill does not exist.
    """
    deleted = skill_service.delete_skill(skill_name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
    return {"deleted": True}
