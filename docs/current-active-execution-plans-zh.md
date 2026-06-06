# 当前活跃执行计划台账

更新时间：2026-06-03

本文档是 ScienceClaw 当前执行计划的唯一滚动入口。新任务进入执行态前先登记到这里；计划完成后从本台账移除，并移动到 `docs/archive/plans/`。

## 使用规则

- `AGENTS.md` 只引用本台账，不直接引用单个阶段计划，避免旧计划继续影响执行。
- 活跃计划必须写清楚当前状态、权威文档、下一批最小增量和验收命令。
- 已完成、废弃或被新计划取代的计划文档必须移入 `docs/archive/plans/`，并在本台账的“归档记录”中保留索引。
- 不把部署教程、长期设计说明或普通参考资料放入归档计划目录，除非它们曾作为执行计划使用。

## 活跃计划

（当前无活跃计划。）

## 归档记录

| 计划文档 | 归档原因 | 后续事项 |
| --- | --- | --- |
| `docs/archive/plans/tools-classification-rework-plan-zh.md` | Tools / MCP / ToolUniverse 中文分类治理、非 embedding 工具发现索引、三段式 adapter/API、README/skill/Agent 提示收口已完成并逐步提交。 | `npm --prefix ScienceClaw/frontend run build` 仍受既有 Vite/Rollup 绝对路径 `fileName` 问题影响；后续若要修复构建链路，应新建独立计划。 |
| `docs/archive/plans/mcp-https-integration-completion-audit-zh.md` | 第三方 HTTPS MCP 接入第 0-5 批已完成；第 5 批联调和完成审计均已有提交证据。 | 残余未测项和累积警告已记录；后续若加强 live LLM chat/SSE 或前端自动化测试，应新建独立计划。 |
| `docs/archive/plans/frontend-typescript-remediation-plan-zh.md` | 已完成主要目标：`vue-tsc` 从 63 条错误收敛到 0，生产构建通过。 | VNC 后端 signed URL 路由已闭环，见 `docs/archive/plans/vnc-signed-url-plan-zh.md`。 |
| `docs/archive/plans/tech-debt-audit-report-v2.md` | 前端技术债治理施工单 v2 批次 1-10 已完成；剩余 major migration 候选项需另行建独立计划。 | 如继续处理 Vite/Vitest、Tailwind/Reka、Vue Router、Vue I18n v11 等依赖债务，应新建独立活跃施工单。 |
| `docs/archive/plans/vnc-signed-url-plan-zh.md` | VNC signed URL 全链路已完成：后端 HMAC 签名 + WebSocket 代理、前端 API + VNCViewer 接线、单测（4/4 通过）、Docker 运行态验证、noVNC 手动 smoke 确认可交互。sandbox 容器网络和 Chromium headless 均正常。 | 无后续阻塞项。sandbox 内图形化 Chromium 联网问题为独立事项，与 VNC 接口无关。 |
| `docs/archive/plans/session-password-protection-design.md` | 会话密码保护已完成：后端 bcrypt 密码字段、服务端内存解锁、离开会话/退出登录锁回、受保护资源统一门禁、前端密码弹窗/锁图标/i18n、测试和运行态验证均已闭环。 | 无后续阻塞项。 |

## 已归档计划残余事项

| 归档计划 | 残余未测项 | 累积警告 |
| --- | --- | --- |
