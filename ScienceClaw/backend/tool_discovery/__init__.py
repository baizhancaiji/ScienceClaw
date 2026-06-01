"""Keyword-only tool discovery package.

This package builds a lightweight searchable index over expandable tool
sources without injecting full catalogs into the Agent tool list.
"""

from .schemas import (
    ToolIndexItem,
    ToolInfoResult,
    ToolRunRequest,
    ToolRunResult,
    ToolSearchRequest,
    ToolSearchResult,
)
from .service import ToolDiscoveryService, get_tool_discovery_service, set_tool_discovery_service

__all__ = [
    "ToolDiscoveryService",
    "ToolIndexItem",
    "ToolInfoResult",
    "ToolRunRequest",
    "ToolRunResult",
    "ToolSearchRequest",
    "ToolSearchResult",
    "get_tool_discovery_service",
    "set_tool_discovery_service",
]
