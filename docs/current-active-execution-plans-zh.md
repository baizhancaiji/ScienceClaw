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

- 状态：批次 2 已完成；下一批次为批次 3「Task Service 客户端整理」。
- 权威文档：`docs/tech-debt-audit-report-v2.md`
- 登记原因：该施工单要求先处理 VNC signed URL 活跃计划；当前 VNC 剩余项已明确降级为待 Codex App 内置浏览器手工验证的暂停项，因此技术债治理可以进入执行态。
- 已完成最小增量：
  - 明确 task-service 信任模型：前端通过 `/task-service` 代理访问，compose 也暴露 `scheduler_api` 到宿主 `12002`，因此 task-service 自身必须验证 bearer session id。
  - 新增 `ScienceClaw/task-service/app/auth.py`，按主后端 `user_sessions` session-id 合同解析 bearer token。
  - `tasks.py` 和 `webhooks.py` 按普通用户 owner 过滤；管理员 `role=admin` 保留全量可见能力。
  - 新增 `ScienceClaw/task-service/tests/test_auth_isolation.py`，覆盖未授权、普通用户跨用户 404、管理员全量列表、创建时 owner 写入。
  - 新增 Vitest 前端测试基座：`ScienceClaw/frontend/vitest.config.ts`、`test`/`test:run`/`test:coverage` 脚本、`happy-dom` 环境和 V8 coverage provider。
  - 首批前端测试覆盖 `content.ts`、`fileType.ts`、`useSessionSearch.ts`，共 12 个单元测试；测试样例不依赖 Pinia 或未落地架构。
- 下一批最小增量：
  - 批次 3「Task Service 客户端整理」：新建共享 task-service API client，统一 `/task-service` base URL、超时、token 注入和错误映射，让 `tasks.ts` 与 `webhooks.ts` 复用同一边界。
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
