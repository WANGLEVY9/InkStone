// src/types/index.ts

// ── Project ──
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

export interface CreateProjectRequest {
  name: string;
  description?: string;
  cover_image?: string;
}

export interface UpdateProjectRequest {
  name?: string;
  status?: string;
  description?: string;
  cover_image?: string;
  word_count?: number;
  is_pinned?: boolean;
}

// ── Activity Heatmap ──
export interface ActivityDay {
  date: string;
  count: number;
}

export interface HeatmapResponse {
  data: ActivityDay[];
  total_active_days: number;
}

// ── World ──
export interface WorldSetting {
  id: string;
  project_id: string;
  name: string;
  summary: string | null;
  file_path: string;
  created_at: string;
  updated_at: string;
  content?: string;
}

export interface CreateWorldRequest {
  name: string;
  content: string;
  summary?: string;
}

export interface UpdateWorldRequest {
  name?: string;
  content?: string;
  summary?: string;
}

// ── Character ──
export interface Character {
  id: string;
  project_id: string;
  name: string;
  summary: string | null;
  file_path: string;
  created_at: string;
  updated_at: string;
  content?: string;
}

export interface CharacterMeta {
  tags: string[];
  type: string;
  age: string;
  content: string;
}

export interface CreateCharacterRequest {
  name: string;
  content: string;
  summary?: string;
}

export interface UpdateCharacterRequest {
  name?: string;
  content?: string;
  summary?: string;
}

// ── Outline ──
export interface Outline {
  id: string;
  project_id: string;
  parent_id: string | null;
  title: string;
  type: string;
  sort_order: number;
  file_path: string;
  created_at: string;
  updated_at: string;
  content?: string;
  children?: Outline[];
}

export interface CreateOutlineRequest {
  title: string;
  content: string;
  type?: string;
  parent_id?: string;
  sort_order?: number;
}

export interface UpdateOutlineRequest {
  title?: string;
  content?: string;
  type?: string;
  parent_id?: string;
  sort_order?: number;
}

// ── Chapter ──
export interface Chapter {
  id: string;
  project_id: string;
  title: string;
  word_count: number;
  status: string;
  chapter_number: number;
  summary: string | null;
  published_at: string | null;
  file_path: string;
  created_at: string;
  updated_at: string;
  content?: string;
}

export interface CreateChapterRequest {
  title: string;
  content: string;
  word_count?: number;
  chapter_number?: number;
  summary?: string;
}

export interface UpdateChapterRequest {
  title?: string;
  content?: string;
  word_count?: number;
  status?: string;
  chapter_number?: number;
  summary?: string;
}


// ── Session / Chat ──
export interface Session {
  id: string;
  project_id: string;
  title: string | null;
  created_at: string;
  last_active_at: string;
}

export interface CreateSessionRequest {
  title?: string;
}

export interface ChatRequest {
  message: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'tool' | 'system';
  content: string;
  thinking_content?: string;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
}

export interface ToolCall {
  id: string;
  name: string;
  arguments: string;
}

// ── SSE Events ──
export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
}

// ── Chat Bubble (for Ant Design X Bubble.List) ──

export interface ChatTimelineEvent {
  type: 'thinking' | 'text' | 'tool' | 'system' | 'error';
  content?: string;
  name?: string;
  status?: 'running' | 'completed';
  isDelegate?: boolean;
  isReadOnly?: boolean;
  toolCallId?: string;
  result?: unknown;
  subTimeline?: ChatTimelineEvent[];
}

export interface ChatBubbleMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  status: 'loading' | 'updating' | 'success' | 'error';
  agent?: string;
  streaming?: boolean;
  timeline?: ChatTimelineEvent[];
  feedback?: 'like' | 'dislike' | 'default';
}

// ── Tree Node (for Ant Design Tree) ──
export interface TreeNodeData {
  key: string;
  title: string;
  children?: TreeNodeData[];
  type?: string;
  content?: string;
  isLeaf?: boolean;
}

// ── System Config ──
export interface ConfigItem {
  key: string;
  value: string | null;
}

export interface ConfigResponse {
  items: ConfigItem[];
}

export interface UpdateConfigRequest {
  llm_base_url?: string | null;
  anthropic_api_key?: string | null;
  langsmith_api_key?: string | null;
  langsmith_tracing?: boolean | null;
  langsmith_endpoint?: string | null;
  langsmith_project?: string | null;
  llm_model?: string | null;
  llm_max_tokens?: number | null;
}

export interface ConfigTestResponse {
  success: boolean;
  model?: string | null;
  latency_ms?: number | null;
  error_code?: string | null;
  message?: string | null;
}

// ── Skill ──
export interface Skill {
  name: string;
  description: string;
  domain: string | null;
  tags: string[];
  content?: string;
}

export interface CreateSkillRequest {
  name: string;
  description: string;
  content: string;
  domain?: string | null;
  tags?: string[];
}

export interface UpdateSkillRequest {
  description?: string;
  content?: string;
  domain?: string | null;
  tags?: string[];
}
