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
    is_pinned INTEGER DEFAULT 0,
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

-- Application configuration (global key-value store)
CREATE TABLE IF NOT EXISTS app_config (
    key   TEXT PRIMARY KEY NOT NULL,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 伏笔管理（供 ForeshadowingService 使用）
CREATE TABLE IF NOT EXISTS foreshadowing (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    description TEXT NOT NULL,
    foreshadowed_at TEXT DEFAULT '',
    expected_resolve_at TEXT DEFAULT '',
    status TEXT DEFAULT 'pending',
    target_chapter_id TEXT DEFAULT '',
    related_entities TEXT DEFAULT '[]',
    notes TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_fs_project ON foreshadowing(project_id);
CREATE INDEX IF NOT EXISTS idx_fs_status ON foreshadowing(project_id, status);

-- ============================================================
-- 跨对话知识共享系统
-- ============================================================

-- 通用结构化事实（角色属性、世界设定条目等）
CREATE TABLE IF NOT EXISTS knowledge_facts (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    fact_key TEXT NOT NULL,
    fact_value TEXT NOT NULL,
    summary TEXT NOT NULL,
    embedding BLOB,
    source_session_id TEXT,
    confidence REAL DEFAULT 1.0,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_kf_project ON knowledge_facts(project_id);
CREATE INDEX IF NOT EXISTS idx_kf_entity ON knowledge_facts(project_id, entity_type, entity_id);

-- 时间线事件
CREATE TABLE IF NOT EXISTS knowledge_events (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    chapter_number INTEGER,
    sequence INTEGER DEFAULT 0,
    event_type TEXT NOT NULL DEFAULT 'plot',
    involved_entities TEXT,
    embedding BLOB,
    source_session_id TEXT,
    is_confirmed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_ke_project ON knowledge_events(project_id);
CREATE INDEX IF NOT EXISTS idx_ke_timeline ON knowledge_events(project_id, chapter_number, sequence);

-- 角色关系
CREATE TABLE IF NOT EXISTS knowledge_relationships (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    source_entity_id TEXT NOT NULL,
    target_entity_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    description TEXT,
    strength INTEGER DEFAULT 5,
    source_session_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_kr_project ON knowledge_relationships(project_id);
CREATE INDEX IF NOT EXISTS idx_kr_entities ON knowledge_relationships(project_id, source_entity_id, target_entity_id);

-- 伏笔追踪
CREATE TABLE IF NOT EXISTS knowledge_foreshadowing (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    description TEXT NOT NULL,
    expected_resolve_chapter INTEGER,
    actual_resolve_chapter INTEGER,
    status TEXT NOT NULL DEFAULT 'pending',
    priority TEXT NOT NULL DEFAULT 'normal',
    related_chapter_id TEXT,
    resolved_by_chapter_id TEXT,
    embedding BLOB,
    source_session_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_kfs_project ON knowledge_foreshadowing(project_id);
CREATE INDEX IF NOT EXISTS idx_kfs_status ON knowledge_foreshadowing(project_id, status);

-- 增量变更日志
CREATE TABLE IF NOT EXISTS knowledge_delta_log (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    target_table TEXT NOT NULL,
    record_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_kdl_project ON knowledge_delta_log(project_id);
CREATE INDEX IF NOT EXISTS idx_kdl_session ON knowledge_delta_log(project_id, session_id);
CREATE INDEX IF NOT EXISTS idx_kdl_status ON knowledge_delta_log(project_id, status);
