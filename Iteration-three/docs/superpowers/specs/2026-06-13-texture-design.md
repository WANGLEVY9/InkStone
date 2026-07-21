# 前端纹理精致化设计文档

**日期**：2026-06-13  
**主题**：砚台前端“书房/文房”主题纹理升级（纯 CSS/SVG 程序化纹理）  
**范围**：`frontend/src/styles/theme.css`、`frontend/src/styles/vditor-override.css`、`frontend/src/components/layout/IconSidebar.tsx`  
**目标**：在不引入静态图片的前提下，通过程序化纹理增强侧边栏木纹、印章压印/墨晕反馈、编辑器稿纸质感，使界面从“扁平色块”向“有触感的文房四宝”演进。

---

## 背景与问题

当前前端已经建立了完整的“砚台丹青”视觉语言（宣纸色、朱砂红、宋体字形），但仍有以下扁平感：

1. `IconSidebar` 使用纯色 `#3A2A1F`，没有真实书案侧板的木纹质感。
2. `.seal-stamp` 虽形似印章，但缺少“按下”和“墨晕”反馈；主按钮 hover 仍是 Ant Design 默认效果。
3. `MarkdownEditor` 已调成宣纸底色，但仍是纯色，缺少稿纸横线，光标也是默认颜色。

本次设计聚焦 B/D/E 三处，采用**纯 CSS/SVG 程序化纹理**（方案 A），便于版本控制、主题切换和 Retina 显示。

---

## 设计原则

1. **无静态资源**：所有纹理用内联 SVG data URI 或 CSS 渐变实现，不增加 HTTP 请求。
2. **可调参数化**：纹理透明度、行高、旋转角度全部用 CSS 变量控制，方便后续微调。
3. **不破坏功能**：导航、编辑、全屏、z-index 等现有行为保持不变。
4. **可访问性优先**：纹理足够淡，文字对比度保持 ≥ 4.5:1；支持 `prefers-reduced-motion`。

---

## 1. 新增纹理 Token

在 `frontend/src/styles/theme.css` 的 `:root` 中追加：

```css
:root {
  /* ----- Wood grain for IconSidebar ----- */
  --texture-wood-grain: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 200 200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.05 0.005' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.95 0 0 0 0 0.90 0 0 0 0 0.84 0 0 0 0.12 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
  --texture-wood-opacity: 0.10;

  /* ----- Ruled paper for MarkdownEditor ----- */
  --texture-paper-ruled: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='30.4' viewBox='0 0 100 30.4'><line x1='0' y1='30.4' x2='100' y2='30.4' stroke='%23C9B999' stroke-width='0.5' stroke-opacity='0.25'/></svg>");
  --texture-paper-ruled-line-height: 30.4px;

  /* ----- Ink bleed for hover/press ----- */
  --texture-ink-bleed: radial-gradient(circle at center, rgba(200, 50, 61, 0.10) 0%, transparent 70%);
}
```

并新增三个工具类：

```css
.wood-texture {
  background-color: var(--wood-deep);
  background-image: var(--texture-wood-grain);
  background-blend-mode: soft-light;
}

.paper-ruled {
  background-image: var(--texture-paper-ruled);
  background-size: 100% var(--texture-paper-ruled-line-height);
}

.ink-press:active {
  transform: scale(0.96);
}
```

> 注：木纹 SVG 的 `baseFrequency='0.05 0.005'` 让噪点在水平方向拉伸，形成木纤维走向；稿纸 SVG 高度与编辑器行高一致，避免横线错位。

---

## 2. IconSidebar 木纹改造

### 2.1 视觉目标
让左侧 64px 固定边栏像一块嵌在书案里的深色木板，既有木纹走向，又不抢夺主内容注意力。

### 2.2 改动点

- 给 `Sider` 的 `style` 增加 `.wood-texture` 类，替换当前纯色背景。
- 右侧内阴影 `box-shadow: inset -2px 0 4px rgba(0, 0, 0, 0.25)` 保留侧板嵌入感。
- 激活项指示灯从 2px 竖线改为小圆点“铜钉”样式：
  - 直径 6px
  - 颜色 `var(--vermilion)`
  - `box-shadow: inset 0 1px 1px rgba(255,255,255,0.25), 0 1px 2px rgba(0,0,0,0.3)`
- 顶部“砚”字印章 hover 时仅做轻微放大，不破坏木纹氛围。

### 2.3 可访问性
木纹叠加后需实测图标与背景对比度；若低于 4.5:1，降低 `--texture-wood-opacity` 至 0.06。

---

## 3. 印章与墨晕反馈

### 3.1 `.seal-stamp` 压印感

```css
.seal-stamp {
  /* 在现有样式上追加 */
  box-shadow:
    0 1px 2px rgba(159, 37, 48, 0.40),
    inset 0 0 0 1px rgba(255, 255, 255, 0.15),
    inset 0 -1px 0 rgba(0, 0, 0, 0.20);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.seal-stamp:active {
  transform: scale(0.96);
  box-shadow:
    inset 0 2px 4px rgba(0, 0, 0, 0.25),
    inset 0 0 0 1px rgba(255, 255, 255, 0.10);
}
```

- 给每个印章实例分配固定小角度：例如标题处 `rotate(-1deg)`，卡片内 `rotate(1deg)`，避免机械对齐；角度通过组件内联 `style` 传入，不使用随机数（保证 SSR/渲染稳定）。

### 3.2 主按钮墨晕 hover

对 `antd Button type="primary"` 的 hover 状态做覆盖：

```css
.ant-btn-primary::after {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--texture-ink-bleed);
  opacity: 0;
  transition: opacity 0.25s ease-out;
  pointer-events: none;
  border-radius: inherit;
}

.ant-btn-primary:hover::after {
  opacity: 1;
}
```

- 仅对主要操作按钮生效；`danger` / `link` 样式不添加墨晕，避免混乱。

### 3.3 动效降级

```css
@media (prefers-reduced-motion: reduce) {
  .seal-stamp,
  .ant-btn-primary::after {
    transition: none;
  }
  .seal-stamp:active {
    transform: none;
  }
}
```

---

## 4. MarkdownEditor 稿纸背景

### 4.1 视觉目标
让写作区看起来像一沓有淡淡横线的宣纸稿纸，光标像朱笔，但预览区保持干净以利阅读。

### 4.2 改动点

在 `frontend/src/styles/vditor-override.css` 中，给编辑区追加 `.paper-ruled`：

```css
.vditor-ir,
.vditor-sv,
.vditor-wysiwyg {
  background:
    var(--paper-elevated)
    var(--texture-paper-ruled) !important;
  background-size: 100% var(--texture-paper-ruled-line-height) !important;
}

/* 预览区不带横线 */
.vditor-preview,
.vditor-preview .vditor-reset {
  background: var(--paper-elevated) !important;
}
```

- 光标颜色改为朱笔色：

```css
.vditor-ir,
.vditor-wysiwyg,
.vditor-sv {
  caret-color: var(--vermilion-deep);
}
```

- 保持现有 padding、字体、heading 样式不变。

### 4.3 行高对齐
编辑器当前 `font-size: 16px; line-height: 1.9;`，对应行高 `30.4px`。稿纸 SVG 高度与此一致，横线落在每行底部，避免视觉错位。若后续调整行高，必须同步修改 `--texture-paper-ruled-line-height`。

---

## 5. 组件影响面

| 文件 | 改动内容 |
|------|----------|
| `frontend/src/styles/theme.css` | 新增纹理变量与工具类；扩展 `.seal-stamp`、`.ant-btn-primary` 样式。 |
| `frontend/src/styles/vditor-override.css` | 编辑区加 `.paper-ruled`；光标改色；预览区保持纯色。 |
| `frontend/src/components/layout/IconSidebar.tsx` | `Sider` 应用 `.wood-texture`；激活指示灯改为铜钉样式。 |

无需改动 `App.tsx` 的 `ConfigProvider`，因为本次升级全部基于 CSS 变量和工具类。

---

## 6. 性能与兼容性

1. **SVG data URI 体积**：木纹和稿纸 SVG 均小于 800 bytes，gzip 后约 300 bytes，无额外网络请求。
2. **渲染性能**：`background-blend-mode: soft-light` 在侧栏固定区域使用，仅 64px 宽，对 GPU 压力极小；编辑区稿纸为背景图 repeat，不会触发重排。
3. **浏览器兼容**：`background-blend-mode` 和 `caret-color` 在现代浏览器均支持；如遇到旧版浏览器，背景会优雅降级为纯色。
4. **无障碍**：
   - 木纹透明度 ≤ 12%，保证图标对比度。
   - 墨晕 hover 不依赖颜色传递唯一信息。
   - 所有新增动画支持 `prefers-reduced-motion`。

---

## 7. 验收标准

- [ ] `IconSidebar` 在浅色/深色内容对比下，木纹可见但不抢眼，图标清晰可辨。
- [ ] `.seal-stamp` hover/active 有明确压印反馈，各实例角度自然不呆板。
- [ ] 主按钮 hover 有从中心扩散的墨晕效果。
- [ ] `MarkdownEditor` 编辑区出现淡横线稿纸背景，光标为朱红色；预览区无横线。
- [ ] 所有改动通过 `npm run type-check` 和 `npm run lint`。
- [ ] 在 `prefers-reduced-motion: reduce` 下无缩放/扩散动画。

---

## 8. 后续可升级方向（不在本次范围）

- 若方案 A 的木纹真实感不足，可考虑方案 B：引入 1-2 张 tileable PNG 纹理图。
- 为 Dashboard 的书架封面 `BookCover` 增加更多织物纹理细节。
- 为聊天界面的 thinking/tool 卡片加入轻微纸张阴影层次。
