# Dashboard Redesign

Date: 2026-05-10

## Problem

Current Dashboard is too plain — it's essentially a project listing page with three client-side stat cards, a search bar, and a project grid. It lacks visual richness, interactive features, and a sense of writing activity/history.

## Goals

1. **Richer layout** — left-right split with a visually engaging left panel
2. **Writing activity visualization** — GitHub-style heatmap showing daily writing activity
3. **Bookshelf metaphor** — projects displayed as books on shelves, fitting the novel-writing domain
4. **More interactions** — sorting, filtering, pin/favorite, view toggle

## Design

### Page Layout: Left-Right Split

The Dashboard uses a two-column layout. Left panel is fixed-width (~280px), right panel fills remaining space.

#### Left Panel: Stats Dashboard (Grid Mosaic)

A CSS Grid with 2 columns that arranges stats in a mosaic pattern:

```
┌─────────────────────────┐
│     Writing Heatmap     │  ← spans 2 columns, full heatmap
│   (activity_log data)   │
├────────────┬────────────┤
│ Total Proj │ Total Words│  ← 2 stat cards side by side
│    12      │  45.2万    │
├────────────┴────────────┤
│   Active Projects: 5    │  ← spans 2 columns, accent highlight
│                    [▶]  │
└─────────────────────────┘
```

**Heatmap details:**
- 365-day grid, 7 rows (days of week) x ~53 columns (weeks)
- Color scale: 5 levels from empty (#161b22) to intense (#39d353), matching GitHub's dark theme
- Data source: `activity_log` table, aggregated by `DATE(created_at)`
- Shows total active days count below the grid
- Month labels along the bottom

**Stat cards:**
- Total projects: `projects.length`
- Total words: sum of `word_count` across all projects
- Active projects: count where `status === 'active'`, displayed with accent color (blue) and a play icon

#### Right Panel: Bookshelf

##### Control Bar

A horizontal row with:
- **Search input** — filters projects by name (client-side)
- **Sort dropdown** — options: 最近更新, 最早创建, 名称, 字数最多
- **Filter dropdown** — options: 全部, 活跃, 已归档
- **View toggle** — grid view (bookshelf) vs list view
- **+ button** — green, opens create project modal

##### Bookshelf View (Default)

Projects displayed as uniform-sized book covers on wooden shelves:

```
┌─ wooden shelf background ──────────────────────────┐
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│  │ ★    │ │      │ │      │ │      │              │
│  │COVER │ │COVER │ │COVER │ │COVER │              │
│  │      │ │      │ │      │ │      │              │
│  │title │ │title │ │title │ │title │              │
│  │words │ │words │ │words │ │words │              │
│  └──────┘ └──────┘ └──────┘ └──────┘              │
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ ← wood plank
├─ wooden shelf background ──────────────────────────┤
│  ┌──────┐ ┌──────┐ ┌──────┐                        │
│  │      │ │      │ │      │                        │
│  │COVER │ │COVER │ │COVER │                        │
│  │      │ │      │ │      │                        │
│  │title │ │title │ │title │                        │
│  │words │ │words │ │words │                        │
│  └──────┘ └──────┘ └──────┘                        │
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
└────────────────────────────────────────────────────┘
```

**Book cover design:**
- Uniform size: ~80px wide x 120px tall
- Background: unified cloth/paper texture with different color tints per project (5 preset colors selected by `project.name.length % 5`). Use CSS `background-blend-mode` to blend a subtle noise/texture pattern with a solid color
- If `cover_image` is set: use the image as background instead of colored texture
- Genre tag: small text at top (e.g., "SCIENCE FICTION", "FANTASY") — derived from project metadata or default to "NOVEL"
- Title: project name, bold, centered, white text
- Word count: small text at bottom
- Pinned projects: gold star icon (⭐) in top-right corner
- Wooden shelf: brown gradient background with a thick wood plank at the bottom, `box-shadow` for depth

**Shelf layout:**
- Books wrap to next shelf based on available width (~4-5 books per shelf)
- Each shelf is a row with wooden background and plank
- New project: dashed-border placeholder at end of last shelf, or just use the + button in control bar

##### List View (Alternative)

Toggle to a compact list view for projects that prefer information density:
- Each project as a row with: small cover thumbnail, name, description snippet, word count, last updated
- Same sort/filter controls apply

### Interaction Features

#### Sorting

Client-side sort of the project list. Options:
- 最近更新 (default): `updated_at DESC`
- 最早创建: `created_at ASC`
- 名称: `name ASC` (alphabetical)
- 字数最多: `word_count DESC`

#### Filtering

Client-side filter. Options:
- 全部 (default)
- 活跃: `status === 'active'`
- 已归档: `status === 'archived'`

#### Pin/Favorite

- New DB column: `projects.is_pinned BOOLEAN DEFAULT 0`
- Pinned projects always sort to the top, regardless of current sort order
- Toggle pin via context menu or a pin icon on the book cover
- Visual: gold star (⭐) on pinned books

### Data Model Changes

#### New Table: `activity_log`

Records every content creation/update for heatmap data.

```sql
CREATE TABLE IF NOT EXISTS activity_log (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    activity_type TEXT NOT NULL,  -- 'world' | 'character' | 'outline' | 'chapter' | 'review'
    ref_id TEXT NOT NULL,         -- ID of the related content
    action TEXT NOT NULL,         -- 'create' | 'update'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_activity_log_created_at ON activity_log(created_at);
CREATE INDEX IF NOT EXISTS idx_activity_log_project_id ON activity_log(project_id);
```

#### Modified Table: `projects`

Add `is_pinned` column:

```sql
ALTER TABLE projects ADD COLUMN is_pinned BOOLEAN DEFAULT 0;
```

### API Changes

#### New Endpoint: Heatmap Data

```
GET /api/v1/activity/heatmap?days=365
```

Response:
```json
{
  "data": [
    { "date": "2025-05-10", "count": 5 },
    { "date": "2025-05-11", "count": 2 },
    ...
  ],
  "total_active_days": 127
}
```

Backend aggregation query:
```sql
SELECT DATE(created_at) as date, COUNT(*) as count
FROM activity_log
WHERE created_at >= date('now', '-365 days')
GROUP BY DATE(created_at)
ORDER BY date
```

#### Modified Endpoint: List Projects

`GET /api/v1/projects/` response now includes `is_pinned` field.

#### Modified Endpoint: Update Project

`POST /api/v1/projects/{id}/update` now accepts `is_pinned` field.

### Backend Implementation: Activity Logging

Insert `activity_log` records in the service layer when content is created or updated. Affected services:

- `world.py` — `create_world`, `update_world`
- `character.py` — `create_character`, `update_character`
- `outline.py` — `create_outline`, `update_outline`
- `chapter.py` — `create_chapter`, `update_chapter`
- `review.py` — `create_review`

Each service call inserts an `activity_log` row with the appropriate `activity_type`, `ref_id`, and `action`.

### Frontend Component Structure

```
Dashboard.tsx (refactored)
├── LeftPanel (new component)
│   ├── ActivityHeatmap (new)
│   ├── StatCard x2 (reused from current)
│   └── ActiveProjectsCard (new, accent style)
├── RightPanel
│   ├── ControlBar (refactored from current search + button row)
│   │   ├── SearchInput
│   │   ├── SortDropdown
│   │   ├── FilterDropdown
│   │   ├── ViewToggle
│   │   └── NewProjectButton (+)
│   └── BookshelfView (new, replaces current ProjectCard grid)
│       ├── BookShelf (shelf container with wooden background)
│       │   └── BookCover x N (replaces ProjectCard)
│       └── EmptyState (when no projects)
└── CreateProjectModal (existing, kept)
```

### Cover Image

The `projects.cover_image` column already exists in the schema but has no CRUD yet.

- When `cover_image` is null (default): use unified cloth/paper texture with color tint as mock cover, 5 preset colors selected by `project.name.length % 5`
- When `cover_image` is set: display the image as book cover background
- Cover image upload/edit CRUD is **out of scope** for this change — use existing field as-is, gradients serve as mock covers

### View Toggle Behavior

- **Bookshelf view** (default): the wooden shelf layout described above
- **List view**: compact rows, each showing: small gradient/color square, project name, description snippet, word count tag, relative date, pin icon
- Toggle stored in `localStorage` (persists across sessions)

### Dependencies

#### Heatmap: `react-activity-calendar`

- npm: `react-activity-calendar` (~48k weekly downloads, actively maintained)
- GitHub: https://github.com/grubersjoe/react-activity-calendar
- Purpose-built GitHub-style calendar heatmap, TypeScript, zero runtime deps
- Built-in dark/light theme via `colorScheme` prop
- Usage: `<ActivityCalendar data={data} colorScheme="dark" />`
- Data format: `{ date: string, count: number, level: number }[]`

#### Bookshelf: Custom CSS (no library)

No production-ready React bookshelf library exists. Build with:
- CSS Grid/Flexbox for shelf rows
- CSS gradients for wooden shelf texture and plank
- Uniform book cover size (~80x120px)
- Hover transitions for interactivity
- ~80-120 lines of component CSS

## Out of Scope

- Cover image upload (reserved for future)
- Activity log pruning/cleanup
- Project archiving UI (status field exists but no UI to change it)
- Drag-to-reorder shelves
