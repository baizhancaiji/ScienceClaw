import re
import time
import uuid
from typing import Any

from backend.mcp import client
from backend.mcp.crypto import decrypt_secret, encrypt_secret
from backend.mcp import repository
from backend.mcp.schemas import (
    CreateMCPServerRequest,
    MCPMaskedHeader,
    MCPServerDetailItem,
    MCPServerListItem,
    UpdateMCPServerRequest,
)


_SLUG_RE = re.compile(r"[^a-z0-9]+")
_MAX_VERIFY_ERROR_CHARS = 300


class MCPVerifyResult(MCPServerDetailItem):
    duration_ms: int = 0


async def create_server(
    user_id: str,
    request: CreateMCPServerRequest,
    encryption_key: str | bytes | None,
) -> MCPServerDetailItem:
    now = _now()
    doc = {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "name": request.name,
        "slug": _normalize_slug(request.name),
        "transport": "https",
        "endpoint_url": request.endpoint_url,
        "auth_mode": request.auth_mode,
        "auth_config": _build_auth_config(request, encryption_key),
        "enabled": request.enabled,
        "verify_status": "unknown",
        "verify_error": "",
        "last_verified_at": None,
        "last_synced_at": None,
        "tool_count": 0,
        "created_at": now,
        "updated_at": now,
    }
    created = await repository.create_server(doc)
    return _to_detail_item(created)


async def list_servers(user_id: str) -> list[MCPServerListItem]:
    docs = await repository.list_servers(user_id)
    return [_to_list_item(doc) for doc in docs]


async def get_server(server_id: str, user_id: str) -> MCPServerDetailItem | None:
    doc = await repository.get_server(server_id, user_id)
    if doc is None:
        return None
    return _to_detail_item(doc)


async def update_server(
    server_id: str,
    user_id: str,
    request: UpdateMCPServerRequest,
    encryption_key: str | bytes | None,
) -> MCPServerDetailItem | None:
    existing = await repository.get_server(server_id, user_id)
    if existing is None:
        return None
    patch = _build_update_patch(existing, request, encryption_key)
    updated = await repository.update_server(server_id, user_id, patch)
    if updated is None:
        return None
    return _to_detail_item(updated)


async def delete_server(server_id: str, user_id: str) -> None:
    await repository.delete_server(server_id, user_id)


async def verify_server(
    server_id: str,
    user_id: str,
    encryption_key: str | bytes | None,
) -> MCPVerifyResult | None:
    started_at = time.monotonic()
    existing = await repository.get_server(server_id, user_id)
    if existing is None:
        return None
    try:
        headers = _build_request_headers(existing, encryption_key)
        await client.initialize(existing["endpoint_url"], headers=headers)
        tools = await client.list_tools(existing["endpoint_url"], headers=headers)
        patch = {
            "verify_status": "healthy",
            "verify_error": "",
            "last_verified_at": _now(),
            "tool_count": len(tools),
            "updated_at": _now(),
        }
    except client.MCPClientError as exc:
        patch = {
            "verify_status": "error",
            "verify_error": _summarize_verify_error(exc),
            "last_verified_at": _now(),
            "updated_at": _now(),
        }
    except ValueError as exc:
        patch = {
            "verify_status": "error",
            "verify_error": _summarize_verify_error(
                client.MCPClientError(
                    code="mcp_auth_error",
                    message=str(exc),
                    retryable=False,
                )
            ),
            "last_verified_at": _now(),
            "updated_at": _now(),
        }
    updated = await repository.update_server(server_id, user_id, patch)
    if updated is None:
        return None
    return MCPVerifyResult(
        **_to_detail_item(updated).model_dump(),
        duration_ms=_duration_ms(started_at),
    )


def _build_update_patch(
    existing: dict[str, Any],
    request: UpdateMCPServerRequest,
    encryption_key: str | bytes | None,
) -> dict[str, Any]:
    patch: dict[str, Any] = {"updated_at": _now()}
    if request.name is not None:
        patch["name"] = request.name
        patch["slug"] = _normalize_slug(request.name)
    if request.endpoint_url is not None:
        patch["endpoint_url"] = request.endpoint_url
        patch["verify_status"] = "unknown"
        patch["verify_error"] = ""
    if request.enabled is not None:
        patch["enabled"] = request.enabled
    if request.auth_mode is not None:
        patch["auth_mode"] = request.auth_mode
        patch["auth_config"] = _build_auth_config(request, encryption_key, existing)
        patch["verify_status"] = "unknown"
        patch["verify_error"] = ""
    return patch


def _build_auth_config(
    request: CreateMCPServerRequest | UpdateMCPServerRequest,
    encryption_key: str | bytes | None,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    auth_mode = request.auth_mode or (existing or {}).get("auth_mode") or "none"
    if auth_mode == "bearer":
        token = (request.bearer_token or "").strip()
        if not token and existing:
            return dict(existing.get("auth_config") or {})
        return {"bearer_token_encrypted": encrypt_secret(token, encryption_key)}
    if auth_mode == "headers":
        headers = request.headers
        if headers is None and existing:
            return dict(existing.get("auth_config") or {})
        encrypted_headers = [
            {
                "name": header.name,
                "value_encrypted": encrypt_secret(header.value, encryption_key),
            }
            for header in (headers or [])
        ]
        return {"headers_encrypted": encrypted_headers}
    return {}


def _build_request_headers(
    server_doc: dict[str, Any],
    encryption_key: str | bytes | None,
) -> dict[str, str]:
    auth_mode = server_doc.get("auth_mode", "none")
    auth_config = server_doc.get("auth_config") or {}
    if auth_mode == "bearer":
        token = decrypt_secret(auth_config.get("bearer_token_encrypted"), encryption_key)
        return {"Authorization": f"Bearer {token}"} if token else {}
    if auth_mode == "headers":
        headers: dict[str, str] = {}
        for header in auth_config.get("headers_encrypted", []):
            name = header.get("name", "")
            value = decrypt_secret(header.get("value_encrypted"), encryption_key)
            if name and value:
                headers[name] = value
        return headers
    return {}


def _summarize_verify_error(exc: client.MCPClientError) -> str:
    message = f"{exc.code}: {exc.message}"
    if len(message) <= _MAX_VERIFY_ERROR_CHARS:
        return message
    return message[: _MAX_VERIFY_ERROR_CHARS - 3] + "..."


def _to_list_item(doc: dict[str, Any]) -> MCPServerListItem:
    auth_config = doc.get("auth_config") or {}
    return MCPServerListItem(
        id=str(doc.get("_id", "")),
        name=doc.get("name", ""),
        slug=doc.get("slug", ""),
        transport=doc.get("transport", "https"),
        endpoint_url=doc.get("endpoint_url", ""),
        auth_mode=doc.get("auth_mode", "none"),
        enabled=bool(doc.get("enabled", True)),
        verify_status=doc.get("verify_status", "unknown"),
        verify_error=doc.get("verify_error", ""),
        tool_count=int(doc.get("tool_count", 0)),
        last_verified_at=doc.get("last_verified_at"),
        last_synced_at=doc.get("last_synced_at"),
        has_bearer_token=bool(auth_config.get("bearer_token_encrypted")),
        masked_headers=_masked_headers(auth_config),
    )


def _to_detail_item(doc: dict[str, Any]) -> MCPServerDetailItem:
    item = _to_list_item(doc)
    return MCPServerDetailItem(
        **item.model_dump(),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


def _masked_headers(auth_config: dict[str, Any]) -> list[MCPMaskedHeader]:
    return [
        MCPMaskedHeader(name=header.get("name", ""), masked_value="********")
        for header in auth_config.get("headers_encrypted", [])
    ]


def _normalize_slug(name: str) -> str:
    slug = _SLUG_RE.sub("_", name.strip().lower()).strip("_")
    return slug or "mcp_server"


def _now() -> int:
    return int(time.time())


def _duration_ms(started_at: float) -> int:
    return max(0, int((time.monotonic() - started_at) * 1000))
