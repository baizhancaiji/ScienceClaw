"""LangChain adapters for the three-step expandable tool workflow."""
from __future__ import annotations

import asyncio
import json
from typing import Any

from langchain_core.tools import tool

from backend.tool_discovery import ToolRunRequest, ToolSearchRequest
from backend.tool_discovery.service import get_tool_discovery_service

_DEFAULT_DISCOVERY_USER_ID = "default_user"


def _run_async(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


@tool
def tool_search(
    query: str,
    source_type: str | None = None,
    category_zh: str | None = None,
    limit: int = 5,
    debug: bool = False,
) -> dict:
    """Search expandable tools by keyword before requesting schema or running them.

    Use this for ToolUniverse, HTTPS MCP, and external Python tools. It returns
    short candidates only. Call tool_info on one returned tool_ref before tool_run.
    Do not request or expect a full catalog.
    """
    try:
        request = ToolSearchRequest(
            query=query,
            source_type=source_type,
            category_zh=category_zh,
            limit=limit,
            debug=debug,
        )
        results = _run_async(
            get_tool_discovery_service().search(request, _DEFAULT_DISCOVERY_USER_ID)
        )
        return {"results": [result.model_dump(exclude_none=True) for result in results]}
    except Exception as exc:
        return {"error": str(exc)}


@tool
def tool_info(tool_ref: str) -> dict:
    """Get one expandable tool's description, parameter schema, examples, and limits."""
    try:
        info = _run_async(
            get_tool_discovery_service().get_info(tool_ref, _DEFAULT_DISCOVERY_USER_ID)
        )
        return info.model_dump(exclude_none=True)
    except Exception as exc:
        return {"error": str(exc)}


@tool
def tool_run(tool_ref: str, arguments: str) -> dict:
    """Run one expandable tool with structured JSON arguments from tool_info."""
    try:
        parsed = json.loads(arguments or "{}")
    except json.JSONDecodeError:
        return {"error": f"Invalid JSON in arguments: {arguments}"}
    if not isinstance(parsed, dict):
        return {"error": "arguments must be a JSON object"}

    try:
        request = ToolRunRequest(tool_ref=tool_ref, arguments=parsed)
        result = _run_async(
            get_tool_discovery_service().run(
                request.tool_ref,
                request.arguments,
                _DEFAULT_DISCOVERY_USER_ID,
            )
        )
        return result.model_dump(exclude_none=True)
    except Exception as exc:
        return {"error": str(exc)}
