from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse
import uuid

import httpx


DEFAULT_MCP_TIMEOUT_SECONDS = 15.0
MCP_PROTOCOL_VERSION = "2024-11-05"


@dataclass
class MCPClientError(Exception):
    code: str
    message: str
    retryable: bool = False
    status_code: int | None = None

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.status_code is not None:
            data["status_code"] = self.status_code
        return data


@dataclass
class MCPRemoteTool:
    name: str
    description: str
    input_schema_raw: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema_raw": self.input_schema_raw,
        }


async def initialize(
    endpoint_url: str,
    headers: dict[str, str] | None = None,
    timeout_seconds: float = DEFAULT_MCP_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    return await request(
        endpoint_url,
        "initialize",
        params={
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {
                "name": "ScienceClaw",
                "version": "0.1",
            },
        },
        headers=headers,
        timeout_seconds=timeout_seconds,
    )


async def list_tools(
    endpoint_url: str,
    headers: dict[str, str] | None = None,
    timeout_seconds: float = DEFAULT_MCP_TIMEOUT_SECONDS,
) -> list[MCPRemoteTool]:
    result = await request(
        endpoint_url,
        "tools/list",
        params={},
        headers=headers,
        timeout_seconds=timeout_seconds,
    )
    return _parse_tools_list_result(result)


async def request(
    endpoint_url: str,
    method: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout_seconds: float = DEFAULT_MCP_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    _validate_https_endpoint(endpoint_url)
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": method,
        "params": params or {},
    }
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds),
            verify=True,
        ) as http_client:
            response = await http_client.post(
                endpoint_url,
                json=payload,
                headers=_build_headers(headers),
            )
    except httpx.TimeoutException as exc:
        raise MCPClientError(
            code="remote_mcp_timeout",
            message="Remote MCP request timed out",
            retryable=True,
        ) from exc
    except httpx.ConnectError as exc:
        raise MCPClientError(
            code="remote_mcp_connection_error",
            message="Remote MCP connection failed",
            retryable=True,
        ) from exc
    except httpx.TransportError as exc:
        raise MCPClientError(
            code="remote_mcp_transport_error",
            message="Remote MCP transport failed",
            retryable=True,
        ) from exc

    if response.status_code >= 400:
        raise MCPClientError(
            code="remote_mcp_http_error",
            message=f"Remote MCP returned HTTP {response.status_code}",
            retryable=response.status_code >= 500,
            status_code=response.status_code,
        )

    try:
        body = response.json()
    except ValueError as exc:
        raise MCPClientError(
            code="remote_mcp_invalid_response",
            message="Remote MCP returned invalid JSON",
            retryable=False,
        ) from exc

    return _parse_jsonrpc_response(body)


def _validate_https_endpoint(endpoint_url: str) -> None:
    parsed = urlparse((endpoint_url or "").strip())
    if parsed.scheme != "https" or not parsed.netloc or not parsed.path:
        raise MCPClientError(
            code="invalid_mcp_endpoint",
            message="MCP endpoint must use https://<host>/<path>",
            retryable=False,
        )


def _build_headers(headers: dict[str, str] | None) -> dict[str, str]:
    merged = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    for key, value in (headers or {}).items():
        if key and value:
            merged[key] = value
    return merged


def _parse_jsonrpc_response(body: Any) -> dict[str, Any]:
    if not isinstance(body, dict) or body.get("jsonrpc") != "2.0":
        raise MCPClientError(
            code="remote_mcp_invalid_response",
            message="Remote MCP returned an invalid JSON-RPC response",
            retryable=False,
        )
    if "error" in body:
        error = body.get("error") or {}
        message = error.get("message") if isinstance(error, dict) else None
        raise MCPClientError(
            code="remote_mcp_error",
            message=message or "Remote MCP error",
            retryable=False,
        )
    result = body.get("result")
    if not isinstance(result, dict):
        raise MCPClientError(
            code="remote_mcp_invalid_response",
            message="Remote MCP returned an invalid result",
            retryable=False,
        )
    return result


def _parse_tools_list_result(result: dict[str, Any]) -> list[MCPRemoteTool]:
    tools = result.get("tools")
    if not isinstance(tools, list):
        raise MCPClientError(
            code="remote_mcp_invalid_tools",
            message="Remote MCP tools/list returned an invalid tools list",
            retryable=False,
        )
    return [_parse_remote_tool(tool) for tool in tools]


def _parse_remote_tool(tool: Any) -> MCPRemoteTool:
    if not isinstance(tool, dict):
        raise MCPClientError(
            code="remote_mcp_invalid_tools",
            message="Remote MCP tool entry is invalid",
            retryable=False,
        )
    name = tool.get("name")
    if not isinstance(name, str) or not name.strip():
        raise MCPClientError(
            code="remote_mcp_invalid_tools",
            message="Remote MCP tool entry is missing name",
            retryable=False,
        )
    description = tool.get("description")
    input_schema = tool.get("inputSchema")
    if input_schema is None:
        input_schema = {"type": "object", "properties": {}}
    if not isinstance(input_schema, dict):
        raise MCPClientError(
            code="remote_mcp_invalid_tools",
            message="Remote MCP tool entry has invalid inputSchema",
            retryable=False,
        )
    return MCPRemoteTool(
        name=name.strip(),
        description=description.strip() if isinstance(description, str) else "",
        input_schema_raw=dict(input_schema),
    )
