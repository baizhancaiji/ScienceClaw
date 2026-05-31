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
from backend.mcp.schemas import MCPServerDetailItem, MCPServerListItem  # noqa: E402


def _test_user() -> User:
    return User(id="user-1", username="tester", role="user")


def _make_app(authenticated: bool = True) -> FastAPI:
    app = FastAPI()
    app.include_router(mcp_route.router, prefix="/api/v1")
    if authenticated:
        app.dependency_overrides[require_user] = _test_user
    return app


def _server_detail(**overrides) -> MCPServerDetailItem:
    data = {
        "id": "server-1",
        "name": "GitHub MCP",
        "slug": "github_mcp",
        "endpoint_url": "https://example.com/mcp",
        "auth_mode": "none",
        "enabled": True,
        "created_at": 1,
        "updated_at": 2,
    }
    data.update(overrides)
    return MCPServerDetailItem(**data)


class MCPServerRouteTests(unittest.TestCase):
    def test_server_routes_require_authenticated_user(self):
        response = TestClient(_make_app(authenticated=False)).get("/api/v1/mcp/servers")

        self.assertEqual(401, response.status_code)

    def test_list_servers_uses_current_user_and_standard_response(self):
        list_servers = AsyncMock(
            return_value=[
                MCPServerListItem(
                    id="server-1",
                    name="GitHub MCP",
                    slug="github_mcp",
                    endpoint_url="https://example.com/mcp",
                    auth_mode="none",
                    enabled=True,
                )
            ]
        )

        with patch.object(mcp_route.service, "list_servers", new=list_servers):
            response = TestClient(_make_app()).get("/api/v1/mcp/servers")

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, response.json()["code"])
        self.assertEqual("server-1", response.json()["data"][0]["id"])
        list_servers.assert_awaited_once_with("user-1")

    def test_create_server_passes_body_user_and_encryption_key(self):
        create_server = AsyncMock(return_value=_server_detail())
        verify_server = AsyncMock()
        previous_key = os.environ.get("MCP_CONFIG_ENCRYPTION_KEY")
        os.environ["MCP_CONFIG_ENCRYPTION_KEY"] = "route-key"
        try:
            with (
                patch.object(mcp_route.service, "create_server", new=create_server),
                patch.object(mcp_route.service, "verify_server", new=verify_server),
            ):
                response = TestClient(_make_app()).post(
                    "/api/v1/mcp/servers",
                    json={
                        "name": "GitHub MCP",
                        "endpoint_url": "https://example.com/mcp",
                        "auth_mode": "none",
                    },
                )
        finally:
            if previous_key is None:
                os.environ.pop("MCP_CONFIG_ENCRYPTION_KEY", None)
            else:
                os.environ["MCP_CONFIG_ENCRYPTION_KEY"] = previous_key

        self.assertEqual(200, response.status_code)
        self.assertEqual("server-1", response.json()["data"]["id"])
        args = create_server.await_args.args
        self.assertEqual("user-1", args[0])
        self.assertEqual("GitHub MCP", args[1].name)
        self.assertEqual("route-key", args[2])
        verify_server.assert_not_awaited()

    def test_create_server_with_verify_now_verifies_and_syncs_tools(self):
        create_server = AsyncMock(return_value=_server_detail(verify_status="unknown", tool_count=0))
        verify_server = AsyncMock(return_value=_server_detail(verify_status="healthy", tool_count=2))
        previous_key = os.environ.get("MCP_CONFIG_ENCRYPTION_KEY")
        os.environ["MCP_CONFIG_ENCRYPTION_KEY"] = "route-key"
        try:
            with (
                patch.object(mcp_route.service, "create_server", new=create_server),
                patch.object(mcp_route.service, "verify_server", new=verify_server),
            ):
                response = TestClient(_make_app()).post(
                    "/api/v1/mcp/servers",
                    json={
                        "name": "GitHub MCP",
                        "endpoint_url": "https://example.com/mcp",
                        "auth_mode": "none",
                        "verify_now": True,
                    },
                )
        finally:
            if previous_key is None:
                os.environ.pop("MCP_CONFIG_ENCRYPTION_KEY", None)
            else:
                os.environ["MCP_CONFIG_ENCRYPTION_KEY"] = previous_key

        self.assertEqual(200, response.status_code)
        self.assertEqual("healthy", response.json()["data"]["verify_status"])
        self.assertEqual(2, response.json()["data"]["tool_count"])
        verify_server.assert_awaited_once_with(
            "server-1",
            "user-1",
            "route-key",
            sync_tools=True,
        )

    def test_update_server_returns_404_when_service_cannot_find_server(self):
        update_server = AsyncMock(return_value=None)

        with patch.object(mcp_route.service, "update_server", new=update_server):
            response = TestClient(_make_app()).put(
                "/api/v1/mcp/servers/missing",
                json={"name": "Renamed"},
            )

        self.assertEqual(404, response.status_code)
        update_server.assert_awaited_once()

    def test_delete_server_returns_ok_payload(self):
        delete_server = AsyncMock()

        with patch.object(mcp_route.service, "delete_server", new=delete_server):
            response = TestClient(_make_app()).delete("/api/v1/mcp/servers/server-1")

        self.assertEqual(200, response.status_code)
        self.assertEqual({"code": 0, "msg": "ok", "data": {"ok": True}}, response.json())
        delete_server.assert_awaited_once_with("server-1", "user-1")

    def test_toggle_server_enabled_uses_update_model(self):
        update_server = AsyncMock(return_value=_server_detail(enabled=False))

        with patch.object(mcp_route.service, "update_server", new=update_server):
            response = TestClient(_make_app()).put(
                "/api/v1/mcp/servers/server-1/enabled",
                json={"enabled": False},
            )

        self.assertEqual(200, response.status_code)
        self.assertFalse(response.json()["data"]["enabled"])
        args = update_server.await_args.args
        self.assertEqual("server-1", args[0])
        self.assertEqual("user-1", args[1])
        self.assertFalse(args[2].enabled)


if __name__ == "__main__":
    unittest.main()
