import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.mcp import tool_factory  # noqa: E402


class MCPResultNormalizationTests(unittest.TestCase):
    def test_structured_content_is_copied_to_structured(self):
        result = tool_factory.normalize_mcp_tool_result(
            {"structuredContent": {"items": [{"id": 1}]}},
            server={"id": "server-1", "name": "GitHub MCP"},
            tool={
                "id": "tool-1",
                "canonical_name": "mcp__github_mcp__search",
                "original_name": "search",
            },
        )

        self.assertTrue(result["ok"])
        self.assertFalse(result["is_error"])
        self.assertEqual({"id": "server-1", "name": "GitHub MCP"}, result["server"])
        self.assertEqual("mcp__github_mcp__search", result["tool"]["canonical_name"])
        self.assertEqual({"items": [{"id": 1}]}, result["structured"])
        self.assertIn("\"items\"", result["text"])
        self.assertEqual([{"type": "text", "text": result["text"]}], result["content_blocks"])
        self.assertIsNone(result["error"])

    def test_content_text_blocks_are_joined_with_blank_line(self):
        result = tool_factory.normalize_mcp_tool_result(
            {
                "content": [
                    {"type": "text", "text": "first"},
                    {"type": "image", "data": "ignored"},
                    {"text": "second"},
                ]
            }
        )

        self.assertEqual("first\n\nsecond", result["text"])
        self.assertIsNone(result["structured"])
        self.assertEqual([{"type": "text", "text": "first\n\nsecond"}], result["content_blocks"])

    def test_plain_string_content_falls_back_to_text(self):
        result = tool_factory.normalize_mcp_tool_result("plain remote output")

        self.assertTrue(result["ok"])
        self.assertEqual("plain remote output", result["text"])
        self.assertIsNone(result["structured"])

    def test_stringifiable_content_falls_back_to_json_text(self):
        result = tool_factory.normalize_mcp_tool_result({"count": 2, "items": ["a", "b"]})

        self.assertTrue(result["ok"])
        self.assertIn("\"count\": 2", result["text"])
        self.assertIn("\"items\"", result["text"])

    def test_error_envelope_is_preserved_and_offload_compatible(self):
        result = tool_factory.normalize_mcp_tool_result(
            {
                "ok": False,
                "is_error": True,
                "error": {
                    "message": "Remote MCP error",
                    "code": "remote_mcp_error",
                    "retryable": False,
                },
                "text": "remote_mcp_error: Remote MCP error",
            }
        )

        self.assertFalse(result["ok"])
        self.assertTrue(result["is_error"])
        self.assertEqual("remote_mcp_error", result["error"]["code"])
        self.assertEqual("remote_mcp_error: Remote MCP error", result["text"])
        self.assertEqual([{"type": "text", "text": result["text"]}], result["content_blocks"])

    def test_safe_success_envelope_result_is_unwrapped(self):
        result = tool_factory.normalize_mcp_tool_result(
            {
                "ok": True,
                "is_error": False,
                "result": {"content": [{"type": "text", "text": "wrapped output"}]},
            }
        )

        self.assertTrue(result["ok"])
        self.assertFalse(result["is_error"])
        self.assertEqual("wrapped output", result["text"])

    def test_result_with_structured_and_text_keeps_both(self):
        result = tool_factory.normalize_mcp_tool_result(
            {
                "structuredContent": {"total": 1},
                "content": [{"type": "text", "text": "summary"}],
            }
        )

        self.assertEqual({"total": 1}, result["structured"])
        self.assertEqual("summary", result["text"])


if __name__ == "__main__":
    unittest.main()
