import sys
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.route.mcp import router as mcp_router  # noqa: E402
from backend.user.dependencies import User, require_user  # noqa: E402


def _test_user() -> User:
    return User(id="user-1", username="tester", role="user")


def _make_app(authenticated: bool = True) -> FastAPI:
    app = FastAPI()
    app.include_router(mcp_router, prefix="/api/v1")
    if authenticated:
        app.dependency_overrides[require_user] = _test_user
    return app


class MCPRouteSmokeTests(unittest.TestCase):
    def test_mcp_health_route_uses_standard_api_response(self):
        response = TestClient(_make_app()).get("/api/v1/mcp/health")

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            {"code": 0, "msg": "ok", "data": {"status": "ok"}},
            response.json(),
        )

    def test_mcp_health_route_requires_authenticated_user(self):
        response = TestClient(_make_app(authenticated=False)).get("/api/v1/mcp/health")

        self.assertEqual(401, response.status_code)

    def test_main_registers_mcp_router_under_api_v1(self):
        from backend.main import create_app

        app = create_app()
        route_paths = {getattr(route, "path", "") for route in app.routes}

        self.assertIn("/api/v1/mcp/health", route_paths)
        self.assertIn("/health", route_paths)
        self.assertIn("/ready", route_paths)


if __name__ == "__main__":
    unittest.main()
