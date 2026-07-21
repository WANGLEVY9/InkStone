"""Tests for World Settings API endpoints (TDD - RED phase)."""

from __future__ import annotations

from typing import Any, cast


class TestWorldSettingsAPI:
    """Test world settings CRUD endpoints."""

    def test_world_router_exists(self) -> None:
        """World router should exist in api/v1."""
        from app.api.v1.world import router

        assert router is not None
        assert router.prefix == "/projects/{project_id}/world"

    def test_world_list_endpoint_exists(self) -> None:
        """GET / should list all world settings."""
        from app.api.v1.world import router

        # Collect all methods for each path
        path_methods: dict[str, set[str]] = {}
        for r in router.routes:
            route = cast(Any, r)
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        list_path = "/projects/{project_id}/world/"
        assert list_path in path_methods
        assert "GET" in path_methods[list_path]
        assert "POST" in path_methods[list_path]

    def test_world_get_single_endpoint_exists(self) -> None:
        """GET /{world_id} should get a single world setting."""
        from app.api.v1.world import router

        routes: dict[str, Any] = {cast(Any, r).path: r for r in router.routes}
        get_path = "/projects/{project_id}/world/{world_id}"
        assert get_path in routes
        assert routes[get_path].methods == {"GET"}

    def test_world_update_endpoint_exists(self) -> None:
        """POST /{world_id}/update should update a world setting."""
        from app.api.v1.world import router

        routes: dict[str, Any] = {cast(Any, r).path: r for r in router.routes}
        update_path = "/projects/{project_id}/world/{world_id}/update"
        assert update_path in routes
        assert routes[update_path].methods == {"POST"}

    def test_world_delete_endpoint_exists(self) -> None:
        """POST /{world_id}/delete should delete a world setting."""
        from app.api.v1.world import router

        routes: dict[str, Any] = {cast(Any, r).path: r for r in router.routes}
        delete_path = "/projects/{project_id}/world/{world_id}/delete"
        assert delete_path in routes
        assert routes[delete_path].methods == {"POST"}


class TestWorldSettingsRequestModels:
    """Test request models for world settings."""

    def test_create_world_request_model_exists(self) -> None:
        """CreateWorldRequest should exist with required fields."""
        from app.api.v1.world import CreateWorldRequest

        assert hasattr(CreateWorldRequest, "model_fields")
        fields = CreateWorldRequest.model_fields
        assert "name" in fields
        assert "content" in fields

    def test_create_world_request_optional_summary(self) -> None:
        """CreateWorldRequest should have optional summary field."""
        from app.api.v1.world import CreateWorldRequest

        fields = CreateWorldRequest.model_fields
        assert "summary" in fields

    def test_update_world_request_model_exists(self) -> None:
        """UpdateWorldRequest should exist with optional fields."""
        from app.api.v1.world import UpdateWorldRequest

        assert hasattr(UpdateWorldRequest, "model_fields")


class TestWorldRouterRegistered:
    """Test that world router is registered in main app."""

    def test_world_router_in_app(self) -> None:
        """World router should be included in the app."""
        from app.main import create_app

        app = create_app()
        routes = [cast(Any, r).path for r in app.routes]
        assert any("world" in r for r in routes)
