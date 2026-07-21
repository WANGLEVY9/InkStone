"""Tests for Reviews API endpoints (TDD - RED phase)."""

from __future__ import annotations

from typing import Any, cast


class TestReviewsAPI:
    """Test reviews CRUD endpoints (read-only, no update/delete per spec)."""

    def test_review_router_exists(self) -> None:
        """Review router should exist in api/v1."""
        from app.api.v1.reviews import router

        assert router is not None
        assert router.prefix == "/projects/{project_id}/reviews"

    def test_review_list_endpoint_exists(self) -> None:
        """GET / should list all reviews."""
        from app.api.v1.reviews import router

        path_methods: dict[str, set[str]] = {}
        for r in router.routes:
            route = cast(Any, r)
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        list_path = "/projects/{project_id}/reviews/"
        assert list_path in path_methods
        assert "GET" in path_methods[list_path]

    def test_review_create_endpoint_exists(self) -> None:
        """POST / should create a review."""
        from app.api.v1.reviews import router

        path_methods: dict[str, set[str]] = {}
        for r in router.routes:
            route = cast(Any, r)
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        list_path = "/projects/{project_id}/reviews/"
        assert "POST" in path_methods[list_path]

    def test_review_get_single_endpoint_exists(self) -> None:
        """GET /{review_id} should get a single review."""
        from app.api.v1.reviews import router

        path_methods: dict[str, set[str]] = {}
        for r in router.routes:
            route = cast(Any, r)
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        get_path = "/projects/{project_id}/reviews/{review_id}"
        assert get_path in path_methods
        assert "GET" in path_methods[get_path]


class TestReviewsRequestModels:
    """Test request models for reviews."""

    def test_create_review_request_model_exists(self) -> None:
        """CreateReviewRequest should exist with required fields."""
        from app.api.v1.reviews import CreateReviewRequest

        assert hasattr(CreateReviewRequest, "model_fields")
        fields = CreateReviewRequest.model_fields
        assert "content_type" in fields
        assert "content_id" in fields

    def test_create_review_request_optional_fields(self) -> None:
        """CreateReviewRequest should have optional issues, suggestions, overall_score."""
        from app.api.v1.reviews import CreateReviewRequest

        fields = CreateReviewRequest.model_fields
        assert "issues" in fields
        assert "suggestions" in fields
        assert "overall_score" in fields


class TestReviewsRouterRegistered:
    """Test that review router is registered in main app."""

    def test_review_router_in_app(self) -> None:
        """Review router should be included in the app."""
        from app.main import create_app

        app = create_app()
        routes = [cast(Any, r).path for r in app.routes]
        assert any("reviews" in r for r in routes)
