"""Tests for Characters API endpoints."""

from __future__ import annotations

from typing import Any, cast


class TestCharactersAPI:
    """Test character CRUD endpoints."""

    def test_character_router_exists(self) -> None:
        """Character router should exist in api/v1."""
        from app.api.v1.characters import router

        assert router is not None
        assert router.prefix == "/projects/{project_id}/characters"

    def test_character_list_endpoint_exists(self) -> None:
        """GET / should list all characters; POST / should create."""
        from app.api.v1.characters import router

        path_methods: dict[str, set[str]] = {}
        for r in router.routes:
            route = cast(Any, r)
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        list_path = "/projects/{project_id}/characters/"
        assert list_path in path_methods
        assert "GET" in path_methods[list_path]
        assert "POST" in path_methods[list_path]

    def test_character_get_single_endpoint_exists(self) -> None:
        """GET /{character_id} should get a single character."""
        from app.api.v1.characters import router

        routes = {cast(Any, r).path: cast(Any, r) for r in router.routes}
        get_path = "/projects/{project_id}/characters/{character_id}"
        assert get_path in routes
        assert routes[get_path].methods == {"GET"}

    def test_character_update_endpoint_exists(self) -> None:
        """POST /{character_id}/update should update a character."""
        from app.api.v1.characters import router

        routes = {cast(Any, r).path: cast(Any, r) for r in router.routes}
        update_path = "/projects/{project_id}/characters/{character_id}/update"
        assert update_path in routes
        assert routes[update_path].methods == {"POST"}

    def test_character_delete_endpoint_exists(self) -> None:
        """POST /{character_id}/delete should delete a character."""
        from app.api.v1.characters import router

        routes = {cast(Any, r).path: cast(Any, r) for r in router.routes}
        delete_path = "/projects/{project_id}/characters/{character_id}/delete"
        assert delete_path in routes
        assert routes[delete_path].methods == {"POST"}


class TestCharactersRequestModels:
    """Test request models for characters."""

    def test_create_character_request_model_exists(self) -> None:
        """CreateCharacterRequest should exist with required fields."""
        from app.api.v1.characters import CreateCharacterRequest

        assert hasattr(CreateCharacterRequest, "model_fields")
        fields = CreateCharacterRequest.model_fields
        assert "name" in fields
        assert "content" in fields

    def test_create_character_request_optional_summary(self) -> None:
        """CreateCharacterRequest should have optional summary field."""
        from app.api.v1.characters import CreateCharacterRequest

        fields = CreateCharacterRequest.model_fields
        assert "summary" in fields

    def test_update_character_request_model_exists(self) -> None:
        """UpdateCharacterRequest should exist with optional fields."""
        from app.api.v1.characters import UpdateCharacterRequest

        assert hasattr(UpdateCharacterRequest, "model_fields")


class TestCharactersRouterRegistered:
    """Test that character router is registered in main app."""

    def test_character_router_in_app(self) -> None:
        """Character router should be included in the app."""
        from app.main import create_app

        app = create_app()
        routes = [cast(Any, r).path for r in app.routes]
        assert any("characters" in r for r in routes)
