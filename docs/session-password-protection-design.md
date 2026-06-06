# 会话密码保护功能施工单

## 1. 施工目标

为 ScienceClaw 会话增加密码保护能力。受保护会话在未验证密码前，不允许前端或直接 API 读取会话内容、沙盒文件、导出结果或继续聊天。

功能范围：

- 设置、修改、移除会话密码。
- 保存可选密码提示。
- 进入受保护会话时验证密码。
- 通过当前登录账户密码重置或移除会话密码。
- 会话列表显示锁图标。
- 后端统一拦截未解锁的会话内容访问。

安全边界：

- 前端弹窗只负责用户体验。
- 后端必须阻止未解锁请求返回 `events`、文件、导出、VNC、chat 等会话内容或操作能力。
- 当前场景仍按单用户本地部署处理，但保留 `require_user` 和 owner 校验。

## 2. 施工文件

后端：

- `ScienceClaw/backend/deepagent/sessions.py`
- `ScienceClaw/backend/route/sessions.py`
- `ScienceClaw/backend/tests/test_sessions_password.py`

前端：

- `ScienceClaw/frontend/src/api/agent.ts`
- `ScienceClaw/frontend/src/types/response.ts`
- `ScienceClaw/frontend/src/pages/ChatPage.vue`
- `ScienceClaw/frontend/src/components/SessionItem.vue`
- `ScienceClaw/frontend/src/components/session-password/*.vue`
- `ScienceClaw/frontend/src/locales/zh.ts`
- `ScienceClaw/frontend/src/locales/en.ts`

## 3. 当前代码约束

- 后端 `ApiResponse.code` 成功值是 `0`。新增端点成功时使用 `return ApiResponse(data={...})`，不要返回 `code=200`。
- 前端 `apiClient` 会把 `response.data.code !== 0` 当错误处理。
- `async_get_science_session()` 找不到会话时抛 `ScienceSessionNotFoundError`，不是返回 `None`。
- `ScienceSession.save()` 当前只 `$set` 固定字段。新增字段必须加入保存链路。
- 会话列表后端返回结构是 `data.sessions`，前端 `listSessions()` 已按此结构解包。
- 前端响应类型在 `ScienceClaw/frontend/src/types/response.ts`。
- 前端 i18n 当前是扁平字典键，新增文案继续使用扁平键，不引入嵌套 `sessionPassword.*`。
- `ChatPage.vue` 当前 `restoreSession()` 会在加载详情后重放 `session.events`，密码判断必须发生在重放事件之前。
- `SessionItem.vue` 已有 indicators row，锁图标加在现有指标区内，不重写列表项结构。

## 4. 后端施工步骤

### 4.1 扩展会话模型

修改 `ScienceClaw/backend/deepagent/sessions.py`。

在 `ScienceSession` dataclass 增加字段：

```python
password_hash: Optional[str] = None
password_hint: Optional[str] = None
password_unlocked_by: Dict[str, int] = field(default_factory=dict, repr=False)
```

持久化要求：

- `ScienceSession.save()` 的 `update_data` 加入 `password_hash`、`password_hint`。
- `async_get_science_session()` 从 Mongo 文档恢复 `password_hash`、`password_hint`。
- `async_list_science_sessions()` 的 projection 加入 `password_hash`，构造 `ScienceSession` 时恢复该字段。
- `async_create_science_session()` 可不写空密码字段，但对象默认值必须为空。

解锁状态：

- `password_unlocked_by` 只作为服务端内存状态，不写入 Mongo。
- key 使用当前用户 ID。
- value 使用过期时间戳，例如当前时间加 30 分钟。
- 修改、移除、重置密码后清空该会话的解锁状态。

### 4.2 增加密码工具函数和请求模型

修改 `ScienceClaw/backend/route/sessions.py`。

新增导入：

```python
import bcrypt
```

新增请求模型：

```python
class SetPasswordRequest(BaseModel):
    password: str
    hint: Optional[str] = None

class UpdatePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    hint: Optional[str] = None

class RemovePasswordRequest(BaseModel):
    password: str

class VerifyPasswordRequest(BaseModel):
    password: str

class ResetPasswordRequest(BaseModel):
    account_password: str
    new_password: Optional[str] = None
    hint: Optional[str] = None
```

新增公共函数：

```python
def _hash_session_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def _verify_session_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
```

新增 owner 获取函数：

```python
async def _get_owned_session_or_404(
    session_id: str,
    current_user: User,
):
    try:
        session = await async_get_science_session(session_id)
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return session
```

注意：如果写成 FastAPI dependency，函数参数仍需显式包含 `session_id: str` 和 `current_user: User = Depends(require_user)`。

### 4.3 实现解锁校验

在 `ScienceClaw/backend/route/sessions.py` 增加：

```python
_SESSION_PASSWORD_UNLOCK_TTL_SECONDS = 30 * 60

def _session_has_password(session: Any) -> bool:
    return bool(getattr(session, "password_hash", None))

def _is_session_unlocked(session: Any, current_user: User) -> bool:
    if not _session_has_password(session):
        return True
    unlocked_by = getattr(session, "password_unlocked_by", None)
    if not isinstance(unlocked_by, dict):
        return False
    expires_at = int(unlocked_by.get(current_user.id) or 0)
    return expires_at > int(time.time())

def _mark_session_unlocked(session: Any, current_user: User) -> None:
    unlocked_by = getattr(session, "password_unlocked_by", None)
    if not isinstance(unlocked_by, dict):
        unlocked_by = {}
        setattr(session, "password_unlocked_by", unlocked_by)
    unlocked_by[current_user.id] = int(time.time()) + _SESSION_PASSWORD_UNLOCK_TTL_SECONDS

def _clear_session_unlocks(session: Any) -> None:
    setattr(session, "password_unlocked_by", {})

def _require_session_unlocked(session: Any, current_user: User) -> None:
    if not _is_session_unlocked(session, current_user):
        raise HTTPException(status_code=403, detail="Session password required")
```

### 4.4 实现密码端点

在 `ScienceClaw/backend/route/sessions.py` 新增以下端点，放在 `/{session_id}` CRUD 区域附近，且不要破坏 `/skills`、`/tools` 等静态路由顺序。

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| `POST` | `/sessions/{session_id}/password` | 首次设置密码 |
| `PUT` | `/sessions/{session_id}/password` | 校验旧密码后修改密码 |
| `POST` | `/sessions/{session_id}/password/remove` | 校验当前密码后移除密码 |
| `POST` | `/sessions/{session_id}/verify-password` | 校验密码并标记本用户本会话已解锁 |
| `GET` | `/sessions/{session_id}/password-hint` | 返回明文提示 |
| `POST` | `/sessions/{session_id}/reset-password` | 校验账户密码后重置或移除会话密码 |

响应要求：

```python
return ApiResponse(data={"has_password": True})
return ApiResponse(data={"has_password": False})
return ApiResponse(data={"valid": True})
return ApiResponse(data={"hint": session.password_hint})
```

错误处理要求：

- 密码长度小于 4，返回 400。
- 会话不存在，返回 404。
- 非 owner，返回 403。
- 当前密码错误，返回 400。
- 已有密码时重复设置，返回 400。
- 无密码时修改或移除，返回 400。
- 账户密码错误，返回 400。

账户密码校验：

- 查询 `users` collection 的当前用户文档。
- 使用 `users.password_hash` 与 `account_password` 做 bcrypt 校验。
- `new_password` 为空表示移除会话密码，并清空 `password_hint`。
- `new_password` 非空表示设置新会话密码；`hint` 未传时清空旧提示。

### 4.5 扩展列表和详情返回

修改 `ListSessionItem`：

```python
has_password: bool = Field(default=False, description="Whether password protected")
```

修改 `_session_to_list_item()`：

```python
has_password=_session_has_password(session)
```

修改 `GetSessionData`：

```python
has_password: bool = Field(default=False, description="Whether password protected")
locked: bool = Field(default=False, description="Whether current user must verify password")
```

修改 `get_session()`：

- owner 校验保持不变。
- 计算 `locked = _session_has_password(session) and not _is_session_unlocked(session, current_user)`。
- `locked=True` 时返回元数据，但 `events=[]`。
- `locked=False` 时返回完整 `events`。

### 4.6 统一保护会话内容端点

以下端点在读取或操作会话内容前必须调用 `_require_session_unlocked(session, current_user)`：

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

- 第一版禁止分享受密码保护的会话。
- `share_session` 如发现 `_session_has_password(session)`，返回 400。
- 已分享会话设置密码时，应自动取消分享或返回 400 要求先取消分享。优先选择自动取消分享并 `session.is_shared = False`，避免公开链接继续泄露内容。

## 5. 前端施工步骤

### 5.1 扩展类型

修改 `ScienceClaw/frontend/src/types/response.ts`：

```typescript
export interface GetSessionResponse {
  // existing fields
  has_password?: boolean;
  locked?: boolean;
}

export interface ListSessionItem {
  // existing fields
  has_password?: boolean;
}
```

### 5.2 增加 API 方法

修改 `ScienceClaw/frontend/src/api/agent.ts`。

新增类型：

```typescript
export interface SessionPasswordStatus {
  has_password: boolean;
  locked?: boolean;
}

export interface VerifySessionPasswordResult {
  valid: boolean;
}

export interface SessionPasswordHint {
  hint: string | null;
}
```

新增方法，全部返回 `response.data.data`：

- `setSessionPassword(sessionId, { password, hint })`
- `updateSessionPassword(sessionId, { old_password, new_password, hint })`
- `removeSessionPassword(sessionId, { password })`
- `verifySessionPassword(sessionId, { password })`
- `getSessionPasswordHint(sessionId)`
- `resetSessionPassword(sessionId, { account_password, new_password, hint })`

组件错误处理读取 `error.message`，不要只读 `error.response?.data?.detail`。

### 5.3 增加 i18n 文案

修改 `ScienceClaw/frontend/src/locales/zh.ts` 和 `ScienceClaw/frontend/src/locales/en.ts`。

使用扁平键，例如：

```typescript
'Password protected': '已设置密码保护',
'Set session password': '设置会话密码',
'Change session password': '修改会话密码',
'Remove session password': '移除会话密码',
'Verify session password': '验证会话密码',
'Enter session password': '请输入会话密码',
'Password hint': '密码提示',
'Forgot session password?': '忘记会话密码？',
'Account password': '账户密码',
'Session password required': '需要验证会话密码',
'Incorrect session password': '会话密码错误',
'Session password set': '会话密码已设置',
'Session password changed': '会话密码已修改',
'Session password removed': '会话密码已移除',
'Reset session password': '重置会话密码',
```

英文文件补齐同名英文键。

### 5.4 会话列表显示锁图标

修改 `ScienceClaw/frontend/src/components/SessionItem.vue`。

施工点：

- `lucide-vue-next` 导入增加 `Lock`。
- 在现有 indicators row 内增加：

```vue
<Lock
  v-if="session.has_password"
  :size="12"
  class="text-amber-500"
  :title="t('Password protected')"
/>
```

不要新增点击行为。

### 5.5 增加密码弹窗组件

创建目录：

```text
ScienceClaw/frontend/src/components/session-password/
```

建议组件：

- `SessionPasswordDialog.vue`：设置、修改、移除密码。
- `VerifySessionPasswordDialog.vue`：进入会话时验证密码，显示提示和忘记密码入口。
- `ResetSessionPasswordDialog.vue`：通过账户密码重置会话密码。

表单要求：

- 密码最少 4 个字符。
- 设置/修改/重置新密码时需要二次确认。
- hint 最大 100 字符。
- hint 明确提示“不要包含密码本身”。
- loading 状态禁用提交按钮。
- 错误消息使用 `error.message || t('...')`。
- 成功后 emit `success`，由父组件刷新会话状态。

### 5.6 ChatPage 接入验证流

修改 `ScienceClaw/frontend/src/pages/ChatPage.vue`。

新增状态：

```typescript
const sessionHasPassword = ref(false)
const showVerifyPasswordDialog = ref(false)
const showSessionPasswordDialog = ref(false)
```

在 `restoreSession()` 中，`agentApi.getSession(restoreTarget)` 成功后、重放 `session.events` 前插入：

```typescript
sessionHasPassword.value = !!session.has_password

if (session.has_password && session.locked) {
  title.value = session.title || title.value
  showVerifyPasswordDialog.value = true
  return
}
```

验证成功回调：

```typescript
const handleSessionPasswordVerified = async () => {
  showVerifyPasswordDialog.value = false
  await restoreSession()
}
```

取消验证：

```typescript
const handleSessionPasswordCancelled = () => {
  showVerifyPasswordDialog.value = false
  router.replace('/')
}
```

右上角 header actions 中增加密码管理按钮，放在搜索、分享、文件按钮同一区域：

- 无密码：显示开锁/设置按钮，点击打开设置模式。
- 有密码：显示锁按钮，点击打开管理菜单或管理弹窗。

密码状态变更成功后：

- 更新 `sessionHasPassword`。
- 触发左侧会话列表刷新或通过已有 session update 机制更新当前项。

## 6. 后端测试单

新增 `ScienceClaw/backend/tests/test_sessions_password.py`。

覆盖项：

- 未登录访问密码端点返回 401。
- 非 owner 访问返回 403。
- 不存在 session 返回 404。
- 设置密码后 Mongo 文档存在 `password_hash`，且不保存明文。
- `async_get_science_session()` 能恢复密码字段。
- `async_list_science_sessions()` 能恢复列表所需 `password_hash`。
- 会话列表返回 `has_password=true`。
- 未解锁获取详情返回 `has_password=true`、`locked=true`、`events=[]`。
- 验证密码错误返回 `valid=false` 或 400，但不得解锁。
- 验证密码正确后详情返回完整 `events`。
- 修改密码后旧密码失效，新密码有效。
- 移除密码后 `has_password=false`，`password_hint` 清空。
- 账户密码重置成功后旧会话密码失效。
- 账户密码错误时重置返回 400。
- 未解锁访问 files/export/chat/vnc/share 等受保护端点返回 403。
- 有密码会话不能公开分享。

运行命令：

```powershell
$env:PYTHONNOUSERSITE = "1"
conda run -p D:\conda\envs\scienceclaw pytest ScienceClaw/backend/tests/test_sessions_password.py
```

## 7. 前端验证单

至少手工验证：

- 会话列表中受保护会话显示锁图标。
- 点击受保护会话后，页面不显示历史消息，先显示验证弹窗。
- 输入错误密码后不能加载消息。
- 输入正确密码后加载历史消息。
- 刷新页面后需要重新验证或在 TTL 内保持解锁，按后端实现确认。
- 设置密码后当前按钮状态和左侧锁图标立即更新。
- 修改密码后旧密码不能再解锁。
- 移除密码后进入会话不再弹验证。
- 忘记密码流程用账户密码可重置或移除会话密码。
- 中英文切换后新增文案都有翻译。

## 8. 验收标准

后端验收：

- 所有新增端点遵循 `ApiResponse.code=0` 成功约定。
- 未解锁时，直接调用受保护资源 API 不能拿到会话内容。
- `password_hash` 不包含明文密码。
- `password_hint` 可返回但不随详情接口默认泄露。
- 受密码保护会话不能通过公开分享绕过保护。

前端验收：

- TypeScript 类型通过。
- 新增文案全部走 i18n。
- `ChatPage.restoreSession()` 不会在未验证时重放 `events`。
- 锁图标不破坏现有 SessionItem 布局。
- 错误提示能显示当前 `apiClient` 抛出的 `ApiError.message`。

## 9. 回滚方案

如需回滚：

1. 移除前端新增密码按钮、弹窗组件、API 方法、类型字段和 locale 文案。
2. 移除后端新增密码端点和门禁调用。
3. 从 `ScienceSession` 移除 `password_hash`、`password_hint`、`password_unlocked_by` 字段。
4. 保留 Mongo 中已存在的 `password_hash` / `password_hint` 字段不影响旧代码读取，可后续用迁移脚本清理。

## 10. 施工顺序

1. 后端会话模型持久化链路。
2. 后端密码工具函数、请求模型、密码端点。
3. 后端 `has_password` / `locked` 返回。
4. 后端会话内容端点统一门禁。
5. 后端测试。
6. 前端类型和 API。
7. 前端 i18n。
8. 前端 `SessionItem.vue` 锁图标。
9. 前端密码弹窗。
10. 前端 `ChatPage.vue` 验证流和管理按钮。
11. 手工验收。

## 11. 工时估算

| 任务 | 估算 | 说明 |
| --- | ---: | --- |
| 后端模型持久化链路 | 1.0h | dataclass、save、get/list/projection/cache |
| 后端密码端点 | 2.5h | bcrypt、请求模型、错误处理 |
| 后端统一解锁门禁 | 2.0h | 详情、chat、files、export、share 等端点 |
| 后端测试 | 2.0h | owner、锁定、解锁、资源端点 |
| 前端 API 和类型 | 0.5h | `agent.ts`、`response.ts` |
| 前端 i18n | 0.5h | zh/en 扁平键 |
| 前端会话列表锁图标 | 0.5h | 基于现有 indicators row |
| 前端 ChatPage 验证流 | 1.5h | 插入 restoreSession 早返回逻辑 |
| 前端弹窗组件 | 2.5h | 设置、验证、重置 |
| 前端测试/手工验收 | 1.5h | 受保护会话完整流程 |
| 总计 | 14.5h | 以后端真实门禁为准 |
