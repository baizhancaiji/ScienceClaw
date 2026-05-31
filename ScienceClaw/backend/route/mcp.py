import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.mcp import service
from backend.mcp.schemas import (
    CreateMCPServerRequest,
    ToggleMCPServerRequest,
    ToggleMCPToolRequest,
    UpdateMCPServerRequest,
)
from backend.user.dependencies import User, require_user


router = APIRouter(prefix="/mcp", tags=["mcp"], dependencies=[Depends(require_user)])


class ApiResponse(BaseModel):
    code: int = Field(default=0)
    msg: str = Field(default="ok")
    data: Any = Field(default=None)


@router.get("/health", response_model=ApiResponse)
async def mcp_health() -> ApiResponse:
    return ApiResponse(data={"status": "ok"})


@router.get("/servers", response_model=ApiResponse)
async def list_mcp_servers(current_user: User = Depends(require_user)) -> ApiResponse:
    servers = await service.list_servers(current_user.id)
    return ApiResponse(data=[server.model_dump() for server in servers])


@router.post("/servers", response_model=ApiResponse)
async def create_mcp_server(
    body: CreateMCPServerRequest,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    encryption_key = _encryption_key()
    server = await service.create_server(current_user.id, body, encryption_key)
    if body.verify_now:
        verified = await service.verify_server(
            server.id,
            current_user.id,
            encryption_key,
            sync_tools=True,
        )
        if verified is not None:
            server = verified
    return ApiResponse(data=server.model_dump())


@router.put("/servers/{server_id}", response_model=ApiResponse)
async def update_mcp_server(
    server_id: str,
    body: UpdateMCPServerRequest,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    server = await service.update_server(
        server_id,
        current_user.id,
        body,
        _encryption_key(),
    )
    if server is None:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return ApiResponse(data=server.model_dump())


@router.delete("/servers/{server_id}", response_model=ApiResponse)
async def delete_mcp_server(
    server_id: str,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    await service.delete_server(server_id, current_user.id)
    return ApiResponse(data={"ok": True})


@router.put("/servers/{server_id}/enabled", response_model=ApiResponse)
async def toggle_mcp_server_enabled(
    server_id: str,
    body: ToggleMCPServerRequest,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    patch = UpdateMCPServerRequest(enabled=body.enabled)
    server = await service.update_server(
        server_id,
        current_user.id,
        patch,
        _encryption_key(),
    )
    if server is None:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return ApiResponse(data=server.model_dump())


@router.post("/servers/{server_id}/verify", response_model=ApiResponse)
async def verify_mcp_server(
    server_id: str,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    result = await service.verify_server(server_id, current_user.id, _encryption_key())
    if result is None:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return ApiResponse(data=result.model_dump())


@router.post("/servers/{server_id}/refresh-tools", response_model=ApiResponse)
async def refresh_mcp_server_tools(
    server_id: str,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    result = await service.refresh_server_tools(server_id, current_user.id, _encryption_key())
    if result is None:
        raise HTTPException(status_code=404, detail="MCP server not found")
    data = result.model_dump()
    data["inserted"] = data.pop("added")
    return ApiResponse(data=data)


@router.get("/servers/{server_id}/tools", response_model=ApiResponse)
async def list_mcp_server_tools(
    server_id: str,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    tools = await service.list_tools_by_server(server_id, current_user.id)
    if tools is None:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return ApiResponse(data=[tool.model_dump() for tool in tools])


@router.get("/tools", response_model=ApiResponse)
async def list_enabled_mcp_tools(current_user: User = Depends(require_user)) -> ApiResponse:
    tools = await service.list_enabled_tools(current_user.id)
    return ApiResponse(data=[tool.model_dump() for tool in tools])


@router.put("/tools/{tool_id}/enabled", response_model=ApiResponse)
async def toggle_mcp_tool_enabled(
    tool_id: str,
    body: ToggleMCPToolRequest,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    tool = await service.toggle_tool_enabled(tool_id, current_user.id, body.enabled)
    if tool is None:
        raise HTTPException(status_code=404, detail="MCP tool not found")
    return ApiResponse(data=tool.model_dump())


def _encryption_key() -> str:
    return os.environ.get("MCP_CONFIG_ENCRYPTION_KEY", "")
