"""World Settings CRUD API endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db.connection import get_db
from app.services.content import ContentService

router = APIRouter(prefix="/projects/{project_id}/world", tags=["world"])


class CreateWorldRequest(BaseModel):
    """Request body for creating a new world setting."""

    name: str = Field(description="Human-readable world setting name.")
    content: str = Field(description="Full content of the world setting in markdown.")
    summary: str = Field(default="", description="Brief summary of the world setting.")


class UpdateWorldRequest(BaseModel):
    """Request body for updating an existing world setting.

    Only provided fields are applied; omitted fields remain unchanged.
    """

    name: str | None = Field(default=None, description="Updated world setting name.")
    content: str | None = Field(default=None, description="Updated world setting content.")
    summary: str | None = Field(default=None, description="Updated world setting summary.")


@router.get("/")
async def list_worlds(project_id: str) -> Any:
    """List all world settings for a project.

    Args:
        project_id: Unique identifier of the parent project.

    Returns:
        A list of world setting metadata records (content excluded).
    """
    async with get_db() as db:
        service = ContentService(db)
        worlds = await service.get_all_world_settings(project_id)
        return worlds


@router.post("/")
async def create_world(project_id: str, request: CreateWorldRequest) -> Any:
    """Create a new world setting for a project.

    Args:
        project_id: Unique identifier of the parent project.
        request: World setting creation payload.

    Returns:
        The newly created world setting record.
    """
    async with get_db() as db:
        service = ContentService(db)
        world_id = str(uuid.uuid4())
        world = await service.create_world_setting(
            project_id=project_id,
            world_setting_id=world_id,
            name=request.name,
            content=request.content,
            summary=request.summary,
        )
        return world


@router.get("/{world_id}")
async def get_world(project_id: str, world_id: str) -> Any:
    """Retrieve a single world setting with its full content.

    Args:
        project_id: Unique identifier of the parent project.
        world_id: Unique identifier of the world setting.

    Returns:
        The world setting record including content.

    Raises:
        HTTPException: 404 if the world setting does not exist.
    """
    async with get_db() as db:
        service = ContentService(db)
        world = await service.get_world_setting(world_id, project_id)
        if not world:
            raise HTTPException(status_code=404, detail="World not found")
        return world


@router.post("/{world_id}/update")
async def update_world(project_id: str, world_id: str, request: UpdateWorldRequest) -> Any:
    """Update an existing world setting.

    Only fields present in the request are modified; omitted fields remain unchanged.

    Args:
        project_id: Unique identifier of the parent project.
        world_id: Unique identifier of the world setting to update.
        request: World setting update payload.

    Returns:
        The updated world setting record.

    Raises:
        HTTPException: 404 if the world setting does not exist.
    """
    async with get_db() as db:
        service = ContentService(db)
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.summary is not None:
            update_data["summary"] = request.summary

        world = await service.update_world_setting(
            world_setting_id=world_id,
            project_id=project_id,
            content=request.content or "",
            **update_data,
        )
        if not world:
            raise HTTPException(status_code=404, detail="World not found")
        return world


@router.post("/{world_id}/delete")
async def delete_world(project_id: str, world_id: str) -> Any:
    """Delete a world setting and its associated content file.

    Args:
        project_id: Unique identifier of the parent project.
        world_id: Unique identifier of the world setting to delete.

    Returns:
        A confirmation dict with the deleted world setting ID.

    Raises:
        HTTPException: 404 if the world setting does not exist.
    """
    async with get_db() as db:
        service = ContentService(db)
        world = await service.get_world_setting(world_id, project_id)
        if not world:
            raise HTTPException(status_code=404, detail="World not found")

        # Delete metadata record first, then remove the content file.
        await db.execute(
            "DELETE FROM world_settings_meta WHERE id = ? AND project_id = ?",
            (world_id, project_id),
        )
        await db.commit()

        await service.storage.delete(world["file_path"])

        return {"status": "deleted", "world_id": world_id}
