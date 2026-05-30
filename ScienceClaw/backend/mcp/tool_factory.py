import re
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, create_model


COMPLEX_SCHEMA_HINT = (
    "[This MCP tool exposes a complex schema. Pass arguments as a JSON object in `payload`.]"
)

_COMPLEX_SCHEMA_KEYS = {"oneOf", "anyOf", "allOf", "not", "$ref", "patternProperties"}
_TOOL_NAME_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class MCPToolDefinition:
    name: str
    description: str
    args_schema: type[BaseModel]
    input_schema_complex: bool

    def func(self, **_kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError("MCP tool execution is reserved for a later MCP batch")


def build_tool_definition(tool_doc: dict[str, Any]) -> MCPToolDefinition:
    is_complex = _is_complex_schema(tool_doc.get("input_schema_raw"))
    args_schema = schema_to_pydantic_model(
        tool_doc.get("input_schema_raw") or {},
        model_name=_model_name(tool_doc.get("canonical_name", "mcp_tool")),
    )
    description = _tool_description(tool_doc, is_complex)
    return MCPToolDefinition(
        name=canonical_tool_name(
            str(tool_doc.get("server_slug") or tool_doc.get("server_id") or "mcp_server"),
            str(tool_doc.get("original_name") or tool_doc.get("display_name") or "tool"),
        )
        if not tool_doc.get("canonical_name")
        else str(tool_doc["canonical_name"]),
        description=description,
        args_schema=args_schema,
        input_schema_complex=is_complex,
    )


def schema_to_pydantic_model(
    input_schema: dict[str, Any],
    model_name: str = "MCPToolArgs",
) -> type[BaseModel]:
    if _is_complex_schema(input_schema):
        return create_model(
            model_name,
            payload=(dict[str, Any], Field(...)),
        )
    if input_schema.get("type") != "object" or not isinstance(input_schema.get("properties"), dict):
        return create_model(
            model_name,
            payload=(dict[str, Any], Field(default_factory=dict)),
        )

    required = input_schema.get("required")
    required_fields = set(required if isinstance(required, list) else [])
    fields: dict[str, Any] = {}
    for field_name, field_schema in input_schema["properties"].items():
        if not isinstance(field_name, str) or not isinstance(field_schema, dict):
            continue
        annotation = _schema_to_annotation(field_schema, f"{model_name}_{field_name}")
        default = _field_default(field_name, field_schema, required_fields)
        fields[field_name] = (annotation, default)

    config = None
    if input_schema.get("additionalProperties") is False:
        config = ConfigDict(extra="forbid")
    return create_model(model_name, __config__=config, **fields)


def canonical_tool_name(server_slug: str, tool_name: str) -> str:
    return f"mcp__{_normalize_name_part(server_slug)}__{_normalize_name_part(tool_name)}"


def _schema_to_annotation(schema: dict[str, Any], model_name: str) -> Any:
    if _is_complex_schema(schema):
        return dict[str, Any]
    enum_values = schema.get("enum")
    if isinstance(enum_values, list) and enum_values:
        return Literal[tuple(enum_values)]
    schema_type = schema.get("type")
    if schema_type == "string":
        return str
    if schema_type == "integer":
        return int
    if schema_type == "number":
        return float
    if schema_type == "boolean":
        return bool
    if schema_type == "array":
        items = schema.get("items")
        item_type = _schema_to_annotation(items, f"{model_name}_item") if isinstance(items, dict) else Any
        return list[item_type]
    if schema_type == "object":
        if isinstance(schema.get("properties"), dict):
            return schema_to_pydantic_model(schema, model_name)
        return dict[str, Any]
    return Any


def _field_default(
    field_name: str,
    schema: dict[str, Any],
    required_fields: set[str],
) -> Any:
    if "default" in schema:
        return Field(default=schema["default"], description=schema.get("description"))
    if field_name in required_fields:
        return Field(..., description=schema.get("description"))
    return Field(default=None, description=schema.get("description"))


def _is_complex_schema(schema: Any) -> bool:
    if not isinstance(schema, dict):
        return False
    if any(key in schema for key in _COMPLEX_SCHEMA_KEYS):
        return True
    for value in schema.values():
        if isinstance(value, dict) and _is_complex_schema(value):
            return True
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and _is_complex_schema(item):
                    return True
    return False


def _tool_description(tool_doc: dict[str, Any], is_complex: bool) -> str:
    server_name = str(tool_doc.get("server_name") or tool_doc.get("server_slug") or "MCP")
    description = str(tool_doc.get("description") or "").strip()
    text = f"[MCP:{server_name}] {description}".strip()
    if is_complex:
        return f"{COMPLEX_SCHEMA_HINT}\n\n{text}"
    return text


def _normalize_name_part(value: str) -> str:
    normalized = _TOOL_NAME_RE.sub("_", value.strip().lower()).strip("_")
    return normalized or "tool"


def _model_name(value: str) -> str:
    parts = [part.capitalize() for part in _normalize_name_part(value).split("_") if part]
    return "".join(parts) + "Args" if parts else "MCPToolArgs"
