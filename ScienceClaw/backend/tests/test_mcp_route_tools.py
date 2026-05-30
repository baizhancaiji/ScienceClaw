import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.route import mcp as mcp_route  # noqa: E402
from backend.user.dependencies import User, require_user  # noqa: E402
from backend.mcp.schemas import MCPToolListItem  # noqa: E402
from backend.mcp.service import MCPRefreshResult, MCPVerifyResult  # noqa: E402


def _test_user() -> User:
    return User(id="user-1", username="tester", role="user")


def _make_app(authenticated: bool = True) -> FastAPI:
    app = FastAPI()
    app.include_router(mcp_route.router, prefix="/api/v1")
    if authenticated:
        app.dependency_overrides[require_user] = _test_user
    return app


def _tool(**overrides):
    data = {
        "id": "tool-1",
        "server_id": "server-1",
        "original_name": "search",
        "tool_slug": "search",
        "canonical_name": "mcp__github_mcp__search",
        "display_name": "search",
        "description": "Search",
        "input_schema_raw": {},
        "input_schema_normalized": {},
        "enabled": True,
        "removed": False,
    }
    data.update(overrides)
    return MCPToolListItem(**data)


def _server_result(**overrides):
    data = {
        "id": "server-1",
        "name": "GitHub MCP",
        "slug": "github_mcp",
        "endpoint_url": "https://example.com/mcp",
        "auth_mode": "none",
        "enabled": True,
        "verify_status": "healthy",
        "tool_count": 2,
        "duration_ms": 12,
    }
    data.update(overrides)
    return MCPVerifyResult(**data)


def _refresh_result(**overrides):
    data = {
        "id": "server-1",
        "name": "GitHub MCP",
        "slug": "github_mcp",
        "endpoint_url": "https://example.com/mcp",
        "auth_mode": "none",
        "enabled": True,
        "tool_count": 2,
        "added": 1,
        "updated": 2,
        "removed": 1,
        "duration_ms": 23,
    }
    data.update(overrides)
    return MCPRefreshResult(**data)


class MCPToolRouteTests(unittest.TestCase):
    def test_tool_routes_require_authenticated_user(self):
        response = TestClient(_make_app(authenticated=False)).get("/api/v1/mcp/tools")

        self.assertEqual(401, response.status_code)

    def test_verify_server_route_passes_user_and_key(self):
        verify_server = AsyncMock(return_value=_server_result())
        previous_key = os.environ.get("MCP_CONFIG_ENCRYPTION_KEY")
        os.environ["MCP_CONFIG_ENCRYPTION_KEY"] = "route-key"
        try:
            with patch.object(mcp_route.service, "verify_server", new=verify_server):
                response = TestClient(_make_app()).post(
                    "/api/v1/mcp/servers/server-1/verify"
                )
        finally:
            if previous_key is None:
                os.environ.pop("MCP_CONFIG_ENCRYPTION_KEY", None)
            else:
                os.environ["MCP_CONFIG_ENCRYPTION_KEY"] = previous_key

        self.assertEqual(200, response.status_code)
        self.assertEqual("healthy", response.json()["data"]["verify_status"])
        verify_server.assert_awaited_once_with("server-1", "user-1", "route-key")

    def test_verify_server_route_returns_404_when_missing(self):
        with patch.object(mcp_route.service, "verify_server", new=AsyncMock(return_value=None)):
            response = TestClient(_make_app()).post("/api/v1/mcp/servers/missing/verify")

        self.assertEqual(404, response.status_code)

    def test_refresh_tools_route_maps_added_to_inserted(self):
        refresh_server_tools = AsyncMock(return_value=_refresh_result())

        with patch.object(
            mcp_route.service,
            "refresh_server_tools",
            new=refresh_server_tools,
        ):
            response = TestClient(_make_app()).post(
                "/api/v1/mcp/servers/server-1/refresh-tools"
            )

        self.assertEqual(200, response.status_code)
        data = response.json()["data"]
        self.assertEqual(1, data["inserted"])
        self.assertEqual(2, data["updated"])
        self.assertEqual(1, data["removed"])
        self.assertNotIn("added", data)
        refresh_server_tools.assert_awaited_once()

    def test_refresh_tools_route_returns_404_when_missing(self):
        with patch.object(
            mcp_route.service,
            "refresh_server_tools",
            new=AsyncMock(return_value=None),
        ):
            response = TestClient(_make_app()).post(
                "/api/v1/mcp/servers/missing/refresh-tools"
            )

        self.assertEqual(404, response.status_code)

    def test_list_server_tools_route_returns_tools(self):
        list_tools_by_server = AsyncMock(return_value=[_tool()])

        with patch.object(
            mcp_route.service,
            "list_tools_by_server",
            new=list_tools_by_server,
        ):
            response = TestClient(_make_app()).get("/api/v1/mcp/servers/server-1/tools")

        self.assertEqual(200, response.status_code)
        self.assertEqual("tool-1", response.json()["data"][0]["id"])
        list_tools_by_server.assert_awaited_once_with("server-1", "user-1")

    def test_list_server_tools_route_returns_404_when_missing_server(self):
        with patch.object(
            mcp_route.service,
            "list_tools_by_server",
            new=AsyncMock(return_value=None),
        ):
            response = TestClient(_make_app()).get("/api/v1/mcp/servers/missing/tools")

        self.assertEqual(404, response.status_code)

    def test_list_enabled_tools_route_uses_current_user(self):
        list_enabled_tools = AsyncMock(return_value=[_tool()])

        with patch.object(mcp_route.service, "list_enabled_tools", new=list_enabled_tools):
            response = TestClient(_make_app()).get("/api/v1/mcp/tools")

        self.assertEqual(200, response.status_code)
        self.assertEqual("mcp__github_mcp__search", response.json()["data"][0]["canonical_name"])
        list_enabled_tools.assert_awaited_once_with("user-1")

    def test_toggle_tool_enabled_route_returns_updated_tool(self):
        toggle_tool_enabled = AsyncMock(return_value=_tool(enabled=False))

        with patch.object(
            mcp_route.service,
            "toggle_tool_enabled",
            new=toggle_tool_enabled,
        ):
            response = TestClient(_make_app()).put(
                "/api/v1/mcp/tools/tool-1/enabled",
                json={"enabled": False},
            )

        self.assertEqual(200, response.status_code)
        self.assertFalse(response.json()["data"]["enabled"])
        toggle_tool_enabled.assert_awaited_once_with("tool-1", "user-1", False)

    def test_toggle_tool_enabled_route_returns_404_when_missing(self):
        with patch.object(
            mcp_route.service,
            "toggle_tool_enabled",
            new=AsyncMock(return_value=None),
        ):
            response = TestClient(_make_app()).put(
                "/api/v1/mcp/tools/missing/enabled",
                json={"enabled": True},
            )

        self.assertEqual(404, response.status_code)


if __name__ == "__main__":
    unittest.main()
