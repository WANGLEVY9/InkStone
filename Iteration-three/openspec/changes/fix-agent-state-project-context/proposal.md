## Why

当前 agent 实现存在一个关键 bug：`OrchestratorState.project_context` 在初始化时被硬编码为空值，导致 LLM 无法感知项目中已有的世界观、角色、大纲和章节数据。这违背了系统设计的初衷——LLM 应该能够参考已有的项目上下文来保持生成内容的一致性。

核心问题：
1. `chat.py` 中 `initial_state` 的 `project_context` 是空字典
2. `builder.py` 中 `orchestrator_node` 虽然定义了 `ORCHESTRATOR_USER_TEMPLATE`，但从未使用它来注入项目上下文

## What Changes

修改 4 个文件，修复 state 未正确加载项目数据的问题：

1. **content.py** - 新增 4 个查询方法：
   - `get_all_world_settings(project_id)` - 获取项目所有世界观
   - `get_all_characters(project_id)` - 获取项目所有角色
   - `get_root_outline(project_id)` - 获取项目根大纲
   - `get_all_chapters(project_id)` - 获取项目所有章节

2. **chat.py** - 修改 initial_state 创建逻辑：
   - 在创建图初始状态前，调用上述方法加载 `project_context`
   - 将硬编码的空值替换为从数据库查询的实际数据

3. **builder.py** - 修改 orchestrator_node：
   - 使用 `ORCHESTRATOR_USER_TEMPLATE` 格式化项目上下文
   - 将格式化后的用户消息与系统消息一起发送给 LLM

4. **orchestrator.py** - 调整模板（如需要）：
   - 确保 `ORCHESTRATOR_USER_TEMPLATE` 正确接收项目上下文

## Capabilities

### Modified Capabilities

- **orchestrator-agent**: 修复上下文注入，使 LLM 能感知已有项目数据
- **content-service**: 新增批量查询接口，支持加载完整项目上下文

### Technical Details

- **数据加载时机**: 在 `chat_stream_endpoint` 创建 `initial_state` 前
- **加载范围**: 项目下所有世界观、角色、大纲、章节的元数据（不含完整 content 以节省 token）
- **模板注入**: 在每次 `orchestrator_node` 调用时，通过 `ORCHESTRATOR_USER_TEMPLATE` 注入当前 `project_context`

## Impact

- **修改文件**: backend/app/services/content.py, backend/app/api/v1/chat.py, backend/app/core/graph/builder.py, backend/app/core/prompts/orchestrator.py
- **新增文件**: 无
- **API 变更**: 无
- **数据库变更**: 无
- **测试影响**: 需更新 `test_e2e_chat.py` 验证上下文正确加载
