# 会话密码保护功能归档施工单

## 1. 完成状态

状态：已完成并归档。

完成日期：2026-06-06

本施工单为 ScienceClaw 会话增加密码保护能力。受保护会话在未验证密码前，不返回历史消息、沙盒文件、PDF 导出、VNC 地址，也不能继续聊天或执行会话派生保存操作。

最终方案已移除 `X-Session-Unlock-Token` / `unlock_token` 设计。解锁状态只保存在后端当前进程内，用户离开受保护会话后前端显式锁回；再次进入时必须先输入会话密码，再加载会话内容。

## 2. 最终行为

- 会话可设置、修改、移除密码，并保存可选密码提示。
- 密码规则由前后端共同执行：不少于 4 位，且在小写字母、大写字母、数字中至少包含两种。
- 设置/修改/重置密码时，确认密码输入框会实时提示两次输入不一致。
- 会话列表对受保护会话显示锁图标。
- 未验证进入受保护会话时，详情接口只返回元数据，`events=[]`，前端显示验证弹窗。
- 验证成功后，当前用户在后端进程内标记为已解锁，前端随后重新加载会话内容。
- 切换会话导致 `ChatPage` 卸载时，前端调用 `POST /sessions/{session_id}/password/lock` 锁回当前受保护会话。
- 用户主动退出登录时，前端调用 `POST /sessions/password/lock-all` 锁回当前用户在后端缓存中的受保护会话。
- 登录后默认进入 `/` 新会话首页，不自动加载历史会话；只有用户原本访问历史会话 URL 被登录页重定向时，才按显式 redirect 返回。

## 3. 涉及文件

后端：

- `ScienceClaw/backend/deepagent/sessions.py`
- `ScienceClaw/backend/route/sessions.py`
- `ScienceClaw/backend/tests/test_sessions_password.py`

前端：

- `ScienceClaw/frontend/src/api/agent.ts`
- `ScienceClaw/frontend/src/types/response.ts`
- `ScienceClaw/frontend/src/pages/ChatPage.vue`
- `ScienceClaw/frontend/src/components/SessionItem.vue`
- `ScienceClaw/frontend/src/components/session-password/SessionPasswordDialog.vue`
- `ScienceClaw/frontend/src/components/session-password/VerifySessionPasswordDialog.vue`
- `ScienceClaw/frontend/src/components/session-password/ResetSessionPasswordDialog.vue`
- `ScienceClaw/frontend/src/components/session-password/SessionPasswordDialogs.spec.ts`
- `ScienceClaw/frontend/src/composables/useAuth.ts`
- `ScienceClaw/frontend/src/composables/useSessionListUpdate.ts`
- `ScienceClaw/frontend/src/composables/useSessionListUpdate.spec.ts`
- `ScienceClaw/frontend/src/locales/zh.ts`
- `ScienceClaw/frontend/src/locales/en.ts`

## 4. 后端落地

`ScienceSession` 新增字段：

```python
password_hash: Optional[str] = None
password_hint: Optional[str] = None
password_unlocked_by: Dict[str, bool] = field(default_factory=dict, repr=False)
```

持久化策略：

- `password_hash`、`password_hint` 写入 Mongo。
- `password_unlocked_by` 只作为后端进程内状态，不写入 Mongo。
- `ScienceSession.save()`、`async_get_science_session()`、`async_list_science_sessions()` 已对齐密码字段。

密码处理：

- 使用 `bcrypt` 哈希和校验会话密码。
- 后端 `_validate_session_password_strength()` 强制执行长度和字符类别规则。
- `password_hint` 最长 100 字符，空字符串归一化为 `None`。

解锁/锁定：

```python
def _is_session_unlocked(session: Any, current_user: User) -> bool:
    if not _session_has_password(session):
        return True
    unlocked_by = getattr(session, "password_unlocked_by", None)
    if not isinstance(unlocked_by, dict):
        return False
    return bool(unlocked_by.get(current_user.id))
```

关键点：

- 无 header、无 query token、无前端持久化 unlock token。
- `_mark_session_unlocked()` 只写入 `password_unlocked_by[current_user.id] = True`。
- `_lock_session_for_user()` 移除当前用户的内存解锁标记。
- `_clear_session_unlocks()` 在设置、修改、移除、重置密码时清空该会话所有解锁状态。

## 5. 后端接口

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| `POST` | `/sessions/{session_id}/password` | 首次设置会话密码 |
| `PUT` | `/sessions/{session_id}/password` | 校验旧密码后修改密码 |
| `POST` | `/sessions/{session_id}/password/remove` | 校验当前密码后移除密码 |
| `POST` | `/sessions/{session_id}/verify-password` | 校验密码并标记当前用户当前会话已解锁 |
| `GET` | `/sessions/{session_id}/password-hint` | 返回密码提示 |
| `POST` | `/sessions/{session_id}/reset-password` | 校验账户密码后重置或移除会话密码 |
| `POST` | `/sessions/{session_id}/password/lock` | 锁回当前用户对该会话的解锁状态 |
| `POST` | `/sessions/password/lock-all` | 锁回当前用户在进程缓存中的受保护会话 |

响应约定：

```python
return ApiResponse(data={"has_password": True})
return ApiResponse(data={"has_password": False})
return ApiResponse(data={"valid": True})
return ApiResponse(data={"locked": True})
return ApiResponse(data={"hint": session.password_hint})
```

所有成功响应仍遵守 `ApiResponse.code=0`。

## 6. 受保护资源

以下接口在读取或操作会话内容前调用 `_require_session_unlocked(session, current_user)`：

- `GET /sessions/{session_id}`
- `POST /sessions/{session_id}/chat`
- `POST /sessions/{session_id}/stop`
- `POST /sessions/{session_id}/clear_unread_message_count`
- `GET /sessions/{session_id}/files`
- `GET /sessions/{session_id}/sandbox-file`
- `GET /sessions/{session_id}/sandbox-file/download`
- `POST /sessions/{session_id}/upload`
- `POST /sessions/{session_id}/export-pdf`
- `POST /sessions/{session_id}/vnc/signed-url`
- `POST /sessions/{session_id}/skills/save`
- `POST /sessions/{session_id}/tools/save`
- `POST /sessions/{session_id}/share`
- `DELETE /sessions/{session_id}/share`

分享策略：

- 受密码保护的会话不能公开分享。
- 已分享会话设置密码时自动取消分享，避免旧公开链接继续暴露内容。

## 7. 前端落地

类型与 API：

- `GetSessionResponse` 新增 `has_password?: boolean`、`locked?: boolean`。
- `ListSessionItem` 新增 `has_password?: boolean`。
- `agent.ts` 新增密码管理 API 和锁定 API。
- 所有会话 API 调用均不再传 `X-Session-Unlock-Token`。

组件：

- `SessionItem.vue` 在会话指标区显示锁图标。
- `SessionPasswordDialog.vue` 负责设置、修改、移除密码。
- `VerifySessionPasswordDialog.vue` 负责进入受保护会话时验证密码。
- `ResetSessionPasswordDialog.vue` 负责用账户密码重置或移除会话密码。

`ChatPage.vue`：

- `restoreSession()` 在重放 `events` 前检查 `session.has_password && session.locked`。
- 锁定时只显示验证弹窗，不渲染历史消息。
- 验证成功后重新调用 `restoreSession()`。
- 验证取消后跳回 `/`。
- 组件卸载时对受保护会话调用 `lockSessionPassword()`。

`useAuth.ts`：

- 用户主动退出登录时先调用 `lockAllSessionPasswords()`。
- 静默退出不额外调用锁定接口，避免 token 已失效时触发重复鉴权拦截。

i18n：

- 新增文案均使用 `zh.ts` / `en.ts` 扁平键。
- 密码规则文案已同时提供中英文。

## 8. 验收记录

已执行命令：

```powershell
$env:PYTHONNOUSERSITE='1'
conda run -p D:\conda\envs\scienceclaw pytest ScienceClaw/backend/tests/test_sessions_password.py -q
```

结果：`14 passed`

```powershell
$env:PYTHONNOUSERSITE='1'
conda run -p D:\conda\envs\scienceclaw pytest ScienceClaw/backend/tests/test_sessions_password.py ScienceClaw/backend/tests/test_sessions_vnc_route.py ScienceClaw/backend/tests/test_sessions_pdf_export.py -q
```

结果：`34 passed`

```powershell
cd D:\trae\ScienceClaw\ScienceClaw\frontend
npm run type-check
npm run test:run -- src/components/session-password/SessionPasswordDialogs.spec.ts src/composables/useSessionListUpdate.spec.ts
npm run test:run
npm run build
```

结果：

- `vue-tsc` 通过。
- 局部 Vitest：`6 passed`
- 完整 Vitest：`106 passed`
- Vite build 通过。

```powershell
git diff --check
```

结果：无空白错误；仅有既有 CRLF 提示。


- 已执行 `detect_changes(scope=all)`。
- 风险等级：HIGH。
- 影响流程：聊天、VNC、会话读取等跨社区流程。
- 覆盖方式：后端密码/VNC/PDF 回归、前端完整 Vitest、type-check、build。

运行态：

- 后端 OpenAPI 已不包含 `X-Session-Unlock-Token` / `unlock_token`。
- OpenAPI 已包含 `password/lock` 与 `password/lock-all`。
- Codex in-app Browser 打开 `http://localhost:5173/`，页面标题为 `ScienceClaw`。

## 9. 回滚说明

如需回滚：

1. 移除前端密码按钮、弹窗组件、API 方法、类型字段和 locale 文案。
2. 移除后端密码端点和 `_require_session_unlocked()` 门禁调用。
3. 从 `ScienceSession` 移除 `password_hash`、`password_hint`、`password_unlocked_by` 字段。
4. Mongo 中已存在的 `password_hash` / `password_hint` 字段不会影响旧代码读取，可后续用迁移脚本清理。
