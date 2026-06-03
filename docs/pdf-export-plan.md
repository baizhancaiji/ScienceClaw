# 方案 A 实现细则：Playwright 后端 PDF 导出

**执行状态**：已登记到 `docs/current-active-execution-plans-zh.md`，按当前活跃施工单推进。

**登记日期**：2026-06-03

---

## 0. 现状确认

| 项 | 状态 |
|---|---|
| 后端容器 Python Playwright | ✅ 已安装 `playwright==1.58.0` |
| 后端容器 Chromium 二进制 | ❌ 未安装（需 `playwright install chromium`） |
| Sandbox 容器 Python Playwright | ✅ 已安装 `playwright==1.58.0` |
| Sandbox 容器 Chromium 二进制 | ✅ `/usr/bin/chromium-browser`，PDF 生成已验证（5812 bytes） |
| 前端 CSS（chat-message-renderer.css） | ✅ 679 行，含 KaTeX/Mermaid/代码块/表格样式 |
| 前端 ChatMessage.vue markdownRef | ✅ `ref<HTMLElement | null>`，指向已渲染 DOM |
| 前端现有"转PDF"按钮 | ✅ 当前仅注入 `inputMessage = '转成pdf'` |

**关键决策**：PDF 渲染服务放在 **sandbox 容器**而非 backend 容器——sandbox 已有 Chromium + Playwright + CJK 字体，零额外安装。

---

## 1. 架构总览

```
前端 (ChatMessage.vue)
  │  点击"转为PDF"
  │  提取 markdownRef.innerHTML + computed styles
  ▼
后端 (sessions.py)
  │  POST /sessions/{id}/export-pdf
  │  转发 HTML+CSS 到 sandbox
  ▼
Sandbox (sandbox:8080)
  │  POST /v1/render-pdf
  │  Playwright chromium → page.pdf()
  │  返回 PDF binary
  ▼
后端 → 前端
  │  StreamingResponse(pdf_bytes)
  ▼
前端：自动下载 PDF 文件
```

---

## 2. 前端改动（4 个文件）

### 2.1 `src/api/agent.ts` — 新增 API 调用

```typescript
export async function exportMessagePdf(
  sessionId: string,
  payload: { html: string; css: string; dark: boolean }
): Promise<Blob> {
  const response = await apiClient.post(
    `/sessions/${sessionId}/export-pdf`,
    payload,
    { responseType: 'blob' }
  );
  return response.data as Blob;
}
```

### 2.2 `src/composables/usePdfExport.ts` — 新增 composable（核心）

```typescript
// 职责：
// 1. 从 markdownRef 提取 innerHTML
// 2. 收集渲染所需的 CSS（内联关键样式）
// 3. 调用 API 生成 PDF
// 4. 触发浏览器下载

export function usePdfExport() {
  const exporting = ref(false);

  const extractMessageHtml = (markdownRef: HTMLElement): { html: string; css: string } => {
    // 1. 克隆 markdownRef.innerHTML（已渲染的 DOM，含 SVG mermaid 图表）
    const html = markdownRef.innerHTML;

    // 2. 收集 CSS：提取 <style> 标签中 .markdown-content 相关规则
    //    + chat-message-renderer.css 中的规则
    //    + KaTeX CSS（从 <link> 或 <style> 中提取）
    //    + hljs 代码高亮 CSS
    const css = collectRenderCss();

    return { html, css };
  };

  const collectRenderCss = (): string => {
    // 策略：遍历 document.styleSheets，收集包含以下选择器的规则：
    //   .markdown-content, .katex, .hljs, .mermaid, pre, code, table
    // 去重合并为一个 CSS 字符串
  };

  const exportPdf = async (sessionId: string, markdownRef: HTMLElement, dark: boolean) => {
    exporting.value = true;
    try {
      const { html, css } = extractMessageHtml(markdownRef);
      const blob = await exportMessagePdf(sessionId, { html, css, dark });
      // 触发下载
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `chat-${sessionId}-${Date.now()}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      exporting.value = false;
    }
  };

  return { exporting, exportPdf };
}
```

**CSS 收集策略**（详细）：

```
收集优先级：
1. document.styleSheets 中含 .markdown-content 选择器的规则 → 必选
2. 含 .katex 选择器的规则 → 必选（公式）
3. 含 .hljs 选择器的规则 → 必选（代码高亮）
4. 含 .mermaid 选择器的规则 → 必选（图表）
5. 通用 reset/base 规则 → 可选（Playwright 自带默认样式）

实现方式：
- 遍历 document.styleSheets
- 对每个 sheet，尝试 sheet.cssRules（同源可访问）
- 跨域 stylesheet（CDN）跳过，改用硬编码的必要规则
- KaTeX CSS 如果是 CDN 加载的，需要硬编码一份或改为本地引入
```

### 2.3 `src/components/ChatMessage.vue` — 改动极小

```diff
- const handleConvertToPdf = () => {
-   emit("convertToPdf");
- };

+ const handleConvertToPdf = async () => {
+   if (!markdownRef.value) return;
+   await pdfExport.exportPdf(sessionId, markdownRef.value, isDark.value);
+ };
```

需要：
- 注入 `sessionId` prop（从 ChatPage 传入）
- 引入 `usePdfExport` composable
- 引入 `isDark` 状态（从主题 composable 或 CSS 媒体查询判断）

### 2.4 `src/pages/ChatPage.vue` — 传递 sessionId

```diff
  <ChatMessage
    :message="group.message"
+   :session-id="sessionId"
    ...
  />
```

移除 `handleConvertToPdf` 中的 `inputMessage.value = '转成pdf'`。

---

## 3. 后端改动（2 个文件）

### 3.1 `route/sessions.py` — 新增 PDF 导出端点

```python
@router.post("/{session_id}/export-pdf")
async def export_message_pdf(
    session_id: str,
    body: ExportPdfRequest,
    current_user: User = Depends(get_current_user),
):
    """
    将前端提交的单条助手消息 HTML+CSS 渲染为 PDF。
    实际渲染委托给 sandbox 容器的 Playwright 服务。
    """
    # 1. 权限校验
    session = await async_get_science_session(session_id)
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # 2. 构造完整 HTML 文档
    full_html = build_pdf_html(body.html, body.css, body.dark)

    # 3. 调用 sandbox 渲染服务
    pdf_bytes = await call_sandbox_render_pdf(full_html)

    # 4. 流式返回 PDF
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="chat-{session_id}.pdf"'
        },
    )
```

**Pydantic Model**：

```python
class ExportPdfRequest(BaseModel):
    html: str = Field(..., description="助手消息的 innerHTML")
    css: str = Field("", description="渲染所需的 CSS")
    dark: bool = Field(False, description="是否暗色主题")
```

**HTML 模板构建**：

```python
def build_pdf_html(html: str, css: str, dark: bool) -> str:
    theme_class = "dark" if dark else ""
    return f"""<!DOCTYPE html>
<html lang="zh-CN" class="{theme_class}">
<head>
  <meta charset="UTF-8">
  <style>
    /* Base reset */
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      margin: 20px;
      line-height: 1.6;
      color: {'#e5e7eb' if dark else '#1f2937'};
      background: {'#1e1e1e' if dark else '#ffffff'};
    }}
    /* App CSS */
    {css}
  </style>
</head>
<body>
  <div class="markdown-content" style="padding: 0;">
    {html}
  </div>
</body>
</html>"""
```

### 3.2 `route/sessions.py` — Sandbox API 调用

```python
async def call_sandbox_render_pdf(html: str) -> bytes:
    """调用 sandbox 的 Playwright PDF 渲染接口"""
    import httpx

    sandbox_url = settings.SANDBOX_REST_URL  # http://sandbox:8080

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{sandbox_url}/v1/render-pdf",
            json={"html": html},
        )
        resp.raise_for_status()
        return resp.content
```

---

## 4. Sandbox 改动（1 个文件）

### 4.1 Sandbox API 新增端点

**位置**：sandbox 的 FastAPI/Flask 路由文件

```python
from playwright.sync_api import sync_playwright
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()

class RenderPdfRequest(BaseModel):
    html: str = Field(..., description="完整 HTML 文档")

# 全局 Playwright 浏览器实例（懒加载单例）
_browser = None

def _get_browser():
    global _browser
    if _browser is None or not _browser.is_connected():
        pw = sync_playwright().start()
        _browser = pw.chromium.launch(
            headless=True,
            executable_path="/usr/bin/chromium-browser",
            args=["--no-sandbox", "--disable-gpu"],
        )
    return _browser

@router.post("/v1/render-pdf")
def render_pdf(body: RenderPdfRequest):
    """接收 HTML，返回 PDF bytes"""
    browser = _get_browser()
    page = browser.new_page()

    try:
        page.set_content(body.html, wait_until="networkidle")
        # 等待 Mermaid/图片等异步渲染完成
        page.wait_for_timeout(500)

        pdf_bytes = page.pdf(
            format="A4",
            margin={"top": "20mm", "bottom": "20mm", "left": "15mm", "right": "15mm"},
            print_background=True,
            display_header_footer=False,
        )
    finally:
        page.close()

    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
    )
```

**关键细节**：

| 项 | 说明 |
|---|---|
| 浏览器单例 | 避免每次请求启动 Chromium（冷启动 ~2s，复用 <100ms） |
| `executable_path` | sandbox 中 Chromium 在 `/usr/bin/chromium-browser` |
| `--no-sandbox` | 容器内以 root 运行，必须禁用 Chromium 沙箱 |
| `wait_until="networkidle"` | 等待异步资源加载完成 |
| `wait_for_timeout(500)` | 额外 500ms 等待 Mermaid/图片渲染 |
| `print_background=True` | 保留代码块/表格背景色 |
| 内存泄漏防护 | `page.close()` 在 finally 中确保执行 |

---

## 5. 样式处理（关键难点）

### 5.1 KaTeX CSS

**问题**：KaTeX CSS 通常从 CDN 加载（`<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@x.x.x/dist/katex.min.css">`），前端 `document.styleSheets` 无法读取跨域 CSS 规则。

**解决方案**：

```
方案 A（推荐）：将 KaTeX CSS 改为本地引入
  - npm install katex → node_modules/katex/dist/katex.min.css
  - 在 main.ts 或 chat-message-renderer.css 中 @import
  - 好处：前端可读取，PDF 可内联

方案 B：硬编码一份 KaTeX CSS 到 build_pdf_html()
  - 从 node_modules/katex/dist/katex.min.css 读取
  - 写入后端模板
  - 好处：零前端改动，但需同步版本

方案 C：PDF 渲染时从 CDN 加载
  - 在 build_pdf_html 的 <head> 中加 <link>
  - Playwright wait_until="networkidle" 会等待加载
  - 好处：最简单，但依赖网络，sandbox 容器需能访问外网
```

**推荐方案 C**：最简单，sandbox 容器已有外网访问能力（`WEBSEARCH_URL` 配置说明可联网）。如果 CDN 不可达再切方案 A。

### 5.2 hljs 代码高亮 CSS

同 KaTeX——如果当前是 CDN 引入，PDF HTML 中加 `<link>` 让 Playwright 加载即可。

### 5.3 暗色主题

`build_pdf_html()` 的 `<html class="dark">` 会匹配 CSS 中的 `.dark .xxx` 选择器，样式自动切换。

---

## 6. 交互流程（UX）

```
1. 用户点击助手消息底部的"转为PDF"按钮
2. 按钮变为 loading 状态（exporting = true）
3. 前端提取 innerHTML + CSS → 发送到后端
4. 后端转发到 sandbox → Playwright 渲染 → 返回 PDF
5. 前端收到 Blob → 自动下载 PDF 文件
6. 按钮恢复常态

预估延迟：
  - 首次请求（冷启动浏览器）：~3s
  - 后续请求（复用浏览器实例）：~1-2s
  - 网络传输：~200ms（单条消息 HTML 体积小）
  - 总计：~1.5-3s
```

---

## 7. 文件变更清单

| 文件 | 变更类型 | 行数估算 |
|---|---|---|
| `frontend/src/composables/usePdfExport.ts` | **新增** | ~100 行 |
| `frontend/src/api/agent.ts` | 修改（+1 函数） | +10 行 |
| `frontend/src/components/ChatMessage.vue` | 修改（替换 handleConvertToPdf） | +15 -5 行 |
| `frontend/src/pages/ChatPage.vue` | 修改（传 sessionId，删旧逻辑） | +3 -5 行 |
| `backend/route/sessions.py` | 修改（+1 端点 + 2 辅助函数） | +80 行 |
| `sandbox/api.py`（或等效路由文件） | 修改（+1 端点 + 浏览器单例） | +60 行 |
| **总计** | | **~260 行** |

---

## 8. 实现步骤（按顺序）

### Step 1：Sandbox PDF 渲染端点（后端基础设施）
- 找到 sandbox API 路由文件
- 新增 `POST /v1/render-pdf` 端点
- 实现浏览器单例 + PDF 生成
- 手动 curl 测试：发送 HTML → 返回 PDF
- **验收**：curl 发送含 Mermaid+代码块的 HTML → 下载的 PDF 文本可选中

### Step 2：后端 Sessions 端点
- `route/sessions.py` 新增 `POST /{session_id}/export-pdf`
- 实现 `build_pdf_html()` + `call_sandbox_render_pdf()`
- 权限校验 + 流式返回
- **验收**：httpie/POSTMAN 发送 HTML+CSS → 下载 PDF

### Step 3：前端 API 层
- `agent.ts` 新增 `exportMessagePdf()`
- **验收**：无（被后续步骤覆盖）

### Step 4：前端 usePdfExport composable
- 新增 `usePdfExport.ts`
- 实现 `extractMessageHtml()` + `collectRenderCss()`
- 实现 `exportPdf()` 下载逻辑
- **验收**：console.log 输出提取的 HTML/CSS 内容正确

### Step 5：前端组件集成
- ChatMessage.vue 替换 handleConvertToPdf
- ChatPage.vue 传 sessionId + 移除旧逻辑
- **验收**：点击"转为PDF" → 浏览器自动下载 PDF → PDF 中 Mermaid 图表/代码块/公式/表格正常显示 → 文本可选中复制

### Step 6：边界处理
- exporting 状态：按钮 loading 态
- 错误处理：sandbox 不可达、超时、渲染失败 → toast 提示
- 大消息处理：HTML 超过 5MB 时提示"内容过长"
- 并发控制：同一消息不重复提交

---

## 9. 风险与对策

| 风险 | 概率 | 影响 | 对策 |
|---|---|---|---|
| Sandbox Chromium 崩溃/内存泄漏 | 中 | PDF 生成失败 | 浏览器单例 + 健康检查 + 超时重启 |
| CDN CSS 在 sandbox 中加载失败 | 低 | 公式/代码样式缺失 | 回退方案 A：本地引入 CSS |
| 超长消息 HTML 过大 | 低 | 传输/渲染超时 | 限制 5MB，超限时提示 |
| Mermaid SVG 内含外部资源 | 低 | 图表不完整 | sandbox 已可访问外网 |
| 并发请求导致 Chromium 卡死 | 中 | 服务不可用 | 队列化：同一时刻只允许 1 个渲染任务 |

---

## 10. 后续可选优化

| 优化 | 优先级 | 说明 |
|---|---|---|
| 浏览器实例健康检查 | P1 | 定期检查 is_connected()，断连自动重启 |
| 渲染队列 | P2 | 多请求排队，避免并发 OOM |
| PDF 元数据 | P3 | 添加标题、作者、创建时间等 PDF metadata |
| 自定义 PDF 样式 | P3 | 允许用户选择 A4/Letter、边距、是否含页眉页脚 |
| 缓存已生成的 PDF | P3 | 同一消息不重复渲染（消息内容不变则复用） |
