from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


ToolSourceType = Literal["tooluniverse", "https_mcp", "external_python_tool"]
SchemaStatus = Literal["available", "missing", "complex"]


class ToolIndexItem(BaseModel):
    tool_ref: str
    source_type: ToolSourceType
    name: str
    display_name: str = ""
    name_zh: str = ""
    description: str = ""
    description_zh: str = ""
    category_zh: str = "其他"
    aliases: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    provider: str = ""
    enabled: bool = True
    blocked: bool = False
    schema_status: SchemaStatus = "missing"
    has_examples: bool = False
    last_success_at: int | None = None

    @field_validator("display_name")
    @classmethod
    def default_display_name(cls, value: str, info) -> str:
        if value:
            return value
        data = info.data
        return str(data.get("name") or "")


class ToolSearchRequest(BaseModel):
    query: str = ""
    source_type: ToolSourceType | None = None
    category_zh: str | None = None
    limit: int = Field(default=5, ge=1, le=30)
    debug: bool = False


class ToolSearchResult(BaseModel):
    tool_ref: str
    name: str
    cat_zh: str
    why: str
    score: float | None = None
    source_type: ToolSourceType | None = None
    hit_fields: list[str] | None = None


class ToolInfoResult(BaseModel):
    tool_ref: str
    source_type: ToolSourceType
    name: str
    display_name: str = ""
    description: str = ""
    category_zh: str = "其他"
    input_schema: dict[str, Any] = Field(default_factory=dict)
    examples: list[Any] = Field(default_factory=list)
    provider: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolRunRequest(BaseModel):
    tool_ref: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolRunResult(BaseModel):
    tool_ref: str
    ok: bool = True
    result: Any = None
    error: str = ""


class ToolSearchHit(BaseModel):
    item: ToolIndexItem
    score: float = 0.0
    hit_fields: list[str] = Field(default_factory=list)
