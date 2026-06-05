from __future__ import annotations

import inspect
from typing import Any, Protocol

from backend.tooluniverse_allowlist import inventory_item, is_allowed_tool_name

from .aliases import (
    classify_tool_text,
    get_tool_category_aliases,
    map_tool_category_to_zh,
)
from .schemas import ToolIndexItem, ToolInfoResult, ToolRunResult


class ToolDiscoveryProvider(Protocol):
    source_type: str

    async def list_index_items(self, user_id: str) -> list[ToolIndexItem]:
        ...

    async def get_info(self, tool_ref: str, user_id: str) -> ToolInfoResult:
        ...

    async def run(self, tool_ref: str, arguments: dict[str, Any], user_id: str) -> ToolRunResult:
        ...


class ToolUniverseProvider:
    source_type = "tooluniverse"

    async def list_index_items(self, user_id: str) -> list[ToolIndexItem]:
        from backend.route.tooluniverse import (
            _build_tools_list,
            _get_translation,
            _get_tu,
            _translate_tool_list_item,
        )

        tu = _get_tu()
        if tu is None:
            return []
        raw_items = _build_tools_list(tu)
        trans = _get_translation("zh")
        items: list[ToolIndexItem] = []
        for raw in raw_items:
            localized = _translate_tool_list_item(raw, trans) if trans else dict(raw)
            name = str(raw.get("name") or "")
            if not name:
                continue
            inv = inventory_item(name)
            category_zh = (
                inv.sub_category
                if inv and inv.sub_category
                else map_tool_category_to_zh(raw.get("category"), localized.get("category_zh"))
            )
            items.append(
                ToolIndexItem(
                    tool_ref=f"tooluniverse:{name}",
                    source_type="tooluniverse",
                    name=name,
                    display_name=name,
                    description=str(raw.get("description") or ""),
                    description_zh=str(localized.get("description") or ""),
                    category_zh=category_zh,
                    aliases=_dedupe([*get_tool_category_aliases(category_zh), str(raw.get("category") or ""), inv.main_category if inv else ""]),
                    keywords=_dedupe([name, str(raw.get("category") or ""), category_zh, inv.main_category if inv else "", "ToolUniverse"]),
                    provider="ToolUniverse",
                    schema_status="available" if int(raw.get("param_count") or 0) > 0 else "missing",
                    has_examples=bool(raw.get("has_examples")),
                )
            )
        return items

    async def get_info(self, tool_ref: str, user_id: str) -> ToolInfoResult:
        from backend.route.tooluniverse import _get_tu

        tool_name = _strip_prefix(tool_ref, "tooluniverse:")
        if not is_allowed_tool_name(tool_name):
            raise LookupError(f"ToolUniverse tool not found: {tool_name}")

        tu = _get_tu()
        if tu is None:
            raise LookupError("ToolUniverse is loading")
        spec = tu.tool_specification(tool_name, format="openai")
        if not spec:
            raise LookupError(f"ToolUniverse tool not found: {tool_name}")
        raw_tool = _find_tu_tool(tu, tool_name)
        category = raw_tool.get("category") if isinstance(raw_tool, dict) else ""
        inv = inventory_item(tool_name)
        category_zh = inv.sub_category if inv and inv.sub_category else map_tool_category_to_zh(category)
        return ToolInfoResult(
            tool_ref=tool_ref,
            source_type="tooluniverse",
            name=tool_name,
            display_name=tool_name,
            description=str(spec.get("description") or ""),
            cat_zh=category_zh,
            input_schema=spec.get("parameters") or {},
            examples=raw_tool.get("test_examples", []) if isinstance(raw_tool, dict) else [],
            provider="ToolUniverse",
            metadata={
                "category": category or "",
                "inventory_main_category": inv.main_category if inv else "",
                "inventory_sub_category": inv.sub_category if inv else "",
                "inventory_availability": inv.availability if inv else "",
                "inventory_reason": inv.reason if inv else "",
            },
        )

    async def run(self, tool_ref: str, arguments: dict[str, Any], user_id: str) -> ToolRunResult:
        from backend.route.tooluniverse import _get_tu

        tool_name = _strip_prefix(tool_ref, "tooluniverse:")
        if not is_allowed_tool_name(tool_name):
            return ToolRunResult(tool_ref=tool_ref, ok=False, error=f"ToolUniverse tool not found: {tool_name}")

        tu = _get_tu()
        if tu is None:
            return ToolRunResult(tool_ref=tool_ref, ok=False, error="ToolUniverse is loading")
        result = tu.run({"name": tool_name, "arguments": arguments})
        if inspect.isawaitable(result):
            result = await result
        return ToolRunResult(tool_ref=tool_ref, ok=True, result=result)


class HTTPSMCPProvider:
    source_type = "https_mcp"

    def __init__(self, encryption_key: str | bytes | None = None) -> None:
        self.encryption_key = encryption_key

    async def list_index_items(self, user_id: str) -> list[ToolIndexItem]:
        from backend.mcp import repository

        docs = await repository.list_enabled_tool_runtime_docs_by_user(user_id)
        items: list[ToolIndexItem] = []
        for doc in docs:
            server = doc.get("server") if isinstance(doc.get("server"), dict) else {}
            name = str(doc.get("canonical_name") or doc.get("original_name") or "")
            display_name = str(doc.get("display_name") or doc.get("original_name") or name)
            category_zh = "网页与外部服务"
            items.append(
                ToolIndexItem(
                    tool_ref=f"https_mcp:{doc.get('_id')}",
                    source_type="https_mcp",
                    name=name,
                    display_name=display_name,
                    description=str(doc.get("description") or ""),
                    category_zh=category_zh,
                    aliases=_dedupe([*get_tool_category_aliases(category_zh), str(server.get("name") or ""), "HTTPS MCP", "MCP"]),
                    keywords=_dedupe([name, display_name, str(doc.get("original_name") or ""), str(server.get("slug") or ""), "https_mcp"]),
                    provider=str(server.get("name") or "HTTPS MCP"),
                    enabled=bool(doc.get("enabled", True)),
                    blocked=bool(doc.get("removed", False)),
                    schema_status=_schema_status(doc.get("input_schema_raw")),
                    has_examples=False,
                    last_success_at=doc.get("last_success_at"),
                )
            )
        return items

    async def get_info(self, tool_ref: str, user_id: str) -> ToolInfoResult:
        doc = await self._runtime_doc(tool_ref, user_id)
        category_zh = "网页与外部服务"
        return ToolInfoResult(
            tool_ref=tool_ref,
            source_type="https_mcp",
            name=str(doc.get("canonical_name") or doc.get("original_name") or ""),
            display_name=str(doc.get("display_name") or doc.get("original_name") or ""),
            description=str(doc.get("description") or ""),
            cat_zh=category_zh,
            input_schema=doc.get("input_schema_raw") or {},
            examples=[],
            provider=str(doc.get("server_name") or "HTTPS MCP"),
            metadata={"server_id": str(doc.get("server_id") or "")},
        )

    async def run(self, tool_ref: str, arguments: dict[str, Any], user_id: str) -> ToolRunResult:
        from backend.mcp import tool_factory

        doc = await self._runtime_doc(tool_ref, user_id)
        definition = tool_factory.build_tool_definition(doc)
        result = definition.func(**arguments)
        return ToolRunResult(tool_ref=tool_ref, ok=True, result=result)

    async def _runtime_doc(self, tool_ref: str, user_id: str) -> dict[str, Any]:
        from backend.mcp import service as mcp_service

        tool_id = _strip_prefix(tool_ref, "https_mcp:")
        docs = await mcp_service.list_enabled_tool_runtime_docs(user_id, self.encryption_key)
        for doc in docs:
            if str(doc.get("id") or doc.get("_id") or "") == tool_id:
                return doc
        raise LookupError(f"HTTPS MCP tool not found: {tool_ref}")


class ExternalPythonToolsProvider:
    source_type = "external_python_tool"

    async def list_index_items(self, user_id: str) -> list[ToolIndexItem]:
        tools = self._load_tools()
        items: list[ToolIndexItem] = []
        for tool in tools:
            name = str(getattr(tool, "name", "") or "")
            if not name:
                continue
            description = str(getattr(tool, "description", "") or "")
            category_zh = classify_tool_text(name, description, default="其他")
            items.append(
                ToolIndexItem(
                    tool_ref=f"external:{name}",
                    source_type="external_python_tool",
                    name=name,
                    display_name=name,
                    description=description,
                    category_zh=category_zh,
                    aliases=_dedupe([*get_tool_category_aliases(category_zh), "Tools", "Python"]),
                    keywords=_dedupe([name, "Tools/*.py", "external_python_tool"]),
                    provider="Tools",
                    schema_status=_schema_status(getattr(tool, "args_schema", None)),
                )
            )
        return items

    async def get_info(self, tool_ref: str, user_id: str) -> ToolInfoResult:
        tool = self._find_tool(tool_ref)
        schema = {}
        args_schema = getattr(tool, "args_schema", None)
        if args_schema is not None and hasattr(args_schema, "model_json_schema"):
            schema = args_schema.model_json_schema()
        name = str(getattr(tool, "name", "") or "")
        description = str(getattr(tool, "description", "") or "")
        category_zh = classify_tool_text(name, description, default="其他")
        return ToolInfoResult(
            tool_ref=tool_ref,
            source_type="external_python_tool",
            name=name,
            display_name=name,
            description=description,
            cat_zh=category_zh,
            input_schema=schema,
            examples=[],
            provider="Tools",
        )

    async def run(self, tool_ref: str, arguments: dict[str, Any], user_id: str) -> ToolRunResult:
        tool = self._find_tool(tool_ref)
        if hasattr(tool, "invoke"):
            result = tool.invoke(arguments)
        else:
            result = tool.func(**arguments)
        return ToolRunResult(tool_ref=tool_ref, ok=True, result=result)

    @staticmethod
    def _load_tools() -> list[Any]:
        import Tools as external_tools

        return list(external_tools.reload_external_tools(force=False))

    def _find_tool(self, tool_ref: str) -> Any:
        name = _strip_prefix(tool_ref, "external:")
        for tool in self._load_tools():
            if getattr(tool, "name", "") == name:
                return tool
        raise LookupError(f"External tool not found: {tool_ref}")


def _find_tu_tool(tu: Any, tool_name: str) -> dict[str, Any] | None:
    all_tools = tu.all_tools if isinstance(tu.all_tools, list) else tu.all_tools.values()
    for tool in all_tools:
        if isinstance(tool, dict) and tool.get("name") == tool_name:
            return tool
    return None


def _strip_prefix(tool_ref: str, prefix: str) -> str:
    if not tool_ref.startswith(prefix):
        raise LookupError(f"Invalid tool_ref for {prefix}: {tool_ref}")
    return tool_ref[len(prefix):]


def _schema_status(schema: Any) -> str:
    if schema is None:
        return "missing"
    raw_schema = schema
    if hasattr(schema, "model_json_schema"):
        raw_schema = schema.model_json_schema()
    if not isinstance(raw_schema, dict) or not raw_schema:
        return "missing"
    if any(key in raw_schema for key in ("oneOf", "anyOf", "allOf", "not", "$ref", "patternProperties")):
        return "complex"
    return "available"


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            result.append(text)
    return result
