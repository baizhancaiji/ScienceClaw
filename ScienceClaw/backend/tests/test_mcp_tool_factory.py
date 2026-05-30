import sys
import unittest
from pathlib import Path
from typing import get_args, get_origin
from unittest.mock import AsyncMock

from pydantic import ValidationError


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.mcp import tool_factory  # noqa: E402


class MCPToolFactoryTests(unittest.TestCase):
    def test_schema_to_pydantic_model_maps_basic_types_and_required_fields(self):
        model = tool_factory.schema_to_pydantic_model(
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 10},
                    "threshold": {"type": "number"},
                    "exact": {"type": "boolean"},
                },
                "required": ["query", "exact"],
            },
            "SearchArgs",
        )

        parsed = model(query="science", exact=True)

        self.assertEqual("science", parsed.query)
        self.assertEqual(10, parsed.limit)
        self.assertIsNone(parsed.threshold)
        with self.assertRaises(ValidationError):
            model(exact=True)

    def test_schema_to_pydantic_model_maps_enum_array_and_nested_object(self):
        model = tool_factory.schema_to_pydantic_model(
            {
                "type": "object",
                "properties": {
                    "mode": {"enum": ["fast", "deep"]},
                    "ids": {"type": "array", "items": {"type": "integer"}},
                    "filters": {
                        "type": "object",
                        "properties": {"active": {"type": "boolean"}},
                        "required": ["active"],
                    },
                },
                "required": ["mode", "ids", "filters"],
            },
            "NestedArgs",
        )

        parsed = model(mode="fast", ids=[1, 2], filters={"active": True})

        self.assertEqual("fast", parsed.mode)
        self.assertEqual([1, 2], parsed.ids)
        self.assertTrue(parsed.filters.active)
        self.assertEqual(list, get_origin(model.model_fields["ids"].annotation))
        self.assertEqual((int,), get_args(model.model_fields["ids"].annotation))
        with self.assertRaises(ValidationError):
            model(mode="slow", ids=[1], filters={"active": True})

    def test_schema_to_pydantic_model_forbids_extra_when_additional_properties_false(self):
        model = tool_factory.schema_to_pydantic_model(
            {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
                "additionalProperties": False,
            },
            "StrictArgs",
        )

        with self.assertRaises(ValidationError):
            model(query="science", unexpected=True)

    def test_complex_schema_falls_back_to_payload(self):
        model = tool_factory.schema_to_pydantic_model(
            {"oneOf": [{"type": "object"}, {"type": "string"}]},
            "ComplexArgs",
        )

        parsed = model(payload={"anything": ["goes"]})

        self.assertEqual({"anything": ["goes"]}, parsed.payload)
        with self.assertRaises(ValidationError):
            model()

    def test_non_object_schema_uses_optional_payload_default(self):
        model = tool_factory.schema_to_pydantic_model({"type": "string"}, "StringArgs")

        parsed = model()

        self.assertEqual({}, parsed.payload)

    def test_canonical_tool_name_normalizes_server_and_tool_parts(self):
        self.assertEqual(
            "mcp__github_mcp__search_repositories",
            tool_factory.canonical_tool_name("GitHub MCP", "Search Repositories"),
        )

    def test_build_tool_definition_includes_mcp_description_and_schema(self):
        definition = tool_factory.build_tool_definition(
            {
                "server_name": "GitHub",
                "server_slug": "github_mcp",
                "original_name": "search_repositories",
                "display_name": "Search",
                "description": "Search repositories",
                "input_schema_raw": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            }
        )

        self.assertEqual("mcp__github_mcp__search_repositories", definition.name)
        self.assertIn("[MCP:GitHub]", definition.description)
        self.assertEqual("science", definition.args_schema(query="science").query)
        self.assertFalse(definition.input_schema_complex)
        with self.assertRaises(NotImplementedError):
            definition.func(query="science")

    def test_tool_definition_runner_calls_remote_tool_and_normalizes_result(self):
        call_tool_safely = AsyncMock(
            return_value={
                "ok": True,
                "is_error": False,
                "result": {"content": [{"type": "text", "text": "remote answer"}]},
            }
        )
        definition = tool_factory.build_tool_definition(
            {
                "id": "tool-1",
                "canonical_name": "mcp__deepwiki__ask_question",
                "original_name": "ask_question",
                "server_name": "DeepWiki",
                "description": "Ask a question",
                "input_schema_raw": {
                    "type": "object",
                    "properties": {"question": {"type": "string"}},
                    "required": ["question"],
                },
                "server": {
                    "id": "server-1",
                    "name": "DeepWiki",
                    "endpoint_url": "https://example.com/mcp",
                    "headers": {"X-Test": "secret"},
                },
                "call_tool_safely": call_tool_safely,
            }
        )

        result = definition.func(question="What is it?")

        self.assertTrue(result["ok"])
        self.assertEqual("remote answer", result["text"])
        self.assertEqual("server-1", result["server"]["id"])
        self.assertEqual("mcp__deepwiki__ask_question", result["tool"]["canonical_name"])
        call_tool_safely.assert_awaited_once_with(
            "https://example.com/mcp",
            "ask_question",
            arguments={"question": "What is it?"},
            headers={"X-Test": "secret"},
        )

    def test_complex_schema_runner_unwraps_payload_arguments(self):
        call_tool_safely = AsyncMock(
            return_value={
                "ok": True,
                "is_error": False,
                "result": {"content": [{"type": "text", "text": "complex answer"}]},
            }
        )
        definition = tool_factory.build_tool_definition(
            {
                "id": "tool-1",
                "canonical_name": "mcp__deepwiki__ask_question",
                "original_name": "ask_question",
                "server_name": "DeepWiki",
                "description": "Ask a question",
                "input_schema_raw": {
                    "type": "object",
                    "properties": {
                        "repoName": {
                            "anyOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}},
                            ]
                        },
                        "question": {"type": "string"},
                    },
                    "required": ["repoName", "question"],
                },
                "server": {
                    "id": "server-1",
                    "name": "DeepWiki",
                    "endpoint_url": "https://example.com/mcp",
                    "headers": {},
                },
                "call_tool_safely": call_tool_safely,
            }
        )

        result = definition.func(
            payload={
                "repoName": "modelcontextprotocol/python-sdk",
                "question": "What is this repository?",
            }
        )

        self.assertTrue(definition.input_schema_complex)
        self.assertEqual("complex answer", result["text"])
        call_tool_safely.assert_awaited_once_with(
            "https://example.com/mcp",
            "ask_question",
            arguments={
                "repoName": "modelcontextprotocol/python-sdk",
                "question": "What is this repository?",
            },
            headers={},
        )

    def test_build_tool_definition_prefixes_complex_schema_hint(self):
        definition = tool_factory.build_tool_definition(
            {
                "canonical_name": "mcp__server__complex",
                "server_name": "Server",
                "description": "Complex input",
                "input_schema_raw": {"$ref": "#/$defs/Input"},
            }
        )

        self.assertTrue(definition.input_schema_complex)
        self.assertTrue(definition.description.startswith(tool_factory.COMPLEX_SCHEMA_HINT))
        self.assertEqual({"x": 1}, definition.args_schema(payload={"x": 1}).payload)


if __name__ == "__main__":
    unittest.main()
