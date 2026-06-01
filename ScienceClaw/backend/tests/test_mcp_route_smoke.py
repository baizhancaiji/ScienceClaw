import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.route.mcp import router as mcp_router  # noqa: E402
from backend.config import settings  # noqa: E402
from backend.user.dependencies import User, require_user  # noqa: E402


_SAMPLE_PATH_PARAMS = {
    "server_id": "server-1",
    "tool_id": "tool-1",
}


def _test_user() -> User:
    return User(id="user-1", username="tester", role="user")


def _make_app(authenticated: bool = True) -> FastAPI:
    app = FastAPI()
    app.include_router(mcp_router, prefix="/api/v1")
    if authenticated:
        app.dependency_overrides[require_user] = _test_user
    return app


def _sample_route_path(path: str) -> str:
    for name, value in _SAMPLE_PATH_PARAMS.items():
        path = path.replace(f"{{{name}}}", value)
    return path


def _sample_route_json(method: str, path: str) -> dict | None:
    if method == "POST" and path.endswith("/servers"):
        return {
            "name": "GitHub MCP",
            "endpoint_url": "https://example.com/mcp",
            "auth_mode": "none",
        }
    if method == "PUT" and path.endswith("/servers/{server_id}"):
        return {"name": "Renamed MCP"}
    if method == "PUT" and path.endswith("/enabled"):
        return {"enabled": True}
    return None


class MCPRouteSmokeTests(unittest.TestCase):
    def test_mcp_health_route_uses_standard_api_response(self):
        response = TestClient(_make_app()).get("/api/v1/mcp/health")

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            {"code": 0, "msg": "ok", "data": {"status": "ok"}},
            response.json(),
        )

    def test_mcp_health_route_requires_authenticated_user(self):
        with patch.object(settings, "auth_provider", "local"):
            response = TestClient(_make_app(authenticated=False)).get("/api/v1/mcp/health")

        self.assertEqual(401, response.status_code)

    def test_all_mcp_routes_require_authenticated_user(self):
        app = _make_app()
        mcp_routes = [
            route
            for route in app.routes
            if isinstance(route, APIRoute) and route.path.startswith("/api/v1/mcp/")
        ]

        self.assertTrue(mcp_routes)
        for route in mcp_routes:
            dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
            self.assertIn(require_user, dependency_calls, route.path)

    def test_all_mcp_route_methods_reject_unauthenticated_requests(self):
        with patch.object(settings, "auth_provider", "local"):
            app = _make_app(authenticated=False)
            client = TestClient(app)
            mcp_routes = [
                route
                for route in app.routes
                if isinstance(route, APIRoute) and route.path.startswith("/api/v1/mcp/")
            ]

            self.assertTrue(mcp_routes)
            for route in mcp_routes:
                methods = sorted(route.methods - {"HEAD", "OPTIONS"})
                for method in methods:
                    response = client.request(
                        method,
                        _sample_route_path(route.path),
                        json=_sample_route_json(method, route.path),
                    )
                    self.assertEqual(401, response.status_code, f"{method} {route.path}")

    def test_main_registers_mcp_router_under_api_v1(self):
        from backend.main import create_app

        app = create_app()
        route_paths = {getattr(route, "path", "") for route in app.routes}

        self.assertIn("/api/v1/mcp/health", route_paths)
        self.assertIn("/api/v1/tools/search", route_paths)
        self.assertIn("/health", route_paths)
        self.assertIn("/ready", route_paths)


if __name__ == "__main__":
    unittest.main()
