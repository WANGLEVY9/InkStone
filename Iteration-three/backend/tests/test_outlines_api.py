"""Tests for Outlines API endpoints (TDD - RED phase)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest


class TestOutlinesAPI:
    """Test outlines CRUD endpoints."""

    def test_outline_router_exists(self) -> None:
        """Outline router should exist in api/v1."""
        from app.api.v1.outlines import router

        assert router is not None
        assert router.prefix == "/projects/{project_id}/outlines"

    def test_outline_list_endpoint_exists(self) -> None:
        """GET / should get root outline (tree structure)."""
        from app.api.v1.outlines import router

        path_methods: dict[str, set[str]] = {}
        for r in router.routes:
            route = cast(Any, r)
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        list_path = "/projects/{project_id}/outlines/"
        assert list_path in path_methods
        assert "GET" in path_methods[list_path]

    def test_outline_create_endpoint_exists(self) -> None:
        """POST / should create an outline node."""
        from app.api.v1.outlines import router

        path_methods: dict[str, set[str]] = {}
        for r in router.routes:
            route = cast(Any, r)
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        list_path = "/projects/{project_id}/outlines/"
        assert "POST" in path_methods[list_path]

    def test_outline_get_single_endpoint_exists(self) -> None:
        """GET /{outline_id} should get a single outline."""
        from app.api.v1.outlines import router

        path_methods: dict[str, set[str]] = {}
        for r in router.routes:
            route = cast(Any, r)
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        get_path = "/projects/{project_id}/outlines/{outline_id}"
        assert get_path in path_methods
        assert "GET" in path_methods[get_path]

    def test_outline_children_endpoint_exists(self) -> None:
        """GET /{outline_id}/children should get children."""
        from app.api.v1.outlines import router

        path_methods: dict[str, set[str]] = {}
        for r in router.routes:
            route = cast(Any, r)
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        children_path = "/projects/{project_id}/outlines/{outline_id}/children"
        assert children_path in path_methods
        assert "GET" in path_methods[children_path]

    def test_outline_update_endpoint_exists(self) -> None:
        """POST /{outline_id}/update should update outline."""
        from app.api.v1.outlines import router

        path_methods: dict[str, set[str]] = {}
        for r in router.routes:
            route = cast(Any, r)
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        update_path = "/projects/{project_id}/outlines/{outline_id}/update"
        assert update_path in path_methods
        assert "POST" in path_methods[update_path]

    def test_outline_delete_endpoint_exists(self) -> None:
        """POST /{outline_id}/delete should delete outline."""
        from app.api.v1.outlines import router

        path_methods: dict[str, set[str]] = {}
        for r in router.routes:
            route = cast(Any, r)
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        delete_path = "/projects/{project_id}/outlines/{outline_id}/delete"
        assert delete_path in path_methods
        assert "POST" in path_methods[delete_path]


class TestOutlinesRequestModels:
    """Test request models for outlines."""

    def test_create_outline_request_model_exists(self) -> None:
        """CreateOutlineRequest should exist with required fields."""
        from app.api.v1.outlines import CreateOutlineRequest

        assert hasattr(CreateOutlineRequest, "model_fields")
        fields = CreateOutlineRequest.model_fields
        assert "title" in fields
        assert "content" in fields
        assert "type" in fields

    def test_create_outline_request_optional_fields(self) -> None:
        """CreateOutlineRequest should have optional parent_id and sort_order."""
        from app.api.v1.outlines import CreateOutlineRequest

        fields = CreateOutlineRequest.model_fields
        assert "parent_id" in fields
        assert "sort_order" in fields

    def test_update_outline_request_model_exists(self) -> None:
        """UpdateOutlineRequest should exist with optional fields."""
        from app.api.v1.outlines import UpdateOutlineRequest

        assert hasattr(UpdateOutlineRequest, "model_fields")


class TestOutlinesRouterRegistered:
    """Test that outline router is registered in main app."""

    def test_outline_router_in_app(self) -> None:
        """Outline router should be included in the app."""
        from app.main import create_app

        app = create_app()
        routes = [cast(Any, r).path for r in app.routes]
        assert any("outlines" in r for r in routes)


class TestOutlineGetTree:
    """Test OutlineService.get_tree recursive tree fetching."""

    @pytest.fixture
    def db_with_tree(self, tmp_path: Path) -> tuple[str, Path]:
        """Create a test database with a 3-level outline tree."""
        import sqlite3
        import tempfile

        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_db.close()
        schema_path = Path(__file__).parent.parent / "app" / "db" / "schema.sql"
        conn = sqlite3.connect(temp_db.name)
        conn.executescript(schema_path.read_text())

        # Create tree: root -> vol1 -> ch1, ch2; vol2 -> ch3
        for node_id, parent_id, title, node_type, sort_order in [
            ("root1", None, "全书大纲", "root", 0),
            ("vol1", "root1", "第一卷", "volume", 1),
            ("vol2", "root1", "第二卷", "volume", 2),
            ("ch1", "vol1", "第一章", "chapter", 1),
            ("ch2", "vol1", "第二章", "chapter", 2),
            ("ch3", "vol2", "第三章", "chapter", 1),
        ]:
            file_path = f"proj1/outlines/{node_id}.md"
            conn.execute(
                "INSERT INTO outlines_meta (id, project_id, parent_id, title, file_path, type, sort_order) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (node_id, "proj1", parent_id, title, file_path, node_type, sort_order),
            )
        conn.commit()
        conn.close()

        return temp_db.name, tmp_path

    @pytest.mark.asyncio
    async def test_get_tree_returns_full_subtree(self, db_with_tree: tuple[str, Path]) -> None:
        """get_tree should return the full nested tree from root."""
        import aiosqlite

        from app.services.outline import OutlineService

        db_path, _ = db_with_tree
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        service = OutlineService(db)

        tree = await service.get_tree("root1", "proj1")

        await db.close()

        assert tree is not None
        assert tree["id"] == "root1"
        assert tree["type"] == "root"
        assert len(tree["children"]) == 2

        vol1 = tree["children"][0]
        assert vol1["id"] == "vol1"
        assert vol1["type"] == "volume"
        assert len(vol1["children"]) == 2
        assert vol1["children"][0]["id"] == "ch1"
        assert vol1["children"][1]["id"] == "ch2"

        vol2 = tree["children"][1]
        assert vol2["id"] == "vol2"
        assert len(vol2["children"]) == 1
        assert vol2["children"][0]["id"] == "ch3"

    @pytest.mark.asyncio
    async def test_get_tree_excludes_content(self, db_with_tree: tuple[str, Path]) -> None:
        """get_tree should not include content field."""
        import aiosqlite

        from app.services.outline import OutlineService

        db_path, _ = db_with_tree
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        service = OutlineService(db)

        tree = await service.get_tree("root1", "proj1")

        await db.close()

        assert tree is not None
        assert "content" not in tree
        for child in tree["children"]:
            assert "content" not in child

    @pytest.mark.asyncio
    async def test_get_tree_leaf_node_has_empty_children(self, db_with_tree: tuple[str, Path]) -> None:
        """Leaf nodes should have children = []."""
        import aiosqlite

        from app.services.outline import OutlineService

        db_path, _ = db_with_tree
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        service = OutlineService(db)

        tree = await service.get_tree("root1", "proj1")

        await db.close()

        assert tree is not None
        chapter = tree["children"][0]["children"][0]
        assert chapter["children"] == []

    @pytest.mark.asyncio
    async def test_get_tree_nonexistent_returns_none(self, db_with_tree: tuple[str, Path]) -> None:
        """get_tree should return None for nonexistent node."""
        import aiosqlite

        from app.services.outline import OutlineService

        db_path, _ = db_with_tree
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        service = OutlineService(db)

        result = await service.get_tree("nonexistent", "proj1")

        await db.close()

        assert result is None


class TestOutlineCreateReturnValue:
    """Test that create_outline returns complete metadata."""

    @pytest.mark.asyncio
    async def test_create_outline_returns_all_metadata(self, tmp_path: Path) -> None:
        """create_outline should return id, project_id, parent_id, title, type, sort_order, file_path."""
        import sqlite3
        import tempfile

        import aiosqlite

        from app.services.content import ContentService, FileSystemStorage

        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_db.close()
        schema_path = Path(__file__).parent.parent / "app" / "db" / "schema.sql"
        conn = sqlite3.connect(temp_db.name)
        conn.executescript(schema_path.read_text())
        conn.close()

        db = await aiosqlite.connect(temp_db.name)
        db.row_factory = aiosqlite.Row
        storage = FileSystemStorage(tmp_path)
        service = ContentService(db, storage)

        result = await service.create_outline(
            project_id="proj1",
            outline_id="root1",
            title="全书大纲",
            content="# 大纲内容",
            outline_type="root",
            parent_id=None,
            sort_order=0,
        )

        await db.close()
        Path(temp_db.name).unlink(missing_ok=True)

        assert result["id"] == "root1"
        assert result["project_id"] == "proj1"
        assert result["parent_id"] is None
        assert result["title"] == "全书大纲"
        assert result["type"] == "root"
        assert result["sort_order"] == 0
        assert "file_path" in result
        assert "created_at" in result
        assert "updated_at" in result


class TestContentServiceGetTree:
    """Test ContentService.get_outline_tree delegation."""

    def test_get_outline_tree_method_exists(self) -> None:
        """ContentService should have get_outline_tree method."""
        import inspect

        from app.services.content import ContentService

        assert hasattr(ContentService, "get_outline_tree")
        sig = inspect.signature(ContentService.get_outline_tree)
        params = list(sig.parameters.keys())
        assert "outline_id" in params
        assert "project_id" in params


class TestOutlineTreeEndpoint:
    """Test GET /{outline_id}/tree endpoint."""

    def test_tree_endpoint_exists(self) -> None:
        """GET /{outline_id}/tree route should exist."""
        from app.api.v1.outlines import router

        path_methods: dict[str, set[str]] = {}
        for r in router.routes:
            route = cast(Any, r)
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        tree_path = "/projects/{project_id}/outlines/{outline_id}/tree"
        assert tree_path in path_methods
        assert "GET" in path_methods[tree_path]


class TestOutlineLevelValidation:
    """Test that create enforces the 3-level hierarchy."""

    @pytest.fixture
    def empty_db(self, tmp_path: Path) -> tuple[str, Path]:
        """Create an empty test database."""
        import sqlite3
        import tempfile

        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_db.close()
        schema_path = Path(__file__).parent.parent / "app" / "db" / "schema.sql"
        conn = sqlite3.connect(temp_db.name)
        conn.executescript(schema_path.read_text())
        conn.close()

        return temp_db.name, tmp_path

    @pytest.mark.asyncio
    async def test_root_must_not_have_parent(self, empty_db: tuple[str, Path]) -> None:
        """Creating a root node with a parent_id should raise ValueError."""
        import aiosqlite

        from app.services.outline import OutlineService

        db_path, _ = empty_db
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        service = OutlineService(db)

        with pytest.raises(ValueError, match="(?i)root.*parent_id"):
            await service.create("proj1", "bad_root", "Root", "content", "root", parent_id="some_parent")

        await db.close()

    @pytest.mark.asyncio
    async def test_volume_parent_must_be_root(self, empty_db: tuple[str, Path]) -> None:
        """Creating a volume under a non-root parent should raise ValueError."""
        import aiosqlite

        from app.services.outline import OutlineService

        db_path, _ = empty_db
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        service = OutlineService(db)

        # Create root -> volume hierarchy
        await service.create("proj1", "root1", "Root", "content", "root")
        await service.create("proj1", "vol1", "Vol", "content", "volume", parent_id="root1")

        # Creating a volume under a volume (not a root) should fail
        with pytest.raises(ValueError, match="(?i)volume.*root"):
            await service.create("proj1", "bad_vol", "BadVol", "content", "volume", parent_id="vol1")

        await db.close()

    @pytest.mark.asyncio
    async def test_chapter_parent_must_be_volume(self, empty_db: tuple[str, Path]) -> None:
        """Creating a chapter under a root should raise ValueError."""
        import aiosqlite

        from app.services.outline import OutlineService

        db_path, _ = empty_db
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        service = OutlineService(db)

        await service.create("proj1", "root1", "Root", "content", "root")

        with pytest.raises(ValueError, match="(?i)chapter.*volume"):
            await service.create("proj1", "bad_ch", "Ch", "content", "chapter", parent_id="root1")

        await db.close()

    @pytest.mark.asyncio
    async def test_only_one_root_per_project(self, empty_db: tuple[str, Path]) -> None:
        """Creating a second root for the same project should raise ValueError."""
        import aiosqlite

        from app.services.outline import OutlineService

        db_path, _ = empty_db
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        service = OutlineService(db)

        await service.create("proj1", "root1", "Root 1", "content", "root")

        with pytest.raises(ValueError, match="already exists"):
            await service.create("proj1", "root2", "Root 2", "content", "root")

        await db.close()

    @pytest.mark.asyncio
    async def test_valid_tree_creation_succeeds(self, empty_db: tuple[str, Path]) -> None:
        """Creating root -> volume -> chapter should succeed."""
        import aiosqlite

        from app.services.outline import OutlineService

        db_path, _ = empty_db
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        service = OutlineService(db)

        root = await service.create("proj1", "root1", "Root", "content", "root")
        vol = await service.create("proj1", "vol1", "Vol", "content", "volume", parent_id="root1")
        ch = await service.create("proj1", "ch1", "Ch", "content", "chapter", parent_id="vol1")

        await db.close()

        assert root["type"] == "root"
        assert vol["parent_id"] == "root1"
        assert ch["parent_id"] == "vol1"


class TestOutlineCascadeDelete:
    """Test that deleting a parent node cascades to children."""

    @pytest.fixture
    def db_with_tree_and_files(self, tmp_path: Path) -> tuple[str, Path]:
        """Create a test database with a tree and corresponding .md files."""
        import sqlite3
        import tempfile

        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_db.close()
        schema_path = Path(__file__).parent.parent / "app" / "db" / "schema.sql"
        conn = sqlite3.connect(temp_db.name)
        conn.executescript(schema_path.read_text())

        proj_dir = tmp_path / "proj1" / "outlines"
        proj_dir.mkdir(parents=True)

        for node_id, parent_id, title, node_type, sort_order in [
            ("root1", None, "全书大纲", "root", 0),
            ("vol1", "root1", "第一卷", "volume", 1),
            ("ch1", "vol1", "第一章", "chapter", 1),
        ]:
            file_path = f"proj1/outlines/{node_id}.md"
            (tmp_path / file_path).write_text(f"Content of {title}")
            conn.execute(
                "INSERT INTO outlines_meta (id, project_id, parent_id, title, file_path, type, sort_order) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (node_id, "proj1", parent_id, title, file_path, node_type, sort_order),
            )
        conn.commit()
        conn.close()

        return temp_db.name, tmp_path

    @pytest.mark.asyncio
    async def test_delete_root_cascades_to_all_descendants(self, db_with_tree_and_files: tuple[str, Path]) -> None:
        """Deleting the root should delete all descendants and their files."""
        import aiosqlite

        from app.services.outline import OutlineService
        from app.services.storage import FileSystemStorage

        db_path, tmp_path = db_with_tree_and_files
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        storage = FileSystemStorage(tmp_path)
        service = OutlineService(db, storage)

        result = await service.delete("root1", "proj1")

        # Verify all nodes deleted
        cursor = await db.execute("SELECT COUNT(*) FROM outlines_meta WHERE project_id = 'proj1'")
        row = await cursor.fetchone()
        assert row is not None
        count = row[0]
        await db.close()

        assert result is True
        assert count == 0
        # Verify files deleted
        assert not (tmp_path / "proj1/outlines/root1.md").exists()
        assert not (tmp_path / "proj1/outlines/vol1.md").exists()
        assert not (tmp_path / "proj1/outlines/ch1.md").exists()

    @pytest.mark.asyncio
    async def test_delete_leaf_node_only_deletes_that_node(self, db_with_tree_and_files: tuple[str, Path]) -> None:
        """Deleting a leaf should only delete that one node."""
        import aiosqlite

        from app.services.outline import OutlineService
        from app.services.storage import FileSystemStorage

        db_path, tmp_path = db_with_tree_and_files
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        storage = FileSystemStorage(tmp_path)
        service = OutlineService(db, storage)

        result = await service.delete("ch1", "proj1")

        cursor = await db.execute("SELECT COUNT(*) FROM outlines_meta WHERE project_id = 'proj1'")
        row = await cursor.fetchone()
        assert row is not None
        count = row[0]
        await db.close()

        assert result is True
        assert count == 2  # root and vol1 remain
        assert not (tmp_path / "proj1/outlines/ch1.md").exists()
        assert (tmp_path / "proj1/outlines/root1.md").exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(self, db_with_tree_and_files: tuple[str, Path]) -> None:
        """Deleting a nonexistent node should return False."""
        import aiosqlite

        from app.services.outline import OutlineService
        from app.services.storage import FileSystemStorage

        db_path, tmp_path = db_with_tree_and_files
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        storage = FileSystemStorage(tmp_path)
        service = OutlineService(db, storage)

        result = await service.delete("nonexistent", "proj1")

        await db.close()

        assert result is False


class TestOutlineAPIIntegration:
    """Integration tests using FastAPI TestClient."""

    def test_cascade_delete_via_api(self) -> None:
        """Deleting a parent node via API should cascade to all descendants."""
        from fastapi.testclient import TestClient

        from app.main import create_app

        app = create_app()
        with TestClient(app) as c:
            r = c.post("/api/v1/projects/", json={"name": "outline-cascade-test"})
            assert r.status_code == 200, r.text
            pid = r.json()["id"]

            try:
                # Create root
                r = c.post(
                    f"/api/v1/projects/{pid}/outlines/",
                    json={"title": "Root", "content": "# Root", "type": "root"},
                )
                assert r.status_code == 200, r.text
                root_id = r.json()["id"]

                # Create volume under root
                r = c.post(
                    f"/api/v1/projects/{pid}/outlines/",
                    json={"title": "Vol1", "content": "# Vol1", "type": "volume", "parent_id": root_id},
                )
                assert r.status_code == 200, r.text
                vol_id = r.json()["id"]

                # Create chapter under volume
                r = c.post(
                    f"/api/v1/projects/{pid}/outlines/",
                    json={"title": "Ch1", "content": "# Ch1", "type": "chapter", "parent_id": vol_id},
                )
                assert r.status_code == 200, r.text
                ch_id = r.json()["id"]

                # Delete root — should cascade
                r = c.post(f"/api/v1/projects/{pid}/outlines/{root_id}/delete")
                assert r.status_code == 200
                assert r.json()["status"] == "deleted"

                # Verify all nodes gone
                r = c.get(f"/api/v1/projects/{pid}/outlines/{root_id}")
                assert r.status_code == 404
                r = c.get(f"/api/v1/projects/{pid}/outlines/{vol_id}")
                assert r.status_code == 404
                r = c.get(f"/api/v1/projects/{pid}/outlines/{ch_id}")
                assert r.status_code == 404
            finally:
                c.delete(f"/api/v1/projects/{pid}")

    def test_level_validation_returns_422(self) -> None:
        """Creating an outline with invalid hierarchy should return 422."""
        from fastapi.testclient import TestClient

        from app.main import create_app

        app = create_app()
        with TestClient(app) as c:
            r = c.post("/api/v1/projects/", json={"name": "outline-validation-test"})
            assert r.status_code == 200, r.text
            pid = r.json()["id"]

            try:
                # Create root
                r = c.post(
                    f"/api/v1/projects/{pid}/outlines/",
                    json={"title": "Root", "content": "# Root", "type": "root"},
                )
                assert r.status_code == 200, r.text
                root_id = r.json()["id"]

                # Try to create chapter directly under root (should be under volume) — 422
                r = c.post(
                    f"/api/v1/projects/{pid}/outlines/",
                    json={"title": "Bad Ch", "content": "# Bad", "type": "chapter", "parent_id": root_id},
                )
                assert r.status_code == 422
                assert "volume" in r.json()["detail"].lower()

                # Try to create a second root — 422
                r = c.post(
                    f"/api/v1/projects/{pid}/outlines/",
                    json={"title": "Root2", "content": "# Root2", "type": "root"},
                )
                assert r.status_code == 422
                assert "already exists" in r.json()["detail"].lower()

                # Try to create root with parent_id — 422
                r = c.post(
                    f"/api/v1/projects/{pid}/outlines/",
                    json={"title": "Bad Root", "content": "# Bad", "type": "root", "parent_id": root_id},
                )
                assert r.status_code == 422
            finally:
                c.delete(f"/api/v1/projects/{pid}")

    def test_get_tree_via_api(self) -> None:
        """GET /{id}/tree should return correct nested structure."""
        from fastapi.testclient import TestClient

        from app.main import create_app

        app = create_app()
        with TestClient(app) as c:
            r = c.post("/api/v1/projects/", json={"name": "outline-tree-test"})
            assert r.status_code == 200, r.text
            pid = r.json()["id"]

            try:
                # Create root
                r = c.post(
                    f"/api/v1/projects/{pid}/outlines/",
                    json={"title": "Root", "content": "# Root", "type": "root"},
                )
                assert r.status_code == 200
                root_id = r.json()["id"]

                # Create volume
                r = c.post(
                    f"/api/v1/projects/{pid}/outlines/",
                    json={
                        "title": "Vol1",
                        "content": "# Vol1",
                        "type": "volume",
                        "parent_id": root_id,
                        "sort_order": 1,
                    },
                )
                assert r.status_code == 200
                vol_id = r.json()["id"]

                # Create chapter
                r = c.post(
                    f"/api/v1/projects/{pid}/outlines/",
                    json={"title": "Ch1", "content": "# Ch1", "type": "chapter", "parent_id": vol_id, "sort_order": 1},
                )
                assert r.status_code == 200
                ch_id = r.json()["id"]

                # Get tree
                r = c.get(f"/api/v1/projects/{pid}/outlines/{root_id}/tree")
                assert r.status_code == 200
                tree = r.json()

                # Verify structure
                assert tree["id"] == root_id
                assert tree["type"] == "root"
                assert "content" not in tree  # tree does not include content
                assert len(tree["children"]) == 1

                vol = tree["children"][0]
                assert vol["id"] == vol_id
                assert vol["type"] == "volume"
                assert len(vol["children"]) == 1

                ch = vol["children"][0]
                assert ch["id"] == ch_id
                assert ch["type"] == "chapter"
                assert ch["children"] == []

                # 404 for nonexistent
                r = c.get(f"/api/v1/projects/{pid}/outlines/nonexistent/tree")
                assert r.status_code == 404
            finally:
                c.delete(f"/api/v1/projects/{pid}")
