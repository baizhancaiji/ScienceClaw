import asyncio
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.deepagent import agent  # noqa: E402
from backend.mcp.schemas import MCPToolListItem  # noqa: E402


def _tool_item(**overrides) -> MCPToolListItem:
    data = {
        "id": "tool-1",
        "server_id": "server-1",
        "original_name": "search",
        "tool_slug": "search",
        "canonical_name": "mcp__github_mcp__search",
        "display_name": "Search",
        "description": "Search repositories",
        "input_schema_raw": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        "input_schema_normalized": {},
        "enabled": True,
        "removed": False,
    }
    data.update(overrides)
    return MCPToolListItem(**data)


class AgentMCPInjectionTests(unittest.TestCase):
    def test_collect_user_mcp_tools_skips_without_user_id(self):
        with patch.object(agent.mcp_service, "list_enabled_tools", new=AsyncMock()) as list_tools:
            tools = asyncio.run(agent._collect_user_mcp_tools(None))

        self.assertEqual([], tools)
        list_tools.assert_not_called()

    def test_collect_user_mcp_tools_wraps_enabled_tools(self):
        list_enabled_tools = AsyncMock(return_value=[_tool_item()])

        with patch.object(agent.mcp_service, "list_enabled_tool_runtime_docs", new=list_enabled_tools):
            tools = asyncio.run(agent._collect_user_mcp_tools("user-1"))

        self.assertEqual(["mcp__github_mcp__search"], [tool.name for tool in tools])
        self.assertIn("[MCP:github_mcp]", tools[0].description)
        self.assertEqual("science", tools[0].args_schema(query="science").query)
        with self.assertRaises(NotImplementedError):
            tools[0].invoke({"query": "science"})
        list_enabled_tools.assert_awaited_once_with("user-1", "")

    def test_collect_user_mcp_tools_handles_fifty_tool_scale(self):
        runtime_docs = [
            _tool_item(
                id=f"tool-{index}",
                original_name=f"tool_{index}",
                tool_slug=f"tool-{index}",
                canonical_name=f"mcp__scale_mcp__tool_{index}",
                display_name=f"Tool {index}",
            )
            for index in range(50)
        ]
        list_enabled_tools = AsyncMock(return_value=runtime_docs)

        with patch.object(agent.mcp_service, "list_enabled_tool_runtime_docs", new=list_enabled_tools):
            started_at = time.perf_counter()
            tools = asyncio.run(agent._collect_user_mcp_tools("user-1"))
            duration_ms = int((time.perf_counter() - started_at) * 1000)

        self.assertEqual(50, len(tools))
        self.assertEqual("mcp__scale_mcp__tool_0", tools[0].name)
        self.assertEqual("mcp__scale_mcp__tool_49", tools[-1].name)
        self.assertLess(duration_ms, 1000)
        list_enabled_tools.assert_awaited_once_with("user-1", "")

    def test_collect_user_mcp_tools_skips_existing_tool_name(self):
        list_enabled_tools = AsyncMock(return_value=[_tool_item()])

        with patch.object(agent.mcp_service, "list_enabled_tool_runtime_docs", new=list_enabled_tools):
            tools = asyncio.run(
                agent._collect_user_mcp_tools(
                    "user-1",
                    existing_tool_names={"mcp__github_mcp__search"},
                )
            )

        self.assertEqual([], tools)

    def test_append_user_mcp_tools_keeps_existing_order_and_appends_mcp_tools(self):
        existing_tool = type("Tool", (), {"name": "web_search"})()
        list_enabled_tools = AsyncMock(return_value=[_tool_item()])

        with patch.object(agent.mcp_service, "list_enabled_tool_runtime_docs", new=list_enabled_tools):
            tools = asyncio.run(agent._append_user_mcp_tools([existing_tool], "user-1"))

        self.assertEqual(["web_search", "mcp__github_mcp__search"], [tool.name for tool in tools])

    def test_deep_agent_passes_appended_mcp_tools_to_agent_factory(self):
        existing_tool = type("Tool", (), {"name": "web_search"})()
        mcp_tool = type("Tool", (), {"name": "mcp__github_mcp__search"})()
        created_kwargs = {}
        workspace_root = tempfile.mkdtemp()

        class SandboxStub:
            def __init__(self, *args, **kwargs):
                self.workspace = str(Path(workspace_root) / "session-1")
                Path(self.workspace).mkdir(parents=True, exist_ok=True)

            async def get_context(self):
                return {"success": True, "data": "sandbox info"}

        def create_deep_agent_stub(**kwargs):
            created_kwargs.update(kwargs)
            return object()

        async def append_mcp_tools(tools, user_id):
            tools.extend([mcp_tool])
            return tools

        with (
            patch.object(agent, "get_llm_model", return_value=type("Model", (), {"profile": {}})()),
            patch.object(agent, "get_blocked_skills", new=AsyncMock(return_value=set())),
            patch.object(agent, "get_blocked_tools", new=AsyncMock(return_value=set())),
            patch.object(agent._dir_watcher, "has_changed", return_value=False),
            patch.object(agent, "_collect_tools", return_value=[existing_tool]),
            patch.object(agent, "_append_user_mcp_tools", new=append_mcp_tools),
            patch.object(agent, "FullSandboxBackend", new=SandboxStub),
            patch.object(agent, "_build_backend", return_value=object()),
            patch.object(agent, "create_deep_agent", new=create_deep_agent_stub),
            patch.object(agent.os.path, "isdir", return_value=False),
            patch.object(agent, "_WORKSPACE_DIR", workspace_root),
        ):
            asyncio.run(agent.deep_agent("session-1", user_id="user-1"))

        self.assertEqual(
            ["web_search", "mcp__github_mcp__search"],
            [tool.name for tool in created_kwargs["tools"]],
        )


if __name__ == "__main__":
    unittest.main()
