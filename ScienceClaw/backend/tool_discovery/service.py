from __future__ import annotations

from pathlib import Path
from typing import Any

from .index_store import ToolIndexStore
from .providers import (
    ExternalPythonToolsProvider,
    HTTPSMCPProvider,
    ToolDiscoveryProvider,
    ToolUniverseProvider,
)
from .schemas import (
    ToolIndexItem,
    ToolInfoResult,
    ToolRunResult,
    ToolSearchRequest,
    ToolSearchResult,
)


class ToolDiscoveryService:
    def __init__(
        self,
        providers: list[ToolDiscoveryProvider] | None = None,
        index_store: ToolIndexStore | None = None,
    ) -> None:
        self.providers = providers or [
            ToolUniverseProvider(),
            HTTPSMCPProvider(),
            ExternalPythonToolsProvider(),
        ]
        self.index_store = index_store or ToolIndexStore(_default_index_path())

    async def rebuild_index(self, user_id: str) -> list[ToolIndexItem]:
        items: list[ToolIndexItem] = []
        for provider in self.providers:
            items.extend(await provider.list_index_items(user_id))
        self.index_store.rebuild(items)
        return items

    async def search(self, request: ToolSearchRequest, user_id: str) -> list[ToolSearchResult]:
        if self.index_store.is_empty():
            await self.rebuild_index(user_id)
        hits = self.index_store.search(
            request.query,
            source_type=request.source_type,
            category_zh=request.category_zh,
            limit=request.limit,
        )
        results: list[ToolSearchResult] = []
        for hit in hits:
            item = hit.item
            why = self._why(hit.hit_fields, item)
            payload: dict[str, Any] = {
                "tool_ref": item.tool_ref,
                "name": item.display_name or item.name,
                "cat_zh": item.category_zh,
                "why": why,
            }
            if request.debug:
                payload.update(
                    {
                        "score": round(hit.score, 4),
                        "source_type": item.source_type,
                        "hit_fields": hit.hit_fields,
                    }
                )
            results.append(ToolSearchResult(**payload))
        return results

    async def get_info(self, tool_ref: str, user_id: str) -> ToolInfoResult:
        provider = self._provider_for_tool_ref(tool_ref)
        return await provider.get_info(tool_ref, user_id)

    async def run(self, tool_ref: str, arguments: dict[str, Any], user_id: str) -> ToolRunResult:
        provider = self._provider_for_tool_ref(tool_ref)
        return await provider.run(tool_ref, arguments, user_id)

    def _provider_for_tool_ref(self, tool_ref: str) -> ToolDiscoveryProvider:
        source_type = _source_type_from_ref(tool_ref)
        for provider in self.providers:
            if provider.source_type == source_type:
                return provider
        raise LookupError(f"No provider registered for {tool_ref}")

    @staticmethod
    def _why(hit_fields: list[str], item: ToolIndexItem) -> str:
        if not hit_fields:
            return f"属于“{item.category_zh}”"
        labels = {
            "name": "名称",
            "display_name": "展示名",
            "name_zh": "中文名",
            "category_zh": "分类",
            "aliases": "别名",
            "keywords": "关键词",
            "provider": "来源",
            "description": "描述",
            "description_zh": "中文描述",
            "fts": "全文索引",
        }
        readable = "、".join(labels.get(field, field) for field in hit_fields[:3])
        return f"命中{readable}，分类为“{item.category_zh}”"


def _source_type_from_ref(tool_ref: str) -> str:
    if tool_ref.startswith("tooluniverse:"):
        return "tooluniverse"
    if tool_ref.startswith("https_mcp:"):
        return "https_mcp"
    if tool_ref.startswith("external:"):
        return "external_python_tool"
    raise LookupError(f"Unsupported tool_ref: {tool_ref}")


def _default_index_path() -> Path:
    cache_dir = Path(__file__).resolve().parents[3] / "var" / "tool_discovery"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "tool_index.sqlite3"
