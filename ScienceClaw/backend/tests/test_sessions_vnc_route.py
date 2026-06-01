import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.config import settings  # noqa: E402
from backend.deepagent.sessions import ScienceSessionNotFoundError  # noqa: E402
from backend.route import sessions as sessions_route  # noqa: E402
from backend.user.dependencies import User, require_user  # noqa: E402


@dataclass
class FakeScienceSession:
    session_id: str = "session-1"
    user_id: str = "user-1"


def _test_user() -> User:
    return User(id="user-1", username="tester", role="user")


def _make_app(authenticated: bool = True) -> FastAPI:
    app = FastAPI()
    app.include_router(sessions_route.router, prefix="/api/v1")
    if authenticated:
        app.dependency_overrides[require_user] = _test_user
    return app


class SessionsVncRouteTests(unittest.TestCase):
    def test_vnc_signed_url_requires_authenticated_user(self):
        with patch.object(settings, "auth_provider", "local"):
            response = TestClient(_make_app(authenticated=False)).post(
                "/api/v1/sessions/session-1/vnc/signed-url",
                json={"expire_minutes": 15},
            )

        self.assertEqual(401, response.status_code)

    def test_vnc_signed_url_rejects_non_owner_session(self):
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=FakeScienceSession(user_id="other-user")),
        ):
            response = TestClient(_make_app()).post(
                "/api/v1/sessions/session-1/vnc/signed-url",
                json={"expire_minutes": 15},
            )

        self.assertEqual(403, response.status_code)

    def test_vnc_signed_url_returns_signed_ws_path_and_ttl(self):
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=FakeScienceSession()),
        ), patch.object(sessions_route, "_now_ts", return_value=1_000):
            response = TestClient(_make_app()).post(
                "/api/v1/sessions/session-1/vnc/signed-url",
                json={"expire_minutes": 2},
            )

        self.assertEqual(200, response.status_code)
        payload = response.json()["data"]
        self.assertEqual(120, payload["expires_in"])
        self.assertTrue(payload["signed_url"].startswith("/api/v1/sessions/session-1/vnc/ws?"))
        self.assertIn("expires=1120", payload["signed_url"])
        self.assertIn("user_id=user-1", payload["signed_url"])
        self.assertIn("sig=", payload["signed_url"])

    def test_vnc_signed_url_returns_404_for_missing_session(self):
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(side_effect=ScienceSessionNotFoundError("session missing")),
        ):
            response = TestClient(_make_app()).post(
                "/api/v1/sessions/session-1/vnc/signed-url",
                json={"expire_minutes": 15},
            )

        self.assertEqual(404, response.status_code)


if __name__ == "__main__":
    unittest.main()
