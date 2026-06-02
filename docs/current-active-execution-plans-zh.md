# 当前活跃执行计划台账

更新时间：2026-06-01

本文档是 ScienceClaw 当前执行计划的唯一滚动入口。新任务进入执行态前先登记到这里；计划完成后从本台账移除，并移动到 `docs/archive/plans/`。

## 使用规则

- `AGENTS.md` 只引用本台账，不直接引用单个阶段计划，避免旧计划继续影响执行。
- 活跃计划必须写清楚当前状态、权威文档、下一批最小增量和验收命令。
- 已完成、废弃或被新计划取代的计划文档必须移入 `docs/archive/plans/`，并在本台账的“归档记录”中保留索引。
- 不把部署教程、长期设计说明或普通参考资料放入归档计划目录，除非它们曾作为执行计划使用。

## 活跃计划

### VNC signed URL 接口闭环

- 状态：已补齐，暂停为待 Codex App 内置浏览器 smoke；不再阻塞技术债治理登记。
- 来源：前端 TypeScript 修复中发现 `VNCViewer.vue` 已消费 `getVNCUrl()` 返回的 `signed_url`，但当前审查未找到后端 `/sessions/{sessionId}/vnc/signed-url` 路由实现。
- 关联归档计划：`docs/archive/plans/frontend-typescript-remediation-plan-zh.md`
- 已完成最小增量：
  - 确认后端此前不存在 `/sessions/{sessionId}/vnc/signed-url` 路由；sandbox 实际 noVNC WebSocket 入口为 `/websockify`。
  - 在 `ScienceClaw/backend/route/sessions.py` 新增 session 属主校验后的 `POST /sessions/{session_id}/vnc/signed-url`，返回 `{ signed_url, expires_in }`。
  - 新增 `GET /sessions/{session_id}/vnc/ws` WebSocket 签名校验与 sandbox `/websockify` 代理，避免前端直接裸连 sandbox。
  - 新增 `ScienceClaw/backend/tests/test_sessions_vnc_route.py` 覆盖认证、属主校验、404 和响应合同。
  - 2026-06-01 复核 Docker 运行态时，backend、frontend、sandbox、MongoDB、Redis 等容器均在运行；普通 API signed-url 合同可在登录态下验证，但最终 takeover smoke 必须使用 Codex App 内置浏览器，不使用 Playwright MCP 结果替代。
  - 2026-06-02 尝试通过 Codex App 内置浏览器打开 `http://localhost:5173/`；浏览器控制面在 `Page.navigate` 和 `Runtime.evaluate` 均超时，无法形成有效页面证据。
- 已验证：

```powershell
PYTHONNOUSERSITE=1 conda run -p D:/conda/envs/scienceclaw python -m unittest ScienceClaw/backend/tests/test_sessions_vnc_route.py
npm --prefix .\ScienceClaw\frontend run type-check
npm --prefix .\ScienceClaw\frontend run build
```

- 剩余手工项：在可用 session 下用 Codex App 内置浏览器做一次 `?vnc=1` takeover smoke。当前阻塞点是 Codex App 内置浏览器控制面超时，而不是 VNC 代码或 Docker 运行态；该项保留为暂停手工验证项，不作为 `docs/tech-debt-audit-report-v2.md` 登记进入执行态的阻塞项。

### 前端技术债治理施工单 v2

- 状态：批次 6 `ChatMessage.vue` 渐进拆分已完成；下一批最小增量进入批次 7 颜色 token 分层治理。
- 权威文档：`docs/tech-debt-audit-report-v2.md`
- 登记原因：该施工单要求先处理 VNC signed URL 活跃计划；当前 VNC 剩余项已明确降级为待 Codex App 内置浏览器手工验证的暂停项，因此技术债治理可以进入执行态。
- 已完成最小增量：
  - 明确 task-service 信任模型：前端通过 `/task-service` 代理访问，compose 也暴露 `scheduler_api` 到宿主 `12002`，因此 task-service 自身必须验证 bearer session id。
  - 新增 `ScienceClaw/task-service/app/auth.py`，按主后端 `user_sessions` session-id 合同解析 bearer token。
  - `tasks.py` 和 `webhooks.py` 按普通用户 owner 过滤；管理员 `role=admin` 保留全量可见能力。
  - 新增 `ScienceClaw/task-service/tests/test_auth_isolation.py`，覆盖未授权、普通用户跨用户 404、管理员全量列表、创建时 owner 写入。
  - 新增 Vitest 前端测试基座：`ScienceClaw/frontend/vitest.config.ts`、`test`/`test:run`/`test:coverage` 脚本、`happy-dom` 环境和 V8 coverage provider。
  - 首批前端测试覆盖 `content.ts`、`fileType.ts`、`useSessionSearch.ts`，共 12 个单元测试；测试样例不依赖 Pinia 或未落地架构。
  - 新增 `ScienceClaw/frontend/src/api/taskClient.ts`，统一 task-service 的 `/task-service` base URL、30s timeout、bearer token 注入、401 logout 事件和错误映射。
  - `tasks.ts` 与 `webhooks.ts` 已复用共享 `taskClient`；既有导出函数和响应解包保持不变，`tooluniverse.ts` 未修改。
  - 新增 `ScienceClaw/frontend/src/api/taskClient.spec.ts`，覆盖 base URL、token header、显式 Authorization 不覆盖、错误映射、401 清 token 和 `auth:logout`。
  - 新增 `ScienceClaw/frontend/src/types/json.ts`，定义递归 `JsonValue`/`JsonObject` 类型和 `isJsonObject` narrowing。
  - `tooluniverse.ts` 已将工具参数收紧为 `Record<string, JsonValue>`，工具结果和 `return_schema` 收紧为 `unknown`；保持 `return resp.data` 后端裸业务对象解包不变。
  - `ScienceToolDetail.vue` 已在视图层 narrow `unknown` 结果，并用显式输入 getter/setter 维护 DOM 表单值与 JSON 参数边界。
  - 新增 `json.spec.ts` 与 `tooluniverse.spec.ts`，覆盖嵌套对象、数组、`null` 参数透传，以及 ToolUniverse 列表响应不额外 unwrap。
  - `ScienceClaw/frontend/src/api/client.ts` 已为 refresh queue、refresh request marker 和 retryable request config 定义显式类型，移除该队列上的宽泛 `any`。
  - 新增 `ScienceClaw/frontend/src/api/client.spec.ts`，覆盖两个并发 401 请求只触发一次 refresh，并在队列释放后用新 token 重试。
  - 新增 `ScienceClaw/frontend/src/types/toolPayload.ts`，定义 `ToolArgs`/`ToolResultContent` 和工具参数、工具结果字段访问 helper。
  - `ToolContent`/`ToolEventData` 已从宽泛 `any` 收紧到共享工具 payload 类型；ActivityPanel、ToolUse、各 tool view 和 ChatPage save prompt 调用点已改为显式 narrowing。
  - 新增 `toolPayload.spec.ts`，覆盖对象/string/null 参数、字段读取、预览生成和结果对象 narrowing。
  - 新增 `ScienceClaw/frontend/src/utils/smartMerge.ts`，将 ChatPage/SharePage 重复的工具事件合并规则抽成纯函数。
  - 新增 `smartMerge.spec.ts`，覆盖有效值覆盖、`undefined`/`null`/空对象跳过，以及数组、`0`、`false`、空字符串仍可覆盖。
  - 新增 `ScienceClaw/frontend/src/utils/planSteps.ts`，将 ChatPage/SharePage 重复的 pending-tool 目标步骤选择规则抽成纯函数。
  - 新增 `planSteps.spec.ts`，覆盖 `running > completed > first` 优先级和空步骤列表。
  - 新增 `ScienceClaw/frontend/src/utils/activitySnapshot.ts`，将 ChatPage/SharePage 重复的 Activity snapshot 生成规则抽成纯函数。
  - 新增 `activitySnapshot.spec.ts`，覆盖 activity list 浅拷贝、plan 深拷贝和空 plan。
  - 新增 `ScienceClaw/frontend/src/utils/pendingTools.ts`，将 ChatPage/SharePage 重复的 pending-tool 关联规则抽成明确输入/输出的局部 mutation helper。
  - 新增 `pendingTools.spec.ts`，覆盖 pending tool 关联、重复 tool 跳过、未解析 pending id 清空，以及缺失 `tools` 列表初始化。
  - 新增 `ScienceClaw/frontend/src/utils/chatMessageContent.ts`，将 `ChatMessage.vue` 的 rendered HTML/special viewer/suggested questions 拆分规则抽成 helper。
  - 新增 `chatMessageContent.spec.ts`，覆盖 HTML 合并、suggested questions 提取、special viewer source 转换和空内容回退。
  - 新增 `ScienceClaw/frontend/src/utils/markdownRenderer.ts`，将 Markdown link renderer 规则抽成纯 helper。
  - 新增 `markdownRenderer.spec.ts`，覆盖 marked v15 token、旧 API 字符串参数、外链 target 和缺失 href 回退。
  - 扩展 `markdownRenderer.ts`，将代码块 token 归一化、复制 payload 转义和行号/折叠布局规则抽成纯 helper。
  - 扩展 `markdownRenderer.spec.ts`，覆盖 marked code token、旧 API 字符串参数、复制属性转义和折叠阈值。
  - 扩展 `markdownRenderer.ts`，将普通 code block HTML 生成规则抽成 `renderHighlightedCodeBlock` helper。
  - 扩展 `markdownRenderer.spec.ts`，覆盖代码块 controls/line metadata/copy payload 和长代码块折叠提示。
  - 扩展 `markdownRenderer.ts`，将 Mermaid loading placeholder 和 render error HTML 抽成纯 helper。
  - 扩展 `markdownRenderer.spec.ts`，覆盖 Mermaid wrapper/code encoding/loading text/content id，以及错误提示和 raw code 展示。
  - 扩展 `markdownRenderer.ts`，将 KaTeX render、公式预处理和公式占位符后处理抽成纯 helper，并继续由 `ChatMessage.vue` 提供原有占位符计数器。
  - 扩展 `markdownRenderer.spec.ts`，覆盖 KaTeX display render、块级/行内公式占位符、非公式文本跳过和公式 HTML 回填。
  - 扩展 `markdownRenderer.ts`，将单个 Mermaid wrapper 的 code decode、cache 命中、`mermaid.render`、loading/content DOM 更新和错误展示抽成 `renderMermaidWrapper` helper。
  - 扩展 `markdownRenderer.spec.ts`，覆盖 Mermaid SVG 渲染与缓存写入、缓存命中跳过 render，以及 render 失败时复用既有错误 HTML。
  - 扩展 `markdownRenderer.ts`，将 Mermaid 动态 import 单例 promise、module 缓存、初始化状态和初始化配置抽成 `createMermaidLoader` helper。
  - 扩展 `markdownRenderer.spec.ts`，覆盖动态 import 只执行一次、初始化只执行一次、初始化配置保持不变，以及初始化失败仍返回 mermaid module 的既有行为。
  - 新增 `MessageFooter.vue`，将反馈按钮、复制、PDF 转换、文件入口和统计信息展示从 `ChatMessage.vue` 提取为子组件，父组件继续持有交互行为和状态。
  - 新增 `MessageFooter.spec.ts`，覆盖反馈/复制/文件数/统计信息渲染，以及 like/dislike、copy、convertToPdf、showFiles 事件透传。
  - 将 `MessageFooter.vue` 所需的 `.msg-footer-*`、`.msg-action-*`、`.msg-stat-*` 和对应移动端规则从 `ChatMessage.vue` 大样式块迁入 `MessageFooter.vue`。
  - 新增 `ScienceClaw/frontend/src/assets/chat-message-renderer.css`，将 `.markdown-content` 下的 Markdown、code block、KaTeX、Mermaid 和移动端表格样式从 `ChatMessage.vue` 外置到独立样式文件；`ChatMessage.vue` 只保留组件入场动画和搜索命中动画。
- 下一批最小增量：
  - 批次 7 第一段：在 `ScienceClaw/frontend/src/assets/theme.css` 明确颜色 token 分层治理入口，优先盘点并迁移 `ChatMessage.vue` renderer 样式中已稳定的 code、diagram、semantic-state token，不改变消息正文、Markdown、Mermaid、数学公式、代码块复制或附件分支。
- 验收命令：

```bash
PYTHONNOUSERSITE=1 conda run -p D:/conda/envs/scienceclaw python -m unittest discover -s ScienceClaw/task-service/tests -t ScienceClaw/task-service
npm --prefix ScienceClaw/frontend run test:run
npm --prefix ScienceClaw/frontend run test:coverage
npm --prefix ScienceClaw/frontend run type-check
npm --prefix ScienceClaw/frontend run build
gitnexus detect-changes
```

## 归档记录

| 计划文档 | 归档原因 | 后续事项 |
| --- | --- | --- |
| `docs/archive/plans/tools-classification-rework-plan-zh.md` | Tools / MCP / ToolUniverse 中文分类治理、非 embedding 工具发现索引、三段式 adapter/API、README/skill/Agent 提示收口已完成并逐步提交。 | `npm --prefix ScienceClaw/frontend run build` 仍受既有 Vite/Rollup 绝对路径 `fileName` 问题影响；后续若要修复构建链路，应新建独立计划。 |
| `docs/archive/plans/mcp-https-integration-completion-audit-zh.md` | 第三方 HTTPS MCP 接入第 0-5 批已完成；第 5 批联调和完成审计均已有提交证据。 | 残余未测项和累积警告已记录；后续若加强 live LLM chat/SSE 或前端自动化测试，应新建独立计划。 |
| `docs/archive/plans/frontend-typescript-remediation-plan-zh.md` | 已完成主要目标：`vue-tsc` 从 63 条错误收敛到 0，生产构建通过。 | VNC 后端 signed URL 路由仍需单独闭环，已登记为活跃计划。 |

## 已归档计划残余事项

| 归档计划 | 残余未测项 | 累积警告 |
| --- | --- | --- |
| 第三方 HTTPS MCP 接入 | live LLM chat/SSE 长链路、live 非法 JSON HTTPS MCP server、50 工具规模下长时间真实聊天调用、前端自动化测试基座未覆盖；详见 `docs/archive/plans/mcp-https-integration-completion-audit-zh.md`。 | Browserslist 数据陈旧、Vite CSS minify、chunk size、`lark_oapi` deprecation、unclosed event loop ResourceWarning、GitNexus 生成文件未纳入提交；详见归档审计文档。 |
