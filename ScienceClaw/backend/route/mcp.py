import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.mcp import service
from backend.mcp.schemas import (
    CreateMCPServerRequest,
    ToggleMCPServerRequest,
    UpdateMCPServerRequest,
)
from backend.user.dependencies import User, require_user


router = APIRouter(prefix="/mcp", tags=["mcp"])


class ApiResponse(BaseModel):
    code: int = Field(default=0)
    msg: str = Field(default="ok")
    data: Any = Field(default=None)


@router.get("/health", response_model=ApiResponse)
async def mcp_health(_current_user: User = Depends(require_user)) -> ApiResponse:
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
    server = await service.create_server(current_user.id, body, _encryption_key())
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


def _encryption_key() -> str:
    return os.environ.get("MCP_CONFIG_ENCRYPTION_KEY", "")
