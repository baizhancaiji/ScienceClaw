"""
Sessions 路由。

路由：
  PUT    /sessions                          → 创建会话
  GET    /sessions                          → 会话列表
  GET    /sessions/shared/{session_id}      → 获取已分享会话（无需认证）
  GET    /sessions/{session_id}             → 会话详情
  DELETE /sessions/{session_id}             → 删除会话
  POST   /sessions/{session_id}/chat                      → 聊天（SSE）
  POST   /sessions/{session_id}/stop                      → 停止会话
  POST   /sessions/{session_id}/clear_unread_message_count → 清零未读消息计数
  POST   /sessions/{session_id}/share       → 开启分享
  DELETE /sessions/{session_id}/share       → 取消分享
  GET    /sessions/{session_id}/files       → 沙盒文件列表
  GET    /sessions/{session_id}/sandbox-file → 读取沙盒文件
"""
from __future__ import annotations

import asyncio
import html as html_lib
import hmac
import hashlib
import json
import os
import re
import secrets
import time
import textwrap
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlencode

import shutil
from pathlib import Path as _Path

import bcrypt
import httpx
import yaml as _yaml

import shortuuid
from fastapi import APIRouter, HTTPException, Query, Request, Depends, UploadFile, File as FastAPIFile, WebSocket
from fastapi.background import BackgroundTasks
from fastapi.responses import FileResponse, Response
from loguru import logger
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
from starlette.websockets import WebSocketDisconnect

from langchain_core.messages import HumanMessage, SystemMessage

from backend.deepagent.engine import get_llm_model
from backend.deepagent.runner import arun_science_task_stream
from backend.deepagent import sessions as session_store
from backend.deepagent.sessions import (
    ScienceSessionNotFoundError,
    async_create_science_session,
    async_delete_science_session,
    async_get_science_session,
    async_list_science_sessions,
)
from backend.config import settings
from backend.models import get_model_config, list_user_models
from backend.user.dependencies import get_current_user, require_user, User

router = APIRouter(prefix="/sessions", tags=["sessions"])


# ═══════════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════════

class ApiResponse(BaseModel):
    code: int = Field(default=0, description="Business status code, 0 means success")
    msg: str = Field(default="ok", description="Business message")
    data: Any = Field(default=None, description="Response data")


class CreateSessionRequest(BaseModel):
    mode: str = Field(default="deep", description="Session mode")
    model_config_id: Optional[str] = Field(default=None, description="Model config ID")
    selected_skill_names: List[str] = Field(default_factory=list, description="User-selected skill names")


class CreateSessionData(BaseModel):
    session_id: str = Field(..., description="Session ID")
    mode: str = Field(default="deep", description="Session mode")
    selected_skill_names: List[str] = Field(default_factory=list, description="User-selected skill names")


class SessionStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"


class ListSessionItem(BaseModel):
    session_id: str = Field(..., description="Session ID")
    title: Optional[str] = Field(default=None, description="Session title")
    latest_message: Optional[str] = Field(default=None, description="Latest message content")
    latest_message_at: Optional[int] = Field(default=None, description="Latest message timestamp")
    status: str = Field(default=SessionStatus.PENDING, description="Session status")
    unread_message_count: int = Field(default=0, description="Unread message count")
    is_shared: bool = Field(default=False, description="Whether shared")
    mode: str = Field(default="deep", description="Session mode")
    pinned: bool = Field(default=False, description="Whether pinned")
    source: Optional[str] = Field(default=None, description="Session source (e.g. wechat, lark)")
    has_password: bool = Field(default=False, description="Whether password protected")


class ListSessionData(BaseModel):
    sessions: List[ListSessionItem] = Field(..., description="Session list")


class GetSessionData(BaseModel):
    session_id: str = Field(..., description="Session ID")
    title: Optional[str] = Field(default=None, description="Session title")
    status: str = Field(default=SessionStatus.PENDING, description="Session status")
    events: List[Dict[str, Any]] = Field(default_factory=list, description="Session events list")
    is_shared: bool = Field(default=False, description="Whether shared")
    mode: str = Field(default="deep", description="Session mode")
    model_config_id: Optional[str] = Field(default=None, description="Model config ID")
    selected_skill_names: List[str] = Field(default_factory=list, description="User-selected skill names")
    has_password: bool = Field(default=False, description="Whether password protected")
    locked: bool = Field(default=False, description="Whether current user must verify password")


class ChatRequest(BaseModel):
    message: str = Field(default="", description="User message content")
    timestamp: Optional[int] = Field(default=None, description="Message timestamp")
    event_id: Optional[str] = Field(default=None, description="Legacy user message event ID")
    cursor_event_id: Optional[str] = Field(default=None, description="Last received event ID for SSE reconnection replay")
    attachments: Optional[List[str]] = Field(default=None, description="Attachment path list")
    language: Optional[str] = Field(default=None, description="User interface language (e.g. 'zh', 'en')")
    model_config_id: Optional[str] = Field(default=None, description="Model config ID to use (overrides session default)")
    selected_skill_names: List[str] = Field(default_factory=list, description="User-selected skill names for this chat")


class VncSignedUrlRequest(BaseModel):
    expire_minutes: int = Field(default=15, ge=1, le=120, description="Signed VNC URL lifetime in minutes")


class VncSignedUrlData(BaseModel):
    signed_url: str = Field(..., description="Signed noVNC WebSocket URL")
    expires_in: int = Field(..., description="Lifetime in seconds")


class ExportPdfRequest(BaseModel):
    html: str = Field(..., min_length=1, description="Rendered assistant message innerHTML")
    css: str = Field(default="", description="Collected light print CSS")
    locale: str = Field(default="zh", description="Current UI locale")


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


# ═══════════════════════════════════════════════════════════════════
# 内部辅助函数
# ═══════════════════════════════════════════════════════════════════

_VNC_SIGNING_SECRET = os.environ.get("VNC_SIGNING_SECRET") or secrets.token_urlsafe(32)
_PDF_EXPORT_MAX_PAYLOAD_BYTES = 50 * 1024 * 1024
_PDF_EXPORT_CACHE_TTL_SECONDS = 5 * 60
_PDF_EXPORT_TIMEOUT_SECONDS = 120.0
_PDF_EXPORT_CACHE_DIRNAME = "_pdf_export_cache"
_PDF_EXPORT_WORK_DIRNAME = "_pdf_export_work"

_PDF_EXPORT_DEFAULT_TITLE = {
    "zh": "未命名会话",
    "en": "Untitled session",
}
_PDF_EXPORT_ERROR_STATUS = {
    "PDF_EXPORT_ACCESS_DENIED": 403,
    "PDF_EXPORT_SESSION_NOT_FOUND": 404,
    "PDF_EXPORT_PAYLOAD_TOO_LARGE": 413,
    "PDF_EXPORT_RENDER_FAILED": 502,
    "PDF_EXPORT_INVALID_PDF": 502,
    "PDF_EXPORT_TIMEOUT": 504,
    "PDF_EXPORT_UNKNOWN_ERROR": 500,
}
def _now_ts() -> int:
    return int(time.time())


def _new_event_id() -> str:
    return shortuuid.uuid()


def _wrap_event(event: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return {"event": event, "data": data}


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _normalize_pdf_locale(locale: str) -> str:
    return "zh" if locale == "zh" else "en"


def _pdf_error_response(code: str) -> Response:
    status_code = _PDF_EXPORT_ERROR_STATUS.get(code, 500)
    payload = {"code": code, "msg": f"pdf_export.{code.removeprefix('PDF_EXPORT_').lower()}", "data": None}
    return Response(
        content=json.dumps(payload, ensure_ascii=False),
        status_code=status_code,
        media_type="application/json",
    )


def _pdf_payload_size_bytes(body: ExportPdfRequest) -> int:
    return len(body.html.encode("utf-8")) + len(body.css.encode("utf-8"))


def _truncate_pdf_header_title(title: str, limit: int = 15) -> str:
    if len(title) <= limit:
        return title
    return title[:limit] + "..."


def _format_pdf_exported_at(exported_at: datetime, locale: str) -> str:
    timestamp = exported_at.strftime("%Y-%m-%d %H:%M:%S")
    if _normalize_pdf_locale(locale) == "zh":
        return f"导出时间：{timestamp}"
    return f"Exported at: {timestamp}"


def _build_pdf_html(
    html: str,
    css: str,
    *,
    header_title: str,
    exported_at_text: str,
    locale: str,
) -> str:
    lang = _normalize_pdf_locale(locale)
    escaped_title = html_lib.escape(header_title, quote=True)
    escaped_exported_at = html_lib.escape(exported_at_text, quote=True)
    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'self' data: blob:; img-src 'self' data: blob: http: https:; style-src 'unsafe-inline' 'self'; script-src 'none';">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <style>
    @page {{
      size: A4;
      margin: 18mm 14mm;
    }}
    :root {{
      color-scheme: light;
      background: #ffffff;
      color: #111827;
    }}
    html,
    body {{
      margin: 0;
      padding: 0;
      background: #ffffff;
      color: #111827;
    }}
    .pdf-export-root {{
      background: #ffffff;
      color: #111827;
    }}
    .pdf-export-meta {{
      display: none;
    }}
    {css}
  </style>
</head>
<body>
  <main class="markdown-content pdf-export-root">{html}</main>
  <div class="pdf-export-meta" aria-hidden="true">
    <span>{escaped_title}</span>
    <span>{escaped_exported_at}</span>
  </div>
</body>
</html>"""


def _pdf_session_root(session_id: str) -> str:
    return f"/home/scienceclaw/{session_id}"


def _pdf_cache_dir(session_id: str) -> str:
    return f"{_pdf_session_root(session_id)}/{_PDF_EXPORT_CACHE_DIRNAME}"


def _pdf_work_dir(session_id: str, nonce: str) -> str:
    return f"{_pdf_session_root(session_id)}/{_PDF_EXPORT_WORK_DIRNAME}/{nonce}"


def _build_pdf_cache_key(session_id: str, title: str, html: str, css: str) -> str:
    digest = hashlib.sha256()
    digest.update(session_id.encode("utf-8"))
    digest.update(title.encode("utf-8"))
    digest.update(html.encode("utf-8"))
    digest.update(css.encode("utf-8"))
    digest.update(b"light-v1")
    return digest.hexdigest()


def _pdf_cache_pdf_path(session_id: str, cache_key: str) -> str:
    return f"{_pdf_cache_dir(session_id)}/{cache_key}.pdf"


def _pdf_cache_meta_path(session_id: str, cache_key: str) -> str:
    return f"{_pdf_cache_dir(session_id)}/{cache_key}.json"


def _pdf_headers(session_id: str, cache_state: str) -> Dict[str, str]:
    return {
        "Content-Disposition": f'attachment; filename="scienceclaw-{session_id}.pdf"',
        "X-PDF-Export-Cache": cache_state,
    }


def _pdf_response(session_id: str, content: bytes, cache_state: str) -> Response:
    return Response(content=content, media_type="application/pdf", headers=_pdf_headers(session_id, cache_state))


def _is_pdf_bytes(content: bytes) -> bool:
    return content.startswith(b"%PDF")


def _pdf_header_template(header_title: str) -> str:
    escaped_header_title = html_lib.escape(header_title, quote=True)
    return (
        '<div style="font-size:9px;width:100%;padding:0 14mm;color:#4b5563;'
        'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
        f"{escaped_header_title}</div>"
    )


def _pdf_footer_template(exported_at_text: str) -> str:
    escaped_exported_at_text = html_lib.escape(exported_at_text, quote=True)
    return (
        '<div style="font-size:9px;width:100%;padding:0 14mm;color:#6b7280;text-align:right;">'
        f"{escaped_exported_at_text}</div>"
    )


def _build_pdf_render_script() -> str:
    return textwrap.dedent(
        r'''
        import json
        import shutil
        import sys
        import time
        from pathlib import Path

        from playwright.sync_api import sync_playwright


        def main() -> int:
            html_path = Path(sys.argv[1])
            pdf_path = Path(sys.argv[2])
            header_json_path = Path(sys.argv[3])
            config = json.loads(header_json_path.read_text(encoding="utf-8"))
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            html = html_path.read_text(encoding="utf-8")

            playwright = None
            browser = None
            page = None
            try:
                playwright = sync_playwright().start()
                executable = "/usr/bin/chromium-browser"
                if not Path(executable).exists():
                    executable = shutil.which("chromium-browser") or shutil.which("chromium") or shutil.which("google-chrome")
                browser = playwright.chromium.launch(
                    executable_path=executable,
                    args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
                )
                page = browser.new_page()
                page.emulate_media(media="print", color_scheme="light")
                page.set_content(html, wait_until="load")
                page.evaluate("() => document.fonts && document.fonts.ready")
                time.sleep(0.5)
                page.pdf(
                    path=str(pdf_path),
                    format="A4",
                    print_background=True,
                    display_header_footer=True,
                    header_template=config["header_template"],
                    footer_template=config["footer_template"],
                    margin={"top": "18mm", "bottom": "18mm", "left": "14mm", "right": "14mm"},
                )
                return 0
            finally:
                if page is not None:
                    page.close()
                if browser is not None:
                    browser.close()
                if playwright is not None:
                    playwright.stop()


        if __name__ == "__main__":
            raise SystemExit(main())
        '''
    ).strip()


async def _sandbox_write_file(client: httpx.AsyncClient, base: str, path: str, content: str) -> None:
    response = await client.post(f"{base}/v1/file/write", json={"file": path, "content": content})
    response.raise_for_status()


async def _sandbox_download_file(client: httpx.AsyncClient, base: str, path: str) -> bytes:
    response = await client.get(f"{base}/v1/file/download", params={"path": path}, timeout=60)
    response.raise_for_status()
    return response.content


async def _sandbox_exec(
    client: httpx.AsyncClient,
    base: str,
    *,
    command: str,
    exec_dir: str,
    timeout: float,
) -> Dict[str, Any]:
    response = await client.post(
        f"{base}/v1/shell/exec",
        json={
            "command": command,
            "exec_dir": exec_dir,
            "async_mode": False,
            "timeout": int(timeout),
        },
        timeout=timeout + 5,
    )
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data", payload)
    return data if isinstance(data, dict) else {"output": str(data), "exit_code": 0}


async def _sandbox_remove_path(client: httpx.AsyncClient, base: str, path: str) -> None:
    command = f"rm -rf {json.dumps(path)}"
    try:
        await _sandbox_exec(
            client,
            base,
            command=command,
            exec_dir=path.rsplit("/", 1)[0] or "/home/scienceclaw",
            timeout=15,
        )
    except Exception:
        logger.warning("sandbox cleanup failed for {}", path, exc_info=True)


async def _cleanup_expired_pdf_cache(session_id: str) -> None:
    base = _get_sandbox_rest_base()
    cache_dir = _pdf_cache_dir(session_id)
    command = (
        "python - <<'PY'\n"
        "import json, time\n"
        "from pathlib import Path\n"
        f"cache_dir = Path({json.dumps(cache_dir)})\n"
        "now = time.time()\n"
        "if cache_dir.exists():\n"
        "    for meta_path in cache_dir.glob('*.json'):\n"
        "        try:\n"
        "            meta = json.loads(meta_path.read_text(encoding='utf-8'))\n"
        "            if float(meta.get('expires_at', 0)) <= now:\n"
        "                pdf_path = meta_path.with_suffix('.pdf')\n"
        "                pdf_path.unlink(missing_ok=True)\n"
        "                meta_path.unlink(missing_ok=True)\n"
        "        except Exception:\n"
        "            meta_path.unlink(missing_ok=True)\n"
        "PY"
    )
    async with httpx.AsyncClient() as client:
        await _sandbox_exec(client, base, command=command, exec_dir=_pdf_session_root(session_id), timeout=20)


async def _delete_pdf_cache_key_later(session_id: str, cache_key: str, delay_seconds: int) -> None:
    await asyncio.sleep(delay_seconds)
    base = _get_sandbox_rest_base()
    async with httpx.AsyncClient() as client:
        await _sandbox_remove_path(client, base, _pdf_cache_pdf_path(session_id, cache_key))
        await _sandbox_remove_path(client, base, _pdf_cache_meta_path(session_id, cache_key))


async def _download_pdf_cache_if_fresh(session_id: str, cache_key: str) -> Optional[bytes]:
    base = _get_sandbox_rest_base()
    meta_path = _pdf_cache_meta_path(session_id, cache_key)
    pdf_path = _pdf_cache_pdf_path(session_id, cache_key)
    async with httpx.AsyncClient() as client:
        try:
            meta_bytes = await _sandbox_download_file(client, base, meta_path)
            meta = json.loads(meta_bytes.decode("utf-8"))
            if float(meta.get("expires_at", 0)) <= time.time():
                await _sandbox_remove_path(client, base, meta_path)
                await _sandbox_remove_path(client, base, pdf_path)
                return None
            pdf = await _sandbox_download_file(client, base, pdf_path)
            return pdf
        except Exception:
            return None


async def _write_pdf_cache_metadata(session_id: str, cache_key: str) -> None:
    base = _get_sandbox_rest_base()
    now = int(time.time())
    metadata = {
        "created_at": now,
        "expires_at": now + _PDF_EXPORT_CACHE_TTL_SECONDS,
        "session_id": session_id,
    }
    async with httpx.AsyncClient() as client:
        await _sandbox_write_file(
            client,
            base,
            _pdf_cache_meta_path(session_id, cache_key),
            json.dumps(metadata, ensure_ascii=False),
        )


async def _render_pdf_in_sandbox(
    session_id: str,
    full_html: str,
    header_title: str,
    exported_at_text: str,
    cache_pdf_path: str,
) -> bytes:
    base = _get_sandbox_rest_base()
    nonce = secrets.token_urlsafe(12)
    work_dir = _pdf_work_dir(session_id, nonce)
    html_path = f"{work_dir}/message.html"
    script_path = f"{work_dir}/render_pdf.py"
    header_json_path = f"{work_dir}/header_footer.json"
    exec_dir = _pdf_session_root(session_id)
    header_config = {
        "header_template": _pdf_header_template(header_title),
        "footer_template": _pdf_footer_template(exported_at_text),
    }
    async with httpx.AsyncClient() as client:
        try:
            await _sandbox_write_file(client, base, html_path, full_html)
            await _sandbox_write_file(client, base, script_path, _build_pdf_render_script())
            await _sandbox_write_file(client, base, header_json_path, json.dumps(header_config, ensure_ascii=False))
            result = await _sandbox_exec(
                client,
                base,
                command=f"python {json.dumps(script_path)} {json.dumps(html_path)} {json.dumps(cache_pdf_path)} {json.dumps(header_json_path)}",
                exec_dir=exec_dir,
                timeout=_PDF_EXPORT_TIMEOUT_SECONDS,
            )
            exit_code = result.get("exit_code", result.get("returncode", 0))
            if exit_code not in (0, None):
                logger.warning("PDF sandbox render failed for session {}: {}", session_id, result)
                raise RuntimeError("pdf render failed")
            pdf = await _sandbox_download_file(client, base, cache_pdf_path)
            if not _is_pdf_bytes(pdf):
                raise ValueError("invalid pdf")
            return pdf
        finally:
            await _sandbox_remove_path(client, base, work_dir)


def _hash_session_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_session_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _session_has_password(session: Any) -> bool:
    return bool(getattr(session, "password_hash", None))


def _is_session_unlocked(session: Any, current_user: User) -> bool:
    if not _session_has_password(session):
        return True
    unlocked_by = getattr(session, "password_unlocked_by", None)
    if not isinstance(unlocked_by, dict):
        return False
    return bool(unlocked_by.get(current_user.id))


def _mark_session_unlocked(session: Any, current_user: User) -> None:
    unlocked_by = getattr(session, "password_unlocked_by", None)
    if not isinstance(unlocked_by, dict):
        unlocked_by = {}
        setattr(session, "password_unlocked_by", unlocked_by)
    unlocked_by[current_user.id] = True


def _clear_session_unlocks(session: Any) -> None:
    setattr(session, "password_unlocked_by", {})


def _lock_session_for_user(session: Any, current_user: User) -> None:
    unlocked_by = getattr(session, "password_unlocked_by", None)
    if isinstance(unlocked_by, dict):
        unlocked_by.pop(current_user.id, None)


def _require_session_unlocked(session: Any, current_user: User) -> None:
    if not _is_session_unlocked(session, current_user):
        raise HTTPException(status_code=403, detail="Session password required")


async def _get_owned_session_or_404(session_id: str, current_user: User) -> Any:
    try:
        session = await async_get_science_session(session_id)
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return session


def _validate_session_password_strength(password: str, field_name: str = "Password") -> None:
    if len(password) < 4:
        raise HTTPException(status_code=400, detail=f"{field_name} must be at least 4 characters")
    categories = sum([
        any(ch.islower() for ch in password),
        any(ch.isupper() for ch in password),
        any(ch.isdigit() for ch in password),
    ])
    if categories < 2:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must include at least two of lowercase letters, uppercase letters, and numbers",
        )


def _normalize_password_hint(hint: Optional[str]) -> Optional[str]:
    if hint is None:
        return None
    value = hint.strip()
    return value[:100] if value else None


def _session_to_list_item(session) -> ListSessionItem:
    return ListSessionItem(
        session_id=session.session_id,
        title=getattr(session, "title", None),
        latest_message=getattr(session, "latest_message", None),
        latest_message_at=getattr(session, "latest_message_at", None),
        status=getattr(session, "status", SessionStatus.PENDING),
        unread_message_count=getattr(session, "unread_message_count", 0),
        is_shared=getattr(session, "is_shared", False),
        mode=getattr(session, "mode", "deep"),
        pinned=getattr(session, "pinned", False),
        source=getattr(session, "source", None),
        has_password=_session_has_password(session),
    )


def _append_session_event(session: Any, event: Dict[str, Any]) -> None:
    events = getattr(session, "events", None)
    if not isinstance(events, list):
        events = []
        setattr(session, "events", events)
    events.append(event)
    if event.get("event") == "message":
        data = event.get("data") or {}
        content = data.get("content")
        if isinstance(content, str) and content.strip():
            setattr(session, "latest_message", content)
            setattr(session, "latest_message_at", int(data.get("timestamp") or _now_ts()))


def _normalize_selected_skill_names(skill_names: Optional[List[str]]) -> List[str]:
    if not skill_names:
        return []
    normalized: List[str] = []
    seen: Set[str] = set()
    for raw_name in skill_names:
        if not isinstance(raw_name, str):
            continue
        name = raw_name.strip()
        if not name or name in seen:
            continue
        seen.add(name)
        normalized.append(name)
    return normalized


def _count_user_messages(events: List[Dict[str, Any]]) -> int:
    """Count message events with role=user."""
    if not events:
        return 0
    return sum(
        1 for ev in events
        if ev.get("event") == "message" and (ev.get("data") or {}).get("role") == "user"
    )


async def _generate_session_title(first_message: str) -> str:
    """
    Use LLM to generate a short, descriptive chat title from the first user message.
    Returns a fallback if generation fails.
    """
    if not (first_message and first_message.strip()):
        return ""
    prompt = first_message.strip()
    if len(prompt) > 800:
        prompt = prompt[:800] + "..."
    system = (
        "You are a helper. Given the first user message of a chat conversation, "
        "reply with a very short summary to use as the chat title. "
        "Use at most 15 words. Reply in the same language as the user. "
        "Output only the title, no quotes, no explanation, no prefix."
    )
    try:
        llm = get_llm_model(config=None, max_tokens_override=60, streaming=False)
        response = await llm.ainvoke([
            SystemMessage(content=system),
            HumanMessage(content=prompt),
        ])
        title = (response.content or "").strip()
        if title and len(title) > 80:
            title = title[:80].rstrip()
        return title or ""
    except Exception as exc:
        logger.warning("session title generation failed: %s", exc)
        # Fallback: use first line or truncated message
        first_line = prompt.split("\n")[0].strip()
        return first_line[:50] if first_line else ""


# ── SSE 事件映射（runner 事件 → 前端事件）──

def _map_plan_to_steps(plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def _map_status(status: str) -> str:
        status = (status or "pending").strip()
        if status in {"in_progress", "running"}:
            return "running"
        if status == "completed":
            return "completed"
        if status in {"blocked", "failed"}:
            return "failed"
        return "pending"

    return [
        {
            "event_id": _new_event_id(),
            "timestamp": _now_ts(),
            "status": _map_status(str(step.get("status") or "pending")),
            "id": str(step.get("id") or ""),
            "description": str(step.get("content") or ""),
            "tools": step.get("tools") if isinstance(step.get("tools"), list) else [],
        }
        for step in plan
    ]


def _infer_tool_name(tool_function: str) -> str:
    func = (tool_function or "").strip()
    if func in {"web_search", "web_crawl", "internet_search"}:
        return "web_search"
    if func in {"sandbox_exec", "terminal_execute", "terminal_session",
                "sandbox_execute_bash", "sandbox_execute_code"}:
        return func
    if func in {"sandbox_write_file", "file_write", "sandbox_file_operations",
                "sandbox_str_replace_editor"}:
        return func
    if func in {"sandbox_read_file", "file_read"}:
        return func
    if func in {"sandbox_find_files", "file_list"}:
        return func
    if func in {"file_search"}:
        return "grep"
    if func in {"file_replace"}:
        return "edit_file"
    if func in {"terminal_kill"}:
        return "execute"
    if func in {"sandbox_get_context", "sandbox_get_packages", "sandbox_convert_to_markdown"}:
        return func
    if func.startswith("sandbox_browser_") or func == "sandbox_get_browser_info":
        return func
    if func.startswith("browser_"):
        return func
    if func.startswith("markitdown_"):
        return func
    if func in {"ls", "grep", "write", "read_file", "write_file", "edit_file"}:
        return func
    return func or "info"


def _normalize_tool_args(tool_function: str, args: Any, tool_call_id: str) -> Dict[str, Any]:
    if not isinstance(args, dict):
        return {}
    out = dict(args)
    func = (tool_function or "").strip()
    if func in {"read_file", "write_file", "edit_file", "sandbox_read_file", "sandbox_write_file",
                "file_read", "file_write", "file_replace"}:
        if "file" not in out and "file_path" in out:
            out["file"] = out.get("file_path")
    if func in {"execute", "sandbox_exec", "terminal_execute"}:
        out.setdefault("id", tool_call_id)
    return out


def _maybe_wrap_tool_content(
    tool_function: str, tool_args: Dict[str, Any], raw_content: Any, tool_call_id: str
) -> Any:
    func = (tool_function or "").strip()

    # 终端命令执行
    if func in {"execute", "sandbox_exec", "terminal_execute"}:
        if isinstance(raw_content, str):
            try:
                parsed = json.loads(raw_content)
            except (json.JSONDecodeError, TypeError):
                parsed = {"output": raw_content}
        elif isinstance(raw_content, dict):
            parsed = raw_content
        else:
            parsed = {"output": str(raw_content)}

        output = parsed.get("output", str(raw_content))
        command = tool_args.get("command", "")
        session_id = parsed.get("session_id", tool_call_id)
        return {
            "output": output,
            "session_id": session_id,
            "console": [{"ps1": "$", "command": command, "output": output}],
        }

    # 文件读取
    if func in {"read_file", "sandbox_read_file", "file_read"}:
        if isinstance(raw_content, str):
            try:
                parsed = json.loads(raw_content)
                return {"file": parsed.get("file", tool_args.get("file_path", "")), "content": parsed.get("content", "")}
            except (json.JSONDecodeError, TypeError):
                pass
        elif isinstance(raw_content, dict):
            return {"file": raw_content.get("file", tool_args.get("file_path", "")), "content": raw_content.get("content", "")}
        content = raw_content if isinstance(raw_content, str) else str(raw_content)
        return {"file": tool_args.get("file", tool_args.get("file_path", "")), "content": content}

    # 文件写入
    if func in {"write_file", "sandbox_write_file", "file_write"}:
        if isinstance(raw_content, str):
            try:
                parsed = json.loads(raw_content)
                return parsed
            except (json.JSONDecodeError, TypeError):
                pass
        return raw_content

    return raw_content


def _extract_tool_meta(data: Dict[str, Any]) -> Dict[str, Any]:
    """从 runner 事件中提取工具元数据（icon, category, description, sandbox 等）"""
    meta = data.get("tool_meta") or {}
    result: Dict[str, Any] = {
        "icon": meta.get("icon", ""),
        "category": meta.get("category", ""),
        "description": meta.get("description", ""),
    }
    if meta.get("sandbox"):
        result["sandbox"] = True
    return result


# ── 沙盒文件管理辅助函数 ──

_FILE_OP_TOOLS = {
    "sandbox_file_operations",
    "sandbox_str_replace_editor",
    "file_write",
    "sandbox_write_file",
}

_CODE_EXEC_TOOLS = {
    "sandbox_execute_bash",
    "sandbox_execute_code",
    "terminal_execute",
}

_OPEN_WRITE_RE = re.compile(
    r"""open\s*\(\s*(?P<q>['"])(?P<path>.+?)(?P=q)\s*,\s*(?P<q2>['"])(?P<mode>[wxa][+tb]*)(?P=q2)\s*\)"""
)


def _get_sandbox_rest_base() -> str:
    """Derive sandbox REST base URL from SANDBOX_MCP_URL."""
    rest_url = os.environ.get("SANDBOX_REST_URL", "").strip()
    if rest_url:
        return rest_url.rstrip("/")
    mcp_url = os.environ.get("SANDBOX_MCP_URL", "http://sandbox:8080/mcp")
    return mcp_url.rsplit("/", 1)[0].rstrip("/")


def _get_sandbox_vnc_websockify_url() -> str:
    base = _get_sandbox_rest_base()
    if base.startswith("https://"):
        return f"wss://{base.removeprefix('https://')}/websockify"
    if base.startswith("http://"):
        return f"ws://{base.removeprefix('http://')}/websockify"
    return f"ws://{base}/websockify"


def _build_vnc_signature(session_id: str, user_id: str, expires_at: int) -> str:
    payload = f"{session_id}:{user_id}:{expires_at}".encode("utf-8")
    return hmac.new(_VNC_SIGNING_SECRET.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def _is_valid_vnc_signature(session_id: str, user_id: str, expires_at: int, signature: str) -> bool:
    if expires_at < _now_ts():
        return False
    expected = _build_vnc_signature(session_id, user_id, expires_at)
    return hmac.compare_digest(expected, signature or "")


def _extract_sandbox_file_paths(events: List[Dict[str, Any]]) -> Set[str]:
    """Scan session events and extract file paths touched by sandbox tools."""
    paths: Set[str] = set()
    for ev in events:
        if ev.get("event") != "tool":
            continue
        data = ev.get("data") or {}
        func = (data.get("function") or "").strip()
        args = data.get("args") or {}

        if func in _FILE_OP_TOOLS:
            for key in ("path", "file_path", "file", "filename"):
                p = args.get(key)
                if isinstance(p, str) and p.strip():
                    paths.add(p.strip())
                    break

        if func in _CODE_EXEC_TOOLS:
            code = args.get("code") or args.get("command") or ""
            if isinstance(code, str):
                for m in _OPEN_WRITE_RE.finditer(code):
                    paths.add(m.group("path"))

    return paths


# ── 轮次文件快照 / diff ──

_ROUND_FILES_EXCLUDE_DIRS = {"_diagnostic", "tools_staging", "__pycache__", ".git"}
_ROUND_FILES_EXCLUDE_NAMES = {"CONTEXT.md", "planner.md", "AGENTS.md"}


def _snapshot_workspace_files(workspace_dir: _Path) -> Dict[str, float]:
    """Return {relative_path: mtime} for every file under *workspace_dir*."""
    snap: Dict[str, float] = {}
    if not workspace_dir.is_dir():
        return snap
    for fp in workspace_dir.rglob("*"):
        if not fp.is_file():
            continue
        try:
            rel = str(fp.relative_to(workspace_dir))
            snap[rel] = fp.stat().st_mtime
        except (OSError, ValueError):
            continue
    return snap


def _diff_workspace_files(
    pre: Dict[str, float],
    post: Dict[str, float],
    workspace_dir: _Path,
    session_id: str,
) -> List[Dict[str, Any]]:
    """Compare snapshots and return new/modified files, excluding system artefacts."""
    changed: List[Dict[str, Any]] = []
    for rel, mtime in post.items():
        top_dir = rel.split("/", 1)[0] if "/" in rel else ""
        if top_dir in _ROUND_FILES_EXCLUDE_DIRS:
            continue
        basename = rel.rsplit("/", 1)[-1]
        if basename in _ROUND_FILES_EXCLUDE_NAMES:
            continue
        if basename.startswith("."):
            continue

        prev_mtime = pre.get(rel)
        if prev_mtime is not None and prev_mtime >= mtime:
            continue

        fp = workspace_dir / rel
        try:
            stat = fp.stat()
            upload_date = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
            size = stat.st_size
        except OSError:
            continue

        category = "research_data" if top_dir == "research_data" else "output"
        abs_path = str(fp)
        changed.append({
            "file_id": abs_path,
            "filename": basename,
            "relative_path": rel,
            "size": size,
            "upload_date": upload_date,
            "file_url": f"/api/v1/sessions/{session_id}/sandbox-file/download?path={abs_path}",
            "category": category,
        })
    return changed


async def _sandbox_file_list(directory: str) -> List[Dict[str, Any]]:
    """Call sandbox REST API to list files in a directory."""
    base = _get_sandbox_rest_base()
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{base}/v1/file/list", json={"path": directory})
        if resp.status_code != 200:
            return []
        body = resp.json()
        data = body.get("data", body)
        if isinstance(data, dict):
            return data.get("files", [])
        return data if isinstance(data, list) else []


async def _sandbox_file_read(file_path: str) -> Optional[str]:
    """Call sandbox REST API to read a file."""
    base = _get_sandbox_rest_base()
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{base}/v1/file/read", json={"file": file_path})
        if resp.status_code != 200:
            return None
        body = resp.json()
        data = body.get("data", body)
        if isinstance(data, dict):
            return data.get("content", "")
        return str(data)


async def _verify_sandbox_files(paths: Set[str]) -> List[Dict[str, Any]]:
    """Verify which paths still exist in the sandbox and return FileInfo-compatible dicts."""
    dirs_to_scan: Dict[str, Set[str]] = {}
    for p in paths:
        parent = p.rsplit("/", 1)[0] if "/" in p else "/"
        dirs_to_scan.setdefault(parent, set()).add(p)

    existing_files: Dict[str, Dict[str, Any]] = {}
    for directory, expected_paths in dirs_to_scan.items():
        entries = await _sandbox_file_list(directory)
        for entry in entries:
            entry_path = entry.get("path", "")
            if entry_path in expected_paths:
                existing_files[entry_path] = entry

    results: List[Dict[str, Any]] = []
    now_iso = datetime.now(timezone.utc).isoformat()
    for p in sorted(paths):
        entry = existing_files.get(p)
        if entry is None:
            continue
        filename = entry.get("name", p.rsplit("/", 1)[-1] if "/" in p else p)
        mod_time = entry.get("modified_time", "")
        if mod_time and mod_time.isdigit():
            upload_date = datetime.fromtimestamp(int(mod_time), tz=timezone.utc).isoformat()
        else:
            upload_date = mod_time or now_iso
        results.append({
            "file_id": p,
            "filename": filename,
            "size": entry.get("size") or 0,
            "upload_date": upload_date,
            "content_type": "text/plain",
            "file_url": None,
            "metadata": {"sandbox_path": p},
        })
    return results


def _map_science_stream_to_agent_event(evt: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    将 runner 产生的事件映射为前端期望的 SSE 事件格式。

    runner 现在产生自包含的事件（已在 runner 层完成中间件数据合并），
    每个事件都带有完整的 tool_meta、duration_ms，无需额外缓存。
    """
    event_type = str(evt.get("event") or "")
    data = evt.get("data") or {}
    ts = _now_ts()

    if event_type == "thinking":
        return _wrap_event("thinking", {
            "event_id": _new_event_id(), "timestamp": ts,
            "content": data.get("content", ""),
        })

    if event_type in {"plan", "plan_update"}:
        plan = data.get("plan") or []
        if not isinstance(plan, list):
            return None
        return _wrap_event("plan", {"event_id": _new_event_id(), "timestamp": ts, "steps": _map_plan_to_steps(plan)})

    if event_type == "step_start":
        step = data.get("step") or {}
        return _wrap_event("step", {
            "event_id": _new_event_id(), "timestamp": ts,
            "status": "running",
            "id": str(step.get("id") or ""),
            "description": str(step.get("content") or ""),
        })

    if event_type == "step_end":
        return _wrap_event("step", {
            "event_id": _new_event_id(), "timestamp": ts,
            "status": "completed",
            "id": str(data.get("step_id") or ""),
            "description": "",
        })

    if event_type == "message_chunk":
        return _wrap_event("message_chunk", {
            "event_id": _new_event_id(), "timestamp": ts,
            "content": data.get("content", ""), "role": "assistant",
        })

    if event_type == "message_chunk_done":
        return _wrap_event("message_chunk_done", {
            "event_id": _new_event_id(), "timestamp": ts,
        })

    if event_type in {"planning_message", "step_message"}:
        content = data.get("content")
        if not isinstance(content, str):
            content = str(content)
        return _wrap_event("message", {
            "event_id": _new_event_id(), "timestamp": ts,
            "content": content, "role": "assistant", "attachments": [],
        })

    if event_type == "tool_call":
        tool_call_id = str(data.get("tool_call_id") or "")
        tool_function = str(data.get("function") or "")
        tool_args = _normalize_tool_args(tool_function, data.get("args") or {}, tool_call_id)
        tool_meta = _extract_tool_meta(data)
        return _wrap_event("tool", {
            "event_id": _new_event_id(), "timestamp": ts,
            "tool_call_id": tool_call_id,
            "name": _infer_tool_name(tool_function),
            "status": "calling",
            "function": tool_function,
            "args": tool_args,
            "tool_meta": tool_meta,
        })

    if event_type == "tool_result":
        tool_call_id = str(data.get("tool_call_id") or "")
        tool_function = str(data.get("function") or "")
        raw_args = data.get("args")
        # 只在有实际 args 时才 normalize，否则不发送 args（让前端保留 calling 的 args）
        tool_args = _normalize_tool_args(tool_function, raw_args or {}, tool_call_id) if raw_args else None
        content = _maybe_wrap_tool_content(tool_function, tool_args or {}, data.get("content"), tool_call_id)
        tool_meta = _extract_tool_meta(data)
        duration_ms = data.get("duration_ms")

        result = {
            "event_id": _new_event_id(), "timestamp": ts,
            "tool_call_id": tool_call_id,
            "name": _infer_tool_name(tool_function),
            "status": "called",
            "function": tool_function,
            "content": content,
            "duration_ms": duration_ms,
            "tool_meta": tool_meta,
        }
        # 只在有实际 args 时才包含，避免覆盖前端 calling 事件中保存的 args
        if tool_args:
            result["args"] = tool_args
        return _wrap_event("tool", result)

    if event_type == "statistics":
        return _wrap_event("statistics", data)

    if event_type == "error":
        message = data.get("message")
        if not isinstance(message, str):
            message = str(message)
        return _wrap_event("error", {"event_id": _new_event_id(), "timestamp": ts, "error": message})

    return None


# ═══════════════════════════════════════════════════════════════════
# 路由
# ═══════════════════════════════════════════════════════════════════

@router.put("", response_model=ApiResponse)
async def create_session(
    body: CreateSessionRequest = CreateSessionRequest(),
    current_user: User = Depends(require_user),
) -> ApiResponse:
    try:
        model_config_dict = None
        if body.model_config_id:
            mc = await get_model_config(body.model_config_id)
            if mc:
                if not mc.is_system and mc.user_id != current_user.id:
                    raise HTTPException(status_code=403, detail="Cannot use this model")
                model_config_dict = mc.model_dump()

        session = await async_create_science_session(
            mode=body.mode,
            user_id=current_user.id,
            model_config=model_config_dict,
            selected_skill_names=_normalize_selected_skill_names(body.selected_skill_names),
        )
        return ApiResponse(data=CreateSessionData(
            session_id=session.session_id,
            mode=session.mode,
            selected_skill_names=getattr(session, "selected_skill_names", []) or [],
        ).model_dump())
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("create_session failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("", response_model=ApiResponse)
async def list_sessions(current_user: User = Depends(require_user)) -> ApiResponse:
    sessions = await async_list_science_sessions(user_id=current_user.id)
    items = [_session_to_list_item(s) for s in sessions]
    return ApiResponse(data=ListSessionData(sessions=items).model_dump())


@router.get("/shared/{session_id}", response_model=ApiResponse)
async def get_shared_session(session_id: str) -> ApiResponse:
    """获取已分享的会话（无需认证）"""
    try:
        session = await async_get_science_session(session_id)
        if not getattr(session, "is_shared", False):
            raise HTTPException(status_code=404, detail="Shared session not found")
        if _session_has_password(session):
            raise HTTPException(status_code=404, detail="Shared session not found")

        events = getattr(session, "events", []) or []
        return ApiResponse(data=GetSessionData(
            session_id=session.session_id,
            title=getattr(session, "title", None),
            status=getattr(session, "status", SessionStatus.PENDING),
            events=events,
            is_shared=True,
            mode=getattr(session, "mode", "deep"),
            selected_skill_names=getattr(session, "selected_skill_names", []) or [],
            has_password=False,
            locked=False,
        ).model_dump())
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Shared session not found") from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("get_shared_session failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ═══════════════════════════════════════════════════════════════════
# 外置 Skills 管理（必须放在 /{session_id} 路由之前，否则 "skills" 会被当作 session_id）
# ═══════════════════════════════════════════════════════════════════

from backend.mongodb.db import db as _db

_EXTERNAL_SKILLS_DIR = os.environ.get("EXTERNAL_SKILLS_DIR", "/app/Skills")
_BUILTIN_SKILLS_DIR = os.environ.get("BUILTIN_SKILLS_DIR", "/app/builtin_skills")
_WORKSPACE_DIR = os.environ.get("WORKSPACE_DIR", "/home/scienceclaw")
_SKILL_DESCRIPTION_TRANSLATION_COLLECTION = "skill_description_translations"
_SKILL_DESCRIPTION_TRANSLATION_TIMEOUT = 20
_SKILL_METADATA_KEYS = (
    "name",
    "description",
    "description_zh",
    "zh_description",
    "description_i18n",
)


def _is_chinese_description(text: str) -> bool:
    normalized = _normalize_skill_description(text)
    if not normalized:
        return False
    chinese_chars = len(re.findall(r"[\u3400-\u9fff]", normalized))
    ascii_letters = len(re.findall(r"[A-Za-z]", normalized))
    return chinese_chars > 0 and chinese_chars >= ascii_letters


def _normalize_skill_description(value: Any) -> str:
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    return ""


def _extract_skill_description_zh(fm: Dict[str, Any]) -> str:
    for key in ("description_zh", "zh_description"):
        value = _normalize_skill_description(fm.get(key))
        if value:
            return value

    description_i18n = fm.get("description_i18n")
    if isinstance(description_i18n, dict):
        for key in ("zh", "zh-CN", "zh_cn"):
            value = _normalize_skill_description(description_i18n.get(key))
            if value:
                return value

    return ""


def _skill_description_cache_key(description: str) -> str:
    normalized = _normalize_skill_description(description)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _extract_skill_metadata_text(text: str) -> str:
    match = re.match(r"^---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)", text, re.DOTALL)
    if match:
        return match.group(1)

    if not any(re.match(rf"^{re.escape(key)}\s*:", text) for key in _SKILL_METADATA_KEYS):
        return ""

    lines = text.splitlines()
    metadata_lines: List[str] = []
    for line in lines:
        if metadata_lines and not line.strip():
            break
        metadata_lines.append(line)
    return "\n".join(metadata_lines)


def _strip_skill_metadata_text(text: str) -> str:
    match = re.match(r"^---\s*\r?\n.*?\r?\n---\s*(?:\r?\n|$)", text, re.DOTALL)
    if match:
        return text[match.end():].lstrip("\r\n")

    if not any(re.match(rf"^{re.escape(key)}\s*:", text) for key in _SKILL_METADATA_KEYS):
        return text

    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if index > 0 and not line.strip():
            return "".join(lines[index + 1:]).lstrip("\r\n")
    return ""


def _resolve_skill_dir(skill_name: str, include_builtin: bool = True) -> Optional[_Path]:
    if not skill_name or "/" in skill_name or "\\" in skill_name:
        return None

    for base_dir in (_EXTERNAL_SKILLS_DIR, _BUILTIN_SKILLS_DIR):
        if base_dir == _BUILTIN_SKILLS_DIR and not include_builtin:
            continue
        base = _Path(base_dir)
        skill_path = (base / skill_name).resolve()
        try:
            skill_path.relative_to(base.resolve())
        except ValueError:
            continue
        if skill_path.is_dir() and (skill_path / "SKILL.md").is_file():
            return skill_path
    return None


async def _resolve_skill_translation_model_config(user_id: str) -> Optional[Dict[str, Any]]:
    if (getattr(settings, "model_ds_api_key", None) or "").strip():
        return None

    models = await list_user_models(user_id)
    for model in models:
        if model.is_active and (model.api_key or "").strip():
            return model.model_dump()
    return None


async def _populate_skill_description_zh(
    skills: List[Dict[str, Any]],
    user_id: str,
) -> None:
    """Populate Chinese descriptions in-place using frontmatter, cache, then one batch LLM call."""
    pending_by_cache_key: Dict[str, List[Dict[str, Any]]] = {}

    for skill in skills:
        description = _normalize_skill_description(skill.get("description"))
        if not description:
            continue
        if _normalize_skill_description(skill.get("description_zh")):
            continue
        if _is_chinese_description(description):
            skill["description_zh"] = description
            continue
        pending_by_cache_key.setdefault(_skill_description_cache_key(description), []).append(skill)

    if not pending_by_cache_key:
        return

    col = _db.get_collection(_SKILL_DESCRIPTION_TRANSLATION_COLLECTION)
    cursor = col.find(
        {"_id": {"$in": list(pending_by_cache_key.keys())}},
        {"description_zh": 1},
    )
    async for doc in cursor:
        cached = _normalize_skill_description(doc.get("description_zh"))
        if not cached:
            continue
        for skill in pending_by_cache_key.pop(str(doc.get("_id")), []):
            skill["description_zh"] = cached

    if not pending_by_cache_key:
        return

    model_config = await _resolve_skill_translation_model_config(user_id)
    if model_config is None and not (getattr(settings, "model_ds_api_key", None) or "").strip():
        for skills_for_description in pending_by_cache_key.values():
            for skill in skills_for_description:
                skill["description_zh"] = _normalize_skill_description(skill.get("description"))
        return

    items = []
    for cache_key, skills_for_description in pending_by_cache_key.items():
        skill = skills_for_description[0]
        name = str(skill.get("name") or "").strip()
        description = _normalize_skill_description(skill.get("description"))[:1200]
        if not name or not description:
            continue
        items.append({"id": cache_key, "name": name, "description": description})

    if not items:
        return

    prompt = (
        "Translate these AI skill descriptions into concise Simplified Chinese for UI cards. "
        "Preserve product names, file extensions, API names, and quoted trigger phrases when useful. "
        "Return ONLY a JSON object where each key is the given id and each value is one or two short Chinese sentences.\n\n"
        f"{json.dumps(items, ensure_ascii=False)}"
    )

    try:
        llm = get_llm_model(
            config=model_config,
            max_tokens_override=2000,
            streaming=False,
        )
        result = await asyncio.wait_for(
            llm.ainvoke([
                SystemMessage(content="You translate UI skill descriptions into Simplified Chinese."),
                HumanMessage(content=prompt),
            ]),
            timeout=_SKILL_DESCRIPTION_TRANSLATION_TIMEOUT,
        )
        content = _normalize_skill_description(getattr(result, "content", ""))
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE).strip()
        translations = json.loads(content)
        if not isinstance(translations, dict):
            raise ValueError("translation response is not a JSON object")
    except Exception:
        logger.exception("populate_skill_description_zh batch translation failed")
        for skills_for_description in pending_by_cache_key.values():
            for skill in skills_for_description:
                skill["description_zh"] = _normalize_skill_description(skill.get("description"))
        return

    now = int(time.time())
    for cache_key, translated_value in translations.items():
        translated = _normalize_skill_description(translated_value)
        skills_for_description = pending_by_cache_key.get(str(cache_key))
        if not skills_for_description or not translated:
            continue
        skill = skills_for_description[0]
        description = _normalize_skill_description(skill.get("description"))
        name = str(skill.get("name") or "").strip()
        for skill_with_same_description in skills_for_description:
            skill_with_same_description["description_zh"] = translated
        await col.update_one(
            {"_id": cache_key},
            {
                "$set": {
                    "description": description,
                    "description_zh": translated,
                    "skill_name": name,
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )

    for skills_for_description in pending_by_cache_key.values():
        for skill in skills_for_description:
            if not _normalize_skill_description(skill.get("description_zh")):
                skill["description_zh"] = _normalize_skill_description(skill.get("description"))
def _parse_skill_frontmatter(skill_dir: _Path) -> Dict[str, Any]:
    """从 SKILL.md 中解析 YAML front-matter 元数据。"""
    skill_md = skill_dir / "SKILL.md"
    result: Dict[str, Any] = {"name": skill_dir.name, "description": "", "description_zh": ""}
    if not skill_md.is_file():
        return result
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        metadata_text = _extract_skill_metadata_text(text)
        if metadata_text:
            fm = _yaml.safe_load(metadata_text)
            if isinstance(fm, dict):
                result["name"] = fm.get("name", skill_dir.name)
                result["description"] = _normalize_skill_description(fm.get("description"))
                result["description_zh"] = _extract_skill_description_zh(fm)
    except Exception:
        pass
    return result


def _list_skill_dirs(
    base_dir: str,
    builtin: bool = False,
) -> List[Dict[str, Any]]:
    """列出指定目录中所有合法的 skill。"""
    base = _Path(base_dir)
    if not base.is_dir():
        return []
    skills = []
    for child in sorted(base.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if not (child / "SKILL.md").is_file():
            continue
        meta = _parse_skill_frontmatter(child)
        files = [str(f.relative_to(child)) for f in child.rglob("*") if f.is_file()]
        skills.append({**meta, "files": files, "builtin": builtin})
    return skills


class SkillBlockRequest(BaseModel):
    blocked: bool = Field(default=True)


@router.get("/skills", response_model=ApiResponse)
async def list_skills(current_user: User = Depends(require_user)) -> ApiResponse:
    """列出所有 skills（内置排前面，不可屏蔽/删除）+ 外置 skills。"""
    try:
        builtin = _list_skill_dirs(_BUILTIN_SKILLS_DIR, builtin=True)
        external = _list_skill_dirs(_EXTERNAL_SKILLS_DIR, builtin=False)
        all_skills = builtin + external
        await _populate_skill_description_zh(all_skills, current_user.id)

        col = _db.get_collection("blocked_skills")
        blocked_docs = col.find({"user_id": current_user.id}, {"skill_name": 1})
        blocked_names: set = set()
        async for doc in blocked_docs:
            name = doc.get("skill_name")
            if name:
                blocked_names.add(name)

        for s in builtin:
            s["blocked"] = False
        for s in external:
            s["blocked"] = s["name"] in blocked_names

        return ApiResponse(data=all_skills)
    except Exception as exc:
        logger.exception("list_skills failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.put("/skills/{skill_name}/block", response_model=ApiResponse)
async def toggle_block_skill(
    skill_name: str,
    body: SkillBlockRequest,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    """屏蔽或取消屏蔽一个外置 skill。"""
    try:
        col = _db.get_collection("blocked_skills")
        filt = {"user_id": current_user.id, "skill_name": skill_name}
        if body.blocked:
            await col.update_one(filt, {"$set": filt}, upsert=True)
        else:
            await col.delete_one(filt)
        return ApiResponse(data={"skill_name": skill_name, "blocked": body.blocked})
    except Exception as exc:
        logger.exception("toggle_block_skill failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/skills/{skill_name}", response_model=ApiResponse)
async def delete_skill(
    skill_name: str,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    """彻底删除一个外置 skill 目录。"""
    try:
        skill_path = _Path(_EXTERNAL_SKILLS_DIR) / skill_name
        if not skill_path.is_dir():
            raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
        resolved = skill_path.resolve()
        base_resolved = _Path(_EXTERNAL_SKILLS_DIR).resolve()
        if not str(resolved).startswith(str(base_resolved)):
            raise HTTPException(status_code=403, detail="Invalid skill path")
        shutil.rmtree(resolved)
        col = _db.get_collection("blocked_skills")
        await col.delete_many({"skill_name": skill_name})
        return ApiResponse(data={"skill_name": skill_name, "deleted": True})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("delete_skill failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


class SaveSkillRequest(BaseModel):
    skill_name: str = Field(..., description="Name of the skill to save")


@router.post("/{session_id}/skills/save", response_model=ApiResponse)
async def save_skill_from_session(
    session_id: str,
    body: SaveSkillRequest,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    """Copy a skill from the session workspace to the permanent Skills directory."""
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        _require_session_unlocked(session, current_user)

        skill_name = body.skill_name.strip()
        if not skill_name or "/" in skill_name or "\\" in skill_name:
            raise HTTPException(status_code=400, detail="Invalid skill name")

        # Agent 可能将 skill 写在多种位置，按优先级检查
        candidate_paths = [
            _Path(_WORKSPACE_DIR) / session_id / ".agents" / "skills" / skill_name,
            _Path(_WORKSPACE_DIR) / session_id / "skills" / skill_name,
            _Path(_WORKSPACE_DIR) / session_id / skill_name,
        ]
        src = next(
            (p for p in candidate_paths if p.is_dir() and (p / "SKILL.md").is_file()),
            None,
        )

        dst = _Path(_EXTERNAL_SKILLS_DIR) / skill_name

        if src is None:
            # Agent 可能直接编辑了 /skills/ 目录下的已有 skill（in-place 编辑），
            # 此时 workspace 里没有副本，但 /skills/ 已经是最新版本
            if dst.is_dir() and (dst / "SKILL.md").is_file():
                logger.info(
                    f"[Skills] Skill '{skill_name}' not in workspace but already exists "
                    f"in {dst}, treating as in-place update"
                )
                return ApiResponse(data={"skill_name": skill_name, "saved": True})
            raise HTTPException(
                status_code=404,
                detail=f"Skill '{skill_name}' not found in session workspace "
                       f"(checked .agents/skills/, skills/, and {skill_name}/)",
            )

        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

        logger.info(f"[Skills] Saved skill '{skill_name}' from session {session_id} to {dst}")
        return ApiResponse(data={"skill_name": skill_name, "saved": True})
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("save_skill_from_session failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/skills/{skill_name}/files", response_model=ApiResponse)
async def list_skill_files(
    skill_name: str,
    path: str = "",
    current_user: User = Depends(require_user),
) -> ApiResponse:
    """列出某个 skill 内部的文件结构。"""
    try:
        skill_path = _resolve_skill_dir(skill_name)
        if skill_path is None:
            raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
        target = skill_path / path if path else skill_path
        target_resolved = target.resolve()
        if not str(target_resolved).startswith(str(skill_path.resolve())):
            raise HTTPException(status_code=403, detail="Invalid path")
        if not target_resolved.is_dir():
            raise HTTPException(status_code=404, detail="Directory not found")
        items = []
        for child in sorted(target_resolved.iterdir()):
            if child.name.startswith("."):
                continue
            rel = str(child.relative_to(skill_path))
            items.append({
                "name": child.name,
                "path": rel,
                "type": "directory" if child.is_dir() else "file",
            })
        return ApiResponse(data=items)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("list_skill_files failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


class ReadSkillFileRequest(BaseModel):
    file: str


@router.post("/skills/{skill_name}/read", response_model=ApiResponse)
async def read_skill_file(
    skill_name: str,
    body: ReadSkillFileRequest,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    """读取某个 skill 内的文件内容。"""
    try:
        skill_path = _resolve_skill_dir(skill_name)
        if skill_path is None:
            raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
        file_path = (skill_path / body.file).resolve()
        if not str(file_path).startswith(str(skill_path.resolve())):
            raise HTTPException(status_code=403, detail="Invalid file path")
        if not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        content = file_path.read_text(encoding="utf-8", errors="replace")
        if file_path.name == "SKILL.md":
            content = _strip_skill_metadata_text(content)
        return ApiResponse(data={"file": body.file, "content": content})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("read_skill_file failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ═══════════════════════════════════════════════════════════════════
# 外置 Tools 管理（必须放在 /{session_id} 路由之前）
# ═══════════════════════════════════════════════════════════════════

_TOOLS_DIR = os.environ.get("TOOLS_DIR", "/app/Tools")


def _extract_tool_description(py_file: _Path) -> str:
    """从 Python 文件中提取 @tool 函数的首行 docstring。"""
    try:
        content = py_file.read_text(encoding="utf-8", errors="replace")
        match = re.search(r'@tool\s*\ndef\s+\w+\([^)]*\)[^:]*:\s*"""(.*?)"""', content, re.DOTALL)
        if match:
            return match.group(1).strip().split('\n')[0].strip()
    except Exception:
        pass
    return ""


def _list_external_tools() -> List[Dict[str, Any]]:
    """列出 Tools 目录中所有外置工具（排除 __init__.py）。"""
    base = _Path(_TOOLS_DIR)
    if not base.is_dir():
        return []
    tools: List[Dict[str, Any]] = []
    for py_file in sorted(base.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        tools.append({
            "name": py_file.stem,
            "description": _extract_tool_description(py_file),
            "file": py_file.name,
        })
    return tools


class ToolBlockRequest(BaseModel):
    blocked: bool = Field(default=True)


@router.get("/tools", response_model=ApiResponse)
async def list_tools(current_user: User = Depends(require_user)) -> ApiResponse:
    """列出所有外置 tools，包含屏蔽状态。"""
    try:
        tools = _list_external_tools()
        col = _db.get_collection("blocked_tools")
        blocked_docs = col.find({"user_id": current_user.id}, {"tool_name": 1})
        blocked_names: set = set()
        async for doc in blocked_docs:
            name = doc.get("tool_name")
            if name:
                blocked_names.add(name)
        for t in tools:
            t["blocked"] = t["name"] in blocked_names
        return ApiResponse(data=tools)
    except Exception as exc:
        logger.exception("list_tools failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.put("/tools/{tool_name}/block", response_model=ApiResponse)
async def toggle_block_tool(
    tool_name: str,
    body: ToolBlockRequest,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    """屏蔽或取消屏蔽一个外置 tool。"""
    try:
        col = _db.get_collection("blocked_tools")
        filt = {"user_id": current_user.id, "tool_name": tool_name}
        if body.blocked:
            await col.update_one(filt, {"$set": filt}, upsert=True)
        else:
            await col.delete_one(filt)
        return ApiResponse(data={"tool_name": tool_name, "blocked": body.blocked})
    except Exception as exc:
        logger.exception("toggle_block_tool failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/tools/{tool_name}", response_model=ApiResponse)
async def delete_tool(
    tool_name: str,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    """彻底删除一个外置 tool 文件。"""
    try:
        tool_path = _Path(_TOOLS_DIR) / f"{tool_name}.py"
        if not tool_path.is_file():
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        resolved = tool_path.resolve()
        base_resolved = _Path(_TOOLS_DIR).resolve()
        if not str(resolved).startswith(str(base_resolved)):
            raise HTTPException(status_code=403, detail="Invalid tool path")
        resolved.unlink()
        col = _db.get_collection("blocked_tools")
        await col.delete_many({"tool_name": tool_name})
        return ApiResponse(data={"tool_name": tool_name, "deleted": True})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("delete_tool failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/tools/{tool_name}/read", response_model=ApiResponse)
async def read_tool_file(
    tool_name: str,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    """读取一个外置 tool 的源码内容。"""
    try:
        tool_path = _Path(_TOOLS_DIR) / f"{tool_name}.py"
        if not tool_path.is_file():
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        content = tool_path.read_text(encoding="utf-8", errors="replace")
        return ApiResponse(data={"file": f"{tool_name}.py", "content": content})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("read_tool_file failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


class SaveToolRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the tool to save (without .py extension)")
    replaces: str = Field("", description="If this tool replaces an existing tool with a different name, specify the old tool name here")


@router.post("/{session_id}/tools/save", response_model=ApiResponse)
async def save_tool_from_session(
    session_id: str,
    body: SaveToolRequest,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    """Copy a tool from the session workspace to the permanent Tools directory."""
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        _require_session_unlocked(session, current_user)

        tool_name = body.tool_name.strip()
        if not tool_name or "/" in tool_name or "\\" in tool_name:
            raise HTTPException(status_code=400, detail="Invalid tool name")

        src = _Path(_WORKSPACE_DIR) / session_id / "tools_staging" / f"{tool_name}.py"
        if not src.is_file():
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}.py' not found in session workspace tools_staging/",
            )

        content = src.read_text(encoding="utf-8", errors="replace")
        if "@tool" not in content:
            raise HTTPException(
                status_code=400,
                detail="File does not contain a @tool decorated function",
            )

        dst = _Path(_TOOLS_DIR) / f"{tool_name}.py"
        shutil.copy2(src, dst)

        replaces = (body.replaces or "").strip()
        if replaces and replaces != tool_name:
            old_file = _Path(_TOOLS_DIR) / f"{replaces}.py"
            if old_file.is_file():
                old_file.unlink()
                logger.info(f"[Tools] Removed old tool '{replaces}.py' (replaced by '{tool_name}')")

        logger.info(f"[Tools] Saved tool '{tool_name}' from session {session_id} to {dst}")
        return ApiResponse(data={"tool_name": tool_name, "saved": True, "replaced": replaces or None})
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("save_tool_from_session failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ═══════════════════════════════════════════════════════════════════
# 文件上传（保存到 session workspace，让 Agent 可以直接访问）
# ═══════════════════════════════════════════════════════════════════

@router.post("/{session_id}/upload", response_model=ApiResponse)
async def upload_session_file(
    session_id: str,
    file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(require_user),
) -> ApiResponse:
    """Upload a file to session workspace (/home/scienceclaw/{session_id}/)."""
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        _require_session_unlocked(session, current_user)

        workspace_dir = _Path(_WORKSPACE_DIR) / session_id
        workspace_dir.mkdir(parents=True, exist_ok=True)
        workspace_dir.chmod(0o777)

        safe_filename = _Path(file.filename or "upload").name
        if not safe_filename or safe_filename in {".", ".."}:
            safe_filename = "upload"

        target_path = workspace_dir / safe_filename
        if target_path.exists():
            stem = target_path.stem
            suffix = target_path.suffix
            i = 1
            while target_path.exists():
                target_path = workspace_dir / f"{stem}_{i}{suffix}"
                i += 1

        content = await file.read()
        target_path.write_bytes(content)

        abs_path = str(target_path)
        stat = target_path.stat()
        logger.info(f"[Upload] Saved file to {abs_path} ({stat.st_size} bytes)")

        return ApiResponse(data={
            "file_id": abs_path,
            "filename": target_path.name,
            "size": stat.st_size,
            "upload_date": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            "content_type": file.content_type or "application/octet-stream",
            "file_url": f"/api/v1/sessions/{session_id}/sandbox-file/download?path={abs_path}",
            "metadata": {"sandbox_path": abs_path, "session_id": session_id},
        })
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("upload_session_file failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ═══════════════════════════════════════════════════════════════════
# Real-time session notifications (SSE)
# ═══════════════════════════════════════════════════════════════════

@router.get("/notifications")
async def session_notifications(
    request: Request,
    current_user: User = Depends(require_user),
) -> EventSourceResponse:
    """SSE stream that pushes session_created / session_updated events."""
    from backend.notifications import subscribe, unsubscribe

    sub_id, events = await subscribe()
    user_id = current_user.id

    async def event_generator():
        try:
            async for event in events:
                if await request.is_disconnected():
                    break
                evt_data = event.get("data", {})
                if evt_data.get("user_id") and evt_data["user_id"] != user_id:
                    continue
                yield {
                    "event": event["event"],
                    "data": _json_dumps(evt_data),
                }
        except asyncio.CancelledError:
            pass
        finally:
            await unsubscribe(sub_id)

    return EventSourceResponse(event_generator())


@router.post("/{session_id}/vnc/signed-url", response_model=ApiResponse)
async def get_vnc_signed_url(
    session_id: str,
    body: VncSignedUrlRequest = VncSignedUrlRequest(),
    current_user: User = Depends(require_user),
) -> ApiResponse:
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        _require_session_unlocked(session, current_user)

        expires_in = body.expire_minutes * 60
        expires_at = _now_ts() + expires_in
        query = urlencode({
            "expires": str(expires_at),
            "user_id": current_user.id,
            "sig": _build_vnc_signature(session_id, current_user.id, expires_at),
        })
        signed_url = f"/api/v1/sessions/{session_id}/vnc/ws?{query}"
        return ApiResponse(data=VncSignedUrlData(
            signed_url=signed_url,
            expires_in=expires_in,
        ).model_dump())
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("get_vnc_signed_url failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{session_id}/export-pdf")
async def export_session_pdf(
    session_id: str,
    body: ExportPdfRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_user),
) -> Response:
    locale = _normalize_pdf_locale(body.locale)
    try:
        session = await async_get_science_session(session_id)
    except ScienceSessionNotFoundError:
        return _pdf_error_response("PDF_EXPORT_SESSION_NOT_FOUND")
    except Exception:
        logger.exception("export_session_pdf session lookup failed")
        return _pdf_error_response("PDF_EXPORT_UNKNOWN_ERROR")

    if session.user_id != current_user.id:
        return _pdf_error_response("PDF_EXPORT_ACCESS_DENIED")
    if not _is_session_unlocked(session, current_user):
        return _pdf_error_response("PDF_EXPORT_ACCESS_DENIED")

    if _pdf_payload_size_bytes(body) > _PDF_EXPORT_MAX_PAYLOAD_BYTES:
        return _pdf_error_response("PDF_EXPORT_PAYLOAD_TOO_LARGE")

    title = (getattr(session, "title", None) or _PDF_EXPORT_DEFAULT_TITLE[locale]).strip()
    header_title = _truncate_pdf_header_title(title or _PDF_EXPORT_DEFAULT_TITLE[locale])
    exported_at_text = _format_pdf_exported_at(datetime.now().astimezone().replace(microsecond=0), locale)
    cache_key = _build_pdf_cache_key(session_id, title, body.html, body.css)
    full_html = _build_pdf_html(
        body.html,
        body.css,
        header_title=header_title,
        exported_at_text=exported_at_text,
        locale=locale,
    )

    try:
        await _cleanup_expired_pdf_cache(session_id)
        cached_pdf = await _download_pdf_cache_if_fresh(session_id, cache_key)
        if cached_pdf is not None:
            if not _is_pdf_bytes(cached_pdf):
                return _pdf_error_response("PDF_EXPORT_INVALID_PDF")
            return _pdf_response(session_id, cached_pdf, "hit")

        pdf = await _render_pdf_in_sandbox(
            session_id,
            full_html,
            header_title,
            exported_at_text,
            _pdf_cache_pdf_path(session_id, cache_key),
        )
        if not _is_pdf_bytes(pdf):
            return _pdf_error_response("PDF_EXPORT_INVALID_PDF")
        await _write_pdf_cache_metadata(session_id, cache_key)
        background_tasks.add_task(
            _delete_pdf_cache_key_later,
            session_id,
            cache_key,
            _PDF_EXPORT_CACHE_TTL_SECONDS,
        )
        return _pdf_response(session_id, pdf, "miss")
    except httpx.TimeoutException:
        logger.warning("export_session_pdf timed out for session {}", session_id)
        return _pdf_error_response("PDF_EXPORT_TIMEOUT")
    except asyncio.TimeoutError:
        logger.warning("export_session_pdf timed out for session {}", session_id)
        return _pdf_error_response("PDF_EXPORT_TIMEOUT")
    except ValueError as exc:
        if str(exc) == "invalid pdf":
            return _pdf_error_response("PDF_EXPORT_INVALID_PDF")
        logger.warning("export_session_pdf value error for session {}", session_id, exc_info=True)
        return _pdf_error_response("PDF_EXPORT_RENDER_FAILED")
    except Exception:
        logger.exception("export_session_pdf render failed")
        return _pdf_error_response("PDF_EXPORT_RENDER_FAILED")


@router.websocket("/{session_id}/vnc/ws")
async def proxy_vnc_websocket(
    websocket: WebSocket,
    session_id: str,
    expires: int = Query(...),
    user_id: str = Query(...),
    sig: str = Query(...),
) -> None:
    try:
        session = await async_get_science_session(session_id)
        if session.user_id != user_id or not _is_valid_vnc_signature(session_id, user_id, expires, sig):
            await websocket.close(code=1008)
            return
        if not _is_session_unlocked(session, User(id=user_id, username=user_id, role="user")):
            await websocket.close(code=1008)
            return
    except ScienceSessionNotFoundError:
        await websocket.close(code=1008)
        return

    requested_protocol = websocket.headers.get("sec-websocket-protocol", "")
    requested_protocols = [p.strip() for p in requested_protocol.split(",")]
    subprotocol = "binary" if "binary" in requested_protocols else None
    await websocket.accept(subprotocol=subprotocol)

    try:
        import websockets

        upstream_url = _get_sandbox_vnc_websockify_url()
        async with websockets.connect(
            upstream_url,
            subprotocols=["binary"] if subprotocol else None,
            max_size=None,
        ) as upstream:
            async def client_to_upstream() -> None:
                while True:
                    message = await websocket.receive()
                    if message.get("type") == "websocket.disconnect":
                        await upstream.close()
                        return
                    if message.get("bytes") is not None:
                        await upstream.send(message["bytes"])
                    elif message.get("text") is not None:
                        await upstream.send(message["text"])

            async def upstream_to_client() -> None:
                async for message in upstream:
                    if isinstance(message, bytes):
                        await websocket.send_bytes(message)
                    else:
                        await websocket.send_text(message)

            done, pending = await asyncio.wait(
                {
                    asyncio.create_task(client_to_upstream()),
                    asyncio.create_task(upstream_to_client()),
                },
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            for task in done:
                task.result()
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("VNC websocket proxy failed")
        try:
            await websocket.close(code=1011)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════
# Session CRUD（/{session_id} 路由必须在 /skills, /tools 之后）
# ═══════════════════════════════════════════════════════════════════

@router.get("/{session_id}", response_model=ApiResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    try:
        session = await _get_owned_session_or_404(session_id, current_user)

        events = getattr(session, "events", []) or []
        locked = _session_has_password(session) and not _is_session_unlocked(session, current_user)
        # 从 session.model_config 中提取 model_config_id
        mc = getattr(session, "model_config", None)
        mc_id = mc.get("id") if isinstance(mc, dict) else None
        return ApiResponse(data=GetSessionData(
            session_id=session.session_id,
            title=getattr(session, "title", None),
            status=getattr(session, "status", SessionStatus.PENDING),
            events=[] if locked else events,
            is_shared=getattr(session, "is_shared", False),
            mode=getattr(session, "mode", "deep"),
            model_config_id=mc_id,
            selected_skill_names=getattr(session, "selected_skill_names", []) or [],
            has_password=_session_has_password(session),
            locked=locked,
        ).model_dump())
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("get_session failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/{session_id}", response_model=ApiResponse)
async def remove_session(session_id: str, current_user: User = Depends(require_user)) -> ApiResponse:
    try:
        session = await async_get_science_session(session_id)
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        await async_delete_science_session(session_id)
        return ApiResponse(data={"ok": True})
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("remove_session failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Session Update Endpoints (Pin, Archive, Title) ──

class PinRequest(BaseModel):
    pinned: bool

class TitleRequest(BaseModel):
    title: str


@router.post("/{session_id}/password", response_model=ApiResponse)
async def set_session_password(
    session_id: str,
    body: SetPasswordRequest,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        if _session_has_password(session):
            raise HTTPException(status_code=400, detail="Session already has password")
        _validate_session_password_strength(body.password)
        session.password_hash = _hash_session_password(body.password)
        session.password_hint = _normalize_password_hint(body.hint)
        session.is_shared = False
        _clear_session_unlocks(session)
        _mark_session_unlocked(session, current_user)
        await session.save()
        return ApiResponse(data={"has_password": True})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("set_session_password failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.put("/{session_id}/password", response_model=ApiResponse)
async def update_session_password(
    session_id: str,
    body: UpdatePasswordRequest,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        if not _session_has_password(session):
            raise HTTPException(status_code=400, detail="Session has no password")
        if not _verify_session_password(body.old_password, session.password_hash):
            raise HTTPException(status_code=400, detail="Invalid session password")
        _validate_session_password_strength(body.new_password, "New password")
        session.password_hash = _hash_session_password(body.new_password)
        session.password_hint = _normalize_password_hint(body.hint)
        session.is_shared = False
        _clear_session_unlocks(session)
        _mark_session_unlocked(session, current_user)
        await session.save()
        return ApiResponse(data={"has_password": True})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("update_session_password failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{session_id}/password/remove", response_model=ApiResponse)
async def remove_session_password(
    session_id: str,
    body: RemovePasswordRequest,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        if not _session_has_password(session):
            raise HTTPException(status_code=400, detail="Session has no password")
        if not _verify_session_password(body.password, session.password_hash):
            raise HTTPException(status_code=400, detail="Invalid session password")
        session.password_hash = None
        session.password_hint = None
        _clear_session_unlocks(session)
        await session.save()
        return ApiResponse(data={"has_password": False})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("remove_session_password failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{session_id}/verify-password", response_model=ApiResponse)
async def verify_session_password(
    session_id: str,
    body: VerifyPasswordRequest,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        if not _session_has_password(session):
            return ApiResponse(data={"valid": True})
        valid = _verify_session_password(body.password, session.password_hash)
        if valid:
            _mark_session_unlocked(session, current_user)
        return ApiResponse(data={"valid": valid})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("verify_session_password failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{session_id}/password-hint", response_model=ApiResponse)
async def get_session_password_hint(
    session_id: str,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        return ApiResponse(data={"hint": getattr(session, "password_hint", None)})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("get_session_password_hint failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{session_id}/reset-password", response_model=ApiResponse)
async def reset_session_password(
    session_id: str,
    body: ResetPasswordRequest,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        user_doc = await _db.get_collection("users").find_one({"_id": current_user.id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        password_hash = user_doc.get("password_hash")
        if not password_hash or not _verify_session_password(body.account_password, password_hash):
            raise HTTPException(status_code=400, detail="Invalid account password")

        if body.new_password:
            _validate_session_password_strength(body.new_password, "New password")
            session.password_hash = _hash_session_password(body.new_password)
            session.password_hint = _normalize_password_hint(body.hint)
            session.is_shared = False
            has_password = True
        else:
            session.password_hash = None
            session.password_hint = None
            has_password = False

        _clear_session_unlocks(session)
        if has_password:
            _mark_session_unlocked(session, current_user)
        await session.save()
        return ApiResponse(data={"has_password": has_password})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("reset_session_password failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{session_id}/password/lock", response_model=ApiResponse)
async def lock_session_password(
    session_id: str,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        if _session_has_password(session):
            _lock_session_for_user(session, current_user)
        return ApiResponse(data={"locked": _session_has_password(session)})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("lock_session_password failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/password/lock-all", response_model=ApiResponse)
async def lock_all_session_passwords(current_user: User = Depends(require_user)) -> ApiResponse:
    locked_count = 0
    try:
        async with session_store._sessions_lock:
            for session in session_store._sessions.values():
                if getattr(session, "user_id", None) == current_user.id and _session_has_password(session):
                    before = _is_session_unlocked(session, current_user)
                    _lock_session_for_user(session, current_user)
                    if before:
                        locked_count += 1
        return ApiResponse(data={"locked": True, "count": locked_count})
    except Exception as exc:
        logger.exception("lock_all_session_passwords failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch("/{session_id}/pin", response_model=ApiResponse)
async def update_session_pin(
    session_id: str,
    request: PinRequest,
    current_user: User = Depends(require_user)
) -> ApiResponse:
    """Pin or unpin a session."""
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        session.pinned = request.pinned
        await session.save()
        return ApiResponse(data={"session_id": session_id, "pinned": request.pinned})
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("update_session_pin failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch("/{session_id}/title", response_model=ApiResponse)
async def update_session_title(
    session_id: str,
    request: TitleRequest,
    current_user: User = Depends(require_user)
) -> ApiResponse:
    """Update session title."""
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        session.title = request.title
        await session.save()
        return ApiResponse(data={"session_id": session_id, "title": request.title})
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("update_session_title failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{session_id}/clear_unread_message_count", response_model=ApiResponse)
async def clear_unread_message_count(
    session_id: str,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        _require_session_unlocked(session, current_user)
        session.unread_message_count = 0
        await session.save()
        return ApiResponse(data={"ok": True})
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("clear_unread_message_count failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{session_id}/stop", response_model=ApiResponse)
async def stop_session(
    session_id: str,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        _require_session_unlocked(session, current_user)
        session.cancel()
        setattr(session, "status", SessionStatus.COMPLETED)
        await session.save()
        return ApiResponse(data={"ok": True})
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("stop_session failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Background agent execution (decoupled from SSE) ──

import asyncio as _asyncio

_agent_tasks: Dict[str, "_asyncio.Task[None]"] = {}
_agent_queues: Dict[str, "_asyncio.Queue[Optional[Dict[str, str]]]"] = {}


async def cleanup_orphaned_sessions() -> int:
    """Mark orphaned sessions as completed on startup.

    Called during lifespan startup — any RUNNING session or PENDING session
    with events must be orphaned because the process was restarted.
    Brand-new PENDING sessions (no events) are left intact.
    """
    now = _now_ts()
    result = await _db.get_collection("sessions").update_many(
        {"$or": [
            {"status": SessionStatus.RUNNING},
            {"status": SessionStatus.PENDING, "events.0": {"$exists": True}},
        ]},
        {
            "$set": {"status": SessionStatus.COMPLETED, "updated_at": now},
            "$push": {"events": {
                "event": "done",
                "data": {
                    "event_id": shortuuid.uuid(),
                    "timestamp": now,
                    "statistics": {},
                    "interrupted": True,
                },
            }},
        },
    )
    if result.modified_count:
        logger.info(
            f"[Startup] Cleaned up {result.modified_count} orphaned session(s) "
            "(running/pending → completed)"
        )
    return result.modified_count


async def graceful_shutdown_agents() -> None:
    """Cancel every running agent task and bulk-update DB status.

    Called during lifespan shutdown so that a normal restart does not
    leave orphaned sessions in the database.
    """
    tasks_to_cancel = [
        (sid, t) for sid, t in list(_agent_tasks.items()) if not t.done()
    ]
    for sid, task in tasks_to_cancel:
        task.cancel()
    for sid, task in tasks_to_cancel:
        try:
            await task
        except (_asyncio.CancelledError, Exception):
            pass

    _agent_tasks.clear()
    _agent_queues.clear()

    now = _now_ts()
    result = await _db.get_collection("sessions").update_many(
        {"status": {"$in": [SessionStatus.RUNNING, SessionStatus.PENDING]}},
        {
            "$set": {"status": SessionStatus.COMPLETED, "updated_at": now},
            "$push": {"events": {
                "event": "done",
                "data": {
                    "event_id": shortuuid.uuid(),
                    "timestamp": now,
                    "statistics": {},
                    "interrupted": True,
                },
            }},
        },
    )
    cancelled = len(tasks_to_cancel)
    orphaned = result.modified_count
    if cancelled or orphaned:
        logger.info(
            f"[Shutdown] Cancelled {cancelled} agent task(s), "
            f"cleaned up {orphaned} orphaned session(s)"
        )


def _emit_to_sse(session_id: str, event: Dict[str, str]) -> None:
    """Push an SSE event dict to the live queue (if a client is connected)."""
    q = _agent_queues.get(session_id)
    if q is not None:
        try:
            q.put_nowait(event)
        except Exception:
            pass


async def _agent_background_worker(
    session: Any,
    session_id: str,
    message: str,
    attachments: List[str],
    event_id: Optional[str] = None,
    timestamp: Optional[int] = None,
    language: Optional[str] = None,
) -> None:
    """Run agent in a background task. Results are saved to DB and pushed to SSE."""
    from backend.notifications import publish as _notify

    user_attachments = attachments or []
    _is_im = getattr(session, "source", None) in ("wechat", "lark")
    _im_user_id = getattr(session, "user_id", None)

    if message.strip():
        user_event = _wrap_event("message", {
            "event_id": event_id or _new_event_id(),
            "timestamp": timestamp or _now_ts(),
            "content": message,
            "role": "user",
            "attachments": user_attachments,
        })
        _append_session_event(session, user_event)
        await session.save()
        if _is_im and _im_user_id:
            _notify("session_updated", {
                "session_id": session_id,
                "user_id": _im_user_id,
                "session_event": user_event,
            })

    session.reset_cancel()
    setattr(session, "status", SessionStatus.RUNNING)
    await session.save()

    # Snapshot workspace before agent execution for round-level file tracking
    pre_file_snapshot = _snapshot_workspace_files(session.vm_root_dir)

    statistics: Dict[str, Any] = {}
    _chunk_buffer: list[str] = []

    def _emit(evt_name: str, data_json: str) -> None:
        _emit_to_sse(session_id, {"event": evt_name, "data": data_json})
        if _is_im and _im_user_id:
            _notify("session_updated", {
                "session_id": session_id,
                "user_id": _im_user_id,
                "session_event": {"event": evt_name, "data": json.loads(data_json)},
            })

    # Generate title after the first user message
    if message.strip() and not (getattr(session, "title", None) or "").strip():
        events = getattr(session, "events", []) or []
        if _count_user_messages(events) <= 1:
            try:
                gen_title = await _generate_session_title(message)
                if gen_title:
                    setattr(session, "title", gen_title)
                    await session.save()
                    _emit("title", _json_dumps({
                        "event_id": _new_event_id(),
                        "timestamp": _now_ts(),
                        "title": gen_title,
                    }))
            except Exception as exc:
                logger.warning("Title generation failed: %s", exc)

    try:
        async for evt in arun_science_task_stream(
            session=session, query=message or "", attachments=user_attachments,
            language=language,
        ):
            if session.is_cancelled():
                _emit("error", _json_dumps({
                    "event_id": _new_event_id(), "timestamp": _now_ts(),
                    "error": "Session stopped by user",
                }))
                return

            mapped = _map_science_stream_to_agent_event(evt)
            if mapped is None:
                continue

            if mapped.get("event") == "statistics":
                statistics = mapped.get("data", {})
                continue

            evt_name = mapped.get("event")

            if evt_name == "message_chunk":
                _chunk_buffer.append(mapped.get("data", {}).get("content", ""))
                _emit(evt_name, _json_dumps(mapped["data"]))
                continue

            if evt_name == "message_chunk_done":
                if _chunk_buffer:
                    full_content = "".join(_chunk_buffer)
                    persist_event = _wrap_event("message", {
                        "event_id": _new_event_id(), "timestamp": _now_ts(),
                        "content": full_content, "role": "assistant", "attachments": [],
                    })
                    _append_session_event(session, persist_event)
                    await session.save()
                    _chunk_buffer.clear()
                _emit(evt_name, _json_dumps(mapped["data"]))
                continue

            _append_session_event(session, mapped)
            if evt_name in ["message", "tool", "step", "plan"]:
                await session.save()
            _emit(evt_name, _json_dumps(mapped["data"]))

    except Exception as exc:
        logger.exception(f"[AgentWorker] session={session_id} failed")
        error_event = _wrap_event("error", {
            "event_id": _new_event_id(), "timestamp": _now_ts(), "error": str(exc),
        })
        _append_session_event(session, error_event)
        _emit(error_event["event"], _json_dumps(error_event["data"]))

    finally:
        if _chunk_buffer:
            full_content = "".join(_chunk_buffer)
            persist_event = _wrap_event("message", {
                "event_id": _new_event_id(), "timestamp": _now_ts(),
                "content": full_content, "role": "assistant", "attachments": [],
            })
            _append_session_event(session, persist_event)
            _chunk_buffer.clear()

        setattr(session, "status", SessionStatus.COMPLETED)

        # Auto-detect skills
        try:
            saved_skills = {
                d.name for d in _Path(_EXTERNAL_SKILLS_DIR).iterdir()
                if d.is_dir() and not d.name.startswith(".")
            } if _Path(_EXTERNAL_SKILLS_DIR).is_dir() else set()
            detected_skills: set = set()
            for sub in [".agents/skills", "skills"]:
                skills_dir = _Path(_WORKSPACE_DIR) / session_id / sub
                if not skills_dir.is_dir():
                    continue
                for child in sorted(skills_dir.iterdir()):
                    if (child.is_dir()
                            and not child.name.startswith(".")
                            and (child / "SKILL.md").is_file()
                            and child.name not in saved_skills
                            and child.name not in detected_skills):
                        detected_skills.add(child.name)
                        _emit("skill_save_prompt", _json_dumps({
                            "event_id": _new_event_id(),
                            "timestamp": _now_ts(),
                            "skill_name": child.name,
                        }))
        except Exception:
            logger.debug("skill auto-detect skipped", exc_info=True)

        # Auto-detect tools
        try:
            staging_dir = _Path(_WORKSPACE_DIR) / session_id / "tools_staging"
            if staging_dir.is_dir():
                saved_tools = {
                    f.stem for f in _Path(_TOOLS_DIR).glob("*.py")
                    if f.name != "__init__.py"
                } if _Path(_TOOLS_DIR).is_dir() else set()
                for child in sorted(staging_dir.glob("*.py")):
                    tool_name = child.stem
                    if tool_name not in saved_tools and "@tool" in child.read_text(encoding="utf-8", errors="replace"):
                        _emit("tool_save_prompt", _json_dumps({
                            "event_id": _new_event_id(),
                            "timestamp": _now_ts(),
                            "tool_name": tool_name,
                        }))
        except Exception:
            logger.debug("tool auto-detect skipped", exc_info=True)

        # Compute files created/modified during this round
        round_files: List[Dict[str, Any]] = []
        try:
            post_file_snapshot = _snapshot_workspace_files(session.vm_root_dir)
            round_files = _diff_workspace_files(
                pre_file_snapshot, post_file_snapshot,
                session.vm_root_dir, session_id,
            )
        except Exception:
            logger.debug("round_files diff failed", exc_info=True)

        done_event = _wrap_event("done", {
            "event_id": _new_event_id(),
            "timestamp": _now_ts(),
            "statistics": statistics,
            "round_files": round_files,
        })
        _append_session_event(session, done_event)
        await session.save()
        _emit(done_event["event"], _json_dumps(done_event["data"]))

        # Signal SSE stream completion
        q = _agent_queues.get(session_id)
        if q is not None:
            try:
                q.put_nowait(None)
            except Exception:
                pass

        _agent_tasks.pop(session_id, None)
        _agent_queues.pop(session_id, None)
        logger.info(f"[AgentWorker] session={session_id} completed")


@router.post("/{session_id}/chat")
async def chat_with_session(
    session_id: str, 
    body: ChatRequest, 
    request: Request, 
    current_user: User = Depends(require_user)
) -> EventSourceResponse:

    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        _require_session_unlocked(session, current_user)
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # Hot-swap model config if the user switched models mid-conversation
    if body.model_config_id:
        current_mc = getattr(session, "model_config", None)
        current_mc_id = current_mc.get("id") if isinstance(current_mc, dict) else None
        if body.model_config_id != current_mc_id:
            mc = await get_model_config(body.model_config_id)
            if mc:
                if not mc.is_system and mc.user_id != current_user.id:
                    raise HTTPException(status_code=403, detail="Cannot use this model")
                session.model_config = mc.model_dump()
                await session.save()
                logger.info(f"[Chat] Model switched for session {session_id}: {current_mc_id} → {body.model_config_id}")

    selected_skill_names = _normalize_selected_skill_names(body.selected_skill_names)
    if selected_skill_names != (getattr(session, "selected_skill_names", []) or []):
        session.selected_skill_names = selected_skill_names
        await session.save()
        logger.info(f"[Chat] Selected skills updated for session {session_id}: {selected_skill_names}")

    existing_task = _agent_tasks.get(session_id)
    is_reconnect = existing_task is not None and not existing_task.done()

    # Orphan detection: session DB says RUNNING but no live agent task exists
    # (happens after a server restart). Don't start a phantom agent — just
    # mark completed and inform the client immediately.
    # Only RUNNING sessions can be orphaned; PENDING sessions never had an
    # agent so they are simply idle (not orphaned).
    is_orphan = (
        not is_reconnect
        and session.status == SessionStatus.RUNNING
        and not body.message
    )
    if is_orphan:
        session.status = SessionStatus.COMPLETED
        done_data = {
            "event_id": _new_event_id(),
            "timestamp": _now_ts(),
            "statistics": {},
            "interrupted": True,
        }
        _append_session_event(session, _wrap_event("done", done_data))
        await session.save()
        logger.info(f"[Chat] Orphaned session {session_id} recovered → completed")

        async def _orphan_generator():
            yield {"event": "done", "data": _json_dumps(done_data)}

        return EventSourceResponse(_orphan_generator())

    # Create a fresh SSE queue for this connection
    queue: _asyncio.Queue[Optional[Dict[str, str]]] = _asyncio.Queue()
    _agent_queues[session_id] = queue

    if not is_reconnect:
        task = _asyncio.create_task(
            _agent_background_worker(
                session, session_id,
                body.message or "", body.attachments or [],
                event_id=body.event_id, timestamp=body.timestamp,
                language=body.language,
            )
        )
        _agent_tasks[session_id] = task
    else:
        logger.info(f"[Chat] Reconnecting SSE to running agent for session {session_id}")

    # Capture the cursor so we can replay missed events on reconnection.
    # Keep it separate from the persisted user-message event_id so restored
    # history is not de-duplicated away on the frontend.
    client_cursor = (
        body.cursor_event_id
        if is_reconnect
        else None
    ) or (body.event_id if is_reconnect else None)

    async def event_generator():
        try:
            # On reconnection: replay events the client missed (between getSession and now)
            if client_cursor:
                found_cursor = False
                for evt in list(session.events):
                    evt_data = evt.get("data", {})
                    if not found_cursor:
                        if evt_data.get("event_id") == client_cursor:
                            found_cursor = True
                        continue
                    yield {"event": evt["event"], "data": _json_dumps(evt_data)}

            # Stream live events from the background worker
            while True:
                try:
                    event = await _asyncio.wait_for(queue.get(), timeout=600)
                except _asyncio.TimeoutError:
                    break
                if event is None:
                    break
                yield event
        except _asyncio.CancelledError:
            pass
        finally:
            if _agent_queues.get(session_id) is queue:
                _agent_queues.pop(session_id, None)

    return EventSourceResponse(event_generator())


@router.post("/{session_id}/share", response_model=ApiResponse)
async def share_session(
    session_id: str,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        _require_session_unlocked(session, current_user)
        if _session_has_password(session):
            raise HTTPException(status_code=400, detail="Password protected sessions cannot be shared")
        session.is_shared = True
        await session.save()
        return ApiResponse(data={"session_id": session_id, "is_shared": True})
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("share_session failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/{session_id}/share", response_model=ApiResponse)
async def unshare_session(
    session_id: str,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        _require_session_unlocked(session, current_user)
        session.is_shared = False
        await session.save()
        return ApiResponse(data={"session_id": session_id, "is_shared": False})
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("unshare_session failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ═══════════════════════════════════════════════════════════════════
# 沙盒文件管理
# ═══════════════════════════════════════════════════════════════════

def _classify_file(rel_path: str) -> str:
    """Classify a workspace file by its relative path into a UI category."""
    top_dir = rel_path.split("/", 1)[0] if "/" in rel_path else ""
    basename = rel_path.rsplit("/", 1)[-1]

    if top_dir in ("_diagnostic", "tools_staging", "__pycache__"):
        return "process"
    if basename in ("CONTEXT.md", "planner.md", "AGENTS.md") or basename.startswith("."):
        return "process"
    if top_dir in ("research_data",):
        return "process"
    if basename.endswith(".pyc"):
        return "process"
    return "result"


@router.get("/{session_id}/files", response_model=ApiResponse)
async def list_session_files(
    session_id: str,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    """列出 session workspace 目录（/home/scienceclaw/{session_id}/）下的所有文件。"""
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        _require_session_unlocked(session, current_user)

        workspace_dir = session.vm_root_dir
        if not workspace_dir.is_dir():
            return ApiResponse(data=[])

        file_list: List[Dict[str, Any]] = []
        for file_path in sorted(workspace_dir.rglob("*")):
            if not file_path.is_file():
                continue
            abs_path = str(file_path)
            try:
                rel_path = str(file_path.relative_to(workspace_dir))
            except ValueError:
                rel_path = file_path.name
            try:
                stat = file_path.stat()
                upload_date = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                file_size = stat.st_size
            except OSError:
                upload_date = datetime.now(timezone.utc).isoformat()
                file_size = 0
            file_list.append({
                "file_id": abs_path,
                "filename": file_path.name,
                "size": file_size,
                "upload_date": upload_date,
                "content_type": "text/plain",
                "file_url": f"/api/v1/sessions/{session_id}/sandbox-file/download?path={abs_path}",
                "category": _classify_file(rel_path),
                "metadata": {"sandbox_path": abs_path, "session_id": session_id},
            })

        return ApiResponse(data=file_list)
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("list_session_files failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{session_id}/sandbox-file")
async def read_sandbox_file(
    session_id: str,
    path: str,
    current_user: User = Depends(require_user),
):
    """代理读取沙盒文件内容。path 必须在 session workspace 目录下。"""
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        _require_session_unlocked(session, current_user)

        workspace_prefix = str(session.vm_root_dir) + "/"
        if not path.startswith(workspace_prefix):
            raise HTTPException(status_code=403, detail="File path not under session workspace")

        local_path = _Path(path)
        if local_path.is_file():
            try:
                content = local_path.read_text(encoding="utf-8", errors="replace")
                return ApiResponse(data={"file": path, "content": content})
            except Exception:
                pass

        content = await _sandbox_file_read(path)
        if content is None:
            raise HTTPException(status_code=404, detail="File not found")

        return ApiResponse(data={"file": path, "content": content})
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("read_sandbox_file failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{session_id}/sandbox-file/download")
async def download_sandbox_file(
    session_id: str,
    path: str = Query(...),
    current_user: User = Depends(require_user),
):
    """直接返回沙盒文件原始内容（用于下载/预览）。优先本地文件系统，回退 sandbox API。"""
    try:
        session = await _get_owned_session_or_404(session_id, current_user)
        _require_session_unlocked(session, current_user)

        workspace_prefix = str(session.vm_root_dir) + "/"
        if not path.startswith(workspace_prefix):
            raise HTTPException(status_code=403, detail="File path not under session workspace")

        local_path = _Path(path)
        if local_path.is_file():
            return FileResponse(
                path=str(local_path),
                filename=local_path.name,
                media_type="application/octet-stream",
            )

        content = await _sandbox_file_read(path)
        if content is None:
            raise HTTPException(status_code=404, detail="File not found")

        filename = path.rsplit("/", 1)[-1] if "/" in path else path
        from urllib.parse import quote
        try:
            filename.encode("ascii")
            cd_header = f'attachment; filename="{filename}"'
        except UnicodeEncodeError:
            encoded = quote(filename)
            cd_header = f"attachment; filename*=UTF-8''{encoded}"
        return Response(
            content=content.encode("utf-8") if isinstance(content, str) else content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": cd_header},
        )
    except ScienceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("download_sandbox_file failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
