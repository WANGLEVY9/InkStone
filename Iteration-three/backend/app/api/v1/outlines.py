"""Outlines CRUD API endpoints with nested structure support."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db.connection import get_db
from app.services.content import ContentService

router = APIRouter(prefix="/projects/{project_id}/outlines", tags=["outlines"])


class CreateOutlineRequest(BaseModel):
    """Request payload for creating a new outline node."""

    title: str = Field(description="Outline node title")
    content: str = Field(description="Outline content in markdown")
    type: str = Field(default="chapter", description="Node type (e.g., chapter, section, part)")
    parent_id: str | None = Field(default=None, description="Parent outline ID for nested hierarchy")
    sort_order: int = Field(default=0, description="Display order among siblings")


class UpdateOutlineRequest(BaseModel):
    """Request payload for updating an existing outline node."""

    title: str | None = Field(default=None, description="New title if changing")
    content: str | None = Field(default=None, description="New content if changing")
    type: str | None = Field(default=None, description="New type if changing")
    parent_id: str | None = Field(default=None, description="New parent ID for reparenting")
    sort_order: int | None = Field(default=None, description="New sort order")


@router.get("/")
async def get_root_outline(project_id: str) -> dict[str, Any]:
    """Get root outline (tree structure, parent_id IS NULL)."""
    async with get_db() as db:
        service = ContentService(db)
        outline = await service.get_root_outline(project_id)
        if not outline:
            raise HTTPException(status_code=404, detail="Root outline not found")
        return outline


@router.post("/")
async def create_outline(project_id: str, request: CreateOutlineRequest) -> dict[str, Any]:
    """Create a new outline node."""
    async with get_db() as db:
        service = ContentService(db)
        outline_id = str(uuid.uuid4())
        try:
            outline = await service.create_outline(
                project_id=project_id,
                outline_id=outline_id,
                title=request.title,
                content=request.content,
                outline_type=request.type,
                parent_id=request.parent_id,
                sort_order=request.sort_order,
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        return outline


@router.get("/{outline_id}")
async def get_outline(project_id: str, outline_id: str) -> dict[str, Any]:
    """Get a single outline with content."""
    async with get_db() as db:
        service = ContentService(db)
        outline = await service.get_outline(outline_id, project_id)
        if not outline:
            raise HTTPException(status_code=404, detail="Outline not found")
        return outline


@router.get("/{outline_id}/children")
async def get_outline_children(project_id: str, outline_id: str) -> list[dict[str, Any]]:
    """Get child outlines for nested structure."""
    async with get_db() as db:
        service = ContentService(db)
        children = await service.get_outline_children(outline_id, project_id)
        return children


@router.get("/{outline_id}/tree")
async def get_outline_tree(project_id: str, outline_id: str) -> dict[str, Any]:
    """Get the full subtree rooted at outline_id (without content)."""
    async with get_db() as db:
        service = ContentService(db)
        tree = await service.get_outline_tree(outline_id, project_id)
        if not tree:
            raise HTTPException(status_code=404, detail="Outline not found")
        return tree


@router.post("/{outline_id}/update")
async def update_outline(project_id: str, outline_id: str, request: UpdateOutlineRequest) -> dict[str, Any]:
    """Update an outline."""
    async with get_db() as db:
        service = ContentService(db)
        update_data: dict[str, str | int | None] = {}
        if request.title is not None:
            update_data["title"] = request.title
        if request.type is not None:
            update_data["type"] = request.type
        if request.sort_order is not None:
            update_data["sort_order"] = request.sort_order
        if request.parent_id is not None:
            update_data["parent_id"] = request.parent_id

        outline = await service.update_outline(
            outline_id=outline_id,
            project_id=project_id,
            content=request.content or "",
            **update_data,
        )
        if not outline:
            raise HTTPException(status_code=404, detail="Outline not found")
        return outline


@router.post("/{outline_id}/delete")
async def delete_outline(project_id: str, outline_id: str) -> dict[str, Any]:
    """Delete an outline and all its descendants (cascade)."""
    async with get_db() as db:
        service = ContentService(db)
        deleted = await service.delete_outline(outline_id, project_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Outline not found")
        return {"status": "deleted", "outline_id": outline_id}
