import asyncio
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.tool_discovery.index_store import ToolIndexStore  # noqa: E402
from backend.tool_discovery.schemas import ToolIndexItem, ToolInfoResult, ToolRunResult, ToolSearchRequest  # noqa: E402
from backend.tool_discovery.service import ToolDiscoveryService  # noqa: E402


def _run(coro):
    return asyncio.run(coro)


class FakeProvider:
    def __init__(self, source_type="tooluniverse", tool_ref="tooluniverse:PubMed_search_articles", category_zh="学术文献"):
        self.source_type = source_type
        self.tool_ref = tool_ref
        self.category_zh = category_zh

    async def list_index_items(self, user_id: str):
        return [
            ToolIndexItem(
                tool_ref=self.tool_ref,
                source_type=self.source_type,
                name=self.tool_ref.split(":", 1)[1],
                display_name="PubMed_search_articles",
                description="Search articles",
                description_zh="搜索论文",
                category_zh=self.category_zh,
                aliases=["论文", "医学论文", "PubMed"],
                keywords=["literature", "pubmed"],
                provider=self.source_type,
                schema_status="available",
                has_examples=True,
            )
        ]

    async def get_info(self, tool_ref: str, user_id: str):
        return ToolInfoResult(
            tool_ref=tool_ref,
            source_type=self.source_type,
            name=tool_ref.split(":", 1)[1],
            cat_zh=self.category_zh,
            input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
            provider=self.source_type,
        )

    async def run(self, tool_ref: str, arguments: dict, user_id: str):
        return ToolRunResult(tool_ref=tool_ref, ok=True, result={"query": arguments["query"]})


class ToolDiscoveryServiceTests(unittest.TestCase):
    def test_search_rebuilds_index_and_returns_minimal_fields_by_default(self):
        service = ToolDiscoveryService(providers=[FakeProvider()], index_store=ToolIndexStore())

        results = _run(service.search(ToolSearchRequest(query="医学论文", limit=5), "user-1"))

        self.assertEqual(1, len(results))
        self.assertEqual("tooluniverse:PubMed_search_articles", results[0].tool_ref)
        self.assertEqual("学术文献", results[0].cat_zh)
        self.assertIsNone(results[0].score)
        self.assertIsNone(results[0].source_type)
        self.assertIsNone(results[0].hit_fields)

    def test_search_debug_includes_diagnostics_only_when_requested(self):
        service = ToolDiscoveryService(providers=[FakeProvider()], index_store=ToolIndexStore())

        results = _run(service.search(ToolSearchRequest(query="医学论文", limit=5, debug=True), "user-1"))

        self.assertIsNotNone(results[0].score)
        self.assertEqual("tooluniverse", results[0].source_type)
        self.assertIn("aliases", results[0].hit_fields or [])

    def test_info_and_run_dispatch_by_tool_ref_prefix(self):
        service = ToolDiscoveryService(providers=[FakeProvider()], index_store=ToolIndexStore())

        info = _run(service.get_info("tooluniverse:PubMed_search_articles", "user-1"))
        result = _run(service.run("tooluniverse:PubMed_search_articles", {"query": "CRISPR"}, "user-1"))

        self.assertEqual("学术文献", info.cat_zh)
        self.assertTrue(result.ok)
        self.assertEqual({"query": "CRISPR"}, result.result)

    def test_service_can_index_three_expandable_source_types(self):
        service = ToolDiscoveryService(
            providers=[
                FakeProvider("tooluniverse", "tooluniverse:PubMed_search_articles", "学术文献"),
                FakeProvider("https_mcp", "https_mcp:tool-1", "网页与外部服务"),
                FakeProvider("external_python_tool", "external:pdf_convert", "文档处理"),
            ],
            index_store=ToolIndexStore(),
        )

        items = _run(service.rebuild_index("user-1"))

        self.assertEqual(
            ["external_python_tool", "https_mcp", "tooluniverse"],
            sorted(item.source_type for item in items),
        )


if __name__ == "__main__":
    unittest.main()
