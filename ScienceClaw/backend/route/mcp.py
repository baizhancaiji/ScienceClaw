from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter(prefix="/mcp", tags=["mcp"])


class ApiResponse(BaseModel):
    code: int = Field(default=0)
    msg: str = Field(default="ok")
    data: Any = Field(default=None)


@router.get("/health", response_model=ApiResponse)
async def mcp_health() -> ApiResponse:
    return ApiResponse(data={"status": "ok"})
