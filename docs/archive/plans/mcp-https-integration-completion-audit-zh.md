# 第三方 HTTPS MCP 接入完成审计

更新时间：2026-05-31

## 结论

`docs/mcp-https-integration-design-zh.md` 定义的第 0-5 批实现和第 5 批联调收口已完成。该设计文档继续作为长期设计说明保留在 `docs/`，本文件只归档本轮执行计划的完成证据、未测项和累积警告。

## 完成证据

| 批次 | 证据提交 | 结论 |
| --- | --- | --- |
| 5.1 简单 server 联调 | `ffc3efd Complete simple MCP server regression` | DeepWiki create -> verify -> refresh -> enable -> chat call smoke 已通过。 |
| 5.2 复杂 schema 联调 | `99fb473 Prove complex MCP payload fallback` | anyOf 复杂 schema 被识别为 payload mode，UI 有提示，wrapper 调用不崩溃。 |
| 5.3 异常路径联调 | `d91cc0e Prove MCP abnormal-path handling` | 连接失败、403、500 live smoke 已覆盖；非法 JSON 用单元测试覆盖。 |
| 5.4 规模与性能边界 | `fc61dc5 Prove MCP scale boundary` | 50 个临时 MCP 工具下 Tools 页、Settings 页、API 响应和新会话创建均可接受。 |
| 完成审计补齐 | `897f940` `743f2b9` `8fa5189` `f3b626b` | 补齐 create-time verify contract、blocked tool 过滤、>50 工具提示和 MCP 前端 i18n/no bare copy 缺口。 |

## 最终验证

最后一轮完成审计通过以下闸门：

```powershell
npm --prefix ScienceClaw/frontend run type-check
npm --prefix ScienceClaw/frontend run build
$env:PYTHONNOUSERSITE='1'; conda run -p D:\conda\envs\scienceclaw python -m unittest ScienceClaw.backend.tests.test_mcp_route_smoke ScienceClaw.backend.tests.test_mcp_client ScienceClaw.backend.tests.test_mcp_repository ScienceClaw.backend.tests.test_mcp_crypto ScienceClaw.backend.tests.test_mcp_schemas ScienceClaw.backend.tests.test_mcp_service_servers ScienceClaw.backend.tests.test_mcp_route_servers ScienceClaw.backend.tests.test_mcp_service_sync ScienceClaw.backend.tests.test_mcp_route_tools ScienceClaw.backend.tests.test_mcp_tool_factory ScienceClaw.backend.tests.test_mcp_result_normalization ScienceClaw.backend.tests.test_agent_mcp_injection ScienceClaw.backend.tests.test_mcp_sse_protocol
git diff --check
git diff --cached --check
gitnexus detect-changes -r ScienceClaw
```

结果摘要：

- 前端 `vue-tsc` 通过。
- 前端生产构建通过。
- MCP 后端测试 `115 tests OK`。
- GitNexus detect-changes：`risk low`，`affected processes 0`。
- Codex 内置浏览器 smoke：Tools 页和 MCP tab 可打开，控制台 error 为 0。

## 残余未测项

这些项未阻塞本轮 MCP 计划完成，但后续若继续增强 MCP 可靠性，应优先补自动化或 live smoke：

1. 复杂 payload 工具的 live LLM chat/SSE 长链路未完全覆盖；当时模型 API key 失败，payload 执行通过 wrapper contract 验证。
2. live 非法 JSON HTTPS MCP server 未覆盖；因 httpbin POST 返回 405，当前由 `test_mcp_client.py` 的非法响应单元测试覆盖。
3. 50 个启用工具规模下的长时间真实聊天调用未覆盖；当前覆盖到 Agent wrapper 收集、Tools/Settings UI、API 响应和新会话创建耗时。
4. 前端仍未引入专门的 Vitest/Playwright 自动化测试基座；这是设计文档允许的 MVP 测试策略，当前以前端 `type-check + build + browser smoke` 为闸门。

## 累积警告

以下警告在验证中出现，但不是本轮 MCP 改动引入的阻塞项：

1. `npm --prefix ScienceClaw/frontend run build` 提示 Browserslist / `caniuse-lite` 数据约 13 个月未更新。
2. Vite CSS minify 警告：`Expected identifier but found "-"`，位置形如 `<stdin>:4695:2`。
3. Vite CSS minify 警告：嵌套规则不能以 `a` 开头，位置形如 `<stdin>:11927:3`。
4. Vite chunk size 警告：部分 chunk 超过 500 kB。
5. 后端 MCP unittest 中出现第三方库 deprecation warning：`lark_oapi` 使用 `datetime.datetime.utcfromtimestamp()`。
6. 后端 MCP unittest 中出现第三方库 deprecation warning：`lark_oapi` 调用 `asyncio.get_event_loop()` 时无当前 event loop。
7. 后端 MCP unittest 结束时出现 `ResourceWarning: unclosed event loop <ProactorEventLoop ...>`。
8. Git 工作树存在 GitNexus/工具生成文件：`AGENTS.md`、`.claude/`、`CLAUDE.md`。按当前约束，除非明确要求，不纳入 MCP 收口提交。

## 后续事项

- MCP 主计划无活跃实现项。
- 若继续加强 MCP，建议新建独立计划处理“live LLM chat/SSE 长链路自动化”和“前端自动化测试基座”，不要复开本计划。
