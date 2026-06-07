# 施工单：Mermaid 图表交互增强

> **编号**: SC-FE-MERMAID-2026-001
> **创建日期**: 2026-06-07
> **登记状态**: 已登记（2026-06-07，见 `docs/current-active-execution-plans-zh.md`）
> **执行状态**: W1-W4 已完成（2026-06-07 归档）
> **优先级**: P1
> **影响范围**: `ScienceClaw/frontend/src/utils/markdownRenderer.ts`、`ScienceClaw/frontend/src/utils/content.ts`、`ScienceClaw/frontend/src/composables/useMermaidRenderer.ts`、`ScienceClaw/frontend/src/components/ChatMessage.vue`、`ScienceClaw/frontend/src/components/MarkdownEnhancements.vue`、`ScienceClaw/frontend/src/assets/chat-message-renderer.css`、`ScienceClaw/frontend/src/locales/zh.ts`、`ScienceClaw/frontend/src/locales/en.ts`、对应 spec

---

## 一、施工目标

在不改变现有 Mermaid 实时渲染语义的前提下，为聊天消息中的 Mermaid 图表增加图表级交互能力：

| 功能 | 目标行为 | 优先级 |
| --- | --- | --- |
| 下载 SVG | 用户可从每个已渲染 Mermaid 图表下载 `.svg` 文件 | P1 |
| 复制源码 | 用户可复制当前图表对应的 Mermaid 源码 | P1 |
| 全屏查看 | 用户可从消息内直接打开复杂图表的全屏查看 | P1 |
| 缩放 | 用户可在消息内放大、缩小、重置图表视图，并看到当前缩放比例 | P1 |
| 拖动/平移 | 图表放大后可在消息内拖动查看局部内容；滚轮缩放在实现成本可控时一并支持 | P1 |
| 源码查看 | 用户可在图表内切换查看 Mermaid 源码，便于调试和复用 | P2 |

本施工单只处理图表交互增强，不重新设计 Mermaid 语法、渲染主题、消息流式协议或后端数据结构。

核心交互口径：大部分操作必须直接在聊天消息中的 Mermaid 图表上完成，不要求用户先展开或进入全屏。全屏只作为复杂大图的增强查看模式，不作为复制、下载、缩放或拖动的前置条件。

---

## 二、现状锚点

### 2.1 Markdown 代码块分流

**文件**: `ScienceClaw/frontend/src/composables/useMarkdownRenderer.ts`

现有 Markdown renderer 已把 `mermaid` / `mmd` 代码块分流到 Mermaid placeholder，把 `mermaid-source` / `mmd-source` / `literal-mermaid` 作为普通源码代码块展示。后续不得破坏这两个语义。

### 2.2 Mermaid placeholder 已保存源码

**文件**: `ScienceClaw/frontend/src/utils/markdownRenderer.ts`

`renderMermaidPlaceholder()` 当前生成 `.mermaid-wrapper`，并通过 `data-mermaid-code="${encodeURIComponent(code)}"` 保存原始 Mermaid 源码。

结论：复制源码不需要重新解析 Markdown，可以直接从 wrapper 解码获得。

### 2.3 Mermaid 渲染结果是 SVG 字符串

**文件**: `ScienceClaw/frontend/src/utils/markdownRenderer.ts`

`renderMermaidWrapper()` 当前通过 `mermaid.render(renderId, code)` 获取 `{ svg }`，并把 SVG 写入 `.mermaid-content`。

结论：下载 SVG 可以从 `.mermaid-content svg` 序列化，也可以复用渲染阶段获得的 SVG 字符串。优先选择 DOM 序列化，避免改变现有缓存合同。

### 2.4 渲染调度集中在 composable

**文件**: `ScienceClaw/frontend/src/composables/useMermaidRenderer.ts`

`useMermaidRenderer()` 当前负责 `.mermaid-wrapper` 扫描、动态加载 Mermaid、异步渲染、MutationObserver 调度和流式输出后的最终渲染。

结论：新增图表交互初始化应与渲染完成状态绑定，避免对未渲染 wrapper 绑定无效行为。

### 2.5 图表样式已有独立 CSS 区域

**文件**: `ScienceClaw/frontend/src/assets/chat-message-renderer.css`

Mermaid 样式集中在 `.markdown-content .mermaid-wrapper`、`.mermaid-loading`、`.mermaid-content`、`.mermaid-error`、`.mermaid-raw-code`。

结论：工具栏、viewport、缩放层和源码面板样式应继续收口在该文件中，不回灌到 `ChatMessage.vue`。

### 2.6 现有 Markdown 增强层可复用

**文件**: `ScienceClaw/frontend/src/components/MarkdownEnhancements.vue`

该组件已有图片 lightbox 的缩放、拖动、滚轮缩放，以及代码块全屏复制逻辑。

结论：Mermaid 全屏和交互事件可复用现有增强层的交互模型，但应避免直接把图片 lightbox 状态和 Mermaid 状态混用。

### 2.7 Markdown 点击委派入口已存在

**文件**: `ScienceClaw/frontend/src/components/ChatMessage.vue`

`handleMarkdownClick()` 当前已经在 `.markdown-content` 上处理图片 lightbox 和代码块全屏按钮。

结论：Mermaid 工具栏点击可以优先接入 `handleMarkdownClick()` 的事件委派；`MarkdownEnhancements.vue` 更适合承接全屏 overlay 状态和暴露全屏打开方法。不要把所有 Mermaid 内嵌操作都塞进 overlay 组件里，避免职责反转。

### 2.8 DOMPurify 白名单会影响工具栏结构

**文件**: `ScienceClaw/frontend/src/utils/content.ts`

当前 DOMPurify 仅显式增加了 Mermaid 的 `data-mermaid-id`、`data-mermaid-code`、`id`，以及 SVG/KaTeX 相关属性。

结论：如果工具栏使用 `button`、`title`、`aria-label`、`data-mermaid-action`、`data-mermaid-state`、`hidden` 等属性，需要同步评估 sanitize 后是否保留，并补充 `content.spec.ts` 或 `markdownRenderer.spec.ts` 覆盖。

---

## 三、边界与约束

1. 不改变 assistant 消息中 `mermaid` / `mmd` 代码块实时渲染为图表的行为。
2. 不改变 user 消息当前纯文本展示策略。
3. 不改变 `mermaid-source` / `mmd-source` / `literal-mermaid` 作为源码展示的语义。
4. Mermaid 仍保持动态加载，不把 `mermaid` 纳入首屏同步依赖。
5. 新增所有用户可见文案必须接入 i18n，同时更新 `zh.ts` 和 `en.ts`。
6. 新增按钮必须有可访问名称或 tooltip，不得只依赖图标。
7. 缩放和平移应作用于外层 viewport，不直接改写 Mermaid 生成的 SVG 内部节点。
8. DOMPurify 白名单必须只增加实际需要的安全属性，不扩大到无界 HTML 权限；新增属性必须有 sanitize 后 HTML 单测覆盖。
9. 施工前如涉及修改函数、class 或 method，先按 AGENTS 中 GitNexus 规则做影响分析；提交前运行 `gitnexus detect-changes`。
10. 本施工单不覆盖已完成的 `docs/frontend-perf-optimization-plan-zh.md` 中 Mermaid 重试、并发和 LRU 缓存治理。
11. 图表工具栏必须在消息内可用，至少包含：全屏、复制 Mermaid 源码、放大、缩小、重置、下载 SVG。
12. 图表占位区域必须自适应内容和消息宽度，但设置最大高度上限；超过上限时在图表 viewport 内滚动或拖动查看，不撑爆聊天消息流。

---

## 四、推荐方案

### 4.1 DOM 结构

把 Mermaid placeholder 从单层内容区扩展为：

```html
<div class="mermaid-wrapper" data-mermaid-id="..." data-mermaid-code="...">
  <div class="mermaid-toolbar">...</div>
  <div class="mermaid-loading">...</div>
  <div class="mermaid-viewport">
    <div class="mermaid-transform-layer">
      <div class="mermaid-content" id="..."></div>
    </div>
  </div>
  <pre class="mermaid-source-panel" data-mermaid-source-panel hidden>...</pre>
</div>
```

说明：

- `.mermaid-toolbar` 是消息内主操作入口，至少包含全屏、复制源码、放大、缩小、重置、下载 SVG。
- `.mermaid-viewport` 负责裁剪、滚动和 pointer 事件。
- `.mermaid-transform-layer` 承载 `translate(...) scale(...)`。
- `.mermaid-content` 保持现有 SVG 写入点，降低对渲染逻辑的影响。
- `.mermaid-source-panel` 用于源码查看；复制源码仍以 `data-mermaid-code` 为准。
- `.mermaid-viewport` 高度自适应内容，但应设置最大高度，建议默认 `min(70vh, 720px)` 量级；移动端可降到 `min(65vh, 560px)`，具体值施工时按实际视觉测试微调。

### 4.2 事件所有权

优先采用事件委派：

- `useMermaidRenderer()` 负责渲染完成后的基础状态初始化，例如写入 `data-mermaid-rendered="true"`。
- `ChatMessage.vue` 的 `handleMarkdownClick()` 负责消息内工具栏点击委派，例如复制源码、下载 SVG、放大、缩小、重置、源码面板切换和打开全屏。
- `ChatMessage.vue` 或一个新增 composable 负责消息内 pointer/wheel 事件委派；如果实现逻辑超过局部函数可读范围，优先提取 `useMermaidInteraction.ts`，不要继续膨胀 `ChatMessage.vue`。
- `MarkdownEnhancements.vue` 负责 Mermaid 全屏 overlay 状态和暴露 `openMermaidFullscreen(...)`，不承接所有消息内操作。
- CSS 负责视觉状态，业务状态通过 wrapper dataset 或组件内 Map 维护。

不建议把 Mermaid 图表立即 Vue 子组件化。当前消息正文通过 `v-html` 插入，且 Markdown HTML 有缓存；直接组件化会扩大 `parseContent`、DOMPurify、缓存和流式更新改造面。

### 4.3 下载 SVG

实现要求：

1. 从当前 wrapper 内查找 `.mermaid-content svg`。
2. 用 `XMLSerializer` 序列化 SVG。
3. 确保根 `<svg>` 带 `xmlns="http://www.w3.org/2000/svg"`。
4. 通过 `Blob([svg], { type: "image/svg+xml;charset=utf-8" })` 创建下载链接。
5. 文件名使用 `mermaid-diagram-{index}.svg` 或基于 placeholder id 的稳定名称。

失败态：

- 未渲染完成时禁用下载按钮或显示下载失败提示。
- 渲染错误时下载按钮不可用。

### 4.4 复制源码

实现要求：

1. 从 `.mermaid-wrapper` 读取 `data-mermaid-code`。
2. `decodeURIComponent` 后写入 `navigator.clipboard.writeText(...)`。
3. 成功后显示短暂成功状态；失败时显示可见失败状态。
4. 不从源码 panel 的 DOM 文本反推源码，避免 HTML escape 影响复制结果。

### 4.5 缩放与拖动

状态建议：

```ts
interface MermaidViewState {
  scale: number;
  x: number;
  y: number;
  dragging: boolean;
}
```

状态存储建议：

- 简单实现可使用 wrapper dataset：`data-mermaid-scale`、`data-mermaid-x`、`data-mermaid-y`。
- 如果需要处理拖动中状态、全屏状态同步、滚轮光标锚点计算，优先在 `ChatMessage.vue` 或新增 `useMermaidInteraction.ts` 中用 `WeakMap<Element, MermaidViewState>` 管理，避免把大量状态写入 DOM 字符串。

边界建议：

- 初始缩放：`1`
- 最小缩放：`0.3`
- 最大缩放：`3`
- 步进：`0.25`
- 重置：`scale = 1; x = 0; y = 0`
- 仅当 `scale > 1` 时允许拖动；缩放回 `<= 1` 时重置平移。
- 若滚轮缩放实现成本可控，则支持 `Ctrl + wheel` 或在 Mermaid viewport 聚焦/悬停时滚轮缩放；必须避免普通页面滚动被意外截获。
- 滚轮缩放的缩放中心必须是鼠标光标所在位置，不得使用图表中心、viewport 中心或其他固定点代替。

移动端应优先使用 pointer events，而不是只支持 mouse events。

### 4.6 全屏查看

全屏查看是消息内工具栏的一个按钮，不是其他操作的前置条件。全屏查看应复用 `MarkdownEnhancements.vue` 的 Teleport overlay 模式，单独维护 Mermaid 全屏状态：

- 当前 SVG HTML
- 当前 Mermaid 源码
- 当前缩放和平移
- 下载、复制、重置、关闭动作

---

## 五、施工批次

### W1：工具栏与基础操作

**目标**: 每个 Mermaid 图表在消息内显示工具栏，支持全屏、复制源码和下载 SVG。
**施工状态**: 已完成（2026-06-07）
**验证证据**:

- `cd ScienceClaw/frontend && npm run test:run -- src/utils/markdownRenderer.spec.ts src/composables/useMermaidRenderer.spec.ts src/components/ChatMessage.spec.ts src/composables/useMarkdownRenderer.spec.ts src/utils/content.spec.ts`
- `cd ScienceClaw/frontend && npm run type-check`

**改动文件**:

- `ScienceClaw/frontend/src/utils/markdownRenderer.ts`
- `ScienceClaw/frontend/src/utils/content.ts`
- `ScienceClaw/frontend/src/assets/chat-message-renderer.css`
- `ScienceClaw/frontend/src/components/ChatMessage.vue`
- `ScienceClaw/frontend/src/components/MarkdownEnhancements.vue`
- `ScienceClaw/frontend/src/locales/zh.ts`
- `ScienceClaw/frontend/src/locales/en.ts`
- `ScienceClaw/frontend/src/utils/markdownRenderer.spec.ts`
- `ScienceClaw/frontend/src/utils/content.spec.ts` 或同等 sanitize 覆盖
- `ScienceClaw/frontend/src/components/ChatMessage.spec.ts`

**验收标准**:

- assistant Mermaid 图表渲染后显示复制源码、下载 SVG 按钮。
- assistant Mermaid 图表渲染后显示全屏按钮；W1 只需保证按钮入口和事件分流存在，全屏 overlay 的完整体验在 W4 完成。
- 复制内容与原始 Mermaid 代码完全一致。
- 下载文件是可打开的 SVG。
- 工具栏在消息宽度较窄时不挤压图表正文；按钮可换行或折叠，但不能重叠。
- 工具栏 HTML 经 DOMPurify sanitize 后仍保留必要按钮、`data-*`、`aria-label` 或 `title` 属性。
- user 消息中的 Mermaid fenced code 仍不渲染。
- `mermaid-source` 仍作为源码代码块展示。

**验证命令**:

```powershell
cd ScienceClaw/frontend
npm run test:run -- src/utils/markdownRenderer.spec.ts src/composables/useMermaidRenderer.spec.ts src/components/ChatMessage.spec.ts
npm run type-check
```

### W2：内嵌缩放与拖动

**目标**: 在消息内对 Mermaid 图表进行放大、缩小、重置和拖动。
**施工状态**: 已完成（2026-06-07）
**验证证据**:

- `cd ScienceClaw/frontend && npm run test:run -- src/components/ChatMessage.spec.ts`
- `cd ScienceClaw/frontend && npm run type-check`

**改动文件**:

- `ScienceClaw/frontend/src/components/ChatMessage.vue`
- 可选新增 `ScienceClaw/frontend/src/composables/useMermaidInteraction.ts`
- `ScienceClaw/frontend/src/components/MarkdownEnhancements.vue`
- `ScienceClaw/frontend/src/assets/chat-message-renderer.css`
- `ScienceClaw/frontend/src/locales/zh.ts`
- `ScienceClaw/frontend/src/locales/en.ts`
- `ScienceClaw/frontend/src/components/ChatMessage.spec.ts`
- 如新增 composable，同步新增对应 spec

**验收标准**:

- 点击放大/缩小按钮能稳定更新当前图表缩放比例。
- 缩放范围默认为 `30%` 到 `300%`；如施工中发现视觉或可用性问题，可在文档中记录理由后微调，但不得无上限缩放。
- 重置按钮恢复 `100%` 和居中状态。
- 放大后可拖动查看图表局部。
- 缩放/拖动不影响其他 Mermaid 图表。
- 图表 viewport 高度自适应内容和容器宽度，但有最大高度上限；复杂图表超出上限时仍可通过滚动或拖动查看。
- 如果实现滚轮缩放，滚轮缩放不会导致页面滚动和图表缩放互相抢占；如果暂不实现，必须在 W2 记录原因并保留后续入口。
- 如果实现滚轮缩放，缩放中心必须跟随当前鼠标光标位置；光标指向的图表区域在缩放前后应尽量保持在同一屏幕位置。

2026-06-07 落地说明：

- 本批已实现消息内放大、缩小、重置和放大后拖动，状态按图表实例隔离。
- 图表 viewport 保持最大高度上限，缩放和平移作用在 `.mermaid-transform-layer`，不改写 Mermaid 生成的 SVG 内部节点。
- 本批暂未实现滚轮缩放。原因是当前消息区本身承载长会话滚动、分页加载和搜索定位，若在没有额外命中区域与锚点计算测试的前提下直接截获滚轮，容易与页面滚动互相抢占；因此先保留消息内按钮缩放与拖动的稳定交互，把滚轮缩放留到后续明确批次再做。

**验证命令**:

```powershell
cd ScienceClaw/frontend
npm run test:run -- src/components/ChatMessage.spec.ts
npm run type-check
```

### W3：源码面板与错误态收口

**目标**: 支持图表内查看源码，并补齐渲染失败、下载失败、复制失败状态。
**施工状态**: 已完成（2026-06-07）
**验证证据**:

- `cd ScienceClaw/frontend && npm run test:run -- src/utils/markdownRenderer.spec.ts src/components/ChatMessage.spec.ts`
- `cd ScienceClaw/frontend && npm run type-check`

**改动文件**:

- `ScienceClaw/frontend/src/utils/markdownRenderer.ts`
- `ScienceClaw/frontend/src/utils/content.ts`
- `ScienceClaw/frontend/src/components/ChatMessage.vue`
- `ScienceClaw/frontend/src/components/MarkdownEnhancements.vue`
- `ScienceClaw/frontend/src/assets/chat-message-renderer.css`
- `ScienceClaw/frontend/src/locales/zh.ts`
- `ScienceClaw/frontend/src/locales/en.ts`
- `ScienceClaw/frontend/src/utils/markdownRenderer.spec.ts`
- `ScienceClaw/frontend/src/components/ChatMessage.spec.ts`
- 可选新增 `ScienceClaw/frontend/src/components/MarkdownEnhancements.spec.ts`

**验收标准**:

- 用户可切换显示 Mermaid 源码。
- 源码面板内容不影响复制源码结果。
- 渲染失败时仍展示现有错误信息和原始源码。
- 下载失败、复制失败有明确可见反馈。

2026-06-07 落地说明：

- 已新增消息内 Mermaid 源码面板切换入口，源码面板内容与复制逻辑解耦，复制仍以 `data-mermaid-code` 为准。
- 已把复制源码和下载 SVG 的成功/失败反馈统一收口为图表内短暂状态提示，不再依赖隐式 DOM 标记。
- 保持 Mermaid 渲染失败时继续显示现有错误提示和原始源码，避免源码查看路径与错误态分叉。

**验证命令**:

```powershell
cd ScienceClaw/frontend
npm run test:run -- src/utils/markdownRenderer.spec.ts src/components/ChatMessage.spec.ts
npm run type-check
```

### W4：全屏查看与浏览器验收

**目标**: 复杂 Mermaid 图表可全屏查看，并完成实际浏览器 smoke。
**施工状态**: 已完成（2026-06-07）
**验证证据**:

- `cd ScienceClaw/frontend && npm run test:run -- src/components/MarkdownEnhancements.spec.ts src/components/ChatMessage.spec.ts`
- `cd ScienceClaw/frontend && npm run type-check`
- `cd ScienceClaw/frontend && npm run build`
- `docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"` 显示 `scienceclaw-frontend-1` 持续运行并暴露 `0.0.0.0:5173->5173/tcp`
- 依照 `CODEX_IN_APP_BROWSER.md` 通过固定 `browser-client.mjs` 路径尝试获取 `iab` 会话，运行时返回 `Browser is not available: iab`，因此本批将内置浏览器 smoke 记录为环境阻塞而非功能失败

**改动文件**:

- `ScienceClaw/frontend/src/components/ChatMessage.vue`
- `ScienceClaw/frontend/src/components/MarkdownEnhancements.vue`
- `ScienceClaw/frontend/src/assets/chat-message-renderer.css`
- `ScienceClaw/frontend/src/locales/zh.ts`
- `ScienceClaw/frontend/src/locales/en.ts`
- `ScienceClaw/frontend/src/components/ChatMessage.spec.ts`
- 新增 `ScienceClaw/frontend/src/components/MarkdownEnhancements.spec.ts` 或将全屏暴露方法覆盖并入现有组件测试

**验收标准**:

- Mermaid 全屏查看可打开、关闭、缩放、拖动、复制源码、下载 SVG。
- `MarkdownEnhancements.vue` 当前没有 spec；W4 若新增全屏 overlay，必须同步新增 `MarkdownEnhancements.spec.ts` 或提供同等组件测试覆盖。
- 消息内工具栏仍是主操作入口；全屏只提供更大查看空间。
- 全屏态不会污染图片 lightbox 和代码块全屏状态。
- 移动端宽度下按钮不重叠，图表不溢出到不可操作区域。
- 使用 Codex App in-app browser 完成至少一次本地聊天消息 Mermaid 图表 smoke；若内置浏览器不可用，按 `CODEX_IN_APP_BROWSER.md` 记录阻塞原因。

2026-06-07 落地说明：

- 已为 Mermaid 全屏 overlay 补齐独立缩放、拖动、复制源码、下载 SVG、关闭和状态提示能力，且状态不与图片 lightbox 或代码块全屏混用。
- `MarkdownEnhancements.vue` 新增组件测试覆盖全屏打开、缩放/拖动、复制/下载和关闭行为；`ChatMessage.spec.ts` 保持消息内入口与 inline 交互覆盖。
- 本机构建与类型检查通过，说明全屏扩展未破坏现有前端打包链路。
- 按仓库文档要求尝试 Codex App in-app browser smoke，但固定 `browser-client.mjs` 路径下 `agent.browsers.get("iab")` 返回 `Browser is not available: iab`。该项阻塞属于本机 in-app browser 运行时可用性，不属于 Mermaid 功能回归。

**验证命令**:

```powershell
cd ScienceClaw/frontend
npm run test:run -- src/components/MarkdownEnhancements.spec.ts src/components/ChatMessage.spec.ts
npm run type-check
npm run build
```

---

## 六、回归矩阵

| 场景 | 必须保持 |
| --- | --- |
| assistant 消息 ` ```mermaid ` | 实时渲染为 SVG 图表 |
| assistant 消息 ` ```mmd ` | 实时渲染为 SVG 图表 |
| assistant 消息 ` ```mermaid-source ` | 显示源码代码块，不实时渲染 |
| user 消息 Mermaid fenced code | 纯文本显示，不实时渲染 |
| Mermaid 渲染失败 | 显示错误态和原始源码 |
| 流式输出中 Mermaid 代码逐步到达 | 最终 DOM 稳定后仍能渲染 |
| 多个相同 Mermaid 图表 | 仍可复用缓存，交互状态相互隔离 |
| 代码块复制和代码块全屏 | 不被 Mermaid 工具栏事件影响 |
| 图片 lightbox | 不被 Mermaid 全屏状态影响 |

---

## 七、风险与处理

| 风险 | 影响 | 处理 |
| --- | --- | --- |
| DOMPurify 过滤新增属性 | 工具栏按钮或源码面板异常 | 只补充必要安全属性，并用单测覆盖 sanitize 后 HTML |
| 直接 transform SVG 内部节点 | Mermaid 布局或连线异常 | 只 transform 外层 `.mermaid-transform-layer` |
| 事件委派误伤代码块/图片 | 复制、全屏、lightbox 互相干扰 | 所有 Mermaid action 必须限定在 `.mermaid-wrapper` 内 |
| i18n 遗漏 | 中英文界面文案不一致 | W1-W4 每批都同步更新 `zh.ts` 和 `en.ts` |
| 全屏状态复用图片 lightbox | 不同功能状态污染 | Mermaid 全屏使用独立状态，不共享 image lightbox refs |
| GitNexus 索引陈旧 | 影响分析不准确 | 施工前确认索引状态；必要时运行 `gitnexus analyze --force --index-only --name ScienceClaw` |

---

## 八、当前状态

本施工单已完成并于 2026-06-07 归档。

后续仅保留一个环境侧残余项：待 `CODEX_IN_APP_BROWSER.md` 所述 `iab` 运行时恢复后，补做一次内置浏览器 smoke 记录。
