# 施工单：前端聊天页面性能优化与 Mermaid 渲染可靠性改造

> **编号**: SC-FE-PERF-2026-001
> **创建日期**: 2026-06-06
> **修订日期**: 2026-06-07
> **优先级**: P0
> **影响范围**: `ScienceClaw/frontend/src/`，`ScienceClaw/backend/route/sessions.py`
> **状态**: 已归档（2026-06-07，W1-W5 已完成，W6 转为非必须后续项）

---

## 一、施工目标

本施工单只处理已经由当前代码验证的问题：

| # | 问题 | 当前证据 | 本期处理 |
|---|------|----------|----------|
| 1 | 切换历史会话时 ChatPage 被整棵销毁重建 | `MainLayout.vue:7` 使用 `<router-view :key="routeViewKey" />`，`routeViewKey` 来自 `route.params.sessionId` | W2 |
| 2 | 历史事件逐条 replay 导致 `messages` 多次响应式更新 | `restoreSession()` 对 `session.events` 循环调用 `handleEvent()`，`handleEvent()` 内部会多次 `messages.value.push(...)` | W1 |
| 3 | 消息分组每次依赖完整 `messages` 数组重算 | `useMessageGrouper.ts` 的 `groupedMessages` computed 每次遍历全部消息 | W1 |
| 4 | `GET /sessions/{id}` 原先一次返回全部事件，回归修复后按可见对话消息分页 | 前端 `agent.getSession()` 支持分页参数；后端 `get_session()` 按 user/assistant `message` 计数，tool/step/done 仅随批次附带 | W4 |
| 5 | 消息列表直接渲染全部消息组 | `ChatPage.vue` 对 `groupedMessages` 使用普通 `v-for` | W5 |
| 6 | Mermaid 图表串行渲染、失败后直接展示错误、缓存无上限 | `useMermaidRenderer.ts` 串行 `await renderMermaidWrapper()`；`markdownRenderer.ts` catch 后直接 `renderMermaidError()`；全局 Map 无上限 | W3 |

删除未验证口径：不在文档中承诺固定百分比收益、固定秒级收益、Mermaid 合法复杂语法一定可由重试恢复等没有仓库证据支撑的结论。

---

## 二、现状锚点

### 2.1 ChatPage 销毁重建

**文件**: `ScienceClaw/frontend/src/pages/MainLayout.vue`

```vue
<router-view :key="routeViewKey" />
```

```ts
const routeViewKey = computed(() => {
  const sessionId = route.params.sessionId;
  return Array.isArray(sessionId) ? sessionId.join('/') : (sessionId ?? 'root');
});
```

结论：同一个聊天路由下切换 `sessionId` 会强制销毁并重建 `ChatPage`。

### 2.2 历史事件逐条 replay

**文件**: `ScienceClaw/frontend/src/pages/ChatPage.vue`

```ts
realTime.value = false;
for (const event of session.events) {
  if (isStale()) return;
  handleEvent(event);
}
realTime.value = true;
```

`handleEvent()` 不只是写消息，还会更新 plan、tool 关联、activity timeline、done statistics、错误状态、标题和去重集合。因此本期不得用“只构建 Message[]”的简化 replay 替换它。

### 2.3 消息分组全量重算

**文件**: `ScienceClaw/frontend/src/composables/useMessageGrouper.ts`

```ts
const groupedMessages = computed<GroupedMessage[]>(() => {
  const messages = unref(messagesRef);
  const groups: GroupedMessage[] = [];
  messages.forEach((msg, index) => { ... });
  return groups;
});
```

结论：每次 `messages` 变化都会重新遍历完整数组。历史 replay 期间应减少对 `messages.value` 的写入次数。

### 2.4 后端会话详情分页口径

**前端文件**: `ScienceClaw/frontend/src/api/agent.ts`

```ts
export async function getSession(sessionId: string): Promise<SessionDetail> {
  const response = await apiClient.get<ApiResponse<SessionDetail>>(`/sessions/${sessionId}`);
  return response.data.data;
}
```

**后端文件**: `ScienceClaw/backend/route/sessions.py`

```py
events = getattr(session, "events", []) or []
...
events=[] if locked else events,
```

结论：本期可以先保持默认行为不变，再给 API 增加向后兼容的分页能力。

### 2.5 Mermaid 渲染

**文件**: `ScienceClaw/frontend/src/composables/useMermaidRenderer.ts`

```ts
const GLOBAL_MERMAID_CACHE = new Map<string, string>();
...
for (let i = 0; i < mermaidWrappers.length; i++) {
  if (currentGen !== renderGeneration) return;
  if (!markdownRef.value?.contains(mermaidWrappers[i])) continue;
  await renderMermaidWrapper({ ... });
}
```

**文件**: `ScienceClaw/frontend/src/utils/markdownRenderer.ts`

```ts
try {
  const { svg } = await mermaid.render(makeRenderId(index), code);
  cache.set(code, svg);
  ...
} catch (e) {
  console.error(logPrefix, `Diagram ${index + 1}: render error:`, e);
  if (loadingEl && wrapper.isConnected) {
    loadingEl.innerHTML = renderMermaidError(code);
  }
}
```

结论：缓存存在但无上限；图表按顺序串行渲染；单次失败后不重试。

---

## 三、本期施工范围

### W1：历史 replay 批量提交消息，保留 `handleEvent` 语义

**优先级**: P0
**改动文件**: `ScienceClaw/frontend/src/pages/ChatPage.vue`
**施工状态**: 已完成（2026-06-07）
**验证证据**:

- `cd ScienceClaw/frontend && npm run test:run -- src/pages/ChatPage.spec.ts`
- `cd ScienceClaw/frontend && npm run type-check`

#### W1-Step-1：新增历史 replay 模式

在 `_processedEventIds` 附近新增：

```ts
let _isReplayingHistory = false;
let _replayMessagesBuffer: Message[] | null = null;

const appendMessage = (message: Message) => {
  if (_isReplayingHistory && _replayMessagesBuffer) {
    _replayMessagesBuffer.push(message);
    return;
  }
  messages.value.push(message);
};

const replaceMessageAt = (index: number, message: Message) => {
  if (_isReplayingHistory && _replayMessagesBuffer) {
    _replayMessagesBuffer[index] = message;
    return;
  }
  messages.value[index] = message;
};

const getReplayMessages = () => _replayMessagesBuffer ?? messages.value;
```

#### W1-Step-2：把 `messages.value.push(...)` 改为 `appendMessage(...)`

只改 `ChatPage.vue` 内部写入消息的函数，不改 SSE 入口：

| 函数 | 改法 |
|------|------|
| `handleMessageChunkEvent` | 首 chunk 创建 assistant 消息时使用 `appendMessage(...)`；`_streamingMsgIndex.value = getReplayMessages().length - 1` |
| `handleMessageEvent` | user/assistant 消息和 attachments 消息都使用 `appendMessage(...)` |
| `handleToolEvent` | 推入 tool 消息时使用 `appendMessage(...)` |
| `handleStepEvent` | running step 使用 `appendMessage(...)` |
| `handleErrorEvent` | 错误 assistant 消息使用 `appendMessage(...)` |
| `chat()` | 用户消息和 attachments 的乐观写入使用 `appendMessage(...)` |

#### W1-Step-3：修正读取最后消息/步骤的代码

历史 replay 时，读取消息数组必须读 buffer：

```ts
const getMessagesForMutation = () => getReplayMessages();

const getLastStep = (): StepContent | undefined => {
  return getMessagesForMutation().filter(message => message.type === 'step').pop()?.content as StepContent;
};
```

`appendPendingMessageChunks()`、`handleDoneEvent()` 里访问 `messages.value[...]` 的地方改为访问 `getMessagesForMutation()`。`handleDoneEvent()` 替换最后 assistant 消息时使用 `replaceMessageAt(i, nextMessage)`。

#### W1-Step-4：替换 `restoreSession()` 的 replay 循环

将原循环替换为：

```ts
realTime.value = false;
_isReplayingHistory = true;
_replayMessagesBuffer = [];
try {
  for (const event of session.events) {
    if (isStale()) return;
    handleEvent(event);
  }
  messages.value = _replayMessagesBuffer;
} finally {
  _isReplayingHistory = false;
  _replayMessagesBuffer = null;
  realTime.value = true;
}
```

#### W1-Step-5：测试

新增 `ChatPage` 级别测试或抽出可测 helper。必须覆盖：

- 历史 replay 后 `messages` 内容与旧 `handleEvent` 逐条路径一致。
- `done` 事件仍能把 `statistics` 和 `round_files` 合并到最后一条 assistant 消息。
- `tool`、`plan`、`step` 事件仍能生成 activity snapshot 和工具关联。
- 实时 SSE 路径不进入 `_isReplayingHistory`，仍逐条更新。

---

### W2：复用 ChatPage，取消会话切换时的强制销毁

**优先级**: P0
**改动文件**: `ScienceClaw/frontend/src/pages/MainLayout.vue`，`ScienceClaw/frontend/src/pages/ChatPage.vue`
**施工状态**: 已完成（2026-06-07）
**验证证据**:

- `cd ScienceClaw/frontend && npm run test:run -- src/pages/ChatPage.spec.ts`
- `cd ScienceClaw/frontend && npm run type-check`

#### W2-Step-1：移除 router-view key

`MainLayout.vue`：

```vue
<router-view />
```

同时删除 `computed`、`useRoute` import 和 `routeViewKey`。

#### W2-Step-2：新增完整会话状态重置函数

在 `ChatPage.vue` 中新增：

```ts
const resetSessionRuntimeState = () => {
  flushPendingMessageChunks();
  cancelScheduledChunkFlush();
  if (cancelCurrentChat.value) {
    cancelCurrentChat.value();
    cancelCurrentChat.value = null;
  }

  _processedEventIds.clear();
  _pendingChunkText = '';
  _streamingMsgIndex.value = null;

  inputMessage.value = '';
  isLoading.value = false;
  messages.value = [];
  realTime.value = true;
  follow.value = true;
  title.value = t('New Chat');
  plan.value = undefined;
  lastNoMessageTool.value = undefined;
  lastTool.value = undefined;
  lastEventId.value = undefined;
  attachments.value = [];
  shareMode.value = 'private';
  linkCopied.value = false;
  sharingLoading.value = false;
  thinkingContent.value = '';
  activityItems.value = [];
  activitySnapshots.value = [];
  selectedActivityTurn.value = -1;
  pendingToolCallIds.value = [];

  pendingSkillSave.value = null;
  pendingToolSave.value = null;
  pendingToolReplaces.value = null;
  sessionHasPassword.value = false;
  showVerifyPasswordDialog.value = false;
  showSessionPasswordDialog.value = false;
  lastTurnHadError.value = false;
  messageFlashTokens.value = {};
  closeSessionSearchState();
};
```

不得在会话切换时设置 `_unmounted = false`。`_unmounted` 只表达组件是否真的卸载，由 `onUnmounted()` 管理。

#### W2-Step-3：新增 route param watch

在 `onMounted()` 外层新增：

```ts
watch(
  () => router.currentRoute.value.params.sessionId,
  async (newSessionId, oldSessionId) => {
    if (!oldSessionId || !newSessionId || newSessionId === oldSessionId) return;
    resetSessionRuntimeState();
    sessionId.value = String(newSessionId);
    await restoreSession();
  },
);
```

#### W2-Step-4：锁定旧密码会话

在切换前，如果旧会话有密码，先锁定旧会话：

```ts
const oldSid = String(oldSessionId);
if (oldSid && sessionHasPassword.value) {
  agentApi.lockSessionPassword(oldSid).catch(() => {});
}
```

该逻辑放在 `resetSessionRuntimeState()` 之前。

#### W2-Step-5：测试

必须覆盖：

- 切换 `/chat/a` 到 `/chat/b` 不触发 `ChatPage` unmount。
- 旧会话 SSE cancel 被调用。
- 新会话 title、shareMode、password、activitySnapshots、search 状态不会继承旧值。
- 密码会话切换时会调用 `lockSessionPassword(oldSid)`。

---

### W3：Mermaid 渲染可靠性

**优先级**: P0
**改动文件**: `ScienceClaw/frontend/src/composables/useMermaidRenderer.ts`，`ScienceClaw/frontend/src/utils/markdownRenderer.ts`，对应 spec
**施工状态**: 已完成（2026-06-07）
**验证证据**:

- `cd ScienceClaw/frontend && npm run test:run -- src/utils/markdownRenderer.spec.ts src/composables/useMermaidRenderer.spec.ts`
- `cd ScienceClaw/frontend && npm run type-check`
- `cd ScienceClaw/frontend && npm run test:run`

#### W3-Step-1：增加缓存上限与 LRU 写入

`useMermaidRenderer.ts` 顶层改为：

```ts
const MERMAID_CACHE_MAX_SIZE = 100;
const GLOBAL_MERMAID_CACHE = new Map<string, string>();

const touchMermaidCache = (key: string): string | undefined => {
  const value = GLOBAL_MERMAID_CACHE.get(key);
  if (value === undefined) return undefined;
  GLOBAL_MERMAID_CACHE.delete(key);
  GLOBAL_MERMAID_CACHE.set(key, value);
  return value;
};

const setMermaidCache = (key: string, value: string): void => {
  if (GLOBAL_MERMAID_CACHE.has(key)) {
    GLOBAL_MERMAID_CACHE.delete(key);
  }
  GLOBAL_MERMAID_CACHE.set(key, value);
  while (GLOBAL_MERMAID_CACHE.size > MERMAID_CACHE_MAX_SIZE) {
    const firstKey = GLOBAL_MERMAID_CACHE.keys().next().value;
    if (firstKey === undefined) break;
    GLOBAL_MERMAID_CACHE.delete(firstKey);
  }
};
```

#### W3-Step-2：扩展 `RenderMermaidWrapperOptions`

保持 `makeRenderId?: (index: number) => string` 不变，避免破坏现有调用和测试。

```ts
export interface RenderMermaidWrapperOptions {
  wrapper: Element;
  index: number;
  mermaid: MermaidRenderAdapter;
  cache: Map<string, string>;
  logPrefix?: string;
  makeRenderId?: (index: number) => string;
  getCache?: (key: string) => string | undefined;
  setCache?: (key: string, value: string) => void;
  maxRetries?: number;
  retryDelayMs?: number;
}
```

#### W3-Step-3：实现重试，不改变 ID 签名

`renderMermaidWrapper()` 内部使用：

```ts
const cachedSvg = getCache ? getCache(code) : cache.get(code);
if (cachedSvg !== undefined) {
  if (!wrapper.isConnected) return;
  contentEl.innerHTML = cachedSvg;
  if (loadingEl) loadingEl.style.display = 'none';
  contentEl.style.display = 'block';
  return;
}

let lastError: unknown;
for (let attempt = 0; attempt <= maxRetries; attempt++) {
  try {
    const renderIndex = index * (maxRetries + 1) + attempt;
    const { svg } = await mermaid.render(makeRenderId(renderIndex), code);
    if (setCache) setCache(code, svg);
    else cache.set(code, svg);
    if (!wrapper.isConnected) return;
    contentEl.innerHTML = svg;
    if (loadingEl) loadingEl.style.display = 'none';
    contentEl.style.display = 'block';
    return;
  } catch (e) {
    lastError = e;
    if (attempt < maxRetries) {
      await new Promise(resolve => setTimeout(resolve, retryDelayMs));
      if (!wrapper.isConnected) return;
    }
  }
}
```

所有尝试失败后再调用 `renderMermaidError(code)`。

#### W3-Step-4：渲染调度改为有限并发，默认并发 2

`useMermaidRenderer.ts` 顶层：

```ts
const MERMAID_RENDER_CONCURRENCY = 2;
```

替换 `renderMermaidDiagrams()` 的 for 循环：

```ts
const validWrappers = Array.from(mermaidWrappers)
  .map((wrapper, index) => ({ wrapper, index }))
  .filter(({ wrapper }) => markdownRef.value?.contains(wrapper));

let nextIndex = 0;
const runWorker = async () => {
  while (nextIndex < validWrappers.length) {
    if (currentGen !== renderGeneration) return;
    const item = validWrappers[nextIndex++];
    if (!item.wrapper.isConnected) continue;
    await renderMermaidWrapper({
      wrapper: item.wrapper,
      index: item.index,
      mermaid,
      cache: mermaidCache,
      logPrefix,
      getCache: touchMermaidCache,
      setCache: setMermaidCache,
      maxRetries: 1,
      retryDelayMs: 300,
    });
  }
};

await Promise.allSettled(
  Array.from(
    { length: Math.min(MERMAID_RENDER_CONCURRENCY, validWrappers.length) },
    () => runWorker(),
  ),
);
```

并发上限不得高于 2，除非测试证明 Mermaid 当前版本并发更高仍稳定。

#### W3-Step-5：测试

必须补齐：

- 缓存命中时会刷新 LRU 顺序。
- 超过 100 条时淘汰最旧缓存。
- 第一次 `mermaid.render()` reject、第二次 resolve 时最终显示 SVG。
- 一个 wrapper 渲染失败不会阻止另一个 wrapper 显示 SVG。
- renderGeneration 变化后，不再写入已经过期或脱离 DOM 的 wrapper。

---

### W4：会话事件分页 API

**优先级**: P1
**改动文件**: `ScienceClaw/backend/route/sessions.py`，`ScienceClaw/frontend/src/api/agent.ts`，`ScienceClaw/frontend/src/types/response.ts`，`ScienceClaw/frontend/src/pages/ChatPage.vue`
**施工状态**: 已完成（2026-06-07）
**验证证据**:

- `cd ScienceClaw/frontend && npm run test:run -- src/api/agent.spec.ts src/pages/ChatPage.spec.ts`
- `cd ScienceClaw/frontend && npm run test:run -- src/api/agent.spec.ts src/composables/useSessionSearch.spec.ts src/pages/ChatPage.spec.ts`
- `cd ScienceClaw/frontend && npm run type-check`
- `cd ScienceClaw/frontend && npm run test:run`
- `set PYTHONNOUSERSITE=1; conda run -p D:\conda\envs\scienceclaw pytest ScienceClaw/backend/tests/test_sessions_password.py`

#### W4-Step-1：后端增加可选分页参数

`get_session()` 签名增加：

```py
cursor_event_id: Optional[str] = None,
limit: Optional[int] = None,
direction: str = "latest",
```

规则：

- 不传 `limit` 时保持旧行为，返回全部事件，`has_more=false`。
- `limit` 范围限制为 `1..200`。
- `direction="latest"`：返回最后 `limit` 个事件。
- `direction="before"`：返回 `cursor_event_id` 之前最多 `limit` 个事件。
- `direction="after"`：返回 `cursor_event_id` 之后最多 `limit` 个事件。
- `cursor_event_id` 不存在时返回空数组，`has_more=false`。

新增 helper：

```py
def _slice_session_events(
    events: List[Dict[str, Any]],
    *,
    cursor_event_id: Optional[str],
    limit: Optional[int],
    direction: str,
) -> tuple[List[Dict[str, Any]], bool]:
    if limit is None:
        return events, False
    safe_limit = max(1, min(int(limit), 200))
    if direction == "latest":
        return events[-safe_limit:], len(events) > safe_limit
    index_by_id = {
        ((event.get("data") or {}).get("event_id")): idx
        for idx, event in enumerate(events)
    }
    cursor_index = index_by_id.get(cursor_event_id)
    if cursor_index is None:
        return [], False
    if direction == "before":
        start = max(0, cursor_index - safe_limit)
        return events[start:cursor_index], start > 0
    if direction == "after":
        end = min(len(events), cursor_index + 1 + safe_limit)
        return events[cursor_index + 1:end], end < len(events)
    return events[-safe_limit:], len(events) > safe_limit
```

响应 `GetSessionData` 增加 `has_more: bool = False`。

#### W4-Step-2：前端类型和 API

`GetSessionResponse` 增加：

```ts
has_more?: boolean;
```

`agent.ts`：

```ts
export interface GetSessionOptions {
  cursorEventId?: string;
  limit?: number;
  direction?: 'latest' | 'before' | 'after';
}

export async function getSession(
  sessionId: string,
  options?: GetSessionOptions,
): Promise<SessionDetail> {
  const params: Record<string, string> = {};
  if (options?.cursorEventId) params.cursor_event_id = options.cursorEventId;
  if (options?.limit) params.limit = String(options.limit);
  if (options?.direction) params.direction = options.direction;
  const response = await apiClient.get<ApiResponse<SessionDetail>>(
    `/sessions/${sessionId}`,
    { params },
  );
  return response.data.data;
}
```

#### W4-Step-3：ChatPage 首屏分页

新增状态：

```ts
const hasMoreEvents = ref(false);
const isLoadingMoreEvents = ref(false);
```

`restoreSession()` 先使用：

```ts
session = await agentApi.getSession(restoreTarget, { limit: 20, direction: 'latest' });
hasMoreEvents.value = session.has_more ?? false;
```

#### W4-Step-4：加载更早事件必须保持事件语义

不得把 older events 直接转为 `Message[]` 后 prepend。必须复用 W1 的历史 replay 机制，生成完整状态后再合并消息。

2026-06-07 回归修复已落地：

- 首屏分页从 `limit=100` 改为 `limit=20`。
- 后端分页的 `limit=20` 代表 20 条可见 user/assistant 对话消息；tool/step/done/title 等原始事件不消耗额度，只在选中消息区间内随批次返回，用于前端完整 replay。
- `ChatPage` 维护 `loadedSessionEvents` 和 `firstLoadedEventId`，滚动到顶部后用 `direction='before'` + 最早 `event_id` 拉取更早事件。
- 旧页返回后用 `olderEvents + loadedSessionEvents` 去重合并，再通过历史 replay 机制完整重建消息、plan、tool、done statistics、activity snapshots 等派生状态。
- 加载旧页时先显示顶部“批量加载中”占位；加载前记录触发分页的最早已加载消息作为锚点，旧页请求完成后一次性合并、replay、更新窗口，并按该消息锚点保持视口位置，不使用 `scrollHeight` 差值补偿。
- 批量加载期间保持旧窗口不逐条提交，旧页完成后一次性展示本批可见消息；点击搜索结果的目标事件未加载时，使用同一分页机制后台加载到目标 event 后再跳转。
- 新增 `GET /sessions/{session_id}/search` 后端轻量搜索，只返回 user/assistant message 命中的 `event_id`、事件序号和 snippet；搜索输入不会为了展示结果而加载全部历史消息。

#### W4-Step-5：测试

后端测试：

- 不传 `limit` 时返回全部事件。
- `latest` 返回最后 N 条可见对话消息所在事件区间，工具事件不占 N 的额度。
- `before`/`after` 返回 cursor 前后 N 条可见对话消息所在事件区间并正确设置 `has_more`。
- locked session 仍返回空 events。

前端测试：

- `getSession()` 正确序列化 params。
- `restoreSession()` 能读取 `has_more`，旧响应缺少 `has_more` 时不报错。
- `loadOlderSessionEvents()` 在旧页请求未完成前保持当前窗口稳定，仅显示批量加载占位；请求完成后整批 replay 并一次性展示。
- 会话内搜索由后端返回全会话结果，搜索阶段不加载旧页；点击未加载结果时才分页加载到目标位置。

---

### W5：长列表 DOM 优化

**优先级**: P2
**施工状态**: 已完成（2026-06-07）
**验证证据**:

- `cd ScienceClaw/frontend && npm run test:run -- src/api/agent.spec.ts src/pages/ChatPage.spec.ts`
- `cd ScienceClaw/frontend && npm run type-check`
- `cd ScienceClaw/frontend && npm run test:run`

当前 `ChatPage` 的滚动、搜索和 timeline 依赖 `SimpleBar`：

- `simpleBarRef.value?.scrollToBottom()`
- `simpleBarRef.value?.scrollToElement(target, 160)`
- `simpleBarRef.value.contentWrapperRef`
- `handleScroll()` 里通过真实 DOM 查找 `[data-message-keys*="..."]`

因此不得按旧方案直接把消息区替换为 `@tanstack/vue-virtual`。后续虚拟滚动施工单必须同时改造：

- `SimpleBar` 暴露虚拟滚动需要的 scroll element。
- `scrollToMessageKey()` 支持未挂载消息的索引定位。
- `handleScroll()` 的 active user message 计算不依赖所有 DOM 节点存在。
- Mermaid/markdown 动态高度变化后触发虚拟列表 remeasure。

2026-06-07 落地策略：

- 不引入新依赖，不替换 `SimpleBar`；在现有消息区内按 `groupedMessages` 做窗口化渲染。
- `visibleGroupedEntries` 只渲染当前窗口、前后 overscan 和必要占位，避免长会话把所有消息组一次性挂载进 DOM。
- 顶部和底部 spacer 使用估算高度 + `ResizeObserver` 实测高度；Mermaid/markdown 动态高度变化后会更新缓存高度。
- `scrollToMessageKey()` 支持未挂载消息：先根据 message key 定位 group index，移动渲染窗口，再执行现有 DOM 滚动。
- `handleScroll()` 同时更新可见窗口、timeline active user message，并在顶部阈值内触发 W4 的更早事件分页加载。
- 会话内搜索结果来自后端全会话搜索；点击未加载结果时才分页加载到目标事件，不在搜索阶段全量加载历史。

---

### W6：Mermaid 持久化缓存

**优先级**: P3
**状态**: 本期不施工。

理由：本期先完成内存 LRU 上限和失败重试。IndexedDB 持久化需要额外解决：

- 缓存总容量上限。
- 版本失效策略。
- SVG 安全边界。
- 隐私/多用户隔离。

后续单独施工时再引入 `mermaidCachePersist.ts`。

---

## 四、施工顺序

严格按以下顺序执行：

1. W1：历史 replay 批量提交消息。
2. W2：复用 ChatPage，取消 router-view key。
3. W3：Mermaid 重试、有限并发、LRU 缓存。
4. W4：后端/API 分页与首屏 latest。
5. W5：SimpleBar 内窗口化渲染，保留搜索、时间线和动态高度重测。

W6 本期不施工。

---

## 五、验收标准

| 工作面 | 验收标准 |
|--------|----------|
| W1 | 历史 replay 只在结束时对 `messages.value` 做一次整体赋值；done statistics、round_files、activity snapshot、plan/tool 关联与旧路径一致 |
| W2 | 同一路由下切换 sessionId 不触发 ChatPage unmount；旧 SSE 被取消；旧会话状态不泄漏到新会话 |
| W3 | Mermaid 渲染失败会重试 1 次；单个图失败不阻止其他图显示；缓存最大 100 条并按 LRU 淘汰 |
| W4 | 不带分页参数的旧 API 行为不变；`latest/before/after` helper 测试通过；前端首屏请求使用 `limit=20&direction=latest`，顶部滚动可继续请求 `direction=before` 的更早事件；后端搜索能返回全会话命中但不返回全部历史事件 |
| W5 | 长会话消息区只渲染当前窗口和 overscan；搜索/时间线可定位未挂载消息；Markdown/Mermaid 动态高度可触发重测；点击未加载搜索结果时可分页加载到目标位置再跳转 |

---

## 六、回退方案

| 工作面 | 回退方式 |
|--------|----------|
| W1 | 恢复所有 `appendMessage(...)` 为 `messages.value.push(...)`，删除 replay buffer |
| W2 | 恢复 `MainLayout.vue` 的 `:key="routeViewKey"`，删除 route param watch 和 `resetSessionRuntimeState()` |
| W3 | 删除 retry/LRU/getCache/setCache 参数，恢复串行渲染循环 |
| W4 | 前端恢复无 options 的 `getSession(sessionId)` 调用；后端保留 helper 但不传分页参数时继续返回全部 events |
| W5 | 模板恢复直接遍历 `groupedMessages`；删除 `visibleGroupedEntries`、spacer、group height measurement、顶部分页触发、后端搜索跳转懒加载 |

---

## 七、强制要求

1. 新增用户可见文案必须走 `ScienceClaw/frontend/src/locales/zh.ts` 和 `ScienceClaw/frontend/src/locales/en.ts`。
2. 不得把后端原始异常文本直接展示给用户。
4. 前端验证至少运行：

```bash
cd ScienceClaw/frontend
npm run type-check
npm run test:run
```

5. 后端分页改动至少运行覆盖 sessions route 的测试；主机侧 Python 使用：

```bash
set PYTHONNOUSERSITE=1
conda run -p D:\conda\envs\scienceclaw pytest ScienceClaw/backend/tests/test_sessions_password.py
```
