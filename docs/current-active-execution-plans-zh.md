# 当前活跃执行计划台账

更新时间：2026-06-07

本文档是 ScienceClaw 当前执行计划的唯一滚动入口。新任务进入执行态前先登记到这里；计划完成后从本台账移除，并移动到 `docs/archive/plans/`。

## 使用规则

- `AGENTS.md` 只引用本台账，不直接引用单个阶段计划，避免旧计划继续影响执行。
- 活跃计划必须写清楚当前状态、权威文档、下一批最小增量和验收命令。
- 已完成、废弃或被新计划取代的计划文档必须移入 `docs/archive/plans/`，并在本台账的“归档记录”中保留索引。
- 不把部署教程、长期设计说明或普通参考资料放入归档计划目录，除非它们曾作为执行计划使用。

## 活跃计划

当前活跃执行计划如下。

| 计划 | 当前状态 | 权威文档 | 下一批最小增量 | 验收命令 |
| --- | --- | --- | --- | --- |
| 沙盒接管页扩展施工单 | 执行中。W1/W2/W3 已完成：`VNCViewer` 已支持运行时 `viewOnly` 切换；`TakeOverView` 已升级为会话绑定双 tab 接管页；`ActivityPanel`/`TakeOverView` 已补齐按 `sessionId` 隔离的 BroadcastChannel 快照与增量同步。 | `docs/sandbox-takeover-construction-plan.md` | W4 `BrowserToolView` 新开独立标签页入口；W5 i18n 与最小测试收口。 | `cd D:\trae\ScienceClaw\ScienceClaw\frontend && npm run type-check && npm run test:run -- src/components/ActivityPanel.spec.ts src/components/TakeOverView.spec.ts src/components/VNCViewer.spec.ts` |

## 非必须后续项

| 事项 | 当前结论 | 触发条件 | 参考文档 |
| --- | --- | --- | --- |
| Mermaid 持久化缓存（原前端性能施工单 W6） | 非必须项，暂不施工。W3 已完成内存 LRU 上限、失败重试和有限并发，已覆盖当前主要渲染可靠性与重复渲染成本。 | 只有当真实长会话中大量重复 Mermaid 图表在刷新页面、关闭重开浏览器或新 tab 重新进入后仍造成可感知渲染瓶颈，并有性能采样证据时，再单独建立施工单。 | `docs/archive/plans/frontend-perf-optimization-plan-zh.md` |

## 归档记录

| 计划文档 | 归档原因 | 后续事项 |
| --- | --- | --- |
| `docs/archive/plans/frontend-perf-optimization-plan-zh.md` | 前端聊天页性能优化与 Mermaid 渲染可靠性施工单 W1-W5 已完成；W6 评估后转入“非必须后续项”，不再作为活跃施工单继续执行。 | 仅当持久化缓存出现真实可感知瓶颈并有采样证据时，再新建独立施工单。 |
| `docs/archive/plans/mermaid-interaction-upgrade-plan-zh.md` | Mermaid 图表交互增强 W1-W4 已完成，消息内与全屏交互、测试、构建验收已闭环；Codex App in-app browser smoke 尝试受本机 `iab` 运行时不可用阻塞，已在计划文档中记录。 | 若后续需要补做内置浏览器 smoke，先恢复 `CODEX_IN_APP_BROWSER.md` 所述 `iab` 运行时，再基于同一交互面单独补记验证。 |
| `docs/archive/plans/tools-classification-rework-plan-zh.md` | Tools / MCP / ToolUniverse 中文分类治理、非 embedding 工具发现索引、三段式 adapter/API、README/skill/Agent 提示收口已完成并逐步提交。 | `npm --prefix ScienceClaw/frontend run build` 仍受既有 Vite/Rollup 绝对路径 `fileName` 问题影响；后续若要修复构建链路，应新建独立计划。 |
| `docs/archive/plans/mcp-https-integration-completion-audit-zh.md` | 第三方 HTTPS MCP 接入第 0-5 批已完成；第 5 批联调和完成审计均已有提交证据。 | 残余未测项和累积警告已记录；后续若加强 live LLM chat/SSE 或前端自动化测试，应新建独立计划。 |
| `docs/archive/plans/frontend-typescript-remediation-plan-zh.md` | 已完成主要目标：`vue-tsc` 从 63 条错误收敛到 0，生产构建通过。 | VNC 后端 signed URL 路由已闭环，见 `docs/archive/plans/vnc-signed-url-plan-zh.md`。 |
| `docs/archive/plans/tech-debt-audit-report-v2.md` | 前端技术债治理施工单 v2 批次 1-10 已完成；剩余 major migration 候选项需另行建独立计划。 | 如继续处理 Vite/Vitest、Tailwind/Reka、Vue Router、Vue I18n v11 等依赖债务，应新建独立活跃施工单。 |
| `docs/archive/plans/vnc-signed-url-plan-zh.md` | VNC signed URL 全链路已完成：后端 HMAC 签名 + WebSocket 代理、前端 API + VNCViewer 接线、单测（4/4 通过）、Docker 运行态验证、noVNC 手动 smoke 确认可交互。sandbox 容器网络和 Chromium headless 均正常。 | 无后续阻塞项。sandbox 内图形化 Chromium 联网问题为独立事项，与 VNC 接口无关。 |
| `docs/archive/plans/session-password-protection-design.md` | 会话密码保护已完成：后端 bcrypt 密码字段、服务端内存解锁、离开会话/退出登录锁回、受保护资源统一门禁、前端密码弹窗/锁图标/i18n、测试和运行态验证均已闭环。 | 无后续阻塞项。 |

## 已归档计划残余事项

| 归档计划 | 残余未测项 | 累积警告 |
| --- | --- | --- |
