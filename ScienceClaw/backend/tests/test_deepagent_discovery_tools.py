import asyncio
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.deepagent import agent  # noqa: E402
from backend.deepagent import discovery_tools  # noqa: E402
from backend.tool_discovery import set_tool_discovery_service  # noqa: E402
from backend.tool_discovery.schemas import ToolInfoResult, ToolRunResult, ToolSearchRequest, ToolSearchResult  # noqa: E402


def _invoke(tool_obj, args):
    return tool_obj.invoke(args)


class FakeDiscoveryService:
    def __init__(self):
        self.search_requests = []
        self.info_calls = []
        self.run_calls = []

    async def search(self, request: ToolSearchRequest, user_id: str):
        self.search_requests.append((request, user_id))
        payload = {
            "tool_ref": "tooluniverse:PubMed_search_articles",
            "name": "PubMed_search_articles",
            "cat_zh": "学术文献",
            "why": "命中别名，分类为“学术文献”",
        }
        if request.debug:
            payload.update({"score": 12.5, "source_type": "tooluniverse", "hit_fields": ["aliases"]})
        return [ToolSearchResult(**payload)]

    async def get_info(self, tool_ref: str, user_id: str):
        self.info_calls.append((tool_ref, user_id))
        return ToolInfoResult(
            tool_ref=tool_ref,
            source_type="tooluniverse",
            name="PubMed_search_articles",
            cat_zh="学术文献",
            input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
        )

    async def run(self, tool_ref: str, arguments: dict, user_id: str):
        self.run_calls.append((tool_ref, arguments, user_id))
        return ToolRunResult(tool_ref=tool_ref, ok=True, result={"query": arguments["query"]})


class DeepAgentDiscoveryToolTests(unittest.TestCase):
    def setUp(self):
        self.service = FakeDiscoveryService()
        set_tool_discovery_service(self.service)

    def tearDown(self):
        set_tool_discovery_service(None)

    def test_static_tools_add_only_three_generic_discovery_tools(self):
        tool_names = [tool.name for tool in agent._STATIC_TOOLS]

        self.assertIn("tool_search", tool_names)
        self.assertIn("tool_info", tool_names)
        self.assertIn("tool_run", tool_names)
        self.assertIn("tooluniverse_search", tool_names)
        self.assertIn("tooluniverse_info", tool_names)
        self.assertIn("tooluniverse_run", tool_names)
        self.assertFalse(any(name.startswith("tooluniverse:") for name in tool_names))
        self.assertFalse(any(name.startswith("https_mcp:") for name in tool_names))
        self.assertFalse(any(name.startswith("external:") for name in tool_names))

    def test_tool_search_returns_minimal_fields_by_default(self):
        payload = _invoke(discovery_tools.tool_search, {"query": "医学论文"})
        result = payload["results"][0]

        self.assertEqual(
            {"tool_ref", "name", "cat_zh", "why"},
            set(result.keys()),
        )
        request, user_id = self.service.search_requests[0]
        self.assertFalse(request.debug)
        self.assertEqual("default_user", user_id)

    def test_tool_search_debug_requires_explicit_true(self):
        payload = _invoke(discovery_tools.tool_search, {"query": "医学论文", "debug": True})
        result = payload["results"][0]

        self.assertEqual(12.5, result["score"])
        self.assertEqual("tooluniverse", result["source_type"])
        self.assertEqual(["aliases"], result["hit_fields"])

    def test_tool_info_and_run_dispatch_structured_arguments(self):
        info = _invoke(discovery_tools.tool_info, {"tool_ref": "tooluniverse:PubMed_search_articles"})
        result = _invoke(
            discovery_tools.tool_run,
            {
                "tool_ref": "tooluniverse:PubMed_search_articles",
                "arguments": '{"query":"CRISPR"}',
            },
        )

        self.assertEqual("学术文献", info["cat_zh"])
        self.assertEqual({"query": "CRISPR"}, result["result"])
        self.assertEqual(
            ("tooluniverse:PubMed_search_articles", {"query": "CRISPR"}, "default_user"),
            self.service.run_calls[0],
        )

    def test_tool_run_rejects_non_json_arguments(self):
        payload = _invoke(
            discovery_tools.tool_run,
            {"tool_ref": "tooluniverse:PubMed_search_articles", "arguments": "not-json"},
        )

        self.assertIn("Invalid JSON", payload["error"])


if __name__ == "__main__":
    unittest.main()
