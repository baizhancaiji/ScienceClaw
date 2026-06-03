# VNC signed URL 接口闭环

**执行状态**：✅ 已完成，归档。
**登记日期**：2026-06-01
**完成日期**：2026-06-03

---

## 背景

前端 TypeScript 修复中发现 `VNCViewer.vue` 已消费 `getVNCUrl()` 返回的 `signed_url`，但后端不存在 `/sessions/{sessionId}/vnc/signed-url` 路由实现。

## 已完成工作

### 后端
- `ScienceClaw/backend/route/sessions.py`：
  - `POST /sessions/{session_id}/vnc/signed-url` — session 归属校验 + HMAC 签名 + TTL
  - `WS /sessions/{session_id}/vnc/ws` — 签名校验 + WebSocket 代理至 sandbox `/websockify`
  - 辅助函数：`_get_sandbox_vnc_websockify_url()`、`_build_vnc_signature()`、`_is_valid_vnc_signature()`

### 前端
- `ScienceClaw/frontend/src/api/agent.ts`：`getVNCUrl()` API
- `VNCViewer.vue`：消费 `signed_url` 建立 WebSocket 连接

### 测试
- `ScienceClaw/backend/tests/test_sessions_vnc_route.py`：4 tests 全部通过
  - 认证校验
  - 属主校验
  - 404 处理
  - 签名合同验证

### 验证结果
- `vue-tsc` 类型检查：通过
- `npm run build`：通过
- Docker 运行态：backend、frontend、sandbox、MongoDB、Redis 全部 healthy
- noVNC 手动 smoke（2026-06-03）：画面可打开，关闭 view-only 后鼠标/键盘可交互
- sandbox 容器网络：curl baidu.com 200、Chromium headless example.com 正常

## 与原计划差异

原计划要求使用 Codex App 内置浏览器做 `?vnc=1` takeover smoke，但该浏览器控制面存在 `Page.navigate` / `Runtime.evaluate` 超时问题。最终改为用户手动 noVNC smoke 验证通过。

## 关联文档

- 归档来源：`docs/current-active-execution-plans-zh.md`（已移除）
- 关联归档计划：`docs/archive/plans/frontend-typescript-remediation-plan-zh.md`
