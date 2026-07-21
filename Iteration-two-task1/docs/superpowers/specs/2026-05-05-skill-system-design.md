# Skill System Design

## Overview

Add a global, prompt-driven **Skill** system to the novel-writing agent. Skills are specialized prompts (e.g., writing styles, genre conventions, narrative techniques) that agents can load on-demand via the LangChain progressive disclosure pattern. Both the orchestrator and sub-agents can load skills.

## Motivation

The current system has 5 hardcoded sub-agents with fixed capabilities. Users cannot inject domain knowledge (e.g., "write in wuxia style", "use noir detective conventions") into the agent's behavior. A skill system allows extensible, user-defined specializations without modifying agent code.

## Architecture

### Pattern: Middleware + load_skill Tool (LangChain Progressive Disclosure)

Following the LangChain SQL Assistant Skills tutorial:

1. **`load_skill` tool** — generic tool that loads a skill's full content by name. Does NOT hardcode skill list in its docstring.
2. **`SkillMiddleware`** — `AgentMiddleware` subclass that dynamically reads the current skill list from disk at each `wrap_model_call` and injects skill names + descriptions into the system prompt. This ensures newly created skills are automatically visible without rebuilding tools.

```
User Request
  → SkillMiddleware(orchestrator): reads global skills, injects into system prompt
  → Orchestrator Agent
    → load_skill("wuxia-writing"): loads full skill content
    → delegate_to_chapter(task + skill context)
      → SkillMiddleware(chapter): reads chapter-domain skills, injects into system prompt
      → Chapter Agent writes with skill-enhanced context
```

### Skill Scope

- **Global skills** (`domain` is null/empty): Available to the orchestrator via its `SkillMiddleware`
- **Domain skills** (`domain` = `world`/`character`/`plot`/`chapter`/`review`): Available to the corresponding sub-agent via its domain-scoped `SkillMiddleware`

## Data Model

### Skill File Format

Markdown with YAML frontmatter, stored at `backend/data/skills/{name}.md`:

```markdown
---
name: wuxia-writing
description: 金庸武侠小说写作风格，注重武打场面描写、江湖恩怨和侠义精神
domain: chapter
tags: [武侠, 写作风格, 金庸]
---

[Full prompt content — injected into agent context when loaded]
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier, also the filename (`{name}.md`) |
| `description` | Yes | 1-2 sentence description shown in system prompt for discovery |
| `domain` | No | `world`/`character`/`plot`/`chapter`/`review`. Empty = global (orchestrator) |
| `tags` | No | Auxiliary labels for categorization |

### Parsed Skill Dict

```python
{
    "name": str,
    "description": str,
    "domain": str | None,
    "tags": list[str],
    "content": str,  # The markdown body (everything after frontmatter)
}
```

## New Files

### `backend/app/services/skill.py` — SkillService

```python
class SkillService:
    def __init__(self):
        self.skills_dir = Path("backend/data/skills")

    def list_skills(self, domain: str | None = None) -> list[dict]
        # Read all .md files, parse YAML frontmatter
        # If domain is None, return only global skills (domain is empty)
        # If domain is set, return skills matching that domain

    def get_skill(self, name: str) -> dict | None
        # Read single skill file by name

    def create_skill(self, name: str, description: str, content: str,
                     domain: str | None = None, tags: list[str] | None = None) -> dict
        # Write new skill file with frontmatter

    def update_skill(self, name: str, **kwargs) -> dict | None
        # Update existing skill file fields

    def delete_skill(self, name: str) -> bool
        # Delete skill file
```

Uses `PyYAML` for frontmatter parsing (already a transitive dependency via langchain). Falls back to manual parsing if needed.

### `backend/app/core/agent/skill_middleware.py` — SkillMiddleware + load_skill

```python
from langchain.tools import tool
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from app.services.skill import SkillService

def create_load_skill_tool(skill_service: SkillService):
    """Create the load_skill tool bound to a SkillService instance."""

    @tool
    def load_skill(skill_name: str) -> str:
        """Load a skill's full content into context.
        Use this when you need specialized guidance for a specific domain or style.
        """
        skill = skill_service.get_skill(skill_name)
        if not skill:
            available = ", ".join(s["name"] for s in skill_service.list_skills())
            return f"Skill '{skill_name}' not found. Available: {available}"
        return f"Loaded skill: {skill_name}\n\n{skill['content']}"

    return load_skill


class SkillMiddleware(AgentMiddleware):
    """Injects skill descriptions into system prompt and registers load_skill tool."""

    def __init__(self, domain: str | None = None):
        super().__init__()
        self.domain = domain
        self.skill_service = SkillService()
        self.tools = [create_load_skill_tool(self.skill_service)]

    def wrap_model_call(self, request: ModelRequest, handler) -> ModelResponse:
        # Read current skills dynamically each call
        skills = self.skill_service.list_skills(domain=self.domain)
        if not skills:
            return handler(request)

        skills_list = "\n".join(
            f"- **{s['name']}**: {s['description']}" for s in skills
        )
        skills_addendum = (
            f"\n\n## Available Skills\n\n{skills_list}\n\n"
            "Use the load_skill tool when you need specialized guidance."
        )

        # Append to last system message
        messages = list(request.messages)
        if messages and isinstance(messages[-1], SystemMessage):
            messages[-1] = SystemMessage(
                content=messages[-1].content + skills_addendum
            )
        else:
            messages.append(SystemMessage(content=skills_addendum))

        return handler(request.override(messages=messages))
```

### `backend/app/api/v1/skills.py` — API Routes

```python
router = APIRouter(prefix="/skills", tags=["skills"])
skill_service = SkillService()

@router.get("")           # List skills, ?domain= filter
@router.get("/{name}")    # Get single skill
@router.post("")          # Create skill
@router.post("/{name}/update")  # Update skill
@router.post("/{name}/delete")  # Delete skill
```

Follows existing pattern: `POST /{id}/update` and `POST /{id}/delete` (not PATCH/DELETE).

## Modified Files

### `backend/app/core/graph/builder.py`

In `create_orchestrator_graph()`, add `SkillMiddleware` to the orchestrator agent:

```python
from app.core.agent.skill_middleware import SkillMiddleware

skill_middleware = SkillMiddleware(domain=None)  # Global skills
agent = create_agent(model, tools, system_prompt,
                     checkpointer=checkpointer,
                     middleware=[skill_middleware])
```

### `backend/app/core/agent/langchain_subagents.py`

In each sub-agent factory, add a domain-scoped `SkillMiddleware`:

```python
def create_chapter_agent(project_id, model=None):
    tools = create_chapter_tools(project_id) + create_read_tools(project_id)
    skill_middleware = SkillMiddleware(domain="chapter")
    return create_agent(model, tools, CHAPTER_SYSTEM_PROMPT,
                        middleware=[skill_middleware])
```

Same pattern for all 5 sub-agents with their respective domains.

### `backend/app/main.py`

Register the skills router:

```python
from app.api.v1.skills import router as skills_router
app.include_router(skills_router, prefix="/api/v1")
```

## Dependencies

- `pyyaml` — for YAML frontmatter parsing (currently available as transitive dep via langchain, should be added as explicit dependency in `pyproject.toml`)
- `langchain.agents.middleware` — `AgentMiddleware`, `ModelRequest`, `ModelResponse`, `SystemMessage`

## Implementation Notes

1. **SystemMessage injection**: The middleware appends skill descriptions to the last `SystemMessage` in the request. If `create_agent` uses its own system prompt mechanism (not via SystemMessage), the middleware needs to prepend a new SystemMessage instead. Verify at implementation time how `create_agent` passes the system prompt.
2. **SkillService is synchronous**: Consistent with existing `tool_factory.py` pattern where tools use sync `_invoke_llm_with_retry()`. If async is needed later, add async variants.
3. **File-based storage**: Skills are stored as individual `.md` files. For large skill collections (100+), consider adding an in-memory cache with file modification time checks.

## Example Skill Files

### `backend/data/skills/wuxia-writing.md`

```markdown
---
name: wuxia-writing
description: 金庸武侠小说写作风格，注重武打场面描写、江湖恩怨和侠义精神
domain: chapter
tags: [武侠, 写作风格, 金庸]
---

# 武侠写作指南

## 文风特征
- 使用半文半白的语言风格
- 武打场面注重招式名称和意境描写
- 人物对话要有江湖气概

## 常用元素
- 门派、武功秘籍、江湖恩怨
- 侠义精神：路见不平拔刀相助
- 师徒关系、兄弟情义

## 写作要点
- 环境描写要营造古风意境
- 打斗场面要有节奏感，动静结合
- 人物心理描写要含蓄内敛
```

### `backend/data/skills/noir-detective.md`

```markdown
---
name: noir-detective
description: 硬汉派侦探小说风格，黑色电影氛围，第一人称叙述
domain: chapter
tags: [悬疑, 推理, noir, 硬汉派]
---

# Noir Detective Writing Guide

## Style
- First-person narration, cynical and world-weary
- Short, punchy sentences mixed with longer atmospheric ones
- Heavy use of metaphor and simile, often dark or ironic

## Atmosphere
- Rain-soaked streets, dimly lit offices, smoky bars
- Urban decay, moral ambiguity
- Femme fatale, corrupt officials, desperate clients

## Plot Elements
- A case that starts simple but unravels into something bigger
- The detective gets beaten up but keeps going
- No one is telling the whole truth
```

## API Request/Response Examples

### Create Skill

```http
POST /api/v1/skills
Content-Type: application/json

{
    "name": "wuxia-writing",
    "description": "金庸武侠小说写作风格",
    "domain": "chapter",
    "tags": ["武侠", "金庸"],
    "content": "# 武侠写作指南\n\n## 文风特征\n..."
}
```

### List Skills

```http
GET /api/v1/skills?domain=chapter
```

Response:
```json
[
    {
        "name": "wuxia-writing",
        "description": "金庸武侠小说写作风格",
        "domain": "chapter",
        "tags": ["武侠", "金庸"]
    }
]
```

## Testing Strategy

1. **Unit tests**: SkillService CRUD, frontmatter parsing, domain filtering
2. **Integration tests**: SkillMiddleware injection into system prompt, load_skill tool execution
3. **API tests**: All 5 endpoints with edge cases (duplicate name, missing file, invalid frontmatter)
4. **E2E test**: Create skill via API → invoke agent → verify skill content appears in agent behavior

## Future Extensions (Out of Scope)

- Frontend UI for skill management
- Skill versioning
- Skill sharing across instances
- RAG-based skill discovery for large skill collections
