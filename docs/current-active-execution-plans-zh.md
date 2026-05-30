# 当前活跃执行计划台账

更新时间：2026-05-30

本文档是 ScienceClaw 当前执行计划的唯一滚动入口。新任务进入执行态前先登记到这里；计划完成后从本台账移除，并移动到 `docs/archive/plans/`。

## 使用规则

- `AGENTS.md` 只引用本台账，不直接引用单个阶段计划，避免旧计划继续影响执行。
- 活跃计划必须写清楚当前状态、权威文档、下一批最小增量和验收命令。
- 已完成、废弃或被新计划取代的计划文档必须移入 `docs/archive/plans/`，并在本台账的“归档记录”中保留索引。
- 不把部署教程、长期设计说明或普通参考资料放入归档计划目录，除非它们曾作为执行计划使用。

## 活跃计划

### 第三方 HTTPS MCP 接入

- 状态：执行中；第 1 批 / 1.5 Settings 基础页接入已按最小增量完成并进入本地验证收口；0.1 路由骨架已按 MCP 鉴权原则完成复审收敛。
- 权威文档：`docs/mcp-https-integration-design-zh.md`
- 范围：第三方 HTTPS MCP Server 配置、验证、工具目录缓存、逐工具启用、Agent 工具注入和前端管理界面。
- 当前批次：1.5 Settings 基础页接入；只触碰 `ScienceClaw/frontend/src/api/mcp.ts`、`ScienceClaw/frontend/src/components/settings/SettingsDialog.vue`、`ScienceClaw/frontend/src/components/settings/McpSettings.vue`，新增 MCP tab 并支持 server 列表、新增、编辑、删除、启停。
- 下一批最小增量：2.1 HTTPS MCP client: `initialize`；只触碰 `ScienceClaw/backend/mcp/client.py` 与 `ScienceClaw/backend/tests/test_mcp_client.py`，实现 JSON-RPC 基础请求、`initialize`、超时/TLS/错误映射。
- 建议验证：

```powershell
$env:PYTHONNOUSERSITE='1'; conda run -p D:\conda\envs\scienceclaw python -m unittest ScienceClaw.backend.tests.test_mcp_route_smoke
$env:PYTHONNOUSERSITE='1'; conda run -p D:\conda\envs\scienceclaw python -m unittest ScienceClaw.backend.tests.test_mcp_repository
$env:PYTHONNOUSERSITE='1'; conda run -p D:\conda\envs\scienceclaw python -m unittest ScienceClaw.backend.tests.test_mcp_crypto
$env:PYTHONNOUSERSITE='1'; conda run -p D:\conda\envs\scienceclaw python -m unittest ScienceClaw.backend.tests.test_mcp_schemas
$env:PYTHONNOUSERSITE='1'; conda run -p D:\conda\envs\scienceclaw python -m unittest ScienceClaw.backend.tests.test_mcp_service_servers
$env:PYTHONNOUSERSITE='1'; conda run -p D:\conda\envs\scienceclaw python -m unittest ScienceClaw.backend.tests.test_mcp_route_servers
npm --prefix ScienceClaw/frontend run type-check
npm --prefix ScienceClaw/frontend run build
gitnexus detect-changes -r ScienceClaw
```

Docker Compose 仍是主运行方式；本地分批验证优先使用仓库指定的 `D:\conda\envs\scienceclaw` 环境。

### VNC signed URL 接口闭环

- 状态：待确认/待补齐。
- 来源：前端 TypeScript 修复中发现 `VNCViewer.vue` 已消费 `getVNCUrl()` 返回的 `signed_url`，但当前审查未找到后端 `/sessions/{sessionId}/vnc/signed-url` 路由实现。
- 关联归档计划：`docs/archive/plans/frontend-typescript-remediation-plan-zh.md`
- 下一批最小增量：
  - 搜索并确认后端是否已有等价 VNC 路由或代理入口。
  - 若不存在，新增最小后端 route/service 合同，返回 `{ signed_url, expires_in }`。
  - 前端只在必要时补充错误提示，不扩大 VNC UI 范围。
- 建议验证：

```powershell
npm --prefix .\ScienceClaw\frontend run type-check
npm --prefix .\ScienceClaw\frontend run build
```

并在可用 session 下做一次 `?vnc=1` 浏览器 smoke。

## 归档记录

| 计划文档 | 归档原因 | 后续事项 |
| --- | --- | --- |
| `docs/archive/plans/frontend-typescript-remediation-plan-zh.md` | 已完成主要目标：`vue-tsc` 从 63 条错误收敛到 0，生产构建通过。 | VNC 后端 signed URL 路由仍需单独闭环，已登记为活跃计划。 |
