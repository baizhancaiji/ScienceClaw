# PDF 导出施工单：大内容浅色打印 + 5 分钟缓存 + 完整国际化

**执行状态**：已登记到 `docs/current-active-execution-plans-zh.md`，按当前活跃施工单推进。
**登记日期**：2026-06-03
**当前结论**：采用后端 `sessions` 路由编排 sandbox 现有 REST 能力，不新增 sandbox 镜像内路由。

---

## 0. 硬性要求

1. 支持较大内容导出，前端提交的 `html + css` UTF-8 总体积上限为 50MB。
2. PDF 打印主题固定为浅色，不跟随当前深色主题。
3. PDF 页眉显示被导出的会话标题，最多 15 个字符，超出追加省略号。
4. PDF 页脚显示导出时间，精确到秒。
5. 同内容导出缓存保留 5 分钟，到期销毁。
6. 前后端必须完整国际化，用户可见文案必须走 i18n key。
7. 不允许把后端 `detail`、sandbox stderr、异常字符串、英文原始错误、接口原始返回直接展示给用户。

---

## 1. 当前代码基线

| 模块 | 当前实际情况 | 施工要求 |
|---|---|---|
| 前端入口 | `ScienceClaw/frontend/src/components/MessageFooter.vue` 已有 PDF 按钮，emit `convertToPdf` | 增加导出中/禁用态，所有 title/aria/toast 走 i18n |
| 消息 DOM | `ScienceClaw/frontend/src/components/ChatMessage.vue` 已有 `markdownRef`，指向渲染后的 `.markdown-content` | 读取 `markdownRef.innerHTML`，导出时只提交浅色打印 CSS |
| sessionId | `ChatMessage.vue` 已声明 `sessionId?: string`，`ChatPage.vue` 当前未传 | `ChatPage.vue` 传 `:session-id="sessionId"` |
| 旧占位行为 | `ChatPage.vue` 当前 `handleConvertToPdf()` 写入 `inputMessage.value = '转成pdf'` | 删除旧逻辑，不再把 PDF 请求发给 LLM |
| 前端样式 | `main.ts` 本地 import KaTeX/highlight CSS，`ChatMessage.vue` 引入 `chat-message-renderer.css` | 从同源 styleSheets 收集规则，过滤/覆盖 `.dark` 规则 |
| 后端路由 | `ScienceClaw/backend/route/sessions.py` 已有 `require_user`、`async_get_science_session()`、`_get_sandbox_rest_base()`、`Response` | 在同文件新增 PDF 端点、缓存、错误码和 sandbox 编排 |
| sandbox REST | 运行态已有 `/v1/file/write`、`/v1/shell/exec`、`/v1/file/download` | 复用现有接口写 HTML/脚本、执行 Playwright、下载 PDF |
| sandbox 浏览器 | 容器内 Playwright 可用，Chromium 路径为 `/usr/bin/chromium-browser` | 渲染脚本固定优先使用该路径 |

---

## 2. 架构

```text
ChatMessage.vue
  提取已渲染 HTML + 浅色 CSS + locale
        |
        v
POST /api/v1/sessions/{session_id}/export-pdf
        |
        v
sessions.py
  校验 session 归属
  计算 payload hash
  命中 5 分钟缓存则直接返回 PDF
  未命中则构造浅色 HTML
  写入 sandbox workspace
  执行 Playwright 生成 PDF
  保存 5 分钟缓存
        |
        v
Response(application/pdf)
        |
        v
前端 Blob 下载
```

---

## 3. 后端施工

### 3.1 修改文件

`ScienceClaw/backend/route/sessions.py`

### 3.2 请求模型

```python
class ExportPdfRequest(BaseModel):
    html: str = Field(..., min_length=1, description="Rendered assistant message innerHTML")
    css: str = Field(default="", description="Collected light print CSS")
    locale: str = Field(default="zh", description="Current UI locale")
```

要求：

1. 移除 `dark` 字段，不允许前端控制打印深浅主题。
2. `locale` 只接受 `zh`、`en`；未知值按 `en` 处理。

### 3.3 常量

```python
_PDF_EXPORT_MAX_PAYLOAD_BYTES = 50 * 1024 * 1024
_PDF_EXPORT_CACHE_TTL_SECONDS = 5 * 60
_PDF_EXPORT_TIMEOUT_SECONDS = 120.0
_PDF_EXPORT_CACHE_DIRNAME = "_pdf_export_cache"
_PDF_EXPORT_WORK_DIRNAME = "_pdf_export_work"
```

体积规则：

1. `len(body.html.encode("utf-8")) + len(body.css.encode("utf-8")) <= 50MB`。
2. 超限返回统一错误码 `PDF_EXPORT_PAYLOAD_TOO_LARGE`。
3. 不在错误响应中返回实际 HTML、CSS、stderr 或异常字符串。

### 3.4 错误响应规范

PDF 端点的非 PDF 响应必须统一为 JSON，不允许原始返回。

```json
{
  "code": "PDF_EXPORT_PAYLOAD_TOO_LARGE",
  "msg": "pdf_export.payload_too_large",
  "data": null
}
```

错误码清单：

| HTTP | code | msg i18n key |
|---|---|---|
| 401 | 由现有鉴权处理 | 前端映射现有登录文案 |
| 403 | `PDF_EXPORT_ACCESS_DENIED` | `pdf_export.access_denied` |
| 404 | `PDF_EXPORT_SESSION_NOT_FOUND` | `pdf_export.session_not_found` |
| 413 | `PDF_EXPORT_PAYLOAD_TOO_LARGE` | `pdf_export.payload_too_large` |
| 502 | `PDF_EXPORT_RENDER_FAILED` | `pdf_export.render_failed` |
| 502 | `PDF_EXPORT_INVALID_PDF` | `pdf_export.invalid_pdf` |
| 504 | `PDF_EXPORT_TIMEOUT` | `pdf_export.timeout` |
| 500 | `PDF_EXPORT_UNKNOWN_ERROR` | `pdf_export.unknown_error` |

后端日志可以记录调试信息，但用户响应只能返回 code 和 i18n key。

### 3.5 端点

路径：

```text
POST /api/v1/sessions/{session_id}/export-pdf
```

实现要求：

1. `current_user: User = Depends(require_user)`。
2. `session = await async_get_science_session(session_id)`。
3. 非 owner 返回 `PDF_EXPORT_ACCESS_DENIED`。
4. session 不存在返回 `PDF_EXPORT_SESSION_NOT_FOUND`。
5. 体积超过 50MB 返回 `PDF_EXPORT_PAYLOAD_TOO_LARGE`。
6. 导出时间在后端生成，使用当前服务器时区并精确到秒。
7. 会话标题从 `session.title` 取值，空标题使用 i18n key 对应默认标题。
8. 标题截断使用 `_truncate_pdf_header_title(title, limit=15)`。
9. 缓存 key 使用 `sha256(session_id + title + html + css + "light-v1")`。
10. 缓存命中且未过期时直接返回缓存 PDF。
11. 缓存未命中时调用 `_render_pdf_in_sandbox(...)`。
12. PDF 返回前校验首字节 `%PDF`。
13. 返回 `fastapi.responses.Response`，`media_type="application/pdf"`。

响应头：

```python
{
    "Content-Disposition": f'attachment; filename="scienceclaw-{session_id}.pdf"',
    "X-PDF-Export-Cache": "hit" 或 "miss",
}
```

### 3.6 HTML 包装函数

新增：

```python
def _build_pdf_html(
    html: str,
    css: str,
    *,
    header_title: str,
    exported_at_text: str,
    locale: str,
) -> str:
    ...
```

必须包含：

1. `<!doctype html>`。
2. `<html lang="{locale}">`。
3. 不出现 `class="dark"`。
4. CSP：`default-src 'self' data: blob:; img-src 'self' data: blob: http: https:; style-src 'unsafe-inline' 'self'; script-src 'none';`
5. 浅色固定变量：
   - `color-scheme: light`
   - `background: #ffffff`
   - `color: #111827`
6. `@page` 设置页眉页脚边距空间。
7. 文档内容包裹在 `<main class="markdown-content pdf-export-root">`。

禁止：

1. 使用用户当前 dark mode。
2. 默认引入 CDN。
3. 执行脚本。
4. 把原始错误、stderr 或异常内容注入 HTML。

### 3.7 页眉页脚

页眉页脚由 Playwright `page.pdf()` 的 `display_header_footer=True` 实现。

Header template：

```html
<div style="font-size:9px;width:100%;padding:0 14mm;color:#4b5563;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
  {escaped_header_title}
</div>
```

Footer template：

```html
<div style="font-size:9px;width:100%;padding:0 14mm;color:#6b7280;text-align:right;">
  {escaped_exported_at_text}
</div>
```

标题截断规则：

1. Python 按 Unicode 字符计数。
2. `len(title) <= 15` 原样。
3. `len(title) > 15` 使用 `title[:15] + "..."`。
4. HTML 输出必须转义。

导出时间：

1. 后端生成。
2. 精确到秒。
3. 文案走后端小型 locale 字典：
   - zh：`导出时间：YYYY-MM-DD HH:mm:ss`
   - en：`Exported at: YYYY-MM-DD HH:mm:ss`
4. 前端不得自行拼接页脚时间。

### 3.8 5 分钟缓存

缓存目录：

```text
/home/scienceclaw/{session_id}/_pdf_export_cache/{cache_key}.pdf
/home/scienceclaw/{session_id}/_pdf_export_cache/{cache_key}.json
```

metadata：

```json
{
  "created_at": 1780470000,
  "expires_at": 1780470300,
  "session_id": "..."
}
```

缓存规则：

1. 每次导出前调用 `_cleanup_expired_pdf_cache(session_id)`。
2. 命中未过期缓存时直接通过 sandbox `/v1/file/download` 下载 PDF。
3. 未命中时生成 PDF 并写入缓存目录。
4. 响应返回后注册 `BackgroundTasks`，在 5 分钟后删除本次 cache key 对应 PDF 和 metadata。
5. 若后端进程重启导致 background task 丢失，下一次导出必须通过懒清理删除过期缓存。
6. 临时工作目录 `_pdf_export_work/{nonce}` 在本次导出结束后清理，不保留 5 分钟。

### 3.9 sandbox 编排

新增 `_render_pdf_in_sandbox(...) -> bytes`。

输入：

1. `session_id`
2. `full_html`
3. `header_title`
4. `exported_at_text`
5. `cache_pdf_path`

流程：

1. `base = _get_sandbox_rest_base()`。
2. 写入 HTML 到 `_pdf_export_work/{nonce}/message.html`。
3. 写入渲染脚本到 `_pdf_export_work/{nonce}/render_pdf.py`。
4. `/v1/shell/exec` 执行：
   ```json
   {
     "command": "python <script_path> <html_path> <cache_pdf_path> <header_json_path>",
     "exec_dir": "/home/scienceclaw/{session_id}",
     "async_mode": false,
     "timeout": 120
   }
   ```
5. `/v1/file/download` 下载 `cache_pdf_path`。
6. 校验 `%PDF`。
7. 清理 `_pdf_export_work/{nonce}`。

### 3.10 Playwright 脚本

要求：

1. 使用 `playwright.sync_api.sync_playwright`。
2. Chromium executable 优先 `/usr/bin/chromium-browser`。
3. 启动参数：
   - `--no-sandbox`
   - `--disable-dev-shm-usage`
   - `--disable-gpu`
4. `page.emulate_media(media="print", color_scheme="light")`。
5. `page.set_content(html, wait_until="load")`。
6. 等待 `document.fonts.ready`。
7. 等待 500ms。
8. `page.pdf(...)`：
   - `format="A4"`
   - `print_background=True`
   - `display_header_footer=True`
   - `header_template=<escaped header template>`
   - `footer_template=<escaped footer template>`
   - margin 至少 top/bottom `18mm`，left/right `14mm`
9. finally 关闭 page/browser/playwright。
10. 脚本 stdout/stderr 只用于后端日志，不进入用户响应。

### 3.11 后端测试

新增：

`ScienceClaw/backend/tests/test_sessions_pdf_export.py`

覆盖：

1. 未认证返回 401。
2. 非 owner 返回 `PDF_EXPORT_ACCESS_DENIED`。
3. session 不存在返回 `PDF_EXPORT_SESSION_NOT_FOUND`。
4. `html + css` 超过 50MB 返回 `PDF_EXPORT_PAYLOAD_TOO_LARGE`。
5. 标题 15 字符截断。
6. 页脚时间精确到秒。
7. `dark` 不存在于请求模型和 HTML root。
8. cache miss 首次生成 PDF。
9. 5 分钟内相同 payload 命中缓存。
10. 过期缓存会被删除并重新生成。
11. sandbox timeout 返回 `PDF_EXPORT_TIMEOUT`。
12. 非 PDF 返回 `PDF_EXPORT_INVALID_PDF`。
13. 所有错误响应不包含 stderr、traceback、HTML、CSS、异常原文。

命令：

```powershell
$env:PYTHONNOUSERSITE='1'; conda run -p D:\conda\envs\scienceclaw python -m unittest ScienceClaw.backend.tests.test_sessions_pdf_export
```

---

## 4. 前端施工

### 4.1 API 层

修改：

`ScienceClaw/frontend/src/api/agent.ts`

新增：

```ts
export interface ExportPdfPayload {
  html: string;
  css: string;
  locale: 'zh' | 'en';
}

export async function exportMessagePdf(
  sessionId: string,
  payload: ExportPdfPayload,
): Promise<Blob> {
  const response = await apiClient.post(
    `/sessions/${sessionId}/export-pdf`,
    payload,
    {
      responseType: 'blob',
      timeout: 150000,
    },
  );
  return response.data as Blob;
}
```

要求：

1. 导出接口单独设置 150 秒 timeout，不使用全局 30 秒超时。
2. Blob 错误响应必须解析 JSON code，不允许直接 toast Blob 文本。

### 4.2 新增 composable

新增：

`ScienceClaw/frontend/src/composables/usePdfExport.ts`

职责：

1. 接收 `sessionId`、`markdownRef`、`locale`。
2. 提取 `markdownRef.innerHTML`。
3. 收集浅色打印 CSS。
4. 计算 `html + css` UTF-8 总体积，超过 50MB 前端直接提示 i18n 文案。
5. 调用 `exportMessagePdf()`。
6. 下载 Blob。
7. 暴露 `exporting` 与 `exportPdf()`。

CSS 规则：

1. 遍历 `document.styleSheets`。
2. 只读取同源可访问 `cssRules`。
3. 保留 `.markdown-content`、`.katex`、`.hljs`、`.mermaid`、`pre`、`code`、`table`、`img`、`svg`、`.code-block` 相关规则。
4. 跳过或覆盖 `.dark` 专用规则。
5. 追加浅色 fallback：
   - body/background 白色
   - 文本深色
   - 代码块浅灰背景
   - 表格边框浅灰
   - 图片/SVG 最大宽度 100%
   - 避免代码块、表格、图片被分页切断

错误处理：

1. 后端 code 映射到 i18n key。
2. 未识别 code 使用 `pdf_export.unknown_error`。
3. 不显示 `error.message`、`error.details`、接口 `detail`、Blob 原文。

下载要求：

1. 文件名：`scienceclaw-${sessionId}-${Date.now()}.pdf`。
2. 下载按钮重复点击时直接忽略。
3. `URL.revokeObjectURL(url)` 必须执行。

### 4.3 ChatMessage 集成

修改：

`ScienceClaw/frontend/src/components/ChatMessage.vue`

要求：

1. 引入 `usePdfExport`。
2. 引入 `useI18n`，读取 `locale` 和 `t`。
3. 不再读取 `useTheme` 参与 PDF 打印。
4. `handleConvertToPdf`：
   - 无 `props.sessionId` 或无 `markdownRef.value` 时 toast `t('pdf_export.unavailable')`。
   - 调用 `pdfExport.exportPdf(props.sessionId, markdownRef.value, locale.value)`。
5. `MessageFooter` 传入：
   - `:pdf-exporting="pdfExport.exporting.value"`
   - `:pdf-disabled="!props.sessionId || pdfExport.exporting.value"`
6. 所有新增 title、aria、toast 使用 i18n key。

### 4.4 MessageFooter 状态与国际化

修改：

`ScienceClaw/frontend/src/components/MessageFooter.vue`

新增 props：

```ts
pdfExporting?: boolean;
pdfDisabled?: boolean;
```

新增 i18n 使用：

```ts
const { t } = useI18n();
```

PDF 按钮要求：

1. `:disabled="pdfDisabled || pdfExporting"`。
2. `:title="pdfExporting ? t('pdf_export.exporting') : t('pdf_export.action')"`。
3. `:aria-label="pdfExporting ? t('pdf_export.exporting') : t('pdf_export.action')"`。
4. 导出中显示 loading 图标或现有 spinner。
5. 不再出现硬编码“转成PDF”“正在导出PDF”等中文原文。

### 4.5 ChatPage 接线

修改：

`ScienceClaw/frontend/src/pages/ChatPage.vue`

要求：

1. 给 `ChatMessage` 增加 `:session-id="sessionId"`。
2. 删除 `@convertToPdf="handleConvertToPdf"`。
3. 删除旧 `handleConvertToPdf()`。
4. 不再写入 `inputMessage.value = '转成pdf'`。

### 4.6 locales

修改：

1. `ScienceClaw/frontend/src/locales/zh.ts`
2. `ScienceClaw/frontend/src/locales/en.ts`

新增 key：

```ts
{
  'pdf_export.action': '导出 PDF',
  'pdf_export.exporting': '正在导出 PDF',
  'pdf_export.unavailable': '当前消息无法导出 PDF',
  'pdf_export.payload_too_large': '导出内容超过 50MB，无法生成 PDF',
  'pdf_export.access_denied': '无权导出该会话',
  'pdf_export.session_not_found': '会话不存在或已删除',
  'pdf_export.render_failed': 'PDF 生成失败，请稍后重试',
  'pdf_export.invalid_pdf': 'PDF 文件生成异常，请稍后重试',
  'pdf_export.timeout': 'PDF 生成超时，请稍后重试',
  'pdf_export.unknown_error': 'PDF 导出失败，请稍后重试',
  'pdf_export.success': 'PDF 已开始下载'
}
```

英文同 key 补英文文案。

### 4.7 前端测试

新增或扩展：

1. `ScienceClaw/frontend/src/components/MessageFooter.spec.ts`
2. `ScienceClaw/frontend/src/components/ChatMessage.spec.ts`
3. 新增 `ScienceClaw/frontend/src/composables/usePdfExport.spec.ts`

覆盖：

1. PDF 按钮 title/aria 使用 i18n。
2. 导出中按钮 disabled。
3. 超过 50MB 时不调用 API。
4. 后端错误 code 映射到 i18n key。
5. Blob 错误不原样显示。
6. 不传 dark。

命令：

```powershell
npm --prefix ScienceClaw/frontend run type-check
npm --prefix ScienceClaw/frontend run test:run -- MessageFooter ChatMessage usePdfExport
npm --prefix ScienceClaw/frontend run build
```

---

## 5. 集成验收

### 5.1 sandbox 能力复核

```powershell
docker exec scienceclaw-sandbox-1 sh -lc "python - <<'PY'
from playwright.sync_api import sync_playwright
import shutil
print('playwright-ok')
print(shutil.which('chromium-browser') or shutil.which('chromium') or shutil.which('google-chrome'))
PY"
```

期望输出包含：

```text
playwright-ok
/usr/bin/chromium-browser
```

### 5.2 真实接口 smoke

```powershell
Invoke-WebRequest `
  -Method POST `
  -Uri "http://127.0.0.1:12001/api/v1/sessions/<sessionId>/export-pdf" `
  -Headers @{ Authorization = "Bearer <token>" } `
  -ContentType "application/json" `
  -Body (@{
    html = "<h1>PDF Smoke</h1><pre><code>print('ok')</code></pre>"
    css = ".markdown-content{font-family:Arial,sans-serif} pre{background:#f3f4f6;padding:12px;color:#111827}"
    locale = "zh"
  } | ConvertTo-Json) `
  -OutFile ".\workspace\pdf-smoke.pdf"
```

验收：

1. `workspace/pdf-smoke.pdf` 文件头为 `%PDF`。
2. PDF 页眉包含 15 字符以内标题。
3. PDF 页脚包含秒级导出时间。
4. 打印内容为浅色主题。
5. 5 分钟内重复请求响应头 `X-PDF-Export-Cache` 为 `hit`。
6. 5 分钟后缓存文件被删除或下一次请求触发懒清理删除。

### 5.3 总体验证命令

```powershell
$env:PYTHONNOUSERSITE='1'; conda run -p D:\conda\envs\scienceclaw python -m unittest ScienceClaw.backend.tests.test_sessions_pdf_export
npm --prefix ScienceClaw/frontend run type-check
npm --prefix ScienceClaw/frontend run test:run -- MessageFooter ChatMessage usePdfExport
npm --prefix ScienceClaw/frontend run build
```

---

## 6. 实施顺序

### Step 1：后端错误码、请求模型和 50MB 限制

修改 `ScienceClaw/backend/route/sessions.py`：

1. 新增 `ExportPdfRequest`。
2. 新增 PDF 错误响应 helper。
3. 新增 50MB payload 校验。
4. 确保非 PDF 响应不包含原始异常或 stderr。

停止条件：

1. 401/403/404/413 单测通过。
2. 错误响应只包含 code、msg、data。

### Step 2：页眉页脚与浅色 HTML

实现：

1. `_truncate_pdf_header_title()`。
2. `_format_pdf_exported_at()`。
3. `_build_pdf_html()`。
4. Playwright header/footer template。
5. `page.emulate_media(media="print", color_scheme="light")`。

停止条件：

1. 标题 15 字符截断测试通过。
2. 页脚秒级时间测试通过。
3. HTML 不含 dark root。

### Step 3：5 分钟缓存

实现：

1. cache key。
2. cache metadata。
3. cache hit/miss。
4. background cleanup。
5. lazy cleanup。

停止条件：

1. 5 分钟内相同 payload 命中缓存。
2. 过期缓存被删除。
3. 临时 work 目录导出后清理。

### Step 4：sandbox 真实渲染

实现：

1. 写 HTML。
2. 写渲染脚本。
3. 执行 Playwright。
4. 下载 PDF。
5. 校验 `%PDF`。

停止条件：

1. 真实 PDF 可下载。
2. 页眉页脚存在。
3. 浅色打印生效。

### Step 5：前端 API 与 composable

实现：

1. `exportMessagePdf()`，timeout 150 秒。
2. `usePdfExport.ts`。
3. 50MB 前端校验。
4. Blob 错误 code 解析和 i18n 映射。

停止条件：

1. 超限不发请求。
2. 所有错误 toast 都来自 i18n key。
3. 不传 `dark`。

### Step 6：前端组件与 locales

实现：

1. `ChatMessage.vue` 接线。
2. `MessageFooter.vue` loading/disabled/i18n。
3. `ChatPage.vue` 删除旧占位事件。
4. `zh.ts`、`en.ts` 补全 key。

停止条件：

1. 页面不再出现硬编码“转成PDF”新增文案。
2. `inputMessage.value = '转成pdf'` 不存在。
3. type-check/build 通过。

### Step 7：端到端验收

执行：

1. 后端单测。
2. 前端单测。
3. 前端 type-check/build。
4. 真实浏览器点击下载。
5. 复测缓存命中和 5 分钟销毁。

停止条件：

1. PDF 下载成功。
2. 最大 50MB payload 路径可处理或给出 i18n 错误。
3. 页眉页脚符合要求。
4. 用户界面无任何原始错误返回。

---

## 7. 风险与处理

| 风险 | 等级 | 处理 |
|---|---|---|
| 50MB payload 导致超时 | 中 | 导出接口独立 150 秒前端 timeout，后端/sandbox 120 秒 timeout |
| 缓存未及时删除 | 中 | BackgroundTasks + 每次导出前懒清理 |
| 暗色 CSS 泄漏到打印 | 中 | 前端过滤 `.dark`，后端强制浅色变量，Playwright 强制 light media |
| 页眉标题含 HTML | 中 | 后端截断后 HTML escape |
| 用户看到原始错误 | 高 | 后端只返回 code/i18n key，前端只展示映射文案 |
| 大 PDF 非法或损坏 | 中 | 后端校验 `%PDF`，失败返回 `PDF_EXPORT_INVALID_PDF` |

---

## 8. 不做事项

1. 不新增 `ScienceClaw/sandbox/api.py`。
2. 不修改 AIO sandbox 基础镜像内部 FastAPI 源码。
3. 不默认依赖 CDN。
4. 不把“转成pdf”发送给 LLM。
5. 不在 PDF 中执行任意脚本。
6. 不支持暗色打印主题。
7. 不把缓存保留超过 5 分钟。
