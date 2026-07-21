# Skill 系统前端实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Skill 管理页面（列表 + 编辑）和聊天中 `load_skill` 工具的特殊渲染。

**Architecture:** 新增 3 个文件（API client + 2 个页面组件），修改 4 个现有文件（类型、路由、导航、聊天渲染）。Skill 为全局资源，使用 `SystemLayout`；编辑页复用现有的 `MarkdownEditor`（vditor）。

**Tech Stack:** React 18 + TypeScript + Vite + Ant Design 6 + `@ant-design/x-markdown`

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `frontend/src/types/index.ts` | 修改 | 新增 `Skill`、`CreateSkillRequest`、`UpdateSkillRequest` 接口 |
| `frontend/src/api/skills.ts` | 创建 | Skill REST API 封装 |
| `frontend/src/components/layout/IconSidebar.tsx` | 修改 | 新增"技能"全局导航项 |
| `frontend/src/App.tsx` | 修改 | 注册 `/skills/*` 路由到 `SystemLayout` |
| `frontend/src/pages/skills/SkillManager.tsx` | 创建 | Skill 列表管理页（Tabs + Card 网格） |
| `frontend/src/pages/skills/SkillEdit.tsx` | 创建 | Skill 新建/编辑页（元数据 + vditor） |
| `frontend/src/components/ai/ChatCore.tsx` | 修改 | `TimelineView` 中 `load_skill` 特殊渲染 |

---

## Domain 常量

所有任务共享：

```ts
const DOMAIN_LABELS: Record<string, string> = {
  global: '全局',
  world: '世界观',
  character: '角色',
  plot: '剧情',
  chapter: '章节',
  review: '审校',
};

const DOMAIN_ORDER = ['global', 'world', 'character', 'plot', 'chapter', 'review'];
```

---

### Task 1: 类型定义与 API Client

**Files:**
- Modify: `frontend/src/types/index.ts`
- Create: `frontend/src/api/skills.ts`

- [ ] **Step 1: 在 `types/index.ts` 末尾追加 Skill 类型**

在文件末尾（`ConfigTestResponse` 之后）追加：

```ts
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
```

- [ ] **Step 2: 创建 `api/skills.ts`**

```ts
import client from './client';
import type { Skill, CreateSkillRequest, UpdateSkillRequest } from '@/types';

export const skillsApi = {
  list: () => client.get<Skill[]>('/skills/'),
  get: (name: string) => client.get<Skill>(`/skills/${name}`),
  create: (data: CreateSkillRequest) => client.post<Skill>('/skills/', data),
  update: (name: string, data: UpdateSkillRequest) =>
    client.post<Skill>(`/skills/${name}/update`, data),
  delete: (name: string) => client.post(`/skills/${name}/delete`),
};
```

- [ ] **Step 3: 验证 TypeScript 编译**

Run: `cd frontend && npm run type-check`
Expected: 无新增错误（可能有一些既有错误，确认没有 Skill 相关报错）

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/api/skills.ts
git commit -m "feat(skills): add Skill types and API client"
```

---

### Task 2: IconSidebar 新增"技能"导航项

**Files:**
- Modify: `frontend/src/components/layout/IconSidebar.tsx`

- [ ] **Step 1: 导入 `BookOutlined`**

将第一行导入改为：
```ts
import { HomeOutlined, SettingOutlined, ApiOutlined, BookOutlined } from '@ant-design/icons';
```

- [ ] **Step 2: 添加激活状态判断和导航项**

在 `isSystemSettings` 下方添加：
```ts
const isSkills = location.pathname === '/skills' || location.pathname.startsWith('/skills/');
```

在 `SidebarItem`（首页）下方、`div style={{ flex: 1 }}` 上方添加：
```tsx
<SidebarItem
  icon={<BookOutlined />}
  label="技能"
  active={isSkills}
  onClick={() => navigate('/skills')}
/>
```

- [ ] **Step 3: 验证编译**

Run: `cd frontend && npm run type-check`
Expected: 无新增错误

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/layout/IconSidebar.tsx
git commit -m "feat(skills): add skill navigation to IconSidebar"
```

---

### Task 3: App.tsx 路由注册

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 导入 Skill 页面组件**

在 `import ChatPage from '@/pages/chat/ChatPage';` 下方添加：
```ts
import SkillManager from '@/pages/skills/SkillManager';
import SkillEdit from '@/pages/skills/SkillEdit';
```

- [ ] **Step 2: 在 `SystemLayout` 路由组内添加 skill 路由**

在 `<Route path="/settings" element={<SystemSettings />} />` 下方添加：
```tsx
<Route path="/skills" element={<SkillManager />} />
<Route path="/skills/new" element={<SkillEdit />} />
<Route path="/skills/:skillName/edit" element={<SkillEdit />} />
```

- [ ] **Step 3: 验证编译**

Run: `cd frontend && npm run type-check`
Expected: 此时 `SkillManager` 和 `SkillEdit` 还不存在，会有导入错误，这是预期的。继续执行 Task 4/5 后错误会消失。

---

### Task 4: SkillManager 列表页

**Files:**
- Create: `frontend/src/pages/skills/SkillManager.tsx`

- [ ] **Step 1: 创建 `SkillManager.tsx`**

```tsx
import { useState, useEffect, useMemo } from 'react';
import {
  Tabs, Card, Row, Col, Tag, Empty, Spin, Button, Modal, Input,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAppMessage } from '@/hooks/useAppMessage';
import { skillsApi } from '@/api/skills';
import PageHeader from '@/components/common/PageHeader';
import PageContainer from '@/components/common/PageContainer';
import type { Skill } from '@/types';

const DOMAIN_LABELS: Record<string, string> = {
  global: '全局',
  world: '世界观',
  character: '角色',
  plot: '剧情',
  chapter: '章节',
  review: '审校',
};

const DOMAIN_ORDER = ['global', 'world', 'character', 'plot', 'chapter', 'review'];

const SkillManager = () => {
  const navigate = useNavigate();
  const { message } = useAppMessage();
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    skillsApi.list()
      .then(res => setSkills(res.data))
      .catch(() => message.error('加载技能列表失败'))
      .finally(() => setLoading(false));
  }, [message]);

  const grouped = useMemo(() => {
    const map: Record<string, Skill[]> = {};
    for (const d of DOMAIN_ORDER) map[d] = [];
    for (const s of skills) {
      const d = s.domain || 'global';
      if (!map[d]) map[d] = [];
      map[d].push(s);
    }
    return map;
  }, [skills]);

  const filteredGroups = useMemo(() => {
    if (!search.trim()) return grouped;
    const term = search.trim().toLowerCase();
    const result: Record<string, Skill[]> = {};
    for (const d of DOMAIN_ORDER) {
      result[d] = grouped[d].filter(s =>
        s.name.toLowerCase().includes(term) ||
        s.description.toLowerCase().includes(term) ||
        s.tags.some(t => t.toLowerCase().includes(term))
      );
    }
    return result;
  }, [grouped, search]);

  const handleDelete = (skill: Skill) => {
    Modal.confirm({
      title: '删除确认',
      content: `确定要删除技能 "${skill.name}" 吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await skillsApi.delete(skill.name);
          setSkills(prev => prev.filter(s => s.name !== skill.name));
          message.success('删除成功');
        } catch {
          message.error('删除失败');
        }
      },
    });
  };

  if (loading) {
    return (
      <PageContainer>
        <div style={{ textAlign: 'center', paddingTop: 120 }}>
          <Spin size="large" />
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <PageHeader
        title="技能库"
        subtitle="管理 AI 助手的专长技能"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/skills/new')}
          >
            新建技能
          </Button>
        }
      />

      <Input.Search
        placeholder="搜索技能名称、描述或标签..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        style={{ marginBottom: 24, maxWidth: 400 }}
        allowClear
      />

      <Tabs
        items={DOMAIN_ORDER.map(domain => {
          const list = filteredGroups[domain] || [];
          return {
            key: domain,
            label: `${DOMAIN_LABELS[domain]} (${list.length})`,
            children: list.length === 0 ? (
              <Empty description={`${DOMAIN_LABELS[domain]}领域暂无技能`} />
            ) : (
              <Row gutter={[16, 16]}>
                {list.map(skill => (
                  <Col key={skill.name} xs={24} sm={12} lg={8}>
                    <Card
                      hoverable
                      title={
                        <span style={{
                          fontFamily: 'var(--font-mono)',
                          fontWeight: 600,
                          fontSize: 14,
                        }}>
                          {skill.name}
                        </span>
                      }
                      actions={[
                        <EditOutlined
                          key="edit"
                          onClick={() => navigate(`/skills/${skill.name}/edit`)}
                        />,
                        <DeleteOutlined
                          key="delete"
                          style={{ color: 'var(--vermilion)' }}
                          onClick={() => handleDelete(skill)}
                        />,
                      ]}
                    >
                      <p style={{
                        color: 'var(--ink-medium)',
                        fontSize: 13,
                        lineHeight: 1.6,
                        minHeight: 42,
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                      }}>
                        {skill.description}
                      </p>
                      <div style={{ marginTop: 12, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {skill.domain && skill.domain !== 'global' && (
                          <Tag size="small">{DOMAIN_LABELS[skill.domain] || skill.domain}</Tag>
                        )}
                        {skill.tags.map(tag => (
                          <Tag key={tag} size="small">{tag}</Tag>
                        ))}
                      </div>
                    </Card>
                  </Col>
                ))}
              </Row>
            ),
          };
        })}
      />
    </PageContainer>
  );
};

export default SkillManager;
```

- [ ] **Step 2: 验证编译**

Run: `cd frontend && npm run type-check`
Expected: `SkillManager` 已定义，无导入错误

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/skills/SkillManager.tsx
git commit -m "feat(skills): add SkillManager list page with domain tabs"
```

---

### Task 5: SkillEdit 编辑页

**Files:**
- Create: `frontend/src/pages/skills/SkillEdit.tsx`

- [ ] **Step 1: 创建 `SkillEdit.tsx`**

```tsx
import { useState, useEffect } from 'react';
import {
  Button, Input, Select, Form, Breadcrumb, Spin, Space,
} from 'antd';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAppMessage } from '@/hooks/useAppMessage';
import { skillsApi } from '@/api/skills';
import MarkdownEditor from '@/components/common/MarkdownEditor';
import PageContainer from '@/components/common/PageContainer';
import type { Skill } from '@/types';

const DOMAIN_OPTIONS = [
  { value: 'global', label: '全局' },
  { value: 'world', label: '世界观' },
  { value: 'character', label: '角色' },
  { value: 'plot', label: '剧情' },
  { value: 'chapter', label: '章节' },
  { value: 'review', label: '审校' },
];

const NAME_PATTERN = /^[a-z0-9]+(-[a-z0-9]+)*$/;

const SkillEdit = () => {
  const { skillName } = useParams<{ skillName: string }>();
  const navigate = useNavigate();
  const { message } = useAppMessage();
  const [form] = Form.useForm();

  const isNew = !skillName;
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [content, setContent] = useState('');

  useEffect(() => {
    if (isNew) {
      setLoading(false);
      return;
    }
    skillsApi.get(skillName)
      .then(res => {
        const data: Skill = res.data;
        form.setFieldsValue({
          name: data.name,
          description: data.description,
          domain: data.domain || 'global',
          tags: data.tags || [],
        });
        setContent(data.content || '');
        setLoading(false);
      })
      .catch(() => {
        message.error('加载技能失败');
        navigate('/skills');
      });
  }, [skillName, isNew, form, message, navigate]);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);

      const payload = {
        description: values.description,
        content,
        domain: values.domain === 'global' ? null : values.domain,
        tags: values.tags || [],
      };

      if (isNew) {
        await skillsApi.create({
          name: values.name,
          ...payload,
        });
      } else {
        await skillsApi.update(skillName!, payload);
      }

      message.success('保存成功');
      navigate('/skills');
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
        if (axiosErr.response?.status === 409) {
          message.error(axiosErr.response.data?.detail || '技能名称已存在');
        } else {
          message.error('保存失败');
        }
      }
      // validation errors are handled by Form
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <PageContainer>
        <div style={{ textAlign: 'center', paddingTop: 120 }}>
          <Spin size="large" />
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <Breadcrumb
        style={{ marginBottom: 12, fontFamily: 'var(--font-display)', letterSpacing: '0.04em' }}
        items={[
          { title: <Link to="/skills">技能库</Link> },
          { title: isNew ? '新建技能' : skillName },
        ]}
      />

      <Form
        form={form}
        layout="vertical"
        style={{ marginBottom: 24 }}
        initialValues={{ domain: 'global', tags: [] }}
      >
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <Form.Item
            name="name"
            label="技能名称"
            rules={[
              { required: true, message: '请输入技能名称' },
              {
                pattern: NAME_PATTERN,
                message: '名称只能包含小写字母、数字和连字符',
              },
            ]}
            style={{ flex: 1, minWidth: 240 }}
          >
            <Input placeholder="my-writing-style" disabled={!isNew} />
          </Form.Item>

          <Form.Item
            name="domain"
            label="领域"
            style={{ minWidth: 160 }}
          >
            <Select options={DOMAIN_OPTIONS} />
          </Form.Item>
        </div>

        <Form.Item
          name="description"
          label="描述"
          rules={[{ required: true, message: '请输入描述' }]}
        >
          <Input.TextArea
            rows={2}
            placeholder="一句话描述这个技能的用途..."
          />
        </Form.Item>

        <Form.Item name="tags" label="标签">
          <Select
            mode="tags"
            placeholder="输入标签后按回车"
            style={{ width: '100%' }}
          />
        </Form.Item>
      </Form>

      <div style={{ marginBottom: 8, fontSize: 14, fontWeight: 500, color: 'var(--ink-heavy)' }}>
        技能内容
      </div>
      <MarkdownEditor value={content} onChange={setContent} />

      <div style={{ marginTop: 24, display: 'flex', gap: 12 }}>
        <Button type="primary" loading={saving} onClick={handleSave}>
          保存
        </Button>
        <Button onClick={() => navigate('/skills')}>返回</Button>
      </div>
    </PageContainer>
  );
};

export default SkillEdit;
```

- [ ] **Step 2: 验证编译**

Run: `cd frontend && npm run type-check`
Expected: 无 Skill 相关错误

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/skills/SkillEdit.tsx
git commit -m "feat(skills): add SkillEdit page with Markdown editor"
```

---

### Task 6: ChatCore load_skill 特殊渲染

**Files:**
- Modify: `frontend/src/components/ai/ChatCore.tsx`

- [ ] **Step 1: 在 `TimelineView` 的 `tool` 事件渲染逻辑中，添加 `load_skill` 特殊处理**

找到 `TimelineView` 中 `event.type === 'tool'` 分支的 `children` 部分（大约在原文件第 164-188 行）。将 `children` 的逻辑从：

```tsx
children: event.isDelegate ? (
  hasSubTimeline ? (
    <TimelineView events={event.subTimeline!} depth={depth + 1} />
  ) : (
    <span style={{ fontSize: 12, color: 'var(--ink-light)', fontStyle: 'italic' }}>
      未见副手记录
    </span>
  )
) : event.result != null ? (
  <Typography>
    <pre style={{
      margin: 0,
      whiteSpace: 'pre-wrap',
      wordBreak: 'break-word',
      fontSize: 12,
      lineHeight: 1.6,
      color: 'var(--ink-medium)',
      fontFamily: 'var(--font-mono)',
      maxHeight: 300,
      overflow: 'auto',
    }}>
      {typeof event.result === 'string' ? event.result : JSON.stringify(event.result, null, 2)}
    </pre>
  </Typography>
) : null,
```

替换为：

```tsx
children: event.isDelegate ? (
  hasSubTimeline ? (
    <TimelineView events={event.subTimeline!} depth={depth + 1} />
  ) : (
    <span style={{ fontSize: 12, color: 'var(--ink-light)', fontStyle: 'italic' }}>
      未见副手记录
    </span>
  )
) : event.result != null ? (
  (() => {
    // Special rendering for load_skill tool results
    if (event.name === 'load_skill' && typeof event.result === 'string') {
      const match = event.result.match(/^Loaded skill: ([^\n]+)\n\n([\s\S]*)$/);
      if (match) {
        const skillName = match[1];
        const skillContent = match[2];
        return (
          <div>
            <div style={{
              marginBottom: 8,
              fontSize: 12,
              fontFamily: 'var(--font-mono)',
              color: 'var(--ink-heavy)',
            }}>
              <span style={{
                background: 'var(--paper-sunken)',
                padding: '2px 8px',
                borderRadius: 'var(--radius-sm)',
              }}>
                {skillName}
              </span>
            </div>
            <div style={{
              maxHeight: 300,
              overflow: 'auto',
              fontSize: 12,
              lineHeight: 1.6,
            }}>
              <XMarkdown>{skillContent}</XMarkdown>
            </div>
          </div>
        );
      }
    }
    return (
      <Typography>
        <pre style={{
          margin: 0,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          fontSize: 12,
          lineHeight: 1.6,
          color: 'var(--ink-medium)',
          fontFamily: 'var(--font-mono)',
          maxHeight: 300,
          overflow: 'auto',
        }}>
          {typeof event.result === 'string' ? event.result : JSON.stringify(event.result, null, 2)}
        </pre>
      </Typography>
    );
  })()
) : null,
```

- [ ] **Step 2: 验证编译**

Run: `cd frontend && npm run type-check`
Expected: 无新增错误

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ai/ChatCore.tsx
git commit -m "feat(chat): render load_skill tool results as markdown"
```

---

### Task 7: App.tsx 导入修正与最终验证

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 确认 `SkillEdit` 导入路径正确**

确保导入为 `import SkillEdit from '@/pages/skills/SkillEdit';`。

- [ ] **Step 2: 运行前端完整编译**

Run: `cd frontend && npm run type-check`
Expected: 全部通过（包括 SkillManager 和 SkillEdit 的导入）

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat(skills): register skill routes in App.tsx"
```

---

## Self-Review Checklist

**1. Spec coverage:**
- [x] Skill 管理页面（Tabs + 卡片网格）→ Task 4
- [x] 按 domain 分组展示 → Task 4 中 `DOMAIN_ORDER` + `Tabs.items`
- [x] 新建/编辑 skill → Task 5 `SkillEdit`
- [x] 使用 MarkdownEditor（vditor）→ Task 5 中 `MarkdownEditor`
- [x] 删除确认 → Task 4 `Modal.confirm`
- [x] IconSidebar 独立导航项 → Task 2
- [x] 全局路由 `/skills/*` → Task 3
- [x] 聊天中 `load_skill` 特殊渲染 → Task 6
- [x] API client 与类型 → Task 1

**2. Placeholder scan:**
- [x] 无 "TBD" / "TODO" / "implement later"
- [x] 所有步骤包含完整代码
- [x] 所有步骤包含验证命令

**3. Type consistency:**
- [x] `Skill` 接口中的 `domain` 为 `string | null`，与后端 `SkillResponse` 一致
- [x] `CreateSkillRequest` / `UpdateSkillRequest` 字段与后端 `SkillCreate` / `SkillUpdate` 一致
- [x] `skillsApi.update` 使用 `POST /{name}/update`，与后端路由一致
- [x] `skillsApi.delete` 使用 `POST /{name}/delete`，与后端路由一致
