"""Reviews CRUD API endpoints (read-only per spec)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db.connection import get_db
from app.services.content import ContentService

router = APIRouter(prefix="/projects/{project_id}/reviews", tags=["reviews"])


class CreateReviewRequest(BaseModel):
    """Request payload for creating a new review."""

    content_type: str = Field(description="Type of content being reviewed (e.g., chapter, outline)")
    content_id: str = Field(description="ID of the content being reviewed")
    issues: list[str] = Field(default_factory=list, description="List of identified issues")
    suggestions: list[str] = Field(default_factory=list, description="List of improvement suggestions")
    overall_score: float | None = Field(default=None, description="Overall quality score (0.0-1.0)")


@router.get("/")
async def list_reviews(project_id: str) -> list[dict[str, Any]]:
    """List all reviews for a project."""
    async with get_db() as db:
        service = ContentService(db)
        reviews = await service.get_all_reviews(project_id)
        return reviews


@router.post("/")
async def create_review(project_id: str, request: CreateReviewRequest) -> dict[str, Any]:
    """Create a new review."""
    async with get_db() as db:
        service = ContentService(db)
        review_id = str(uuid.uuid4())
        review = await service.create_review(
            review_id=review_id,
            project_id=project_id,
            content_type=request.content_type,
            content_id=request.content_id,
            issues=request.issues,
            suggestions=request.suggestions,
            overall_score=request.overall_score,
        )
        return review


@router.get("/{review_id}")
async def get_review(project_id: str, review_id: str) -> dict[str, Any]:
    """Get a single review."""
    async with get_db() as db:
        service = ContentService(db)
        review = await service.get_review(review_id, project_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        return review
