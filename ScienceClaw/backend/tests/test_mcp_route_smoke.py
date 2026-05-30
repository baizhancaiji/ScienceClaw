import sys
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.route.mcp import router as mcp_router  # noqa: E402


class MCPRouteSmokeTests(unittest.TestCase):
    def test_mcp_health_route_uses_standard_api_response(self):
        app = FastAPI()
        app.include_router(mcp_router, prefix="/api/v1")

        response = TestClient(app).get("/api/v1/mcp/health")

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            {"code": 0, "msg": "ok", "data": {"status": "ok"}},
            response.json(),
        )

    def test_main_registers_mcp_router_under_api_v1(self):
        from backend.main import create_app

        app = create_app()
        route_paths = {getattr(route, "path", "") for route in app.routes}

        self.assertIn("/api/v1/mcp/health", route_paths)
        self.assertIn("/health", route_paths)
        self.assertIn("/ready", route_paths)


if __name__ == "__main__":
    unittest.main()
