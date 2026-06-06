# ScienceClaw 前端技术债治理施工单 v2

**制定日期**：2026-06-01

**执行状态**：已登记，按 `docs/current-active-execution-plans-zh.md` 最小增量推进

**施工范围**：`ScienceClaw/frontend/src/`，以及会影响前端合同的 `ScienceClaw/backend/`、`ScienceClaw/task-service/` 和 Compose/文档配置

**前置依据**：本施工单来自 2026-06-01 对前端技术债报告的源码复核；复核中已确认原报告包含若干错误方案，本文只保留可执行且已校正的治理项。

**登记状态**：已登记到 `docs/current-active-execution-plans-zh.md`；当前执行批次以台账为准。

---

## 1. 施工目标

把前端技术债治理拆成可验证的小批次，优先解决会影响安全边界、回归能力和跨服务合同的问题，再处理组件拆分、样式治理、工程规范和依赖升级。

### 目标结果

- Task Service 的认证与用户隔离边界被明确，并有回归测试覆盖。
- 前端具备最小自动化测试基座，后续重构不只依赖人工 smoke。
- Task Service 前端客户端收敛到一个共享边界，避免 tasks/webhooks 重复实现。
- 核心协议类型从宽泛 `any` 逐步收紧到可维护的 JSON/unknown 边界。
- `ChatPage.vue` 和 `ChatMessage.vue` 按低风险边界渐进拆分。
- 颜色 token、lint/format、依赖升级进入可持续治理状态。

### 明确不做

- 不修改 `ScienceClaw/frontend/src/api/tooluniverse.ts` 的 `return resp.data`。后端 ToolUniverse 路由返回的是裸业务对象，不是 `ApiResponse.data` 包装。
- 不以“文件行数必须低于某个数字”作为组件拆分验收标准。
- 不一次性引入 Pinia 替换所有模块级 composable 状态。
- 不把 Vite、Tailwind、Vue I18n 等 major upgrade 混入基础治理批次。

---

## 2. 施工前置条件

### 2.1 活跃计划闸门

当前台账仍有 `VNC signed URL 接口闭环` 活跃计划，状态为“已补齐，待可用 session 浏览器 smoke”。本施工单进入执行态前，必须先二选一：

1. 完成该计划剩余的 `?vnc=1` 浏览器 smoke，并归档计划。
2. 在 `docs/current-active-execution-plans-zh.md` 中明确把该计划降级或暂停，再登记本文施工单。

### 2.2 仓库与工具约束

- 开发、构建、测试和文本处理默认使用 Git Bash。
- 需要 host-side Python 时使用 `PYTHONNOUSERSITE=1 conda run -p D:/conda/envs/scienceclaw ...`。
- 非必要不在宿主机直接运行后端/前端服务；完整环境优先走 Docker Compose。

### 2.3 基线命令

每个前端相关批次至少执行：

```bash
npm --prefix ScienceClaw/frontend run type-check
npm --prefix ScienceClaw/frontend run build
```

涉及前端测试基座后，追加：

```bash
npm --prefix ScienceClaw/frontend run test:run
```

涉及 task-service 后端合同时，追加对应 Python 测试：

```bash
PYTHONNOUSERSITE=1 conda run -p D:/conda/envs/scienceclaw python -m unittest <test_module>
```

---

## 3. 总体施工顺序

| 批次 | 主题 | 优先级 | 进入条件 | 完成判定 |
| --- | --- | --- | --- | --- |
| 0 | VNC signed URL 活跃计划收口 | 前置闸门 | 当前台账仍有剩余 smoke | 已完成或明确暂停 |
| 1 | Task Service 认证和用户隔离审计 | P0 | 批次 0 已处理 | 认证合同和跨用户测试落地 |
| 2 | 前端自动化测试基座 | P1 | 批次 1 可并行前置设计 | `test:run` 可执行且有首批测试 |
| 3 | Task Service 客户端整理 | P1 | 批次 1 合同明确，批次 2 提供测试基线 | tasks/webhooks 共用客户端 |
| 4 | 核心类型边界收紧 | P1 | 批次 2 完成 | 协议边界减少宽泛 `any` |
| 5 | `ChatPage.vue` 渐进拆分 | P2 | 批次 2 和 4 完成相关前置 | 纯函数/helper 已抽出并测试 |
| 6 | `ChatMessage.vue` 渐进拆分 | P2 | 批次 2 完成 | renderer/composable/style/footer 已拆出并验证 |
| 7 | 颜色 token 分层治理 | P2 | 批次 2 完成 | light/dark 截图或浏览器 smoke 通过 |
| 8 | ESLint 和 Prettier 基线 | P2 | 批次 2 完成 | lint/format check 可运行 |
| 9 | Pinia 适用性评估 | P3 | 共享状态继续扩张或测试暴露问题 | 得出迁移/不迁移结论 |
| 10 | 依赖升级 | P3 | 基础测试和 build 稳定 | patch/minor 与 major migration 分开处理 |

---

## 4. 分批施工明细

### 批次 0：VNC signed URL 活跃计划收口

**目的**：避免新技术债治理打断已登记的活跃计划。

**施工项**

1. 在可用 session 下执行一次 `?vnc=1` 浏览器 smoke。
2. 若 smoke 通过，把 `VNC signed URL 接口闭环` 从活跃台账移入归档记录。
3. 若短期无法 smoke，在台账中明确阻塞原因和暂停状态，再登记本文施工单。

**验收**

- `docs/current-active-execution-plans-zh.md` 不再存在未决但未解释的 VNC 剩余项。

---

### 批次 1：Task Service 认证和用户隔离审计

**目的**：先修正安全和数据隔离边界，再整理前端客户端。

**已知事实**

- `ScienceClaw/frontend/src/api/tasks.ts` 和 `ScienceClaw/frontend/src/api/webhooks.ts` 都会注入 bearer token。
- `ScienceClaw/task-service/app/api/tasks.py` 和 `ScienceClaw/task-service/app/api/webhooks.py` 当前没有按当前用户做认证依赖和列表过滤。
- 任务 schema 有可选 `user_id`，但访问控制未闭环。

**执行记录**

- 2026-06-02 已确认 task-service 不是纯内部服务：前端通过 `/task-service` 代理访问，compose 同时暴露 `scheduler_api` 到宿主 `12002`。
- 认证合同采用主后端 `user_sessions` 中的 bearer session id；task-service 独立查询同一 MongoDB 的 `user_sessions`，不跨服务导入主后端代码。
- 普通用户只能访问 `user_id` 等于当前用户的 task/webhook；管理员 `role=admin` 可查看和管理全部 task/webhook。

**施工项**

1. 明确 task-service 信任模型：浏览器直连、主后端反向代理，或内部服务专用。
2. 为 task-service 增加认证依赖或代理侧认证合同。
3. 明确普通用户和管理员的任务、webhook 可见范围。
4. 为列表、读取、更新、删除接口补跨用户访问测试。
5. 更新相关 API 文档或台账说明。

**验收**

- 未授权请求失败。
- 普通用户只能访问自己的 task/webhook。
- 管理员能力若存在，必须有显式测试覆盖。
- task-service 认证合同写入对应文档，不只停留在代码实现。

**建议验证命令**

```bash
PYTHONNOUSERSITE=1 conda run -p D:/conda/envs/scienceclaw python -m unittest discover -s ScienceClaw/task-service/tests -t ScienceClaw/task-service
npm --prefix ScienceClaw/frontend run type-check
npm --prefix ScienceClaw/frontend run build
```

---

### 批次 2：前端自动化测试基座

**目的**：建立后续重构的最小回归闸门。

**施工项**

1. 安装 `vitest`、`@vue/test-utils`、`happy-dom` 和覆盖率 provider。
2. 增加 `test`、`test:run`、`test:coverage` 脚本。
3. 新增测试配置，避免同时引入 `jsdom` 和 `happy-dom` 两套 DOM 环境。
4. 首批覆盖稳定边界：
   - `ScienceClaw/frontend/src/utils/content.ts`
   - `ScienceClaw/frontend/src/utils/fileType.ts`
   - `ScienceClaw/frontend/src/composables/useSessionSearch.ts`
   - task-service 客户端错误映射，若批次 3 已开始

**验收**

- `npm --prefix ScienceClaw/frontend run test:run` 通过。
- `type-check` 和 `build` 保持通过。
- 测试样例不依赖尚未存在的 Pinia store 或未落地架构。

**执行记录**

- 2026-06-02 已新增 `ScienceClaw/frontend/vitest.config.ts`，测试环境为 `happy-dom`，coverage provider 为 `v8`，未引入 `jsdom`。
- 已新增 `test`、`test:run`、`test:coverage` 脚本；coverage 产物目录 `coverage/` 已加入 `.gitignore`。
- 首批测试覆盖 `ScienceClaw/frontend/src/utils/content.ts`、`ScienceClaw/frontend/src/utils/fileType.ts`、`ScienceClaw/frontend/src/composables/useSessionSearch.ts`，共 12 个测试；task-service 客户端错误映射留到批次 3 共享 client 落地时覆盖。
- 已验证 `npm --prefix ScienceClaw/frontend run test:run`、`test:coverage`、`type-check`、`build` 均通过。

---

### 批次 3：Task Service 客户端整理

**目的**：在认证合同明确后，消除 tasks/webhooks 两套 Axios 逻辑。

**施工项**

1. 新建 `ScienceClaw/frontend/src/api/taskClient.ts`。
2. 统一 `/task-service` base URL、超时、token 注入、错误映射和认证失效行为。
3. 让 `tasks.ts` 和 `webhooks.ts` 复用 `taskClient.ts`。
4. 不改 `tooluniverse.ts` 的响应解包。
5. 增加客户端测试覆盖 token header、base URL、错误映射和认证失效。

**验收**

- tasks/webhooks 不再各自创建重复 Axios 实例。
- 已有 task 和 webhook 页面行为保持不变。
- `tooluniverse.ts` 仍保持 `return resp.data`。

**执行记录**

- 2026-06-02 已新增 `ScienceClaw/frontend/src/api/taskClient.ts`，统一 `/task-service` base URL、30s timeout、bearer token 注入、401 认证失效处理和 task-service 错误映射。
- `ScienceClaw/frontend/src/api/tasks.ts` 与 `ScienceClaw/frontend/src/api/webhooks.ts` 已复用共享 `taskClient`；现有导出函数签名和响应解包保持不变。
- `ScienceClaw/frontend/src/api/tooluniverse.ts` 未修改，仍保持 `return resp.data`。
- 新增 `ScienceClaw/frontend/src/api/taskClient.spec.ts`，覆盖 token header、base URL、错误映射和 401 认证失效行为。

---

### 批次 4：核心类型边界收紧

**目的**：把共享协议边界从宽泛 `any` 收敛到可维护的 JSON/unknown 类型。

**施工项**

1. 定义递归 JSON 类型：

```ts
export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };
```

2. 工具参数使用 `Record<string, JsonValue>`，不要收窄到只支持基础数组。
3. 工具结果先使用 `unknown`，在 adapter 或视图层 narrowing。
4. 为 Axios refresh queue 定义明确 queue item 类型。
5. 按协议边界、工具渲染、页面局部变量三批治理，不做全仓机械替换。

**验收**

- `npm --prefix ScienceClaw/frontend run type-check` 通过。
- 新增或调整的类型有测试或调用点验证。
- 未把合法嵌套对象、数组或 `null` 参数排除在工具调用外。

**执行记录**

- 第一段协议边界增量已完成：新增 `frontend/src/types/json.ts`，定义递归 `JsonValue`/`JsonObject`，并提供 `isJsonObject` narrowing。
- `frontend/src/api/tooluniverse.ts` 已将工具参数收紧为 `Record<string, JsonValue>`，将工具结果和 `return_schema` 收紧为 `unknown`；`return resp.data` 保持不变。
- `ScienceToolDetail.vue` 在视图层处理 `unknown` 工具结果，并用显式输入 getter/setter 避免把完整 `JsonValue` 直接绑定到 DOM 输入。
- 新增 `json.spec.ts` 与 `tooluniverse.spec.ts`，覆盖嵌套对象、数组、`null` 参数，以及 ToolUniverse 裸业务对象响应不额外 unwrap。
- 第二段 Axios refresh queue 增量已完成：`frontend/src/api/client.ts` 已定义 refresh queue item、refresh request marker 和 retryable request config 类型，移除该队列上的宽泛 `any`。
- 新增 `client.spec.ts`，覆盖两个并发 401 请求只触发一次 refresh，并在队列释放后使用新 token 重试。
- 第三段消息协议工具 payload 增量已完成：新增 `frontend/src/types/toolPayload.ts`，定义 `ToolArgs`/`ToolResultContent` 和工具参数、工具结果访问 helper。
- `ToolContent`/`ToolEventData` 已从宽泛 `any` 收紧到共享工具 payload 类型；ActivityPanel、ToolUse、各 tool view 和 ChatPage save prompt 调用点已改为显式 narrowing。
- 新增 `toolPayload.spec.ts`，覆盖对象/string/null 参数、字段读取、预览生成和结果对象 narrowing。

---

### 批次 5：`ChatPage.vue` 渐进拆分

**目的**：降低聊天页维护成本，同时保持 SSE、消息合并和长会话行为稳定。

**施工项**

1. 提取事件归一化和消息合并纯函数。
2. 提取分享逻辑。
3. 保留现有 `useSessionSearch.ts`，只清理页面接线。
4. 提取 Activity snapshot 和 Plan 合并 helper。
5. 自动化测试和长会话 smoke 稳定后，再评估 `useChatSession` 和 `useSSEEventHandler`。

**验收**

- 消息发送、恢复、Plan、Activity、会话搜索和分享行为保持不变。
- 新抽出的纯函数有单元测试。
- 浏览器长会话 smoke 覆盖至少一次 SSE 流式回复。

**执行记录**

- 第一段纯函数/helper 增量已完成：新增 `frontend/src/utils/smartMerge.ts`，将 ChatPage/SharePage 重复的工具事件合并规则抽成纯函数。
- 新增 `smartMerge.spec.ts`，覆盖有效值覆盖、`undefined`/`null`/空对象跳过，以及数组、`0`、`false`、空字符串仍可覆盖。
- 第二段 Plan helper 增量已完成：新增 `frontend/src/utils/planSteps.ts`，将 ChatPage/SharePage 重复的 pending-tool 目标步骤选择规则抽成纯函数。
- 新增 `planSteps.spec.ts`，覆盖 `running > completed > first` 优先级和空步骤列表。
- 第三段 Activity snapshot helper 增量已完成：新增 `frontend/src/utils/activitySnapshot.ts`，将 ChatPage/SharePage 重复的 Activity snapshot 生成规则抽成纯函数。
- 新增 `activitySnapshot.spec.ts`，覆盖 activity list 浅拷贝、plan 深拷贝和空 plan。
- 第四段 pending-tool 关联 helper 增量已完成：新增 `frontend/src/utils/pendingTools.ts`，将 ChatPage/SharePage 重复的 pending-tool 关联规则抽成明确输入/输出的局部 mutation helper。
- 新增 `pendingTools.spec.ts`，覆盖 pending tool 关联、重复 tool 跳过、未解析 pending id 清空，以及缺失 `tools` 列表初始化。
- 以上增量不改变 SSE 连接、消息 append、Plan 工具关联或 UI 分支。

---

### 批次 6：`ChatMessage.vue` 渐进拆分

**目的**：把 Markdown、数学公式、Mermaid、代码块复制等 renderer 复杂度移出单文件组件。

**施工项**

1. 提取 `useMarkdownRenderer.ts`。
2. 提取 `useMathRenderer.ts`。
3. 提取 `useMermaidRenderer.ts`。
4. 提取 `MessageFooter.vue`。
5. 将 800 行以上样式拆成独立样式文件或明确分区。

**验收**

- Markdown、KaTeX、Mermaid、代码块复制、附件显示行为保持不变。
- Mermaid 仍保持动态加载，不引入首屏无谓加载。
- `ChatMessage` chunk 变化被记录，但不把 chunk 大小作为唯一验收指标。

**执行记录**

- 第一段 parse-content helper 增量已完成：新增 `frontend/src/utils/chatMessageContent.ts`，将 `ChatMessage.vue` 的 rendered HTML/special viewer/suggested questions 拆分规则抽成 helper。
- 新增 `chatMessageContent.spec.ts`，覆盖 HTML 合并、suggested questions 提取、special viewer source 转换和空内容回退。
- 第二段 Markdown link renderer helper 增量已完成：新增 `frontend/src/utils/markdownRenderer.ts`，将 Markdown link renderer 规则抽成纯 helper。
- 新增 `markdownRenderer.spec.ts`，覆盖 marked v15 token、旧 API 字符串参数、外链 target 和缺失 href 回退。
- 第三段 code block renderer helper 增量已完成：扩展 `frontend/src/utils/markdownRenderer.ts`，将代码块 token 归一化、复制 payload 转义和行号/折叠布局规则抽成纯 helper。
- 扩展 `markdownRenderer.spec.ts`，覆盖 marked code token、旧 API 字符串参数、复制属性转义和折叠阈值。
- 第四段 code block HTML renderer helper 增量已完成：扩展 `frontend/src/utils/markdownRenderer.ts`，将普通 code block HTML 生成规则抽成 `renderHighlightedCodeBlock` helper。
- 扩展 `markdownRenderer.spec.ts`，覆盖代码块 controls/line metadata/copy payload 和长代码块折叠提示。
- 第五段 Mermaid renderer helper 增量已完成：扩展 `frontend/src/utils/markdownRenderer.ts`，将 Mermaid loading placeholder 和 render error HTML 抽成纯 helper。
- 扩展 `markdownRenderer.spec.ts`，覆盖 Mermaid wrapper/code encoding/loading text/content id，以及错误提示和 raw code 展示。
- 第六段 math renderer helper 增量已完成：扩展 `frontend/src/utils/markdownRenderer.ts`，将 KaTeX render、公式预处理和公式占位符后处理抽成纯 helper，并继续由 `ChatMessage.vue` 提供原有占位符计数器。
- 扩展 `markdownRenderer.spec.ts`，覆盖 KaTeX display render、块级/行内公式占位符、非公式文本跳过和公式 HTML 回填。
- 第七段 Mermaid render execution helper 增量已完成：扩展 `frontend/src/utils/markdownRenderer.ts`，将单个 Mermaid wrapper 的 code decode、cache 命中、`mermaid.render`、loading/content DOM 更新和错误展示抽成 `renderMermaidWrapper` helper。
- 扩展 `markdownRenderer.spec.ts`，覆盖 Mermaid SVG 渲染与缓存写入、缓存命中跳过 render，以及 render 失败时复用既有错误 HTML。
- 第八段 Mermaid loader/initialization helper 增量已完成：扩展 `frontend/src/utils/markdownRenderer.ts`，将 Mermaid 动态 import 单例 promise、module 缓存、初始化状态和初始化配置抽成 `createMermaidLoader` helper。
- 扩展 `markdownRenderer.spec.ts`，覆盖动态 import 只执行一次、初始化只执行一次、初始化配置保持不变，以及初始化失败仍返回 mermaid module 的既有行为。
- 第九段 `MessageFooter.vue` 增量已完成：新增 `frontend/src/components/MessageFooter.vue`，将反馈按钮、复制、PDF 转换、文件入口和统计信息展示从 `ChatMessage.vue` 提取为子组件，父组件继续持有交互行为和状态。
- 新增 `MessageFooter.spec.ts`，覆盖反馈/复制/文件数/统计信息渲染，以及 like/dislike、copy、convertToPdf、showFiles 事件透传。
- 第十段 footer style 增量已完成：将 `MessageFooter.vue` 所需的 `.msg-footer-*`、`.msg-action-*`、`.msg-stat-*` 和对应移动端规则从 `ChatMessage.vue` 大样式块迁入 `MessageFooter.vue`。
- 第十一段 renderer style 增量已完成：新增 `frontend/src/assets/chat-message-renderer.css`，将 `.markdown-content` 下的 Markdown、code block、KaTeX、Mermaid 和移动端表格样式从 `ChatMessage.vue` 外置到独立样式文件；`ChatMessage.vue` 保留组件入场动画和搜索命中动画。
- 2026-06-02 补施工增量已完成：新增 `frontend/src/composables/useMathRenderer.ts`，将公式预处理和公式占位符回填接线从 `ChatMessage.vue` 移出。
- 新增 `frontend/src/composables/useMarkdownRenderer.ts`，将 marked renderer、highlight.js 语言注册、代码块 HTML、Mermaid placeholder、link renderer、Markdown format、KaTeX 预/后处理和 DOMPurify sanitize 接线集中为 composable。
- 新增 `frontend/src/composables/useMermaidRenderer.ts`，将 Mermaid 缓存、占位符 id、动态 import/初始化、`.mermaid-wrapper` DOM 扫描、异步 SVG 渲染，以及 `watch`/`onMounted` 触发从 `ChatMessage.vue` 移出。
- `ChatMessage.vue` 现在只通过 `useMermaidRenderer` 获取 `createMermaidPlaceholderId`，再传给 `useMarkdownRenderer`；组件内不再直接持有 Mermaid 缓存、计数器、marked renderer、highlight.js 语言注册或 Mermaid DOM 扫描逻辑。
- 新增 `useMathRenderer.spec.ts`、`useMarkdownRenderer.spec.ts`、`useMermaidRenderer.spec.ts`，覆盖公式 composable 边界、Markdown 渲染接线、Mermaid placeholder id、Mermaid 动态加载/渲染和无 wrapper 跳过加载。

**复核与补齐记录**

- 2026-06-02 复核曾确认原执行记录错位，且施工项 1-3 的 composable 未落地；本次补施工已补齐 `useMarkdownRenderer.ts`、`useMathRenderer.ts`、`useMermaidRenderer.ts`。
- 验证已通过：`npm run test:run -- useMarkdownRenderer.spec.ts useMathRenderer.spec.ts useMermaidRenderer.spec.ts markdownRenderer.spec.ts chatMessageContent.spec.ts MessageFooter.spec.ts`、`npm run type-check`、`npm run test:run`、`npm run build`。全量前端测试为 19 个测试文件、77 个用例通过；build 输出中 `mermaid.core` 仍为独立 chunk，Mermaid 动态加载要求保持成立。

---

### 批次 7：颜色 token 分层治理

**目的**：把组件内硬编码颜色迁移到有语义的 token 层，而不是简单搬家。

**施工项**

1. 在 `ScienceClaw/frontend/src/assets/theme.css` 明确 token 层级：
   - `brand`
   - `surface`
   - `border`
   - `text`
   - `semantic-state`
   - `code`
   - `diagram`
2. 首批迁移 `ChatMessage.vue` 和 `MarkdownEnhancements.vue`。
3. Tailwind 配置只映射稳定 token。
4. 实验性渐变保留局部命名，避免污染全局语义层。

**验收**

- light/dark 模式下关键聊天消息、代码块、Mermaid、附件显示正常。
- 颜色迁移不改变交互语义。
- 截图或浏览器 smoke 记录写入批次说明。

**执行记录**

- 第一段 code/diagram/semantic-state token 增量已完成：`frontend/src/assets/theme.css` 新增 chat renderer 专用的 code、diagram、semantic-state token 层。
- `frontend/src/assets/chat-message-renderer.css` 已将稳定的 code block、inline code、Mermaid、KaTeX error 和删除线错误态颜色迁移到语义 token；标题、链接、列表、引用、表格等品牌/实验性渐变仍保留局部硬编码，避免一次性扩大视觉回归面。
- 第二段 code fullscreen token 增量已完成：`MarkdownEnhancements.vue` 的 code fullscreen overlay/header/border/control/success/error 颜色已复用 chat renderer code 与 semantic-state token。
- `npm --prefix ScienceClaw/frontend run type-check` 和 `npm --prefix ScienceClaw/frontend run build` 已通过；build 仅保留既有 Browserslist 数据陈旧提示。
- 由于 Codex App in-app browser 当前返回 `iab` unavailable，Playwright 临时包在 PowerShell/npx 下无法解析 `playwright` 模块，本段使用 Node CSS token smoke 替代浏览器截图：light/dark 均检查 11 个 code fullscreen 所需 token，组件迁移目标无缺失 token 引用且无旧硬编码残留。
- 第三段 selection menu token 增量已完成：`MarkdownEnhancements.vue` 的 selection menu surface、border、text 和 hover 色值已迁移到 light/dark token，暗色样式不再需要组件局部 override。
- 第四段 surface/border token 增量已完成：`chat-message-renderer.css` 的表格单元格、斑马纹、kbd surface/border，以及 code block subtle border 已迁移到 light/dark token，组件局部 dark override 已移除。
- 收尾审计已完成：`chat-message-renderer.css` 的 code block 控件背景、hover、展开提示和 header 分隔线已迁移到 chat code token；剩余硬编码色值限定为标题/链接/列表/引用/分隔线等品牌渐变、KaTeX 轻量装饰、lightbox overlay 和阴影类局部视觉效果，按“实验性渐变保留局部命名”原则不进入全局语义层。
- 批次 7 全量验证已通过：`PYTHONNOUSERSITE=1 conda run -p D:/conda/envs/scienceclaw python -m unittest discover -s ScienceClaw/task-service/tests -t ScienceClaw/task-service` 运行 7 个用例通过；`npm --prefix ScienceClaw/frontend run test:run` 运行 15 个测试文件/65 个用例通过；`npm --prefix ScienceClaw/frontend run test:coverage` 通过且总体 statements 80.56%；`npm --prefix ScienceClaw/frontend run type-check` 和 `npm --prefix ScienceClaw/frontend run build` 通过，build/test 仅保留既有 Browserslist 数据陈旧提示。
- 本段不改变 Markdown、Mermaid、KaTeX、代码块复制、消息正文或附件分支；批次 7 已关闭，下一批进入批次 8 ESLint/Prettier baseline。

---

### 批次 8：ESLint 和 Prettier 基线

**目的**：建立工程规范闸门，先检查新增代码，不强求一次清零历史问题。

**施工项**

1. 把 `prettier` 和 `@types/dompurify` 从 runtime dependencies 移到 devDependencies。
2. 选择 ESLint 主版本后决定使用 flat config 还是 legacy config。
3. 增加 `lint` 和 `format:check`。
4. 暂不引入 Husky 和 lint-staged。
5. 单独评估 `lint:fix` 的机械改动范围。

**验收**

- `npm --prefix ScienceClaw/frontend run lint` 可执行。
- `npm --prefix ScienceClaw/frontend run format:check` 可执行。
- 新增代码不扩大 lint 问题。

**执行记录**

- 已选择 ESLint 9 flat config：新增 `frontend/eslint.config.js`，组合 `@eslint/js`、`typescript-eslint`、`eslint-plugin-vue` 和 `eslint-config-prettier`，忽略 `dist`、`coverage`、`node_modules`。
- `prettier` 和 `@types/dompurify` 已从 runtime dependencies 移到 devDependencies；新增 devDependencies 包括 ESLint 9、Vue/TypeScript flat config 所需插件、`globals` 和 `eslint-config-prettier`。
- 已新增 `lint` 与 `format:check` 脚本；当前 `format:check` 只覆盖本批新增/变更入口 `eslint.config.js` 与 `package.json`，避免对 244 个既有未格式化文件生成机械 diff。
- 暂不引入 Husky 和 lint-staged；暂不新增 `lint:fix` 脚本。
- `npm --prefix ScienceClaw/frontend run lint` 已可执行并通过，当前 baseline 为 0 error/42 warning；`npm --prefix ScienceClaw/frontend run format:check` 已可执行并通过。
- `lint:fix` 机械范围已用 dry-run 评估：在 `ScienceClaw/frontend` 目录运行 `npm exec eslint -- "src/**/*.{ts,vue}" "*.config.ts" --fix-dry-run` 退出 0，dry-run 后仍剩 26 个 warning；本批不执行写入式 fix。

---

### 批次 9：Pinia 适用性评估

**目的**：判断是否需要状态库，而不是把状态库当作默认答案。

**施工项**

1. 列出跨组件共享状态和当前 owner：
   - theme
   - left/right panel
   - file panel
   - session file list
   - settings dialog
   - session notifications
2. 为事件订阅、timer、连接和 localStorage side effect 增加清理测试。
3. 只在需要 DevTools、复杂派生状态、跨页面一致性或 SSR 隔离时迁移 Pinia。
4. 若迁移，先选择 Auth 或 Panel 单一 store 做试点。

**验收**

- 输出迁移决策：暂不迁移、单 store 试点，或分阶段迁移。
- 决策有代码事实和测试结果支撑。

**执行记录**

- 跨组件共享状态 owner 已梳理：
  - theme：`frontend/src/composables/useTheme.ts`，`App.vue` 初始化，负责 `scienceclaw-theme` localStorage 与 `<html>.dark`。
  - left panel：`frontend/src/composables/useLeftPanel.ts`，由 `LeftPanel.vue`、`SessionItem.vue` 等调用，负责 `manus-left-panel-state` localStorage。
  - right panel：`frontend/src/composables/useRightPanel.ts` 当前无调用点，保留为 dormant composable，不构成 store 迁移触发点。
  - file panel：`frontend/src/composables/useFilePanel.ts`，由 Chat/Share/FilePanel/附件相关组件调用，通过 event bus 广播 panel 展示事件。
  - session file list：`frontend/src/composables/useSessionFileList.ts`，由 Chat/Share/SessionFileList/附件入口共享 `visible/shared`。
  - settings dialog：`frontend/src/composables/useSettingsDialog.ts`，由 Chat/Home/LeftPanel/UserMenu/Tasks/SettingsDialog 等共享打开状态与默认 tab。
- 新增 `frontend/src/composables/useSharedStateLifecycle.spec.ts`，覆盖 theme/left panel localStorage side effect、`useRelativeTime` interval 清理、`useSessionNotifications` active subscription cancel 和 reconnect timer 清理。
- `npm --prefix ScienceClaw/frontend run test:run -- src/composables/useSharedStateLifecycle.spec.ts` 运行 5 个用例通过；`npm --prefix ScienceClaw/frontend run test:run` 运行 16 个测试文件/70 个用例通过；`npm --prefix ScienceClaw/frontend run lint` 保持 0 error/42 warning baseline；`npm --prefix ScienceClaw/frontend run type-check` 通过。
- 迁移决策：暂不迁移 Pinia。当前共享状态均为小型 module-scope composable，缺少 DevTools 调试、复杂派生状态、跨页面一致性约束或 SSR 隔离等触发条件；若后续需要迁移，优先选择 Auth 或 Panel 单一 store 做试点。

---

### 批次 10：依赖升级

**目的**：把依赖升级拆成低风险 patch/minor 和独立 major migration。

**施工项**

1. 先更新 Browserslist 数据。
2. 单独处理安全修复和 patch/minor 更新。
3. 为以下 major migration 分别建评估单：
   - Vite
   - Tailwind
   - Vue Router
   - Vue I18n
4. 每次升级都记录 `package.json` 声明版本和 `package-lock.json` 实际安装版本。

**验收**

- `type-check` 和 `build` 通过。
- 涉及样式或组件库时，完成 light/dark 浏览器 smoke。
- major migration 不与功能重构同批提交。

**执行记录**

- Browserslist 数据已先行更新：在 `ScienceClaw/frontend` 运行 `npx update-browserslist-db@latest`，`caniuse-lite` 从 `1.0.30001713` 更新到 `1.0.30001793`，输出 `No target browser changes`。
- npm audit 的默认 npmmirror registry endpoint 当前不可用；改用官方 registry 运行 `npm --prefix ScienceClaw/frontend audit --json --registry=https://registry.npmjs.org` 完成审计。
- 已完成当前主版本内的安全/patch/minor 升级，并同步 `package.json` 声明版本与 `package-lock.json` 实装版本：
  - `axios`：`^1.8.4` -> `^1.16.1`，实装 `1.16.1`。
  - `dompurify`：`^3.2.5` -> `^3.4.7`，实装 `3.4.7`。
  - `mermaid`：`^11.13.0` -> `^11.15.0`，实装 `11.15.0`。
  - `postcss`：`^8.4.24` -> `^8.5.15`，实装 `8.5.15`。
  - `vite`：`^4.3.9` -> `^4.5.14`，实装 `4.5.14`；剩余 Vite/esbuild audit 项需 Vite major migration，不在本批混合处理。
  - `vue-i18n`：`^9.14.4` -> `^9.14.5`，实装 `9.14.5`；安装时提示 v9/v10 已进入维护弃用，应单独评估 v11 migration。
  - `@types/node`：`^24.0.13` -> `^24.12.4`，实装 `24.12.4`。
  - `@vue/test-utils`：`^2.4.9` -> `^2.4.10`，实装 `2.4.10`。
- 升级后官方 audit 剩余 13 项：5 moderate、6 high、2 critical。直接 direct major 候选包括 `vitest`/`@vitest/coverage-v8` -> `4.1.8`，`vite` -> `8.0.16`；其余 `brace-expansion`、`defu`、`glob`、`lodash-es`、`minimatch`、`picomatch`、`rollup`、`uuid`、`yaml` 多为 Tailwind/Reka/Vite/Vitest 传递链，应拆到独立 migration 或 lockfile override 评估。
- 本批未执行样式/组件库 major 升级，且本轮用户要求“不要浏览器验证”；浏览器 smoke 不作为本次提交证据。
- 验证已通过：`npm --prefix ScienceClaw/frontend run type-check`、`npm --prefix ScienceClaw/frontend run build`、`npm --prefix ScienceClaw/frontend run test:run`、`npm --prefix ScienceClaw/frontend run lint`、`npm --prefix ScienceClaw/frontend run format:check`。

---

## 5. 风险与回滚

| 风险 | 触发批次 | 处理方式 |
| --- | --- | --- |
| task-service 认证模型不清导致前端客户端返工 | 批次 1、3 | 先定合同再改客户端 |
| 测试基座引入过多配置噪声 | 批次 2 | 只选 `happy-dom`，首批覆盖纯函数和稳定 composable |
| 组件拆分改变 SSE 或 renderer 行为 | 批次 5、6 | 先抽纯函数和 renderer helper；每批做浏览器 smoke |
| 颜色 token 迁移造成暗色模式回归 | 批次 7 | 每批只迁移少量文件，并做 light/dark 对比 |
| lint/format 产生大规模无关 diff | 批次 8 | 先 check，不默认 fix |
| major upgrade 和重构互相干扰 | 批次 10 | major migration 独立施工单处理 |

回滚原则：每个批次独立提交；若验收失败，优先回滚该批次最后一次提交，不回滚其他已验证批次。

---

## 6. 交付物

每个批次完成时必须产出：

1. 代码或文档改动。
2. 验收命令和结果。
4. 若涉及 UI，附浏览器 smoke 说明或截图路径。
5. 若发现新问题，登记到 `docs/current-active-execution-plans-zh.md` 或对应归档计划的残余事项，不直接塞进当前批次。

---

## 7. 当前状态

本文已从“复核评估报告”改写为“标准施工单”，并已登记到 `docs/current-active-execution-plans-zh.md`。VNC signed URL 剩余 smoke 因 Codex App 内置浏览器控制面超时保留为暂停手工项；技术债治理已进入执行态。当前已完成批次 1、批次 2、批次 3、批次 4「核心类型边界收紧」、批次 5 的四段纯函数/helper 提取，以及批次 6 的 `ChatMessage.vue` parse-content、Markdown link renderer、code block renderer、code block HTML renderer、Mermaid renderer helper、math renderer helper、Mermaid render execution helper、Mermaid loader/initialization helper、`MessageFooter.vue` 提取、footer style 收口、renderer style 外置和 `useMarkdownRenderer.ts`、`useMathRenderer.ts`、`useMermaidRenderer.ts` 补施工；批次 7 已完成 chat renderer、`MarkdownEnhancements.vue` code fullscreen/selection menu、`chat-message-renderer.css` 表格/kbd surface-border 和 code block 控件色值的稳定 token 迁移，且全量验证已通过；批次 8 已建立 ESLint/Prettier baseline；批次 9 已完成 Pinia 适用性评估且决策为暂不迁移；批次 10 已完成 Browserslist 更新、当前主版本内依赖安全/patch/minor 升级和 major migration 拆分记录。本施工单登记的批次 1-10 已完成；剩余依赖债务按独立 major migration 计划处理。
