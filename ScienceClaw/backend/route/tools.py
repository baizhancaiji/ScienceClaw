from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.tool_discovery import ToolRunRequest, ToolSearchRequest
from backend.tool_discovery.service import get_tool_discovery_service
from backend.user.dependencies import User, require_user


router = APIRouter(prefix="/tools", tags=["tools"], dependencies=[Depends(require_user)])


class ApiResponse(BaseModel):
    code: int = Field(default=0)
    msg: str = Field(default="ok")
    data: Any = Field(default=None)


@router.post("/search", response_model=ApiResponse)
async def search_tools(
    body: ToolSearchRequest,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    results = await get_tool_discovery_service().search(body, current_user.id)
    return ApiResponse(data={"results": [item.model_dump(exclude_none=True) for item in results]})


@router.get("/info/{tool_ref:path}", response_model=ApiResponse)
async def get_tool_info(
    tool_ref: str,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    try:
        info = await get_tool_discovery_service().get_info(tool_ref, current_user.id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ApiResponse(data=info.model_dump(exclude_none=True))


@router.post("/run", response_model=ApiResponse)
async def run_tool(
    body: ToolRunRequest,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    try:
        result = await get_tool_discovery_service().run(
            body.tool_ref,
            body.arguments,
            current_user.id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ApiResponse(data=result.model_dump(exclude_none=True))
