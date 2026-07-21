# Outline Tree Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the outline service layer to properly support the tree structure that the database already provides — cascade delete, `get_tree`, level validation, and complete return values.

**Architecture:** Extend `OutlineService` with recursive CTE queries for tree operations, add level validation enforcing root→volume→chapter hierarchy, and expose a new `GET /{id}/tree` API endpoint. The `ContentService` facade gets a thin delegation method.

**Tech Stack:** Python 3.13, FastAPI, aiosqlite, pytest

**Worktree:** `.claude/worktrees/outline-tree` on branch `feat/outline-tree`

**Spec:** `docs/superpowers/specs/2026-05-03-outline-tree-design.md`

---

### Task 1: Fix `OutlineService.create` return value

**Files:**
- Modify: `backend/app/services/outline.py:60-65`
- Test: `backend/tests/test_outlines_api.py`

The current `create` method returns only `{id, project_id, title, file_path}`, omitting `parent_id`, `type`, `sort_order`, `created_at`, `updated_at`.

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_outlines_api.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_outlines_api.py::TestOutlineCreateReturnValue::test_create_outline_returns_all_metadata -v`
Expected: FAIL — `KeyError: 'parent_id'`

- [ ] **Step 3: Fix `OutlineService.create` return value**

In `backend/app/services/outline.py`, change the return statement (lines 60-65):

```python
        return {
            "id": outline_id,
            "project_id": project_id,
            "parent_id": parent_id,
            "title": title,
            "type": outline_type,
            "sort_order": sort_order,
            "file_path": str(file_path),
            "created_at": None,  # populated by DB default
            "updated_at": None,
        }
```

Wait — the DB populates `created_at` and `updated_at` automatically. We should read them back. Replace the entire return block with a re-query:

```python
        # Re-fetch to get DB-populated timestamps
        cursor = await self.db.execute(
            "SELECT * FROM outlines_meta WHERE id = ? AND project_id = ?",
            (outline_id, project_id),
        )
        row = await cursor.fetchone()
        return dict(row)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_outlines_api.py::TestOutlineCreateReturnValue::test_create_outline_returns_all_metadata -v`
Expected: PASS

- [ ] **Step 5: Run full test suite to check for regressions**

Run: `cd backend && uv run pytest --tb=short`
Expected: All 153+ tests pass

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/outline.py backend/tests/test_outlines_api.py
git commit -m "fix(outline): return complete metadata from create"
```

---

### Task 2: Add `get_tree` method to `OutlineService`

**Files:**
- Modify: `backend/app/services/outline.py`
- Test: `backend/tests/test_outlines_api.py`

New method that recursively fetches the subtree rooted at a given node, returning a nested structure without `content`.

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_outlines_api.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_outlines_api.py::TestOutlineGetTree -v`
Expected: FAIL — `AttributeError: 'OutlineService' object has no attribute 'get_tree'`

- [ ] **Step 3: Implement `get_tree` in `OutlineService`**

Add to `backend/app/services/outline.py` after `list_all`:

```python
    async def get_tree(self, node_id: str, project_id: str) -> dict[str, Any] | None:
        """Recursively fetch the subtree rooted at node_id (without content).

        Returns a nested dict with children lists, or None if node not found.
        """
        # Fetch all descendants via recursive CTE
        cursor = await self.db.execute(
            """
            WITH RECURSIVE descendants AS (
                SELECT id, parent_id, title, type, sort_order
                FROM outlines_meta
                WHERE id = ? AND project_id = ?
                UNION ALL
                SELECT om.id, om.parent_id, om.title, om.type, om.sort_order
                FROM outlines_meta om
                JOIN descendants d ON om.parent_id = d.id
                WHERE om.project_id = ?
            )
            SELECT id, parent_id, title, type, sort_order FROM descendants
            """,
            (node_id, project_id, project_id),
        )
        rows = await cursor.fetchall()
        if not rows:
            return None

        # Build lookup: id -> node dict
        nodes: dict[str, dict[str, Any]] = {}
        for row in rows:
            nodes[row["id"]] = {
                "id": row["id"],
                "parent_id": row["parent_id"],
                "title": row["title"],
                "type": row["type"],
                "sort_order": row["sort_order"],
                "children": [],
            }

        # Assemble tree
        root = None
        for node in nodes.values():
            if node["id"] == node_id:
                root = node
            parent_id = node["parent_id"]
            if parent_id and parent_id in nodes:
                nodes[parent_id]["children"].append(node)

        # Sort children by sort_order at each level
        def _sort_children(node: dict[str, Any]) -> None:
            node["children"].sort(key=lambda c: c["sort_order"])
            for child in node["children"]:
                _sort_children(child)

        if root:
            _sort_children(root)
            # Remove parent_id from output (not useful in tree context)
            def _clean(node: dict[str, Any]) -> dict[str, Any]:
                return {
                    "id": node["id"],
                    "title": node["title"],
                    "type": node["type"],
                    "sort_order": node["sort_order"],
                    "children": [_clean(c) for c in node["children"]],
                }
            root = _clean(root)

        return root
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_outlines_api.py::TestOutlineGetTree -v`
Expected: 4 PASS

- [ ] **Step 5: Run full test suite**

Run: `cd backend && uv run pytest --tb=short`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/outline.py backend/tests/test_outlines_api.py
git commit -m "feat(outline): add get_tree method for recursive subtree fetching"
```

---

### Task 3: Add cascade delete to `OutlineService.delete`

**Files:**
- Modify: `backend/app/services/outline.py:128-152`
- Test: `backend/tests/test_outlines_api.py`

Current `delete` only deletes the single node. With the FK constraint, deleting a parent with children will fail. Fix it to cascade.

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_outlines_api.py`:

```python
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
        count = (await cursor.fetchone())[0]
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
        count = (await cursor.fetchone())[0]
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_outlines_api.py::TestOutlineCascadeDelete -v`
Expected: FAIL — `IntegrityError: FOREIGN KEY constraint failed` on the root delete test

- [ ] **Step 3: Implement cascade delete**

Replace `OutlineService.delete` in `backend/app/services/outline.py`:

```python
    async def delete(self, outline_id: str, project_id: str) -> bool:
        """Delete an outline and all its descendants (cascade).

        Args:
            outline_id: Unique identifier of the outline.
            project_id: Identifier of the owning project.

        Returns:
            True if the entity existed and was deleted, False otherwise.
        """
        # Collect all descendants (including self) via recursive CTE
        cursor = await self.db.execute(
            """
            WITH RECURSIVE descendants AS (
                SELECT id FROM outlines_meta WHERE id = ? AND project_id = ?
                UNION ALL
                SELECT om.id FROM outlines_meta om
                JOIN descendants d ON om.parent_id = d.id
                WHERE om.project_id = ?
            )
            SELECT id FROM descendants
            """,
            (outline_id, project_id, project_id),
        )
        rows = await cursor.fetchall()
        if not rows:
            return False

        ids_to_delete = [row["id"] for row in rows]

        # Fetch file paths for all nodes to delete
        placeholders = ",".join("?" for _ in ids_to_delete)
        cursor = await self.db.execute(
            f"SELECT id, file_path FROM outlines_meta WHERE id IN ({placeholders}) AND project_id = ?",
            [*ids_to_delete, project_id],
        )
        file_rows = await cursor.fetchall()
        files_to_delete = {row["id"]: Path(row["file_path"]) for row in file_rows}

        # Delete metadata (children first to respect FK)
        for del_id in reversed(ids_to_delete):
            await self.db.execute(
                "DELETE FROM outlines_meta WHERE id = ? AND project_id = ?",
                (del_id, project_id),
            )
        await self.db.commit()

        # Delete files
        for file_path in files_to_delete.values():
            await self.storage.delete(file_path)

        return True
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_outlines_api.py::TestOutlineCascadeDelete -v`
Expected: 3 PASS

- [ ] **Step 5: Run full test suite**

Run: `cd backend && uv run pytest --tb=short`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/outline.py backend/tests/test_outlines_api.py
git commit -m "feat(outline): cascade delete removes all descendants and their files"
```

---

### Task 4: Add level validation to `OutlineService.create`

**Files:**
- Modify: `backend/app/services/outline.py`
- Test: `backend/tests/test_outlines_api.py`

Enforce the fixed 3-level hierarchy: root (no parent) → volume (parent is root) → chapter (parent is volume). One root per project.

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_outlines_api.py`:

```python
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

        with pytest.raises(ValueError, match="root.*parent_id"):
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

        # Create a volume as parent (not a root)
        await service.create("proj1", "vol1", "Vol", "content", "volume")

        with pytest.raises(ValueError, match="volume.*root"):
            await service.create("proj1", "bad_ch", "Ch", "content", "volume", parent_id="vol1")

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

        with pytest.raises(ValueError, match="chapter.*volume"):
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_outlines_api.py::TestOutlineLevelValidation -v`
Expected: FAIL — validation errors not raised

- [ ] **Step 3: Implement level validation**

Add to `backend/app/services/outline.py` at the top of the `create` method (after the docstring, before `file_path = ...`):

```python
        # Validate level constraints (only for hierarchical types; other types like "main" skip validation)
        if outline_type == "root":
            if parent_id is not None:
                raise ValueError("Root outline must not have a parent_id")
            existing_root = await self.get_root(project_id)
            if existing_root:
                raise ValueError(f"Root outline already exists for project {project_id}")
        elif outline_type == "volume":
            if parent_id is None:
                raise ValueError("Volume outline must have a parent_id")
            parent = await self.get(parent_id, project_id)
            if not parent or parent["type"] != "root":
                raise ValueError("Volume outline parent must be a root outline")
        elif outline_type == "chapter":
            if parent_id is None:
                raise ValueError("Chapter outline must have a parent_id")
            parent = await self.get(parent_id, project_id)
            if not parent or parent["type"] != "volume":
                raise ValueError("Chapter outline parent must be a volume outline")
        # Other types (e.g., "main", "section") are treated as flat/legacy outlines
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_outlines_api.py::TestOutlineLevelValidation -v`
Expected: 5 PASS

- [ ] **Step 5: Run full test suite**

Run: `cd backend && uv run pytest --tb=short`
Expected: All tests pass (note: existing tests use `type="chapter"` with no parent — these are flat outlines that don't trigger validation since `chapter` without `parent_id` will now raise. Check if existing tests need updating.)

If existing tests fail: they create outlines without proper parent chains. Specifically:
- `test_content_service.py:92` creates `type="main"` with `parent_id=None` — this bypasses validation since "main" is not root/volume/chapter
- `test_content_service.py:240` creates `type="main"` with `parent_id=None` — same
- Any test using `type="chapter"` without a parent will now fail — fix by changing to `type="main"` or adding the parent chain
- The validation only triggers for types `root`, `volume`, `chapter`. Other types (like `"main"`) are treated as legacy/flat outlines and skip validation.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/outline.py backend/tests/test_outlines_api.py
git commit -m "feat(outline): enforce root→volume→chapter hierarchy in create"
```

---

### Task 5: Add `get_outline_tree` to `ContentService` facade

**Files:**
- Modify: `backend/app/services/content.py`
- Test: `backend/tests/test_outlines_api.py`

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_outlines_api.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_outlines_api.py::TestContentServiceGetTree -v`
Expected: FAIL — `AttributeError`

- [ ] **Step 3: Add delegation method**

Add to `backend/app/services/content.py` after `get_all_outlines`:

```python
    async def get_outline_tree(self, outline_id: str, project_id: str) -> dict[str, Any] | None:
        """Retrieve the subtree rooted at outline_id (without content)."""
        return await self._outline.get_tree(outline_id, project_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_outlines_api.py::TestContentServiceGetTree -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/content.py backend/tests/test_outlines_api.py
git commit -m "feat(outline): add get_outline_tree to ContentService facade"
```

---

### Task 6: Add `GET /{outline_id}/tree` API endpoint

**Files:**
- Modify: `backend/app/api/v1/outlines.py`
- Test: `backend/tests/test_outlines_api.py`

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_outlines_api.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_outlines_api.py::TestOutlineTreeEndpoint -v`
Expected: FAIL — tree_path not in path_methods

- [ ] **Step 3: Add the endpoint**

Add to `backend/app/api/v1/outlines.py` after the `get_outline_children` endpoint:

```python
@router.get("/{outline_id}/tree")
async def get_outline_tree(project_id: str, outline_id: str) -> dict[str, Any]:
    """Get the full subtree rooted at outline_id (without content)."""
    async with get_db() as db:
        service = ContentService(db)
        tree = await service.get_outline_tree(outline_id, project_id)
        if not tree:
            raise HTTPException(status_code=404, detail="Outline not found")
        return tree
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_outlines_api.py::TestOutlineTreeEndpoint -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `cd backend && uv run pytest --tb=short`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/outlines.py backend/tests/test_outlines_api.py
git commit -m "feat(api): add GET /{outline_id}/tree endpoint"
```

---

### Task 7: Final verification

- [ ] **Step 1: Run full test suite**

Run: `cd backend && uv run pytest --tb=short -v`
Expected: All tests pass

- [ ] **Step 2: Run type checker**

Run: `cd backend && uv run mypy app`
Expected: No new errors (pre-existing errors are acceptable)

- [ ] **Step 3: Run linter**

Run: `cd backend && uv run ruff check app tests`
Expected: No new issues

- [ ] **Step 4: Run formatter check**

Run: `cd backend && uv run ruff format --check app tests`
Expected: All files formatted

- [ ] **Step 5: Final commit (if needed for formatting fixes)**

```bash
git add -A
git commit -m "style: format and lint fixes for outline tree changes"
```
