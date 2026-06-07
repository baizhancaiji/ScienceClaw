# 施工单：TakeOverView 扩展为会话绑定沙盒接管页

> **编号**: SC-FE-SANDBOX-2026-001
> **创建日期**: 2026-06-07
> **修订日期**: 2026-06-07
> **优先级**: P0
> **影响范围**: `ScienceClaw/frontend/src/components/TakeOverView.vue`、`ScienceClaw/frontend/src/components/ActivityPanel.vue`、`ScienceClaw/frontend/src/components/SandboxPreview.vue`、`ScienceClaw/frontend/src/components/toolViews/BrowserToolView.vue`、`ScienceClaw/frontend/src/components/VNCViewer.vue`
> **状态**: 执行中（W1/W2/W3 已完成，下一批 W4）

---

## 一、施工目标

把现有 `TakeOverView` 从“纯 VNC 全屏接管层”扩展为“会话绑定的整页沙盒接管页”，只处理以下已明确需求：

1. 新开标签页后，在同一页内切换 `Terminal` / `Browser` 两个 tab。
2. 接管页在打开时绑定固定 `sessionId`，后续不随主聊天页切换而漂移。
3. Terminal 历史在聊天页与接管页之间快速同步，且不同会话不能串台。
4. Browser 默认只读，可切换为可操作，并且可切回只读。
5. 旧的 `?vnc=1` 直达入口继续兼容。

本期不新建独立 `SandboxWorkspace` 页面，不改后端接口，不引入新的持久化通道。

---

## 二、当前代码基线

| 模块 | 当前实际情况 | 本期处理 |
| --- | --- | --- |
| `TakeOverView.vue` | 当前只在整页覆盖层里渲染一个 `VNCViewer`，显示条件是 takeover 事件或路由 `sessionId + ?vnc=1` | W2 |
| `VNCViewer.vue` | `rfb.viewOnly` 只在连接初始化时赋值一次，没有运行时同步 | W1 |
| `SandboxPreview.vue` | 已有 `Terminal` / `Browser` tab 交互，但 Browser 用 `iframe` 直接嵌 `getSandboxVncUrl()`，Terminal 只消费父级传入的 `history` | W2 复用交互结构，W3/W4 不把它当历史源 |
| `ActivityPanel.vue` | `sandboxHistory` 真正持有沙盒终端历史，并通过 `scanSandboxTools()` 从 tool items 增量写入 | W3 |
| `BrowserToolView.vue` | “Take Over” 当前只发 `window.dispatchEvent('takeover', { sessionId, active: true })`，仍在当前标签页接管 | W4 |
| `MainLayout.vue` | `TakeOverView` 作为全局覆盖组件挂在主布局底部，天然可覆盖聊天页 | 保持不变 |

---

## 三、方案结论

### 3.1 采用扩展 `TakeOverView`，不新建页面

原因只基于当前仓库代码：

1. `TakeOverView.vue` 已经是整页覆盖容器，并已接入 takeover 事件链路。
2. `TakeOverView.vue` 已经支持带 `sessionId + ?vnc=1` 的直达打开。
3. `SandboxPreview.vue` 已经有可复用的 tab 交互模型，不必另造一套 UI。
4. 真正缺的是“会话绑定 + 历史同步 + viewOnly 实时切换”，不是新的页面壳子。

### 3.2 BroadcastChannel 只负责跨标签实时同步

本期 BroadcastChannel 的定位必须收敛：

1. 只处理“已打开聊天页”和“已打开接管页”之间的历史快同步。
2. 不充当持久化存储。
3. 新接管页打开后必须先请求一次快照，再接收增量。
4. 频道名必须按 `sessionId` 隔离，避免多会话串台。

---

## 四、真实问题落点

### 4.1 `TakeOverView.vue` 目前仍是纯 VNC 层

当前模板主体只有：

```vue
<VNCViewer
  :session-id="sessionId"
  :enabled="shouldShow"
  :view-only="false"
/>
```

结论：当前没有 tab、没有 terminal、没有本地历史状态，也没有只读切换。

### 4.2 `VNCViewer.vue` 只在初始化时读取 `viewOnly`

当前连接初始化逻辑：

```ts
rfb = new RFB(...)
rfb.viewOnly = props.viewOnly ?? false
```

结论：如果父组件后续切换 `viewOnly`，现有连接不会自动更新。

### 4.3 `sandboxHistory` 真正归属在 `ActivityPanel.vue`

当前 `ActivityPanel.vue` 内有：

```ts
const sandboxHistory = ref<SandboxExecEntry[]>([])
```

并由 `scanSandboxTools()` 根据 tool items 增量写入：

```ts
sandboxHistory.value.push({ toolName: fn, command: extractCommand(item.tool!), status: 'calling' })
sandboxHistory.value.push({ toolName: fn, command: extractCommand(item.tool!), output: extractOutput(item.tool!), status: 'called' })
```

结论：BroadcastChannel 的广播端应放在 `ActivityPanel.vue` 这一真实状态持有层，而不是写进 `SandboxPreview.vue` 这种展示组件。

### 4.4 `BrowserToolView.vue` 当前不会新开绑定页

当前 `takeOver()` 逻辑只会：

```ts
window.dispatchEvent(new CustomEvent('takeover', {
  detail: { sessionId: props.sessionId, active: true }
}))
```

结论：这还不满足“每个会话新开独立沙盒标签页，且不复用已有页”的约束。

---

## 五、本期施工范围

### W1：让 `VNCViewer` 的只读状态支持运行时切换

**优先级**: P0
**改动文件**: `ScienceClaw/frontend/src/components/VNCViewer.vue`

#### W1-Step-1：补 `props.viewOnly` watcher

新增 watcher，在 `rfb` 已存在时同步：

```ts
watch(() => props.viewOnly, (next) => {
  if (rfb) {
    rfb.viewOnly = next ?? false;
  }
});
```

#### W1-Step-2：保持现有连接生命周期不变

本批不改：

1. 签名 URL 获取逻辑。
2. `enabled` / `sessionId` 触发的重连逻辑。
3. `scaleViewport` 等现有显示行为。

**验收**:

1. 父组件切换 `viewOnly` 时，不需要重连即可生效。
2. 现有 `sessionId` 切换和卸载断连行为不回归。

**本批结果（2026-06-07）**:

1. 已在 `ScienceClaw/frontend/src/components/VNCViewer.vue` 增加 `props.viewOnly` watcher，现有连接可在不重连的情况下同步 `rfb.viewOnly`。
2. 已新增 `ScienceClaw/frontend/src/components/VNCViewer.spec.ts`，覆盖运行时 `viewOnly` 切换与禁用/卸载断连。
3. 已执行 `npm run test:run -- src/components/VNCViewer.spec.ts` 与 `npm run type-check`，通过。
4. 提交前已用本地 `codegraph impact VNCViewer --depth 2` 与 `codegraph callers VNCViewer` 做影响分析；当前批次影响面收敛在 `VNCViewer` 自身。

---

### W2：把 `TakeOverView` 改造成会话绑定沙盒接管页

**优先级**: P0
**改动文件**: `ScienceClaw/frontend/src/components/TakeOverView.vue`

#### W2-Step-1：保持现有入口，扩展显示语义

`shouldShow` 改为同时兼容：

1. takeover 事件触发。
2. `route.params.sessionId + ?vnc=1`
3. `route.params.sessionId + ?sandbox=1`

要求：

1. 旧链接继续可用。
2. 新语义以 `sandbox=1` 为准。

#### W2-Step-2：引入会话绑定状态

在接管页内部引入固定绑定：

1. 打开时从 takeover detail 或路由参数取到 `boundSessionId`。
2. 页面后续只使用 `boundSessionId`，不再追随“当前聊天页会话”。
3. 退出接管只清本页状态，不反向修改聊天页当前 session。

#### W2-Step-3：模板改成双 tab 布局

复用 `SandboxPreview.vue` 已有交互方向，在 `TakeOverView` 内实现：

1. 顶部 tab header。
2. `Terminal` tab 渲染 `SandboxTerminal`。
3. `Browser` tab 渲染 `VNCViewer`。
4. 底部保留退出按钮。

注意：

1. 不直接复用 `SandboxPreview.vue` 的整个组件树，以免把嵌入式预览布局硬塞到整页接管层。
2. 但 tab 名称、默认 tab 选择、布局切换方式应与现有预览交互保持一致。

#### W2-Step-4：增加 Browser 只读切换控制

在 `TakeOverView` 维护：

```ts
const browserViewOnly = ref(true)
```

要求：

1. 默认只读。
2. UI 上可切为可操作。
3. 可再切回只读。
4. 文案全部走 i18n。

**验收**:

1. `/chat/:sessionId?sandbox=1` 可直接打开。
2. `/chat/:sessionId?vnc=1` 仍可打开。
3. 页面内可切换 `Terminal` / `Browser`。
4. Browser 默认只读，切换后即时生效。

**本批结果（2026-06-07）**:

1. 已将 `ScienceClaw/frontend/src/components/TakeOverView.vue` 重构为会话绑定的整页沙盒接管页，支持 `Terminal` / `Browser` 双 tab。
2. 已兼容 `takeover` 事件入口、`/chat/:sessionId?vnc=1` 旧入口和 `/chat/:sessionId?sandbox=1` 新入口。
3. 已在接管页内增加默认只读的 Browser 控制开关，并将新增文案写入 `ScienceClaw/frontend/src/locales/zh.ts` 与 `ScienceClaw/frontend/src/locales/en.ts`。
4. 已新增 `ScienceClaw/frontend/src/components/TakeOverView.spec.ts`，覆盖 `?sandbox=1`、`?vnc=1` 兼容、浏览器只读切换和事件绑定后不随路由漂移。
5. 提交前已执行 `npm run test:run -- src/components/TakeOverView.spec.ts` 与 `npm run type-check`，通过。
6. 提交前已用本地 `codegraph impact TakeOverView --depth 2`、`codegraph callers TakeOverView` 和 `codegraph query TakeOverView` 做影响分析；当前 W2 直接改动面收敛在 `TakeOverView`，挂载入口仍是 `MainLayout.vue`。

---

### W3：把 Terminal 历史跨标签同步落到真实状态持有层

**优先级**: P0
**改动文件**: `ScienceClaw/frontend/src/components/ActivityPanel.vue`、`ScienceClaw/frontend/src/components/TakeOverView.vue`

#### W3-Step-1：定义频道命名

统一使用：

```ts
`sandbox-history:${sessionId}`
```

约束：

1. 一个 session 一个频道。
2. 不允许全局共用固定频道名。

#### W3-Step-2：在 `ActivityPanel.vue` 建立广播端

广播端职责：

1. 以当前会话 `sessionId` 为维度创建 / 切换频道。
2. `sandboxHistory` 追加新记录后，向对应频道发增量消息。
3. 收到 `request-snapshot` 后，回发当前完整快照。
4. 会话切换或组件卸载时关闭旧频道。

这里必须补足当前 `ActivityPanel` 的会话来源。如果组件现有 props 不含 `sessionId`，本批要把 `sessionId` 从上层实际调用处透传进来；不得在文档里假设它“天然存在”。

#### W3-Step-3：在 `TakeOverView.vue` 建立订阅端

订阅端职责：

1. 使用 `boundSessionId` 构造频道。
2. 页面初始化后先发 `request-snapshot`。
3. 收到 `snapshot` 时覆盖本地 `terminalHistory`。
4. 收到 `incremental` 时按顺序追加。
5. 卸载时关闭频道。

#### W3-Step-4：保持 `SandboxTerminal.vue` 为纯展示组件

本批不让 `SandboxTerminal.vue` 直接感知 BroadcastChannel。

要求：

1. 终端组件继续只接受 `history`。
2. 频道与快照逻辑只放在父级。
3. 不在终端组件里塞 session 绑定、副作用或全局事件。

**验收**:

1. 新开接管页后，先拿到当前完整历史，再收到后续增量。
2. 主聊天页切到别的会话时，已打开接管页仍只接收原会话频道。
3. 两个不同 session 同时开接管页时，历史互不串台。

**本批结果（2026-06-07）**:

1. 已新增 `ScienceClaw/frontend/src/utils/sandboxHistoryChannel.ts`，统一频道名和 `request-snapshot` / `snapshot` / `incremental` 协议结构。
2. 已在 `ScienceClaw/frontend/src/components/ActivityPanel.vue` 增加按 `sessionId` 隔离的 BroadcastChannel 广播端；`sandboxHistory` 新增项会发增量，收到 `request-snapshot` 会回完整快照。
3. 已在 `ScienceClaw/frontend/src/components/TakeOverView.vue` 增加订阅端；绑定会话后会先请求快照，再接收后续增量，且只消费当前绑定 `sessionId` 的消息。
4. 已在 `ScienceClaw/frontend/src/pages/ChatPage.vue` 和 `ScienceClaw/frontend/src/pages/SharePage.vue` 补齐 `sessionId` 透传，避免在 `ActivityPanel` 内假设会话天然存在。
5. 已新增 `ScienceClaw/frontend/src/components/ActivityPanel.spec.ts`，并扩展 `ScienceClaw/frontend/src/components/TakeOverView.spec.ts`，覆盖快照响应、增量广播、订阅端接收与跨会话隔离。
6. 提交前已执行 `npm run test:run -- src/components/ActivityPanel.spec.ts src/components/TakeOverView.spec.ts` 与 `npm run type-check`，通过。
7. 提交前已用本地 `codegraph impact ActivityPanel --depth 2`、`codegraph callers ActivityPanel`、`codegraph impact TakeOverView --depth 2` 做影响分析；W3 影响面收敛在 `ActivityPanel`、`TakeOverView` 以及它们的真实调用层 `ChatPage.vue` / `SharePage.vue`。

---

### W4：把 Browser 接管入口改为新建独立标签页

**优先级**: P0
**改动文件**: `ScienceClaw/frontend/src/components/toolViews/BrowserToolView.vue`

#### W4-Step-1：把“Take Over”改成显式新开标签页

目标行为：

```ts
window.open(`/chat/${sessionId}?sandbox=1`, '_blank', 'noopener')
```

要求：

1. 每次点击都新建标签页。
2. 不查找旧页，不覆盖旧页。
3. 不再把“打开沙盒”依赖为当前页 takeover overlay。

#### W4-Step-2：保留兼容入口

如果仓库里其他位置仍依赖 `window.dispatchEvent('takeover', ...)`，本批不要粗暴删掉全局 takeover 能力。处理方式：

1. BrowserToolView 改走新开页。
2. `TakeOverView` 继续兼容旧事件入口与旧 `?vnc=1` 入口。

**验收**:

1. 会话 A 点击后得到独立标签页 A。
2. 会话 B 再点击后得到独立标签页 B。
3. A 页不会被 B 页替换。

---

### W5：补齐国际化和最小验证

**优先级**: P0
**改动文件**: `ScienceClaw/frontend/src/locales/zh.ts`、`ScienceClaw/frontend/src/locales/en.ts`、相关测试文件

#### W5-Step-1：只补缺失文案

当前已存在：

1. `Terminal`
2. `Browser`
3. `Take Over`
4. `Exit Takeover`
5. `Sandbox`

因此本批只补新增的接管页控制文案，例如：

1. Browser 只读开关。
2. Browser 可操作态文案。
3. 接管页里新增的提示文字或 aria-label。

不得重复造已经存在的 key。

#### W5-Step-2：补最小前端测试

至少覆盖：

1. `TakeOverView` 显示条件兼容 `?vnc=1` 与 `?sandbox=1`。
2. `VNCViewer` 能响应 `viewOnly` 变化。
3. 历史同步消息协议在快照与增量场景下不会重复或漏写。

---

## 六、消息协议

### 6.1 频道名

```ts
sandbox-history:${sessionId}
```

### 6.2 消息类型

```ts
type SandboxHistoryChannelMessage =
  | { type: 'request-snapshot'; sessionId: string }
  | { type: 'snapshot'; sessionId: string; entries: SandboxExecEntry[] }
  | { type: 'incremental'; sessionId: string; entry: SandboxExecEntry }
```

要求：

1. `snapshot` 只传完整数组。
2. `incremental` 只传单条新增项。
3. 接收端必须校验 `sessionId` 与本页绑定值一致后再落地。

---

## 七、非本期范围

以下内容不在本施工单：

1. 新建独立 `SandboxWorkspace` 路由或页面。
2. 重做后端会话持久化或 sandbox 数据回放 API。
3. 改造 `SandboxTerminal.vue` 为可交互终端。
4. 改造 Browser 为 noVNC 之外的新实现。
5. 标签页之间的“查找已有页并复用”逻辑。

---

## 八、风险与回滚边界

| 风险 | 触发点 | 控制方式 |
| --- | --- | --- |
| BroadcastChannel 只在双页同时存活时有效 | 聊天页已关闭，接管页再请求快照 | 文档和实现都明确其为实时同步通道，不伪装成持久化能力 |
| `ActivityPanel.vue` 当前可能拿不到显式 `sessionId` | 广播端需要按会话隔离 | 先补真实调用链透传，再写频道逻辑 |
| 旧接管入口可能仍被其他地方依赖 | BrowserToolView 改成新开页 | 保留 `TakeOverView` 对旧事件和 `?vnc=1` 的兼容 |
| viewOnly 切换可能影响现有直连体验 | `VNCViewer` watcher 写错 | 只增 watcher，不改现有连接初始化与重连逻辑 |

回滚原则：

1. W1 可单独回滚，不影响当前 takeover 入口。
2. W2-W4 若中途失败，至少保住旧 `?vnc=1` 全屏 VNC 行为。
3. 未完成 W3 前，不要把新入口切成唯一入口。

---

## 九、验收命令

前端验证至少执行：

```powershell
cd D:\trae\ScienceClaw\ScienceClaw\frontend
npm run type-check
npm run test:run -- src/components/ActivityPanel.spec.ts src/components/TakeOverView.spec.ts src/components/VNCViewer.spec.ts
```

如果测试文件拆分位置不同，允许替换为实际新增或更新后的对应 spec，但不得省略：

1. 类型检查。
2. `ActivityPanel` 历史同步协议验证。
3. `TakeOverView` 行为验证。
4. `VNCViewer` 只读切换验证。

---

## 十、完成标准

同时满足以下条件才算完工：

1. BrowserToolView 点击后总是新开一个绑定当前 `sessionId` 的接管标签页。
2. 接管页里可切 `Terminal` / `Browser`。
3. Terminal 能先拿快照、再收增量。
4. 两个不同 session 的接管页不会串台。
5. Browser 默认只读，且可切换、可切回。
6. `?sandbox=1` 新入口可用，`?vnc=1` 老入口仍可用。
7. 所有新增用户可见文案完成中英文 i18n。
8. 本施工单与 `docs/current-active-execution-plans-zh.md` 保持一致。
