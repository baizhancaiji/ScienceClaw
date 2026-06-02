# 当前活跃执行计划台账

更新时间：2026-06-02

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

- 状态：批次 10 依赖升级已完成；2026-06-02 批次 6 composable 补施工已完成并复验，本施工单登记的批次 1-10 已全部完成。剩余只保留独立 major migration 候选项，需另行建计划处理。
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
  - 2026-06-02 复核更正：原批次 6 执行记录已移回 `tech-debt-audit-report-v2.md` 的批次 6 章节内部；复核发现施工项 1-3 的 composable 缺口后，已补齐 `ScienceClaw/frontend/src/composables/useMarkdownRenderer.ts`、`useMathRenderer.ts`、`useMermaidRenderer.ts`。
  - 批次 6 补施工已将 marked/highlight/DOMPurify 渲染接线、KaTeX 预/后处理、Mermaid 缓存/动态加载/DOM 扫描/生命周期触发从 `ChatMessage.vue` 移入 composable；`ChatMessage.vue` 只保留 UI 状态、点击处理和 composable 接线。
  - 新增 `useMarkdownRenderer.spec.ts`、`useMathRenderer.spec.ts`、`useMermaidRenderer.spec.ts`，覆盖 Markdown 渲染接线、公式 composable 边界、Mermaid placeholder id、动态加载/渲染和无 wrapper 跳过加载。
  - `ScienceClaw/frontend/src/assets/theme.css` 已新增 chat renderer 专用 code、diagram、semantic-state token；`chat-message-renderer.css` 已将稳定的 inline code、code block、Mermaid、KaTeX error 和删除线错误态颜色迁移到 token，品牌/实验性渐变暂不混入全局语义层。
  - `MarkdownEnhancements.vue` 的 code fullscreen overlay/header/border/control/success/error 颜色已复用 chat renderer code 与 semantic-state token；`type-check`、build 和 Node CSS token smoke 已通过。
  - Codex App in-app browser 当前返回 `iab` unavailable，Playwright 临时包在 PowerShell/npx 下无法解析 `playwright` 模块；本段 smoke 使用 Node 校验 light/dark 各 11 个 token、无缺失引用和无旧硬编码残留。
  - `MarkdownEnhancements.vue` 的 selection menu surface、border、text 和 hover 颜色已迁移到 light/dark token，暗色分支由 `.dark` token 覆盖，不再保留组件局部 dark override。
  - `chat-message-renderer.css` 的表格单元格、斑马纹、kbd surface/border，以及 code block subtle border 已迁移到 light/dark token；稳定 surface/border 色值不再保留组件局部 dark override。
  - 批次 7 收尾审计已完成：`chat-message-renderer.css` 的 code block 控件背景、hover、展开提示和 header 分隔线已迁移到 chat code token；剩余硬编码色值限定为标题/链接/列表/引用/分隔线等品牌渐变、KaTeX 轻量装饰、lightbox overlay 和阴影类局部视觉效果，按施工单保留局部命名。
  - 批次 7 全量验证已通过：task-service unittest 7 个用例通过，前端 Vitest 15 个测试文件/65 个用例通过，coverage 总体 statements 80.56%，`type-check` 和 `build` 通过；build/test 仅保留既有 Browserslist 数据陈旧提示。
  - 批次 8 已建立 ESLint 9 flat config baseline：`prettier` 和 `@types/dompurify` 已移入 devDependencies，新增 `lint` 与 `format:check` 脚本，暂不引入 Husky/lint-staged，也不新增 `lint:fix`。
  - `npm --prefix ScienceClaw/frontend run lint` 已可执行并通过，当前 baseline 保留 0 error/42 warning；`npm --prefix ScienceClaw/frontend run format:check` 已可执行并通过，当前检查范围为本批新增/变更入口 `eslint.config.js` 与 `package.json`。
  - `lint:fix` 机械范围已用 dry-run 评估：`npm exec eslint -- "src/**/*.{ts,vue}" "*.config.ts" --fix-dry-run` 在前端目录退出 0，dry-run 后仍剩 26 个 warning；不在本批写入自动修复脚本，避免生成大规模历史格式 diff。
  - 批次 9 已完成 Pinia 适用性评估：theme owner 为 `useTheme`，left panel owner 为 `useLeftPanel`，right panel owner 为当前无调用点的 `useRightPanel`，file panel owner 为 `useFilePanel`，session file list owner 为 `useSessionFileList`，settings dialog owner 为 `useSettingsDialog`，session notifications owner 为 `useSessionNotifications`。
  - 决策为暂不迁移 Pinia：当前共享状态均为小型 module-scope composable，尚未出现需要 DevTools、复杂派生状态、跨页面一致性约束或 SSR 隔离的 store 触发条件；若未来触发，优先用 Auth 或 Panel 单一 store 试点。
  - 新增 `useSharedStateLifecycle.spec.ts`，覆盖 theme/left panel localStorage side effect、relative time interval 清理、session notification active subscription cancel 与 reconnect timer 清理；新增 spec 5 个用例通过，前端测试集 16 个文件/70 个用例通过。
  - 批次 10 已完成 Browserslist 数据更新：`npx update-browserslist-db@latest` 将 `caniuse-lite` 从 `1.0.30001713` 更新到 `1.0.30001793`，输出 `No target browser changes`，后续 build 不再出现既有 Browserslist 数据陈旧提示。
  - 已完成当前主版本内的低风险安全/patch/minor 升级：`axios`、`dompurify`、`mermaid`、`postcss`、`vite`、`vue-i18n`、`@types/node`、`@vue/test-utils` 的声明版本和 lockfile 实装版本已同步记录到权威文档。
  - `npm audit --json` 在默认 npmmirror registry 下因 audit endpoint 未实现失败；改用 `--registry=https://registry.npmjs.org` 后可审计。升级后官方 audit 剩余 13 项，主要进入 Vite/Vitest major、Vue I18n v11、Tailwind/Reka 传递链等独立迁移候选，不与本批混合提交。
  - 批次 10 验证已通过：`npm --prefix ScienceClaw/frontend run type-check`、`build`、`test:run`、`lint`、`format:check` 均通过；本轮按用户要求不做浏览器验证。
- 下一批最小增量：
  - 本施工单无剩余批次；若继续处理依赖债务，应为 Vite/Vitest、Tailwind/Reka、Vue Router、Vue I18n v11 等 major migration 新建独立计划。
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
