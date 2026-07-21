# Implementation Tasks

## Phase 1: ContentService 新增查询方法

- [x] 1.1 在 `content.py` 添加 `get_all_world_settings(project_id)` 方法
- [x] 1.2 在 `content.py` 添加 `get_all_characters(project_id)` 方法
- [x] 1.3 在 `content.py` 添加 `get_root_outline(project_id)` 方法
- [x] 1.4 在 `content.py` 添加 `get_all_chapters(project_id)` 方法

## Phase 2: chat.py 注入项目上下文

- [x] 2.1 修改 `chat_stream_endpoint`，在创建 `initial_state` 前调用 ContentService 查询方法
- [x] 2.2 将硬编码的空 `project_context` 替换为实际查询结果
- [x] 2.3 确保 `ContentService` 在函数开头正确导入

## Phase 3: builder.py 使用模板注入上下文

- [x] 3.1 修改 `orchestrator_node`，在构建 messages 时使用 `ORCHESTRATOR_USER_TEMPLATE`
- [x] 3.2 确保模板正确接收 `state["project_context"]` 的所有字段
- [x] 3.3 验证对话历史正确追加到消息列表

## Phase 4: orchestrator.py 模板调整（如需要）

- [x] 4.1 检查 `ORCHESTRATOR_USER_TEMPLATE` 格式是否与 builder.py 调用匹配
- [x] 4.2 如需要，调整模板变量名称或结构

## Phase 5: 测试

- [ ] 5.1 在 `test_content_service.py` 添加新查询方法的单元测试
- [ ] 5.2 在 `test_e2e_chat.py` 添加验证 project_context 加载的集成测试
- [x] 5.3 运行 `uv run pytest` 确保所有测试通过
- [x] 5.4 运行 `uv run ruff check` 确保代码风格正确