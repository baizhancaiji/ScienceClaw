# 前端 TypeScript 问题审查与分批修复方案

更新时间：2026-05-30

## 目标

将当前 `ScienceClaw/frontend` 的 `vue-tsc` 失败从 63 条错误收敛到 0，并优先恢复类型检查对真实协议和运行风险的识别能力。

本方案只覆盖已发现问题和直接连带风险，不顺手重构 UI、不调整设计、不引入新依赖。每一批必须是最小可验证增量，单批通过后再进入下一批。

## 当前基线

验证命令：

```powershell
npm --prefix .\ScienceClaw\frontend run type-check
```

当前结果：

- `vue-tsc` 失败。
- 共 63 条 `error TS...`。
- 错误主要来自三类：
  - 共享协议类型落后于后端实际事件。
  - 少数组件存在真实运行风险或半截实现。
  - `noUnusedLocals` / `noUnusedParameters` 暴露大量 unused 噪声。

相关配置：

- `ScienceClaw/frontend/tsconfig.app.json` 开启 `strict: true`。
- `noUnusedLocals: true` 和 `noUnusedParameters: true` 已开启，所以 unused 会阻塞类型检查。

## 分级结论

### P0：协议契约漂移

这些问题会让前端真实处理逻辑和 TypeScript 事件模型不一致。优先修复，因为它们会制造误报并掩盖真实后端协议变化。

涉及模块：

- `ScienceClaw/frontend/src/types/event.ts`
- `ScienceClaw/frontend/src/types/message.ts`
- `ScienceClaw/frontend/src/pages/ChatPage.vue`
- `ScienceClaw/frontend/src/pages/SharePage.vue`
- `ScienceClaw/backend/route/sessions.py`
- `ScienceClaw/backend/deepagent/runner.py`

### P1：真实运行风险

这些问题不仅是类型不通过，也可能导致交互失败、URL 错误或移动端行为失效。

涉及模块：

- `ScienceClaw/frontend/src/components/SessionItem.vue`
- `ScienceClaw/frontend/src/components/VNCViewer.vue`
- `ScienceClaw/frontend/src/api/agent.ts`
- `ScienceClaw/backend/route/sessions.py`
- `ScienceClaw/frontend/src/components/ChatMessage.vue`
- `ScienceClaw/frontend/src/pages/MainLayout.vue`

### P2：类型清理与死代码

这些多数是 unused import、unused local、unused handler。它们不一定影响运行，但会持续阻塞 `vue-tsc`。

涉及模块：

- `ScienceClaw/frontend/src/api/agent.ts`
- `ScienceClaw/frontend/src/components/*.vue`
- `ScienceClaw/frontend/src/components/settings/*.vue`
- `ScienceClaw/frontend/src/composables/*.ts`
- `ScienceClaw/frontend/src/pages/*.vue`
- `ScienceClaw/frontend/src/utils/fileType.ts`

## 详细问题与修复方案

### 1. AgentSSEEvent 未覆盖后端实际事件

现象：

- `ChatPage.vue` 处理 `message_chunk`、`message_chunk_done`、`skill_save_prompt`、`tool_save_prompt` 时触发 TS2367。
- TypeScript 认为这些事件永远不可能出现。

证据：

- `ScienceClaw/frontend/src/types/event.ts` 中 `AgentSSEEvent.event` 只声明：
  - `tool`
  - `step`
  - `message`
  - `error`
  - `done`
  - `title`
  - `wait`
  - `plan`
  - `attachments`
  - `thinking`
- `ScienceClaw/backend/route/sessions.py` 会实际发出：
  - `message_chunk`
  - `message_chunk_done`
  - `skill_save_prompt`
  - `tool_save_prompt`
- `ChatPage.vue` 已按这些事件编写运行逻辑。

接口修复方案：

- 在 `ScienceClaw/frontend/src/types/event.ts` 拆分事件类型，不继续使用一个宽泛对象承载所有事件。
- 增加事件 data 类型：
  - `MessageChunkEventData extends BaseEventData`
    - `content: string`
    - `role: "assistant"`
  - `MessageChunkDoneEventData extends BaseEventData`
  - `SkillSavePromptEventData extends BaseEventData`
    - `skill_name: string`
  - `ToolSavePromptEventData extends BaseEventData`
    - `tool_name: string`
- 将 `AgentSSEEvent` 改为 discriminated union：
  - `{ event: "message"; data: MessageEventData }`
  - `{ event: "tool"; data: ToolEventData }`
  - `{ event: "step"; data: StepEventData }`
  - 其他事件逐项声明。

对应代码修复：

- `ChatPage.vue`
  - 保留现有分支。
  - 去掉不必要的 `as MessageEventData` 等断言，只在确实需要兼容未知历史数据时保留局部断言。
- `SharePage.vue`
  - 使用同一套 `AgentSSEEvent` union。
  - 共享页当前不处理 chunk/save prompt 时，明确保持 ignore 或按历史事件回放需求补齐分支。

验收：

- `ChatPage.vue` 中 `message_chunk`、`message_chunk_done`、`skill_save_prompt`、`tool_save_prompt` 相关 TS2367 消失。
- 不改变 SSE 运行逻辑。

### 2. Step 状态缺少 `in_progress`

现象：

- `ChatPage.vue` 判断 `step.status === "in_progress"` 触发 TS2367。

证据：

- `ScienceClaw/frontend/src/types/event.ts` 的 `StepEventData.status` 只有 `"pending" | "running" | "completed" | "failed"`。
- `ScienceClaw/backend/deepagent/runner.py` 会把 todo 状态映射为 `"in_progress"`。
- `ScienceClaw/backend/route/sessions.py` 会把 runner plan 映射给前端。

接口修复方案：

- 新增共享类型：

```ts
export type StepStatus = "pending" | "running" | "in_progress" | "completed" | "failed";
```

- `StepEventData.status` 使用 `StepStatus`。
- `StepContent.status` 也使用同一个 `StepStatus`，避免 `event.ts` 与 `message.ts` 分叉。

对应代码修复：

- `ScienceClaw/frontend/src/types/message.ts`
  - 从 `event.ts` import type `StepStatus`。
  - `StepContent.status` 改为 `StepStatus`。

验收：

- `ChatPage.vue:952` 附近 `in_progress` 判断不再报错。
- `PlanPanel`、`ActivityPanel` 仍能识别 running 和 in_progress。

### 3. ToolContent 与 ToolEventData 的边界过硬

现象：

- `ChatPage.vue` 将合并后的工具对象写入 `ActivityItem.tool` 时触发 TS2322。
- 报错核心是 `tool_call_id` 等字段可能为 `undefined`，但 `ToolContent` 要求必填。

证据：

- `ToolEventData` 当前字段是必填。
- `ToolContent` 当前字段也是必填。
- `ChatPage.vue` 使用 `smartMerge` 和对象扩散合并 tool event，TypeScript 在 `activityItems.value[existingIdx].tool` 可能为 undefined 的情况下推断出 partial object。

修复方案：

- 不放宽 `ToolContent` 的核心字段为可选，避免把后端坏数据合法化。
- 在 `ChatPage.vue` 增加局部 guard 或 helper：
  - `isToolContent(value): value is ToolContent`
  - 或在 existing branch 中先取 `const existingTool = activityItems.value[existingIdx].tool; if (!existingTool) return/add-new`
- 合并后赋值时保证 `tool` 是完整 `ToolContent`。

验收：

- `ChatPage.vue:808` TS2322 消失。
- 不改变 timeline 合并策略。
- 不让缺少 `tool_call_id` 的 tool silently 成为合法完整工具。

### 4. SessionItem 滑动删除是半截实现

现象：

- 模板绑定 `handleTouchStart`、`handleTouchMove`、`handleTouchEnd`，脚本没有定义。
- 同文件存在 `touchStartX`、`touchStartY`、`isSwiping`、`SWIPE_THRESHOLD`、`DELETE_THRESHOLD`，但未使用。
- 同一 `:class` object 中重复 `'bg-amber-400'` key。

证据：

- `ScienceClaw/frontend/src/components/SessionItem.vue` 模板第 12-14 行绑定 touch handlers。
- 脚本第 168-173 行声明 swipe 状态。
- 文件末尾没有 handler 实现。

修复方案有两种，按最小增量推荐方案 A：

方案 A：补齐 swipe handler。

- `handleTouchStart(event: TouchEvent)`
  - 记录起点。
  - 重置 `isSwiping`。
- `handleTouchMove(event: TouchEvent)`
  - 判断横向位移大于纵向位移。
  - 只允许向左滑动删除：`swipeOffset.value = Math.min(0, deltaX)`。
  - 超过阈值时阻止页面滚动。
- `handleTouchEnd()`
  - 若 `Math.abs(swipeOffset.value) >= DELETE_THRESHOLD`，触发 `handleDeleteClick()`。
  - 否则归零。
- 删除未使用的 `watch` import。
- 修复重复 class key：
  - 将 pinned 且非 running 的颜色改成不同 key，例如 `'bg-amber-400': isRunning || (session.pinned && !isRunning)`。

方案 B：删除 swipe UI。

- 移除 touch handler 绑定、swipe background、swipeOffset transform 和相关状态。
- 风险：删除了明显准备实现的移动端交互，不建议作为第一选择。

验收：

- `SessionItem.vue` 中 TS2339、TS1117、相关 unused swipe state 错误消失。
- 桌面点击、重命名、置顶、删除行为不变。

### 5. VNCViewer 把对象当 URL 字符串

现象：

- `VNCViewer.vue` 中 `wsUrl = await getVNCUrl(props.sessionId)` 报 TS2322。
- `getVNCUrl` 返回 `{ signed_url, expires_in }`，不是字符串。

证据：

- `ScienceClaw/frontend/src/api/agent.ts` 声明 `getVNCUrl(...): Promise<{ signed_url: string; expires_in: number }>`。
- `ScienceClaw/frontend/src/components/VNCViewer.vue` 需要传给 noVNC `new RFB(..., wsUrl, ...)` 的是字符串。
- 当前后端代码中未搜到 `vnc/signed-url` 路由实现，存在前后端接口未对齐风险。

修复方案：

- 前端最小修复：
  - `const signed = await getVNCUrl(props.sessionId);`
  - `wsUrl = signed.signed_url;`
  - 若后端返回相对路径，则用当前 origin 转换为 websocket URL：
    - `http:` -> `ws:`
    - `https:` -> `wss:`
- 接口审查：
  - 在 `ScienceClaw/backend/route/sessions.py` 或相关 router 中确认是否存在 `/sessions/{sessionId}/vnc/signed-url`。
  - 如果不存在，新增后端路由或修正前端 endpoint，不能只改 TS。
- 类型命名：
  - 复用 `SignedUrlResponse`，或新增 `VncSignedUrlResponse`，避免 inline object 到处散落。

验收：

- `VNCViewer.vue:45` TS2322 消失。
- 浏览器进入 `?vnc=1` takeover 时，noVNC 收到字符串 URL。
- 若后端路由缺失，必须在本批记录为 blocker，不把前端类型通过当成完整修复。

### 6. FileInfo.category 与 UI 分组不一致

现象：

- `SessionFileListContent.vue` 判断 `f.category === "system"` 触发 TS2367。

证据：

- `ScienceClaw/frontend/src/api/file.ts` 中 `FileInfo.category?: "result" | "process"`。
- `ScienceClaw/backend/route/sessions.py` 的 `_classify_file` 当前只返回 `"result"` 或 `"process"`。
- `SessionFileListContent.vue` 仍判断 `"system"`。

修复方案：

- 推荐最小增量：删除 `|| f.category === "system"`。
- 不建议把 `FileInfo.category` 扩成 `"system"`，除非后端明确恢复该分类。

验收：

- `SessionFileListContent.vue:129` TS2367 消失。
- 文件分组仍保持 result/process。

### 7. ChatMessage linkText 使用前可能未赋值

现象：

- `ChatMessage.vue` 的 link renderer catch 分支使用 `linkText = linkText || ""`，TS2454。

修复方案：

- 初始化：

```ts
let linkText = "";
```

- 保持后续分支赋值逻辑不变。

验收：

- `ChatMessage.vue:478` TS2454 消失。
- markdown link 渲染行为不变。

### 8. MainLayout router-view key 类型不稳定

现象：

- `MainLayout.vue` 中 `:key="$route.params.sessionId"` 报 `string | string[]` 不可赋给 `PropertyKey`。

修复方案：

- 新增 computed：

```ts
const route = useRoute();
const routeViewKey = computed(() => {
  const sessionId = route.params.sessionId;
  return Array.isArray(sessionId) ? sessionId.join("/") : (sessionId ?? "root");
});
```

- 模板改为 `:key="routeViewKey"`。

验收：

- `MainLayout.vue:7` TS2322 消失。
- 切换 session 仍能触发 router-view 重建。

### 9. Unused imports、locals、parameters

现象：

- `vue-tsc` 当前有大量 TS6133 / TS6196。

修复原则：

- 不通过关闭 `noUnusedLocals` 或 `noUnusedParameters` 解决。
- 每个 unused 逐项判断：
  - 确认模板未使用、脚本未使用后删除。
  - 如果变量代表待恢复功能，不在清理批里重建功能，转成后续任务记录。
  - 事件 handler 如果模板没有绑定，优先删除；如果模板本应绑定，则补绑定要放到对应功能批，不混入清理批。

重点文件：

- `ScienceClaw/frontend/src/api/agent.ts`
  - 删除未用 `SessionStatus`、`SkillItem` import。
- `ScienceClaw/frontend/src/components/ActivityPanel.vue`
  - 删除未用 `StepEventData` import。
  - `handleToolClick` 若模板没有调用，删除或绑定到 tool card 点击事件，二选一需按交互意图确认。
- `ScienceClaw/frontend/src/components/ChatMessage.vue`
  - 清理未用 `ToolUse`、`handleToolClick`、`showRoundFilesPanel`、`stepContent`、`toolContent`、`startTime`。
  - 注意不要删除实际模板仍引用的 computed。
- `ScienceClaw/frontend/src/components/FilePanel.vue`
  - 删除未用 import 和 `t`。
- `ScienceClaw/frontend/src/pages/ChatPage.vue`
  - 删除未用 import 和统计格式化函数。
  - `currentUser` 如果只是触发 auth 初始化，应改成明确调用或注释说明，否则删除。
- `ScienceClaw/frontend/src/pages/SharePage.vue`
  - 删除未用 import。
- settings 组件和 utils 文件按 `vue-tsc` 输出逐个删除。

验收：

- 全量 TS6133 / TS6196 消失。
- 不引入行为变化，除非某项 unused 实际揭示了漏绑定，那一项应从清理批移入功能修复批。

## 最小增量执行批次

### Batch 1：SSE/事件协议类型对齐

目的：

- 先修复 shared event contract，消除多个协议相关误报。

文件：

- `ScienceClaw/frontend/src/types/event.ts`
- `ScienceClaw/frontend/src/types/message.ts`
- `ScienceClaw/frontend/src/pages/ChatPage.vue`
- `ScienceClaw/frontend/src/pages/SharePage.vue`

改动：

- 引入 `StepStatus`。
- 将 `AgentSSEEvent` 改成 discriminated union。
- 增加 chunk/save-prompt 事件 data 类型。
- 按新 union 收窄 `ChatPage.vue` 和 `SharePage.vue` 的分支。
- 修复 `ChatPage.vue` tool timeline merge 的完整性 guard。

验证：

```powershell
npm --prefix .\ScienceClaw\frontend run type-check
npm --prefix .\ScienceClaw\frontend run build
```

通过标准：

- 与 `AgentSSEEvent`、`StepStatus`、`ChatPage.vue:808/952/1014/1016/1026/1033` 相关错误消失。
- 若剩余错误只来自组件行为和 unused，进入 Batch 2。

提交建议：

- 单独提交。
- 提交意图：对齐前端 SSE 类型契约。

### Batch 2：组件真实运行风险修复

目的：

- 修复会影响用户交互或运行路径的组件问题。

文件：

- `ScienceClaw/frontend/src/components/SessionItem.vue`
- `ScienceClaw/frontend/src/components/VNCViewer.vue`
- `ScienceClaw/frontend/src/api/agent.ts`
- `ScienceClaw/frontend/src/components/ChatMessage.vue`
- `ScienceClaw/frontend/src/pages/MainLayout.vue`
- `ScienceClaw/frontend/src/components/SessionFileListContent.vue`

改动：

- `SessionItem.vue` 补齐 swipe handlers，修复重复 class key。
- `VNCViewer.vue` 使用 `signed_url` 字段，并确认 URL scheme。
- `agent.ts` 抽出或复用签名 URL response 类型。
- `ChatMessage.vue` 初始化 `linkText`。
- `MainLayout.vue` 对 route param 做稳定 key。
- `SessionFileListContent.vue` 删除 `system` 分类判断。

验证：

```powershell
npm --prefix .\ScienceClaw\frontend run type-check
npm --prefix .\ScienceClaw\frontend run build
```

浏览器 smoke：

- 打开 `http://localhost:5173/`。
- 切换 session，确认列表点击正常。
- 若有可用 session，进入 `?vnc=1` 检查 takeover 是否至少不再因 URL 类型进入前端异常。

通过标准：

- P1 类错误消失。
- 如发现 VNC 后端路由缺失，记录 blocker，不把 takeover 作为已完整验证。

提交建议：

- 单独提交。
- 提交意图：修复类型检查揭示的前端运行风险。

### Batch 3：文件、活动面板、消息组件 unused 清理

目的：

- 清掉高噪声组件层 unused，恢复 `vue-tsc` 可读性。

文件：

- `ScienceClaw/frontend/src/components/ActivityPanel.vue`
- `ScienceClaw/frontend/src/components/ChatMessage.vue`
- `ScienceClaw/frontend/src/components/FilePanel.vue`
- `ScienceClaw/frontend/src/components/RoundFilesPopover.vue`
- `ScienceClaw/frontend/src/components/SandboxTerminal.vue`
- `ScienceClaw/frontend/src/components/SessionFileListContent.vue`
- `ScienceClaw/frontend/src/components/ToolPanelContent.vue`
- `ScienceClaw/frontend/src/components/icons/RobotAvatar.vue`

改动：

- 删除未用 import、局部函数、参数。
- 对 `handleToolClick` / `onFileClick` 这类 handler，先查模板调用：
  - 如果模板没有绑定，删除。
  - 如果交互应存在，补绑定并把该项移回 Batch 2 类型。

验证：

```powershell
npm --prefix .\ScienceClaw\frontend run type-check
```

通过标准：

- 上述组件不再产生 TS6133 / TS6196。

提交建议：

- 单独提交。
- 提交意图：降低组件层 TypeScript 噪声。

### Batch 4：页面和设置页 unused 清理

目的：

- 完成剩余页面层和 settings 层清理。

文件：

- `ScienceClaw/frontend/src/pages/ChatPage.vue`
- `ScienceClaw/frontend/src/pages/SharePage.vue`
- `ScienceClaw/frontend/src/pages/TaskConfigPage.vue`
- `ScienceClaw/frontend/src/pages/ToolsPage.vue`
- `ScienceClaw/frontend/src/components/settings/ChangePasswordDialog.vue`
- `ScienceClaw/frontend/src/components/settings/LarkBindingSettings.vue`
- `ScienceClaw/frontend/src/components/settings/NotificationSettings.vue`
- `ScienceClaw/frontend/src/components/settings/PersonalizationSettings.vue`
- `ScienceClaw/frontend/src/components/settings/TokenStatistics.vue`
- `ScienceClaw/frontend/src/components/settings/WeChatClawBotSettings.vue`
- `ScienceClaw/frontend/src/composables/useSessionGrouping.ts`
- `ScienceClaw/frontend/src/composables/useTheme.ts`
- `ScienceClaw/frontend/src/utils/fileType.ts`

改动：

- 删除剩余 unused。
- 对 callback 参数 unused 的情况，能删除参数就删除参数；不能删时改成 `_param` 前需确认 TS 配置是否仍报 unused。

验证：

```powershell
npm --prefix .\ScienceClaw\frontend run type-check
npm --prefix .\ScienceClaw\frontend run build
```

通过标准：

- `vue-tsc` 0 error。
- build 通过。

提交建议：

- 单独提交。
- 提交意图：恢复前端 TypeScript 检查清洁基线。

### Batch 5：运行回归 smoke

目的：

- 用浏览器确认类型修复没有破坏主要交互。

验证：

- 首页加载无新的 console error。
- 登录态下打开 chat 页面。
- 发送一条短消息，确认：
  - `message_chunk` 流式显示仍工作。
  - activity panel 能显示 thinking/tool/plan。
  - done 后文件列表或 round files 不报错。
- 打开分享页，确认历史事件回放不报错。
- 打开文件面板，确认 result/process 分组。
- 移动宽度或 touch 模拟下检查 session item swipe，不要求 e2e 覆盖，但至少确认桌面点击未被 swipe handler 阻断。

验证命令：

```powershell
npm --prefix .\ScienceClaw\frontend run type-check
npm --prefix .\ScienceClaw\frontend run build
```

通过标准：

- 类型检查通过。
- 构建通过。
- 浏览器 console 没有新增前端运行错误。

提交建议：

- 如果 Batch 5 只验证不改代码，不提交。
- 如果 smoke 发现并修复小问题，单独提交。

## 不建议的修复方式

- 不建议关闭 `noUnusedLocals` / `noUnusedParameters`。
- 不建议把所有字段都改成 optional 来压掉 TS2322。
- 不建议把 `AgentSSEEvent` 保持成宽泛 union 然后继续到处 `as`。
- 不建议把全部 63 条错误混成一个大提交。
- 不建议在 VNC 问题上只修前端赋值，不确认后端路由是否存在。

## 执行顺序总览

1. Batch 1：事件协议类型。
2. Batch 2：真实运行风险组件。
3. Batch 3：核心组件 unused。
4. Batch 4：页面/settings/composable/utils unused。
5. Batch 5：浏览器 smoke。

每批结束都运行：

```powershell
npm --prefix .\ScienceClaw\frontend run type-check
```

有用户可见运行路径变更的批次额外运行：

```powershell
npm --prefix .\ScienceClaw\frontend run build
```

每批独立提交，提交消息遵循 Lore Commit Protocol。
