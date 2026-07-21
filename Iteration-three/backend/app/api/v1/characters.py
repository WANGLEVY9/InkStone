"""Character CRUD API endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db.connection import get_db
from app.services.content import ContentService

router = APIRouter(prefix="/projects/{project_id}/characters", tags=["characters"])


class CreateCharacterRequest(BaseModel):
    """Request body for creating a new character."""

    name: str = Field(description="Human-readable character name.")
    content: str = Field(description="Full content of the character profile in markdown.")
    summary: str = Field(default="", description="Brief summary of the character.")


class UpdateCharacterRequest(BaseModel):
    """Request body for updating an existing character.

    Only provided fields are applied; omitted fields remain unchanged.
    """

    name: str | None = Field(default=None, description="Updated character name.")
    content: str | None = Field(default=None, description="Updated character content.")
    summary: str | None = Field(default=None, description="Updated character summary.")


@router.get("/")
async def list_characters(project_id: str) -> Any:
    """List all characters for a project.

    Args:
        project_id: Unique identifier of the parent project.

    Returns:
        A list of character metadata records (content excluded).
    """
    async with get_db() as db:
        service = ContentService(db)
        characters = await service.get_all_characters(project_id)
        return characters


@router.post("/")
async def create_character(project_id: str, request: CreateCharacterRequest) -> Any:
    """Create a new character for a project.

    Args:
        project_id: Unique identifier of the parent project.
        request: Character creation payload.

    Returns:
        The newly created character record.
    """
    async with get_db() as db:
        service = ContentService(db)
        character = await service.create_character(
            project_id=project_id,
            character_id=str(uuid.uuid4()),
            name=request.name,
            content=request.content,
            summary=request.summary,
        )
        return character


@router.get("/{character_id}")
async def get_character(project_id: str, character_id: str) -> Any:
    """Retrieve a single character with its full content.

    Args:
        project_id: Unique identifier of the parent project.
        character_id: Unique identifier of the character.

    Returns:
        The character record including content.

    Raises:
        HTTPException: 404 if the character does not exist.
    """
    async with get_db() as db:
        service = ContentService(db)
        character = await service.get_character(character_id, project_id)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")
        return character


@router.post("/{character_id}/update")
async def update_character(project_id: str, character_id: str, request: UpdateCharacterRequest) -> Any:
    """Update an existing character.

    Only fields present in the request are modified; omitted fields remain unchanged.

    Args:
        project_id: Unique identifier of the parent project.
        character_id: Unique identifier of the character to update.
        request: Character update payload.

    Returns:
        The updated character record.

    Raises:
        HTTPException: 404 if the character does not exist.
    """
    async with get_db() as db:
        service = ContentService(db)
        update_data: dict[str, str | None] = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.summary is not None:
            update_data["summary"] = request.summary

        character = await service.update_character(
            character_id=character_id,
            project_id=project_id,
            content=request.content or "",
            **update_data,
        )
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")
        return character


@router.post("/{character_id}/delete")
async def delete_character(project_id: str, character_id: str) -> Any:
    """Delete a character and its associated content file.

    Args:
        project_id: Unique identifier of the parent project.
        character_id: Unique identifier of the character to delete.

    Returns:
        A confirmation dict with the deleted character ID.

    Raises:
        HTTPException: 404 if the character does not exist.
    """
    async with get_db() as db:
        service = ContentService(db)
        character = await service.get_character(character_id, project_id)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")

        # Delete metadata record first, then remove the content file.
        await db.execute(
            "DELETE FROM characters_meta WHERE id = ? AND project_id = ?",
            (character_id, project_id),
        )
        await db.commit()

        await service.storage.delete(character["file_path"])

        return {"status": "deleted", "character_id": character_id}
