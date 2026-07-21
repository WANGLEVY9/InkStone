# antd 升级 + AI 聊天 Drawer 可调整大小

日期: 2026-05-09

## 背景

AI 聊天助手目前使用 antd `Drawer` 从右侧滑出，宽度固定 400px，无法调整。用户希望 Drawer 支持拖拽调整宽度。antd 5.x 的 Drawer 不支持 `resizable` 属性，该功能在 antd 6.1.0+ 才引入。因此需要先升级 antd 到 6.x。

## 目标

1. 升级 antd 从 5.21.x 到 6.3.7（最新稳定版）
2. AI 聊天 Drawer 启用 `resizable`，支持拖拽调整宽度
3. 修复升级过程中所有 breaking changes，确保 type-check、lint、build 通过

## 范围

- **包含**：antd 及 @ant-design/icons 升级、breaking changes 修复、Drawer resizable 配置
- **不包含**：AI 按钮拖拽（后续独立任务）、后端变更、路由变更

## 设计

### 1. antd 升级

```
npm install antd@6.3.7 @ant-design/icons@latest
```

升级后需要排查的 breaking changes：
- `Tooltip`/`Popover`/`Popconfirm` 的 deprecated props 重命名（`overlayClassName` → `classNames.root`，`overlayStyle` → `styles.root`，`destroyTooltipOnHide` → `destroyOnHidden`）
- `ConfigProvider` 和 theme token 是否有变化
- `Drawer` 的 `styles`/`classNames` 语义是否变化
- 其他组件 API 变更（通过 type-check 发现）

验证方式：
- `npm run type-check` 通过
- `npm run lint` 通过
- `npm run build` 通过

### 2. Drawer resizable 配置

文件：`frontend/src/components/ai/AIFab.tsx`

在现有 `<Drawer>` 上添加 3 个属性：

```tsx
<Drawer
  title="AI 助手"
  placement="right"
  width={400}
  resizable        // 启用左侧边缘拖拽调整宽度
  minSize={300}    // 最小宽度 300px
  maxSize={800}    // 最大宽度 800px
  open={open}
  onClose={() => setOpen(false)}
  styles={{ body: { padding: 0, display: 'flex', flexDirection: 'column' } }}
>
  <ChatPanel />
</Drawer>
```

- `resizable`：Drawer 左侧边缘出现拖拽手柄，用户可左右拖拽调整宽度
- `minSize={300}`：保证聊天内容可读
- `maxSize={800}`：避免占满屏幕
- 其余配置不变（mask、keyboard、placement 等保持现状）

### 3. 影响范围

| 文件/模块 | 影响 |
|-----------|------|
| `package.json` | antd + @ant-design/icons 版本号 |
| `AIFab.tsx` | 添加 resizable/minSize/maxSize |
| 其他 antd 组件文件 | 可能需要修复 deprecated props（升级后由 type-check 确定） |

## 验收标准

- [ ] antd 版本为 6.3.7
- [ ] AI 聊天 Drawer 可通过拖拽左侧边缘调整宽度
- [ ] 最小宽度 300px，最大宽度 800px
- [ ] `npm run type-check` 通过
- [ ] `npm run lint` 通过
- [ ] `npm run build` 通过
- [ ] 现有功能无回归（手动验证 Drawer 打开/关闭、Ctrl+J 快捷键、聊天功能）
