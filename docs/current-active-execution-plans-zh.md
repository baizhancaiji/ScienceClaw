# 当前活跃执行计划台账

更新时间：2026-05-31

本文档是 ScienceClaw 当前执行计划的唯一滚动入口。新任务进入执行态前先登记到这里；计划完成后从本台账移除，并移动到 `docs/archive/plans/`。

## 使用规则

- `AGENTS.md` 只引用本台账，不直接引用单个阶段计划，避免旧计划继续影响执行。
- 活跃计划必须写清楚当前状态、权威文档、下一批最小增量和验收命令。
- 已完成、废弃或被新计划取代的计划文档必须移入 `docs/archive/plans/`，并在本台账的“归档记录”中保留索引。
- 不把部署教程、长期设计说明或普通参考资料放入归档计划目录，除非它们曾作为执行计划使用。

## 活跃计划

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
| `docs/archive/plans/mcp-https-integration-completion-audit-zh.md` | 第三方 HTTPS MCP 接入第 0-5 批已完成；第 5 批联调和完成审计均已有提交证据。 | 残余未测项和累积警告已记录；后续若加强 live LLM chat/SSE 或前端自动化测试，应新建独立计划。 |
| `docs/archive/plans/frontend-typescript-remediation-plan-zh.md` | 已完成主要目标：`vue-tsc` 从 63 条错误收敛到 0，生产构建通过。 | VNC 后端 signed URL 路由仍需单独闭环，已登记为活跃计划。 |

## 已归档计划残余事项

| 归档计划 | 残余未测项 | 累积警告 |
| --- | --- | --- |
| 第三方 HTTPS MCP 接入 | live LLM chat/SSE 长链路、live 非法 JSON HTTPS MCP server、50 工具规模下长时间真实聊天调用、前端自动化测试基座未覆盖；详见 `docs/archive/plans/mcp-https-integration-completion-audit-zh.md`。 | Browserslist 数据陈旧、Vite CSS minify、chunk size、`lark_oapi` deprecation、unclosed event loop ResourceWarning、GitNexus 生成文件未纳入提交；详见归档审计文档。 |
