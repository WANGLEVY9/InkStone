"""Chapters CRUD API endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db.connection import get_db
from app.services.content import ContentService

router = APIRouter(prefix="/projects/{project_id}/chapters", tags=["chapters"])


class CreateChapterRequest(BaseModel):
    """Request payload for creating a new chapter."""

    title: str = Field(description="Chapter title")
    content: str = Field(description="Full chapter content in markdown")
    word_count: int = Field(default=0, description="Word count of the chapter")
    chapter_number: int | None = Field(default=None, description="Ordinal chapter number")
    summary: str | None = Field(default=None, description="Short summary of the chapter")
    published_at: str | None = Field(default=None, description="ISO-format publication timestamp")


class UpdateChapterRequest(BaseModel):
    """Request payload for updating an existing chapter."""

    title: str | None = Field(default=None, description="New title if changing")
    content: str | None = Field(default=None, description="New content if changing")
    word_count: int | None = Field(default=None, description="Updated word count")
    status: str | None = Field(default=None, description="New status (e.g., draft, published)")
    chapter_number: int | None = Field(default=None, description="Updated chapter number")
    summary: str | None = Field(default=None, description="Updated summary")
    published_at: str | None = Field(default=None, description="Updated ISO-format publication timestamp")


@router.get("/")
async def list_chapters(project_id: str) -> list[dict[str, Any]]:
    """List all chapters (metadata only, no content)."""
    async with get_db() as db:
        service = ContentService(db)
        chapters = await service.get_all_chapters(project_id)
        return chapters


@router.post("/")
async def create_chapter(project_id: str, request: CreateChapterRequest) -> dict[str, Any]:
    """Create a new chapter."""
    async with get_db() as db:
        service = ContentService(db)
        chapter_id = str(uuid.uuid4())
        chapter = await service.create_chapter(
            project_id=project_id,
            chapter_id=chapter_id,
            title=request.title,
            content=request.content,
            word_count=request.word_count,
            chapter_number=request.chapter_number,
            summary=request.summary,
            published_at=request.published_at,
        )
        return chapter


@router.get("/{chapter_id}")
async def get_chapter(project_id: str, chapter_id: str) -> dict[str, Any]:
    """Get a single chapter with content."""
    async with get_db() as db:
        service = ContentService(db)
        chapter = await service.get_chapter(chapter_id, project_id)
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")
        return chapter


@router.post("/{chapter_id}/update")
async def update_chapter(project_id: str, chapter_id: str, request: UpdateChapterRequest) -> dict[str, Any]:
    """Update a chapter."""
    async with get_db() as db:
        service = ContentService(db)
        update_data: dict[str, str | int] = {}
        if request.title is not None:
            update_data["title"] = request.title
        if request.word_count is not None:
            update_data["word_count"] = request.word_count
        if request.status is not None:
            update_data["status"] = request.status
        if request.chapter_number is not None:
            update_data["chapter_number"] = request.chapter_number
        if request.summary is not None:
            update_data["summary"] = request.summary
        if request.published_at is not None:
            update_data["published_at"] = request.published_at

        chapter = await service.update_chapter(
            chapter_id=chapter_id,
            project_id=project_id,
            content=request.content or "",
            **update_data,
        )
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")
        return chapter


@router.post("/{chapter_id}/delete")
async def delete_chapter(project_id: str, chapter_id: str) -> dict[str, Any]:
    """Delete a chapter and its associated content file."""
    async with get_db() as db:
        service = ContentService(db)
        chapter = await service.get_chapter(chapter_id, project_id)
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")

        # Delete metadata first, then content file to avoid orphaned files on failure
        await db.execute(
            "DELETE FROM chapters_meta WHERE id = ? AND project_id = ?",
            (chapter_id, project_id),
        )
        await db.commit()

        await service.storage.delete(chapter["file_path"])

        return {"status": "deleted", "chapter_id": chapter_id}
