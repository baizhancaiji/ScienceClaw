# 当前活跃执行计划台账

更新时间：2026-06-03

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

### PDF 导出施工单

- 状态：已登记，进入活跃施工单；尚未开始实现。
- 权威文档：`docs/pdf-export-plan.md`
- 登记原因：当前前端消息底部已有“转PDF”入口，但仍是把输入框注入为 `转成pdf` 的占位行为；计划要求闭环为前端提取已渲染消息 DOM/CSS、后端转发、sandbox Playwright 生成 PDF 并下载。
- 当前方案：方案 A，Playwright 后端 PDF 导出；PDF 渲染服务放在 sandbox 容器，因为 sandbox 已具备 Chromium、Playwright 和 CJK 字体。
- 下一批最小增量：
  - 在 sandbox API 中新增 `POST /v1/render-pdf`，实现 Chromium 单例、HTML 渲染和 `application/pdf` 响应。
  - 用 curl/httpie 发送最小 HTML 验证返回 PDF binary，并覆盖失败/超时的基础错误路径。
  - 登记实际 sandbox 路由文件位置和验证命令到 `docs/pdf-export-plan.md`，若发现方案细节与运行态不符，先修正文档再继续后端 sessions 端点。
- 验收命令：

```powershell
PYTHONNOUSERSITE=1 conda run -p D:/conda/envs/scienceclaw python -m unittest <sandbox_or_backend_pdf_tests>
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
| `docs/archive/plans/tech-debt-audit-report-v2.md` | 前端技术债治理施工单 v2 批次 1-10 已完成；剩余 major migration 候选项需另行建独立计划。 | 如继续处理 Vite/Vitest、Tailwind/Reka、Vue Router、Vue I18n v11 等依赖债务，应新建独立活跃施工单。 |

## 已归档计划残余事项

| 归档计划 | 残余未测项 | 累积警告 |
| --- | --- | --- |
| 第三方 HTTPS MCP 接入 | live LLM chat/SSE 长链路、live 非法 JSON HTTPS MCP server、50 工具规模下长时间真实聊天调用、前端自动化测试基座未覆盖；详见 `docs/archive/plans/mcp-https-integration-completion-audit-zh.md`。 | Browserslist 数据陈旧、Vite CSS minify、chunk size、`lark_oapi` deprecation、unclosed event loop ResourceWarning、GitNexus 生成文件未纳入提交；详见归档审计文档。 |

