import sys
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.route import tools as tools_route  # noqa: E402
from backend.tool_discovery import set_tool_discovery_service  # noqa: E402
from backend.tool_discovery.schemas import ToolInfoResult, ToolRunResult, ToolSearchRequest, ToolSearchResult  # noqa: E402
from backend.user.dependencies import User, require_user  # noqa: E402


def _test_user() -> User:
    return User(id="user-1", username="tester", role="user")


def _make_app(authenticated: bool = True) -> FastAPI:
    app = FastAPI()
    app.include_router(tools_route.router, prefix="/api/v1")
    if authenticated:
        app.dependency_overrides[require_user] = _test_user
    return app


class FakeDiscoveryService:
    def __init__(self):
        self.search_calls = []
        self.info_calls = []
        self.run_calls = []

    async def search(self, request: ToolSearchRequest, user_id: str):
        self.search_calls.append((request, user_id))
        payload = {
            "tool_ref": "external:pdf_convert",
            "name": "pdf_convert",
            "cat_zh": "文档处理",
            "why": "命中文档处理",
        }
        if request.debug:
            payload.update({"score": 8.0, "source_type": "external_python_tool", "hit_fields": ["aliases"]})
        return [ToolSearchResult(**payload)]

    async def get_info(self, tool_ref: str, user_id: str):
        self.info_calls.append((tool_ref, user_id))
        if tool_ref == "missing:tool":
            raise LookupError("not found")
        return ToolInfoResult(
            tool_ref=tool_ref,
            source_type="external_python_tool",
            name="pdf_convert",
            cat_zh="文档处理",
            input_schema={"type": "object"},
        )

    async def run(self, tool_ref: str, arguments: dict, user_id: str):
        self.run_calls.append((tool_ref, arguments, user_id))
        return ToolRunResult(tool_ref=tool_ref, ok=True, result={"ok": True})


class ToolsRouteTests(unittest.TestCase):
    def setUp(self):
        self.service = FakeDiscoveryService()
        set_tool_discovery_service(self.service)

    def tearDown(self):
        set_tool_discovery_service(None)

    def test_tool_routes_require_authenticated_user(self):
        response = TestClient(_make_app(authenticated=False)).post(
            "/api/v1/tools/search",
            json={"query": "PDF 转换"},
        )

        self.assertEqual(401, response.status_code)

    def test_search_route_uses_current_user_and_hides_debug_by_default(self):
        response = TestClient(_make_app()).post(
            "/api/v1/tools/search",
            json={"query": "PDF 转换", "limit": 5},
        )

        self.assertEqual(200, response.status_code)
        result = response.json()["data"]["results"][0]
        self.assertEqual({"tool_ref", "name", "cat_zh", "why"}, set(result.keys()))
        request, user_id = self.service.search_calls[0]
        self.assertFalse(request.debug)
        self.assertEqual("user-1", user_id)

    def test_search_route_returns_debug_only_when_requested(self):
        response = TestClient(_make_app()).post(
            "/api/v1/tools/search",
            json={"query": "PDF 转换", "debug": True},
        )

        self.assertEqual(200, response.status_code)
        result = response.json()["data"]["results"][0]
        self.assertEqual(8.0, result["score"])
        self.assertEqual("external_python_tool", result["source_type"])
        self.assertEqual(["aliases"], result["hit_fields"])

    def test_info_and_run_routes_use_current_user(self):
        client = TestClient(_make_app())

        info_response = client.get("/api/v1/tools/info/external:pdf_convert")
        run_response = client.post(
            "/api/v1/tools/run",
            json={"tool_ref": "external:pdf_convert", "arguments": {"path": "a.pdf"}},
        )

        self.assertEqual(200, info_response.status_code)
        self.assertEqual("文档处理", info_response.json()["data"]["cat_zh"])
        self.assertEqual(200, run_response.status_code)
        self.assertEqual(
            ("external:pdf_convert", {"path": "a.pdf"}, "user-1"),
            self.service.run_calls[0],
        )

    def test_info_route_returns_404_for_missing_tool(self):
        response = TestClient(_make_app()).get("/api/v1/tools/info/missing:tool")

        self.assertEqual(404, response.status_code)


if __name__ == "__main__":
    unittest.main()
