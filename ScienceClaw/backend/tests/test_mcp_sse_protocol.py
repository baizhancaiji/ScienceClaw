import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.deepagent.sse_protocol import SSEProtocolManager  # noqa: E402


class MCPSSEProtocolTests(unittest.TestCase):
    def test_register_mcp_tool_adds_https_mcp_metadata(self):
        manager = SSEProtocolManager()

        manager.register_mcp_tool(
            "mcp__github_mcp__search",
            "Search repositories",
            server_id="server-1",
            server_name="GitHub MCP",
            server_slug="github_mcp",
            tool_id="tool-1",
            original_tool_name="search",
        )

        meta = manager.get_tool_meta("mcp__github_mcp__search")

        self.assertTrue(meta["mcp"])
        self.assertEqual("https_mcp", meta["source_type"])
        self.assertEqual("server-1", meta["server_id"])
        self.assertEqual("GitHub MCP", meta["server_name"])
        self.assertEqual("github_mcp", meta["server_slug"])
        self.assertEqual("tool-1", meta["tool_id"])
        self.assertEqual("search", meta["original_tool_name"])

    def test_mcp_tool_name_fallback_marks_https_mcp_source(self):
        manager = SSEProtocolManager()

        meta = manager.get_tool_meta("mcp__github_mcp__search")

        self.assertTrue(meta["mcp"])
        self.assertEqual("https_mcp", meta["source_type"])
        self.assertEqual("github_mcp", meta["server_name"])
        self.assertEqual("github_mcp", meta["server_slug"])
        self.assertEqual("search", meta["original_tool_name"])

    def test_non_mcp_unknown_tool_keeps_generic_metadata(self):
        manager = SSEProtocolManager()

        meta = manager.get_tool_meta("unknown_tool")

        self.assertNotIn("mcp", meta)
        self.assertEqual("custom", meta["category"])


if __name__ == "__main__":
    unittest.main()
