"""Project CRUD API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db.connection import get_db
from app.services.project_repository import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)

router = APIRouter(prefix="/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    """Request body for creating a new project."""

    name: str = Field(description="Human-readable project name.")
    description: str | None = Field(default=None, description="Optional project description.")
    cover_image: str | None = Field(default=None, description="Optional cover image URL/path.")


class UpdateProjectRequest(BaseModel):
    """Request body for updating an existing project.

    Only provided fields are applied; omitted fields remain unchanged.
    """

    name: str | None = Field(default=None, description="Updated project name.")
    status: str | None = Field(default=None, description="Updated project status.")
    description: str | None = Field(default=None, description="Updated project description.")
    cover_image: str | None = Field(default=None, description="Updated cover image URL/path.")
    word_count: int | None = Field(default=None, description="Updated total word count.")


@router.post("/")
async def create_project_endpoint(request: CreateProjectRequest) -> Any:
    """Create a new project.

    Args:
        request: Project creation payload.

    Returns:
        The newly created project record.
    """
    async with get_db() as db:
        project = await create_project(
            db,
            request.name,
            description=request.description,
            cover_image=request.cover_image,
        )
        return project


@router.get("/{project_id}")
async def get_project_endpoint(project_id: str) -> Any:
    """Retrieve a single project by ID.

    Args:
        project_id: Unique identifier of the project.

    Returns:
        The project record.

    Raises:
        HTTPException: 404 if the project does not exist.
    """
    async with get_db() as db:
        project = await get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project


@router.patch("/{project_id}")
async def update_project_endpoint(project_id: str, request: UpdateProjectRequest) -> Any:
    """Update an existing project.

    Only fields present in the request are modified.

    Args:
        project_id: Unique identifier of the project to update.
        request: Project update payload.

    Returns:
        The updated project record.

    Raises:
        HTTPException: 400 if no update data is provided.
        HTTPException: 404 if the project does not exist.
    """
    async with get_db() as db:
        update_data: dict[str, Any] = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.status is not None:
            update_data["status"] = request.status
        if request.description is not None:
            update_data["description"] = request.description
        if request.cover_image is not None:
            update_data["cover_image"] = request.cover_image
        if request.word_count is not None:
            update_data["word_count"] = request.word_count

        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")

        project = await update_project(db, project_id, **update_data)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project


@router.get("/")
async def list_projects_endpoint(limit: int = 100, offset: int = 0) -> Any:
    """List all projects with pagination.

    Args:
        limit: Maximum number of projects to return.
        offset: Number of projects to skip before returning results.

    Returns:
        A list of project records.
    """
    async with get_db() as db:
        projects = await list_projects(db, limit, offset)
        return projects


@router.delete("/{project_id}")
async def delete_project_endpoint(project_id: str) -> Any:
    """Delete a project and all associated data.

    Args:
        project_id: Unique identifier of the project to delete.

    Returns:
        A confirmation dict with the deleted project ID.
    """
    async with get_db() as db:
        await delete_project(db, project_id)
        return {"status": "deleted", "project_id": project_id}
