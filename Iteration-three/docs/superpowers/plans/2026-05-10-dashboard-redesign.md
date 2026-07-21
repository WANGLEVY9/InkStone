# Dashboard Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the Dashboard from a plain project listing into a left-right split layout with a GitHub-style activity heatmap, bookshelf metaphor for projects, and interactive controls (sort/filter/pin/view toggle).

**Architecture:** Left panel (280px fixed) shows heatmap + stats in a grid mosaic. Right panel shows a bookshelf of project book covers with a control bar. Backend gains an `activity_log` table and a heatmap API endpoint. Content services log activity on create/update/delete. `projects` table gains `is_pinned` column.

**Tech Stack:** React 18 + TypeScript + Ant Design 5, `react-activity-calendar` for heatmap, custom CSS for bookshelf. Python FastAPI + aiosqlite for backend.

**Spec:** [2026-05-10-dashboard-redesign-design.md](../specs/2026-05-10-dashboard-redesign-design.md)

---

## File Map

### Backend — Create
| File | Responsibility |
|------|---------------|
| `backend/app/services/activity_repository.py` | Standalone functions for activity_log CRUD + heatmap aggregation |
| `backend/app/api/v1/activity.py` | FastAPI router for `GET /api/v1/activity/heatmap` |

### Backend — Modify
| File | Change |
|------|--------|
| `backend/app/db/schema.sql` | Add `activity_log` table + `is_pinned` column to `projects` |
| `backend/app/services/project_repository.py` | Add `is_pinned` to allowed update fields |
| `backend/app/api/v1/projects.py` | Add `is_pinned` to `UpdateProjectRequest` |
| `backend/app/services/world.py` | Add activity logging in `create`, `update`, `delete` |
| `backend/app/services/character.py` | Same |
| `backend/app/services/outline.py` | Same |
| `backend/app/services/chapter.py` | Same |
| `backend/app/services/review.py` | Same (create, delete only — no update) |
| `backend/app/main.py` | Register activity router |

### Frontend — Create
| File | Responsibility |
|------|---------------|
| `frontend/src/api/activity.ts` | API client for heatmap endpoint |
| `frontend/src/components/dashboard/ActivityHeatmap.tsx` | Heatmap component using `react-activity-calendar` |
| `frontend/src/components/dashboard/LeftPanel.tsx` | Left panel: heatmap + stat cards in grid mosaic |
| `frontend/src/components/dashboard/BookCover.tsx` | Single book cover component |
| `frontend/src/components/dashboard/BookshelfView.tsx` | Bookshelf layout with wooden shelves |
| `frontend/src/components/dashboard/ListView.tsx` | Alternative list view for projects |
| `frontend/src/components/dashboard/ControlBar.tsx` | Search + sort + filter + view toggle + new button |
| `frontend/src/components/dashboard/RightPanel.tsx` | Right panel: control bar + bookshelf/list |

### Frontend — Modify
| File | Change |
|------|--------|
| `frontend/src/types/index.ts` | Add `is_pinned` to `Project` and `UpdateProjectRequest`, add `ActivityData` type |
| `frontend/src/pages/Dashboard.tsx` | Complete rewrite: left-right split layout |
| `frontend/src/components/common/PageContainer.tsx` | Support full-width mode (remove maxWidth for dashboard) |

---

## Task 1: Database Schema — `activity_log` table + `is_pinned` column

**Files:**
- Modify: `backend/app/db/schema.sql`

- [ ] **Step 1: Add `activity_log` table and `is_pinned` column to schema.sql**

Open `backend/app/db/schema.sql` and append after the `reviews` table definition:

```sql
CREATE TABLE IF NOT EXISTS activity_log (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    ref_id TEXT NOT NULL,
    action TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_activity_log_created_at ON activity_log(created_at);
CREATE INDEX IF NOT EXISTS idx_activity_log_project_id ON activity_log(project_id);
```

Add `is_pinned` to the `projects` table definition — add this column after `word_count`:

```sql
    is_pinned BOOLEAN DEFAULT 0,
```

- [ ] **Step 2: Apply schema changes to the running database**

Run from `backend/`:

```bash
sqlite3 novel.db < app/db/schema.sql
```

Or if the database already exists with the old schema, run the ALTER manually:

```bash
sqlite3 novel.db "ALTER TABLE projects ADD COLUMN is_pinned BOOLEAN DEFAULT 0;"
```

- [ ] **Step 3: Verify schema**

```bash
sqlite3 novel.db ".schema activity_log"
sqlite3 novel.db ".schema projects" | grep is_pinned
```

Expected: `activity_log` table exists with correct columns; `projects` table includes `is_pinned`.

- [ ] **Step 4: Commit**

```bash
git add backend/app/db/schema.sql
git commit -m "feat(db): add activity_log table and is_pinned column to projects"
```

---

## Task 2: Activity Repository

**Files:**
- Create: `backend/app/services/activity_repository.py`
- Test: `backend/tests/test_activity_repository.py`

- [ ] **Step 1: Write tests for activity repository**

Create `backend/tests/test_activity_repository.py`:

```python
import uuid
import pytest
from datetime import datetime, timedelta
from app.db.connection import get_db, init_db
from app.services.activity_repository import log_activity, get_heatmap_data


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    yield


async def _create_test_project(db):
    project_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO projects (id, name, data_path) VALUES (?, ?, ?)",
        (project_id, "Test Project", f"/tmp/{project_id}"),
    )
    await db.commit()
    return project_id


@pytest.mark.asyncio
async def test_log_activity_inserts_row():
    async with get_db() as db:
        project_id = await _create_test_project(db)
        activity_id = await log_activity(db, project_id, "chapter", "ch-1", "create")
        assert activity_id is not None

        cursor = await db.execute(
            "SELECT * FROM activity_log WHERE id = ?", (activity_id,)
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row["project_id"] == project_id
        assert row["activity_type"] == "chapter"
        assert row["ref_id"] == "ch-1"
        assert row["action"] == "create"


@pytest.mark.asyncio
async def test_get_heatmap_data_aggregates_by_date():
    async with get_db() as db:
        project_id = await _create_test_project(db)
        today = datetime.now().strftime("%Y-%m-%d")

        await log_activity(db, project_id, "chapter", "ch-1", "create")
        await log_activity(db, project_id, "chapter", "ch-2", "create")
        await log_activity(db, project_id, "world", "w-1", "update")

        result = await get_heatmap_data(db, days=365)
        assert len(result) >= 1
        today_entry = next((r for r in result if r["date"] == today), None)
        assert today_entry is not None
        assert today_entry["count"] == 3


@pytest.mark.asyncio
async def test_get_heatmap_data_empty():
    async with get_db() as db:
        result = await get_heatmap_data(db, days=365)
        assert isinstance(result, list)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && uv run pytest tests/test_activity_repository.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.activity_repository'`

- [ ] **Step 3: Implement activity_repository.py**

Create `backend/app/services/activity_repository.py`:

```python
import uuid
from datetime import datetime, timedelta

import aiosqlite


async def log_activity(
    db: aiosqlite.Connection,
    project_id: str,
    activity_type: str,
    ref_id: str,
    action: str,
) -> str:
    activity_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO activity_log (id, project_id, activity_type, ref_id, action) VALUES (?, ?, ?, ?, ?)",
        (activity_id, project_id, activity_type, ref_id, action),
    )
    await db.commit()
    return activity_id


async def get_heatmap_data(
    db: aiosqlite.Connection,
    days: int = 365,
) -> list[dict[str, object]]:
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    cursor = await db.execute(
        """
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM activity_log
        WHERE DATE(created_at) >= ?
        GROUP BY DATE(created_at)
        ORDER BY date
        """,
        (cutoff,),
    )
    rows = await cursor.fetchall()
    return [{"date": row["date"], "count": row["count"]} for row in rows]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && uv run pytest tests/test_activity_repository.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/activity_repository.py backend/tests/test_activity_repository.py
git commit -m "feat(api): add activity repository with log_activity and get_heatmap_data"
```

---

## Task 3: Activity API Endpoint

**Files:**
- Create: `backend/app/api/v1/activity.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_activity_api.py`

- [ ] **Step 1: Write test for heatmap endpoint**

Create `backend/tests/test_activity_api.py`:

```python
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.db.connection import get_db, init_db


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    yield


@pytest.mark.asyncio
async def test_heatmap_endpoint_returns_data(client: AsyncClient):
    async with get_db() as db:
        project_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO projects (id, name, data_path) VALUES (?, ?, ?)",
            (project_id, "Test", f"/tmp/{project_id}"),
        )
        await db.execute(
            "INSERT INTO activity_log (id, project_id, activity_type, ref_id, action) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), project_id, "chapter", "ch-1", "create"),
        )
        await db.commit()

    resp = await client.get("/api/v1/activity/heatmap?days=365")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "total_active_days" in data
    assert isinstance(data["data"], list)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/test_activity_api.py -v
```

Expected: FAIL — 404 (route not registered yet).

- [ ] **Step 3: Create activity router**

Create `backend/app/api/v1/activity.py`:

```python
from fastapi import APIRouter
from app.db.connection import get_db
from app.services.activity_repository import get_heatmap_data

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("/heatmap")
async def heatmap_endpoint(days: int = 365):
    async with get_db() as db:
        data = await get_heatmap_data(db, days=days)
    total_active_days = len(data)
    return {"data": data, "total_active_days": total_active_days}
```

- [ ] **Step 4: Register router in main.py**

In `backend/app/main.py`, add the import and register the router in `create_app()`:

Add import:
```python
from app.api.v1.activity import router as activity_router
```

Add in `create_app()` alongside other routers:
```python
app.include_router(activity_router, prefix="/api/v1")
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend && uv run pytest tests/test_activity_api.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/activity.py backend/app/main.py backend/tests/test_activity_api.py
git commit -m "feat(api): add GET /api/v1/activity/heatmap endpoint"
```

---

## Task 4: Add `is_pinned` to Projects

**Files:**
- Modify: `backend/app/services/project_repository.py`
- Modify: `backend/app/api/v1/projects.py`

- [ ] **Step 1: Add `is_pinned` to allowed update fields**

In `backend/app/services/project_repository.py`, find the `update_project` function. Locate the `allowed` set and add `"is_pinned"`:

```python
allowed = {"name", "status", "description", "cover_image", "word_count", "is_pinned"}
```

- [ ] **Step 2: Add `is_pinned` to UpdateProjectRequest**

In `backend/app/api/v1/projects.py`, find the `UpdateProjectRequest` class and add:

```python
is_pinned: bool | None = None
```

- [ ] **Step 3: Verify with existing tests**

```bash
cd backend && uv run pytest tests/test_projects*.py -v -k "update"
```

Expected: Existing update tests still pass (new field is optional).

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/project_repository.py backend/app/api/v1/projects.py
git commit -m "feat(api): add is_pinned field to project update"
```

---

## Task 5: Activity Logging in Content Services

**Files:**
- Modify: `backend/app/services/world.py`
- Modify: `backend/app/services/character.py`
- Modify: `backend/app/services/outline.py`
- Modify: `backend/app/services/chapter.py`
- Modify: `backend/app/services/review.py`
- Test: `backend/tests/test_activity_logging.py`

- [ ] **Step 1: Write test for activity logging**

Create `backend/tests/test_activity_logging.py`:

```python
import uuid
import pytest
from app.db.connection import get_db, init_db
from app.services.world import WorldSettingService
from app.services.character import CharacterService
from app.services.chapter import ChapterService
from app.services.outline import OutlineService
from app.services.review import ReviewService


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    yield


async def _create_test_project(db):
    project_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO projects (id, name, data_path) VALUES (?, ?, ?)",
        (project_id, "Test", f"/tmp/{project_id}"),
    )
    await db.commit()
    return project_id


@pytest.mark.asyncio
async def test_world_create_logs_activity():
    async with get_db() as db:
        project_id = await _create_test_project(db)
        service = WorldSettingService(db)
        wid = str(uuid.uuid4())
        await service.create(project_id, wid, "Test World", "# Test")

        cursor = await db.execute(
            "SELECT * FROM activity_log WHERE project_id = ? AND activity_type = 'world'",
            (project_id,),
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row["action"] == "create"
        assert row["ref_id"] == wid


@pytest.mark.asyncio
async def test_character_create_logs_activity():
    async with get_db() as db:
        project_id = await _create_test_project(db)
        service = CharacterService(db)
        cid = str(uuid.uuid4())
        await service.create(project_id, cid, "Hero", "# Hero")

        cursor = await db.execute(
            "SELECT * FROM activity_log WHERE project_id = ? AND activity_type = 'character'",
            (project_id,),
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row["action"] == "create"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/test_activity_logging.py -v
```

Expected: FAIL — no activity_log rows inserted yet.

- [ ] **Step 3: Add activity logging to WorldSettingService**

In `backend/app/services/world.py`, add import at top:

```python
from app.services.activity_repository import log_activity
```

In the `create` method, after the `await self.db.commit()` line, add:

```python
await log_activity(self.db, project_id, "world", world_setting_id, "create")
```

In the `update` method, after the `self._update_metadata(...)` call, add:

```python
await log_activity(self.db, project_id, "world", world_setting_id, "update")
```

In the `delete` method, after the `await self.db.commit()` line, add:

```python
await log_activity(self.db, project_id, "world", world_setting_id, "delete")
```

- [ ] **Step 4: Add activity logging to CharacterService**

In `backend/app/services/character.py`, same pattern as world:

Add import:
```python
from app.services.activity_repository import log_activity
```

In `create` after commit: `await log_activity(self.db, project_id, "character", character_id, "create")`
In `update` after `_update_metadata`: `await log_activity(self.db, project_id, "character", character_id, "update")`
In `delete` after commit: `await log_activity(self.db, project_id, "character", character_id, "delete")`

- [ ] **Step 5: Add activity logging to ChapterService**

In `backend/app/services/chapter.py`, same pattern:

Add import:
```python
from app.services.activity_repository import log_activity
```

In `create` after commit: `await log_activity(self.db, project_id, "chapter", chapter_id, "create")`
In `update` after `_update_metadata`: `await log_activity(self.db, project_id, "chapter", chapter_id, "update")`
In `delete` after commit: `await log_activity(self.db, project_id, "chapter", chapter_id, "delete")`

- [ ] **Step 6: Add activity logging to OutlineService**

In `backend/app/services/outline.py`, same pattern:

Add import:
```python
from app.services.activity_repository import log_activity
```

In `create` after commit: `await log_activity(self.db, project_id, "outline", outline_id, "create")`
In `update` after `_update_metadata`: `await log_activity(self.db, project_id, "outline", outline_id, "update")`
In `delete` after commit: `await log_activity(self.db, project_id, "outline", outline_id, "delete")`

- [ ] **Step 7: Add activity logging to ReviewService**

In `backend/app/services/review.py`, same pattern (only create and delete — reviews have no update):

Add import:
```python
from app.services.activity_repository import log_activity
```

In `create` after commit: `await log_activity(self.db, project_id, "review", review_id, "create")`
In `delete` after commit: `await log_activity(self.db, project_id, "review", review_id, "delete")`

- [ ] **Step 8: Run tests**

```bash
cd backend && uv run pytest tests/test_activity_logging.py -v
```

Expected: All tests PASS.

- [ ] **Step 9: Run full test suite to check for regressions**

```bash
cd backend && uv run pytest -v
```

Expected: All tests pass. No regressions.

- [ ] **Step 10: Commit**

```bash
git add backend/app/services/world.py backend/app/services/character.py backend/app/services/chapter.py backend/app/services/outline.py backend/app/services/review.py backend/tests/test_activity_logging.py
git commit -m "feat(services): add activity logging to all content services"
```

---

## Task 6: Frontend — Install `react-activity-calendar` + Update Types

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/src/types/index.ts`
- Create: `frontend/src/api/activity.ts`

- [ ] **Step 1: Install react-activity-calendar**

```bash
cd frontend && npm install react-activity-calendar
```

- [ ] **Step 2: Update Project type with `is_pinned`**

In `frontend/src/types/index.ts`, add `is_pinned` to the `Project` interface:

```typescript
export interface Project {
  id: string;
  name: string;
  description: string | null;
  cover_image: string | null;
  status: string;
  word_count: number;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
}
```

Add `is_pinned` to `UpdateProjectRequest`:

```typescript
export interface UpdateProjectRequest {
  name?: string;
  status?: string;
  description?: string;
  cover_image?: string;
  word_count?: number;
  is_pinned?: boolean;
}
```

Add `ActivityDay` type for heatmap data:

```typescript
export interface ActivityDay {
  date: string;
  count: number;
}

export interface HeatmapResponse {
  data: ActivityDay[];
  total_active_days: number;
}
```

- [ ] **Step 3: Create activity API client**

Create `frontend/src/api/activity.ts`:

```typescript
import { client } from './client';
import type { HeatmapResponse } from '@/types';

export const activityApi = {
  getHeatmap: (days = 365) =>
    client.get<HeatmapResponse>('/activity/heatmap', { params: { days } }),
};
```

- [ ] **Step 4: Verify type-check passes**

```bash
cd frontend && npm run type-check
```

Expected: No errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/types/index.ts frontend/src/api/activity.ts
git commit -m "feat(frontend): install react-activity-calendar, update types and API client"
```

---

## Task 7: Frontend — ActivityHeatmap Component

**Files:**
- Create: `frontend/src/components/dashboard/ActivityHeatmap.tsx`

- [ ] **Step 1: Create ActivityHeatmap component**

Create `frontend/src/components/dashboard/ActivityHeatmap.tsx`:

```tsx
import { useEffect, useState } from 'react';
import { ActivityCalendar } from 'react-activity-calendar';
import type { ActivityDay } from '@/types';
import { activityApi } from '@/api/activity';
import { theme } from 'antd';

const ActivityHeatmap = () => {
  const { token } = theme.useToken();
  const [data, setData] = useState<ActivityDay[]>([]);
  const [totalDays, setTotalDays] = useState(0);

  useEffect(() => {
    activityApi.getHeatmap(365).then((res) => {
      setData(res.data.data);
      setTotalDays(res.data.total_active_days);
    });
  }, []);

  const calendarData = data.map((d) => ({
    date: d.date,
    count: d.count,
    level: Math.min(Math.ceil(d.count / 2), 4),
  }));

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 8,
        }}
      >
        <span style={{ color: token.colorText, fontSize: 12, fontWeight: 600 }}>
          写作活跃度
        </span>
        <span style={{ color: token.colorTextSecondary, fontSize: 10 }}>
          过去 365 天
        </span>
      </div>
      <ActivityCalendar
        data={calendarData}
        colorScheme="dark"
        theme={{
          light: ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353'],
          dark: ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353'],
        }}
        labels={{
          months: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
          weekdays: ['日', '一', '二', '三', '四', '五', '六'],
          totalCount: '过去一年共写作 {{count}} 天',
        }}
        style={{ color: token.colorTextSecondary }}
      />
      <div style={{ color: token.colorTextSecondary, fontSize: 10, marginTop: 4 }}>
        过去一年共写作 <span style={{ color: '#39d353', fontWeight: 600 }}>{totalDays} 天</span>
      </div>
    </div>
  );
};

export default ActivityHeatmap;
```

- [ ] **Step 2: Verify type-check**

```bash
cd frontend && npm run type-check
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/dashboard/ActivityHeatmap.tsx
git commit -m "feat(frontend): add ActivityHeatmap component using react-activity-calendar"
```

---

## Task 8: Frontend — LeftPanel Component

**Files:**
- Create: `frontend/src/components/dashboard/LeftPanel.tsx`

- [ ] **Step 1: Create LeftPanel component**

Create `frontend/src/components/dashboard/LeftPanel.tsx`:

```tsx
import { theme } from 'antd';
import { ProjectOutlined, EditOutlined, ThunderboltOutlined } from '@ant-design/icons';
import type { Project } from '@/types';
import ActivityHeatmap from './ActivityHeatmap';

interface LeftPanelProps {
  projects: Project[];
}

const LeftPanel = ({ projects }: LeftPanelProps) => {
  const { token } = theme.useToken();
  const totalWords = projects.reduce((sum, p) => sum + p.word_count, 0);
  const activeCount = projects.filter((p) => p.status === 'active').length;

  const statCardStyle: React.CSSProperties = {
    background: token.colorBgElevated,
    borderRadius: 10,
    padding: 14,
  };

  return (
    <div
      style={{
        width: 280,
        flexShrink: 0,
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 8,
        alignContent: 'start',
      }}
    >
      {/* Heatmap — spans 2 columns */}
      <div
        style={{
          gridColumn: '1 / 3',
          background: token.colorBgElevated,
          borderRadius: 10,
          padding: 14,
        }}
      >
        <ActivityHeatmap />
      </div>

      {/* Total projects */}
      <div style={statCardStyle}>
        <div style={{ color: token.colorTextSecondary, fontSize: 10, marginBottom: 4 }}>
          总项目
        </div>
        <div style={{ color: token.colorText, fontSize: 26, fontWeight: 700, lineHeight: 1 }}>
          {projects.length}
        </div>
      </div>

      {/* Total words */}
      <div style={statCardStyle}>
        <div style={{ color: token.colorTextSecondary, fontSize: 10, marginBottom: 4 }}>
          总字数
        </div>
        <div style={{ color: token.colorText, fontSize: 26, fontWeight: 700, lineHeight: 1 }}>
          {totalWords >= 10000
            ? `${(totalWords / 10000).toFixed(1)}`
            : totalWords.toLocaleString()}
          {totalWords >= 10000 && (
            <span style={{ fontSize: 14, color: token.colorTextSecondary, fontWeight: 400 }}>
              万
            </span>
          )}
        </div>
      </div>

      {/* Active projects — spans 2 columns */}
      <div
        style={{
          gridColumn: '1 / 3',
          background: `linear-gradient(135deg, ${token.colorPrimaryBg}, transparent)`,
          border: `1px solid ${token.colorPrimaryBorder}`,
          borderRadius: 10,
          padding: 14,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <div style={{ color: token.colorTextSecondary, fontSize: 10, marginBottom: 4 }}>
            活跃项目
          </div>
          <div style={{ color: token.colorPrimary, fontSize: 26, fontWeight: 700, lineHeight: 1 }}>
            {activeCount}
          </div>
        </div>
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: '50%',
            background: token.colorPrimaryBg,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <ThunderboltOutlined style={{ color: token.colorPrimary, fontSize: 16 }} />
        </div>
      </div>
    </div>
  );
};

export default LeftPanel;
```

- [ ] **Step 2: Verify type-check**

```bash
cd frontend && npm run type-check
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/dashboard/LeftPanel.tsx
git commit -m "feat(frontend): add LeftPanel component with heatmap and stats grid"
```

---

## Task 9: Frontend — BookCover Component

**Files:**
- Create: `frontend/src/components/dashboard/BookCover.tsx`

- [ ] **Step 1: Create BookCover component**

Create `frontend/src/components/dashboard/BookCover.tsx`:

```tsx
import { theme } from 'antd';
import { StarFilled } from '@ant-design/icons';
import type { Project } from '@/types';

interface BookCoverProps {
  project: Project;
  onClick: () => void;
  onTogglePin?: (e: React.MouseEvent) => void;
}

const BOOK_COLORS = ['#667eea', '#f5576c', '#00b4d8', '#e07c4f', '#7b68ee'];

const BookCover = ({ project, onClick, onTogglePin }: BookCoverProps) => {
  const { token } = theme.useToken();
  const colorIndex = project.name.length % BOOK_COLORS.length;
  const bgColor = BOOK_COLORS[colorIndex];

  return (
    <div
      onClick={onClick}
      style={{
        width: 80,
        height: 120,
        borderRadius: 4,
        cursor: 'pointer',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: '3px 3px 10px rgba(0,0,0,0.5)',
        transition: 'transform 0.2s, box-shadow 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-4px)';
        e.currentTarget.style.boxShadow = '3px 6px 16px rgba(0,0,0,0.6)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = '3px 3px 10px rgba(0,0,0,0.5)';
      }}
    >
      {/* Background: cover_image or colored texture */}
      {project.cover_image ? (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: `url(${project.cover_image})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }}
        />
      ) : (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundColor: bgColor,
            backgroundImage:
              'url("data:image/svg+xml,%3Csvg width=\'6\' height=\'6\' viewBox=\'0 0 6 6\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'%23ffffff\' fill-opacity=\'0.08\' fill-rule=\'evenodd\'%3E%3Cpath d=\'M5 0h1L0 6V5zM6 5v1H5z\'/%3E%3C/g%3E%3C/svg%3E")',
          }}
        />
      )}

      {/* Pin star */}
      {project.is_pinned && (
        <div
          onClick={(e) => {
            e.stopPropagation();
            onTogglePin?.(e);
          }}
          style={{ position: 'absolute', top: 4, right: 4, zIndex: 1 }}
        >
          <StarFilled style={{ color: '#e3b341', fontSize: 10 }} />
        </div>
      )}

      {/* Content overlay */}
      <div
        style={{
          position: 'relative',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'flex-end',
          padding: '10px 8px',
        }}
      >
        <div
          style={{
            color: '#fff',
            fontSize: 11,
            fontWeight: 700,
            lineHeight: 1.2,
            textShadow: '0 1px 3px rgba(0,0,0,0.5)',
            overflow: 'hidden',
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
          }}
        >
          {project.name}
        </div>
        <div
          style={{
            color: 'rgba(255,255,255,0.6)',
            fontSize: 8,
            marginTop: 4,
          }}
        >
          {project.word_count.toLocaleString()}字
        </div>
      </div>
    </div>
  );
};

export default BookCover;
```

- [ ] **Step 2: Verify type-check**

```bash
cd frontend && npm run type-check
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/dashboard/BookCover.tsx
git commit -m "feat(frontend): add BookCover component with texture background and pin support"
```

---

## Task 10: Frontend — BookshelfView Component

**Files:**
- Create: `frontend/src/components/dashboard/BookshelfView.tsx`

- [ ] **Step 1: Create BookshelfView component**

Create `frontend/src/components/dashboard/BookshelfView.tsx`:

```tsx
import { theme } from 'antd';
import { useNavigate } from 'react-router-dom';
import type { Project } from '@/types';
import BookCover from './BookCover';

interface BookshelfViewProps {
  projects: Project[];
  onTogglePin: (projectId: string) => void;
}

const BookshelfView = ({ projects, onTogglePin }: BookshelfViewProps) => {
  const { token } = theme.useToken();
  const navigate = useNavigate();

  // Split projects into shelves (5 per row)
  const booksPerShelf = 5;
  const shelves: Project[][] = [];
  for (let i = 0; i < projects.length; i += booksPerShelf) {
    shelves.push(projects.slice(i, i + booksPerShelf));
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
      {shelves.map((shelf, shelfIndex) => (
        <div
          key={shelfIndex}
          style={{
            position: 'relative',
            padding: '16px 12px 20px 12px',
            background:
              shelfIndex === 0
                ? 'linear-gradient(180deg, #2d1f0e, #1a1208)'
                : 'linear-gradient(180deg, #2d1f0e, #1a1208)',
            borderRadius: shelfIndex === 0 ? '8px 8px 0 0' : undefined,
          }}
        >
          <div
            style={{
              display: 'flex',
              gap: 10,
              alignItems: 'flex-end',
              minHeight: 140,
              padding: '0 4px',
              flexWrap: 'wrap',
            }}
          >
            {shelf.map((project) => (
              <BookCover
                key={project.id}
                project={project}
                onClick={() => navigate(`/projects/${project.id}/world`)}
                onTogglePin={() => onTogglePin(project.id)}
              />
            ))}
          </div>
          {/* Wood plank */}
          <div
            style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              height: 8,
              background: 'linear-gradient(180deg, #5c3d1a, #3d2810)',
              borderRadius: '0 0 4px 4px',
              boxShadow: '0 3px 6px rgba(0,0,0,0.5)',
            }}
          />
        </div>
      ))}
      {projects.length === 0 && (
        <div
          style={{
            padding: 40,
            textAlign: 'center',
            color: token.colorTextSecondary,
            background: 'linear-gradient(180deg, #2d1f0e, #1a1208)',
            borderRadius: 8,
          }}
        >
          还没有项目，点击 + 创建第一个吧
        </div>
      )}
    </div>
  );
};

export default BookshelfView;
```

- [ ] **Step 2: Verify type-check**

```bash
cd frontend && npm run type-check
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/dashboard/BookshelfView.tsx
git commit -m "feat(frontend): add BookshelfView component with wooden shelf layout"
```

---

## Task 11: Frontend — ListView Component

**Files:**
- Create: `frontend/src/components/dashboard/ListView.tsx`

- [ ] **Step 1: Create ListView component**

Create `frontend/src/components/dashboard/ListView.tsx`:

```tsx
import { List, Tag, Typography } from 'antd';
import { StarFilled } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { Project } from '@/types';
import { formatDate } from '@/utils/format';

const BOOK_COLORS = ['#667eea', '#f5576c', '#00b4d8', '#e07c4f', '#7b68ee'];

interface ListViewProps {
  projects: Project[];
  onTogglePin: (projectId: string) => void;
}

const ListView = ({ projects, onTogglePin }: ListViewProps) => {
  const navigate = useNavigate();

  return (
    <List
      dataSource={projects}
      renderItem={(project) => {
        const colorIndex = project.name.length % BOOK_COLORS.length;
        return (
          <List.Item
            onClick={() => navigate(`/projects/${project.id}/world`)}
            style={{ cursor: 'pointer', padding: '12px 16px' }}
            actions={[
              project.is_pinned ? (
                <StarFilled
                  key="pin"
                  style={{ color: '#e3b341' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onTogglePin(project.id);
                  }}
                />
              ) : null,
            ]}
          >
            <List.Item.Meta
              avatar={
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: 6,
                    background: BOOK_COLORS[colorIndex],
                    flexShrink: 0,
                  }}
                />
              }
              title={project.name}
              description={
                <span>
                  <Tag color="blue" style={{ fontSize: 10 }}>
                    {project.word_count.toLocaleString()} 字
                  </Tag>
                  <Typography.Text type="secondary" style={{ fontSize: 11 }}>
                    {formatDate(project.updated_at)}
                  </Typography.Text>
                </span>
              }
            />
          </List.Item>
        );
      }}
    />
  );
};

export default ListView;
```

- [ ] **Step 2: Verify type-check**

```bash
cd frontend && npm run type-check
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/dashboard/ListView.tsx
git commit -m "feat(frontend): add ListView component as alternative project view"
```

---

## Task 12: Frontend — ControlBar Component

**Files:**
- Create: `frontend/src/components/dashboard/ControlBar.tsx`

- [ ] **Step 1: Create ControlBar component**

Create `frontend/src/components/dashboard/ControlBar.tsx`:

```tsx
import { Input, Button, Dropdown, theme } from 'antd';
import {
  SearchOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
  PlusOutlined,
} from '@ant-design/icons';

export type SortOption = 'updated_at' | 'created_at' | 'name' | 'word_count';
export type FilterOption = 'all' | 'active' | 'archived';
export type ViewMode = 'bookshelf' | 'list';

interface ControlBarProps {
  search: string;
  onSearchChange: (value: string) => void;
  sort: SortOption;
  onSortChange: (value: SortOption) => void;
  filter: FilterOption;
  onFilterChange: (value: FilterOption) => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  onCreate: () => void;
}

const SORT_LABELS: Record<SortOption, string> = {
  updated_at: '最近更新',
  created_at: '最早创建',
  name: '名称',
  word_count: '字数最多',
};

const FILTER_LABELS: Record<FilterOption, string> = {
  all: '全部',
  active: '活跃',
  archived: '已归档',
};

const ControlBar = ({
  search,
  onSearchChange,
  sort,
  onSortChange,
  filter,
  onFilterChange,
  viewMode,
  onViewModeChange,
  onCreate,
}: ControlBarProps) => {
  const { token } = theme.useToken();

  const sortItems = Object.entries(SORT_LABELS).map(([key, label]) => ({
    key,
    label,
    onClick: () => onSortChange(key as SortOption),
  }));

  const filterItems = Object.entries(FILTER_LABELS).map(([key, label]) => ({
    key,
    label,
    onClick: () => onFilterChange(key as FilterOption),
  }));

  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 14 }}>
      <Input
        prefix={<SearchOutlined />}
        placeholder="搜索项目..."
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
        style={{ flex: 1 }}
        allowClear
      />
      <Dropdown menu={{ items: sortItems, selectedKeys: [sort] }}>
        <Button>{SORT_LABELS[sort]} ▾</Button>
      </Dropdown>
      <Dropdown menu={{ items: filterItems, selectedKeys: [filter] }}>
        <Button>{FILTER_LABELS[filter]} ▾</Button>
      </Dropdown>
      <Button.Group>
        <Button
          type={viewMode === 'bookshelf' ? 'primary' : 'default'}
          icon={<AppstoreOutlined />}
          onClick={() => onViewModeChange('bookshelf')}
        />
        <Button
          type={viewMode === 'list' ? 'primary' : 'default'}
          icon={<UnorderedListOutlined />}
          onClick={() => onViewModeChange('list')}
        />
      </Button.Group>
      <Button type="primary" icon={<PlusOutlined />} onClick={onCreate} />
    </div>
  );
};

export default ControlBar;
```

- [ ] **Step 2: Verify type-check**

```bash
cd frontend && npm run type-check
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/dashboard/ControlBar.tsx
git commit -m "feat(frontend): add ControlBar with search, sort, filter, and view toggle"
```

---

## Task 13: Frontend — Refactor Dashboard.tsx

**Files:**
- Modify: `frontend/src/pages/Dashboard.tsx`

- [ ] **Step 1: Rewrite Dashboard.tsx with left-right layout**

Replace the entire content of `frontend/src/pages/Dashboard.tsx`:

```tsx
import { useState, useEffect, useCallback } from 'react';
import { Modal, Form, Input, Spin } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useAppMessage } from '@/hooks/useAppMessage';
import { projectsApi } from '@/api/projects';
import type { Project } from '@/types';
import LeftPanel from '@/components/dashboard/LeftPanel';
import RightPanel from '@/components/dashboard/RightPanel';
import type { SortOption, FilterOption, ViewMode } from '@/components/dashboard/ControlBar';

const VIEW_MODE_KEY = 'dashboard-view-mode';

const Dashboard = () => {
  const [message] = useAppMessage();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<SortOption>('updated_at');
  const [filter, setFilter] = useState<FilterOption>('all');
  const [viewMode, setViewMode] = useState<ViewMode>(
    () => (localStorage.getItem(VIEW_MODE_KEY) as ViewMode) || 'bookshelf'
  );
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [form] = Form.useForm();

  const loadProjects = useCallback(async () => {
    try {
      setLoading(true);
      const res = await projectsApi.list();
      setProjects(res.data);
    } catch {
      message.error('加载项目列表失败');
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const handleViewModeChange = (mode: ViewMode) => {
    setViewMode(mode);
    localStorage.setItem(VIEW_MODE_KEY, mode);
  };

  const handleTogglePin = async (projectId: string) => {
    const project = projects.find((p) => p.id === projectId);
    if (!project) return;
    try {
      await projectsApi.update(projectId, { is_pinned: !project.is_pinned });
      setProjects((prev) =>
        prev.map((p) => (p.id === projectId ? { ...p, is_pinned: !p.is_pinned } : p))
      );
    } catch {
      message.error('更新置顶状态失败');
    }
  };

  const handleCreate = async (values: { name: string; description?: string }) => {
    try {
      const res = await projectsApi.create(values);
      setProjects((prev) => [res.data, ...prev]);
      setCreateModalOpen(false);
      form.resetFields();
      navigate(`/projects/${res.data.id}/world`);
    } catch {
      message.error('创建项目失败');
    }
  };

  // Sort + filter
  const processed = [...projects]
    .filter((p) => {
      if (filter === 'active') return p.status === 'active';
      if (filter === 'archived') return p.status === 'archived';
      return true;
    })
    .filter((p) => p.name.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      // Pinned always first
      if (a.is_pinned !== b.is_pinned) return a.is_pinned ? -1 : 1;
      switch (sort) {
        case 'updated_at':
          return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
        case 'created_at':
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        case 'name':
          return a.name.localeCompare(b.name, 'zh');
        case 'word_count':
          return b.word_count - a.word_count;
        default:
          return 0;
      }
    });

  return (
    <Spin spinning={loading}>
      <div style={{ display: 'flex', gap: 16 }}>
        <LeftPanel projects={projects} />
        <RightPanel
          projects={processed}
          search={search}
          onSearchChange={setSearch}
          sort={sort}
          onSortChange={setSort}
          filter={filter}
          onFilterChange={setFilter}
          viewMode={viewMode}
          onViewModeChange={handleViewModeChange}
          onCreate={() => setCreateModalOpen(true)}
          onTogglePin={handleTogglePin}
        />
      </div>
      <Modal
        title="新建项目"
        open={createModalOpen}
        onCancel={() => setCreateModalOpen(false)}
        onOk={() => form.submit()}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}>
            <Input placeholder="请输入项目名称" />
          </Form.Item>
          <Form.Item name="description" label="项目描述">
            <Input.TextArea placeholder="请输入项目描述（可选）" rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </Spin>
  );
};

export default Dashboard;
```

- [ ] **Step 2: Create RightPanel wrapper component**

Create `frontend/src/components/dashboard/RightPanel.tsx`:

```tsx
import type { Project } from '@/types';
import ControlBar from './ControlBar';
import type { SortOption, FilterOption, ViewMode } from './ControlBar';
import BookshelfView from './BookshelfView';
import ListView from './ListView';

interface RightPanelProps {
  projects: Project[];
  search: string;
  onSearchChange: (value: string) => void;
  sort: SortOption;
  onSortChange: (value: SortOption) => void;
  filter: FilterOption;
  onFilterChange: (value: FilterOption) => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  onCreate: () => void;
  onTogglePin: (projectId: string) => void;
}

const RightPanel = ({
  projects,
  search,
  onSearchChange,
  sort,
  onSortChange,
  filter,
  onFilterChange,
  viewMode,
  onViewModeChange,
  onCreate,
  onTogglePin,
}: RightPanelProps) => {
  return (
    <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
      <ControlBar
        search={search}
        onSearchChange={onSearchChange}
        sort={sort}
        onSortChange={onSortChange}
        filter={filter}
        onFilterChange={onFilterChange}
        viewMode={viewMode}
        onViewModeChange={onViewModeChange}
        onCreate={onCreate}
      />
      {viewMode === 'bookshelf' ? (
        <BookshelfView projects={projects} onTogglePin={onTogglePin} />
      ) : (
        <ListView projects={projects} onTogglePin={onTogglePin} />
      )}
    </div>
  );
};

export default RightPanel;
```

- [ ] **Step 3: Verify type-check**

```bash
cd frontend && npm run type-check
```

Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Dashboard.tsx frontend/src/components/dashboard/RightPanel.tsx
git commit -m "feat(frontend): refactor Dashboard to left-right split with bookshelf layout"
```

---

## Task 14: Integration Verification

- [ ] **Step 1: Start backend and verify heatmap endpoint**

```bash
cd backend && uv run uvicorn app.main:app --reload &
curl http://localhost:8000/api/v1/activity/heatmap?days=365
```

Expected: `{"data": [], "total_active_days": 0}` (or data if activity_log has rows).

- [ ] **Step 2: Start frontend and verify dashboard renders**

```bash
cd frontend && npm run dev
```

Open http://localhost:5173 — verify:
- Left panel shows heatmap (empty state OK) + stat cards
- Right panel shows control bar + bookshelf (or list) view
- Search, sort, filter, view toggle all work
- Clicking a book navigates to the project
- Creating a new project works
- Toggling pin works (star appears/disappears)

- [ ] **Step 3: Run full backend test suite**

```bash
cd backend && uv run pytest -v
```

Expected: All tests pass.

- [ ] **Step 4: Run frontend type-check and lint**

```bash
cd frontend && npm run type-check && npm run lint
```

Expected: No errors.

- [ ] **Step 5: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix: integration fixes for dashboard redesign"
```
