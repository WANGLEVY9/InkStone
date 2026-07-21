"""Tests for Chapters API endpoints (TDD - RED phase)."""

from __future__ import annotations

from typing import Any, cast


class TestChaptersAPI:
    """Test chapters CRUD endpoints."""

    def test_chapter_router_exists(self) -> None:
        """Chapter router should exist in api/v1."""
        from app.api.v1.chapters import router

        assert router is not None
        assert router.prefix == "/projects/{project_id}/chapters"

    def test_chapter_list_endpoint_exists(self) -> None:
        """GET / should list all chapters."""
        from app.api.v1.chapters import router

        path_methods: dict[str, set[str]] = {}
        for r in router.routes:
            route = cast(Any, r)
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        list_path = "/projects/{project_id}/chapters/"
        assert list_path in path_methods
        assert "GET" in path_methods[list_path]

    def test_chapter_create_endpoint_exists(self) -> None:
        """POST / should create a chapter."""
        from app.api.v1.chapters import router

        path_methods: dict[str, set[str]] = {}
        for r in router.routes:
            route = cast(Any, r)
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        list_path = "/projects/{project_id}/chapters/"
        assert "POST" in path_methods[list_path]

    def test_chapter_get_single_endpoint_exists(self) -> None:
        """GET /{chapter_id} should get a single chapter."""
        from app.api.v1.chapters import router

        path_methods: dict[str, set[str]] = {}
        for r in router.routes:
            route = cast(Any, r)
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        get_path = "/projects/{project_id}/chapters/{chapter_id}"
        assert get_path in path_methods
        assert "GET" in path_methods[get_path]

    def test_chapter_update_endpoint_exists(self) -> None:
        """POST /{chapter_id}/update should update chapter."""
        from app.api.v1.chapters import router

        path_methods: dict[str, set[str]] = {}
        for r in router.routes:
            route = cast(Any, r)
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        update_path = "/projects/{project_id}/chapters/{chapter_id}/update"
        assert update_path in path_methods
        assert "POST" in path_methods[update_path]

    def test_chapter_delete_endpoint_exists(self) -> None:
        """POST /{chapter_id}/delete should delete chapter."""
        from app.api.v1.chapters import router

        path_methods: dict[str, set[str]] = {}
        for r in router.routes:
            route = cast(Any, r)
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        delete_path = "/projects/{project_id}/chapters/{chapter_id}/delete"
        assert delete_path in path_methods
        assert "POST" in path_methods[delete_path]


class TestChaptersRequestModels:
    """Test request models for chapters."""

    def test_create_chapter_request_model_exists(self) -> None:
        """CreateChapterRequest should exist with required fields."""
        from app.api.v1.chapters import CreateChapterRequest

        assert hasattr(CreateChapterRequest, "model_fields")
        fields = CreateChapterRequest.model_fields
        assert "title" in fields
        assert "content" in fields

    def test_create_chapter_request_optional_fields(self) -> None:
        """CreateChapterRequest should have optional word_count."""
        from app.api.v1.chapters import CreateChapterRequest

        fields = CreateChapterRequest.model_fields
        assert "word_count" in fields

    def test_update_chapter_request_model_exists(self) -> None:
        """UpdateChapterRequest should exist with optional fields."""
        from app.api.v1.chapters import UpdateChapterRequest

        assert hasattr(UpdateChapterRequest, "model_fields")

    def test_create_chapter_request_has_new_metadata_fields(self) -> None:
        """CreateChapterRequest should accept chapter_number / summary / published_at."""
        from app.api.v1.chapters import CreateChapterRequest

        fields = CreateChapterRequest.model_fields
        assert "chapter_number" in fields
        assert "summary" in fields
        assert "published_at" in fields

    def test_update_chapter_request_has_new_metadata_fields(self) -> None:
        """UpdateChapterRequest should accept chapter_number / summary / published_at."""
        from app.api.v1.chapters import UpdateChapterRequest

        fields = UpdateChapterRequest.model_fields
        assert "chapter_number" in fields
        assert "summary" in fields
        assert "published_at" in fields


class TestChaptersRouterRegistered:
    """Test that chapter router is registered in main app."""

    def test_chapter_router_in_app(self) -> None:
        """Chapter router should be included in the app."""
        from app.main import create_app

        app = create_app()
        routes = [cast(Any, r).path for r in app.routes]
        assert any("chapters" in r for r in routes)
