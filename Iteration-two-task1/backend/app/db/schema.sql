-- Novel Agent Backend SQLite Schema
-- Metadata only - content stored in Markdown files

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    data_path TEXT NOT NULL,
    description TEXT,
    cover_image TEXT,
    word_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- World settings metadata (content in .md file)
CREATE TABLE IF NOT EXISTS world_settings_meta (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Characters metadata (content in .md file)
CREATE TABLE IF NOT EXISTS characters_meta (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Outlines metadata (content in .md file, supports nesting)
CREATE TABLE IF NOT EXISTS outlines_meta (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    parent_id TEXT REFERENCES outlines_meta(id),
    title TEXT NOT NULL,
    file_path TEXT NOT NULL,
    type TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chapters metadata (content in .md file)
CREATE TABLE IF NOT EXISTS chapters_meta (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    title TEXT NOT NULL,
    file_path TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'draft',
    chapter_number INTEGER DEFAULT 1,
    summary TEXT,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    content_type TEXT NOT NULL,
    content_id TEXT NOT NULL,
    issues TEXT,
    suggestions TEXT,
    overall_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
