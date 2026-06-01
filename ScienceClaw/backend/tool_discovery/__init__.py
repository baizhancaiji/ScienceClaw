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
from .service import ToolDiscoveryService

__all__ = [
    "ToolDiscoveryService",
    "ToolIndexItem",
    "ToolInfoResult",
    "ToolRunRequest",
    "ToolRunResult",
    "ToolSearchRequest",
    "ToolSearchResult",
]
