import asyncio
import sys
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.config import settings  # noqa: E402
from backend.deepagent import sessions as session_store  # noqa: E402
from backend.deepagent.sessions import ScienceSession, ScienceSessionNotFoundError  # noqa: E402
from backend.route import sessions as sessions_route  # noqa: E402
from backend.user.dependencies import User, require_user  # noqa: E402


@dataclass
class FakeScienceSession:
    session_id: str = "session-1"
    user_id: str = "user-1"
    title: str = "Protected Session"
    status: str = "completed"
    events: list = field(default_factory=lambda: [{"event": "message", "data": {"content": "secret"}}])
    is_shared: bool = False
    mode: str = "deep"
    model_config: dict | None = None
    selected_skill_names: list = field(default_factory=list)
    password_hash: str | None = None
    password_hint: str | None = None
    password_unlocked_by: dict = field(default_factory=dict)
    vm_root_dir: Path = field(default_factory=lambda: Path("/tmp/scienceclaw-session-1"))
    saved: bool = False

    async def save(self):
        self.saved = True

    def cancel(self):
        self.status = "completed"


class FakeUsersCollection:
    def __init__(self, user_doc):
        self.user_doc = user_doc

    async def find_one(self, _query):
        return self.user_doc


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *_args):
        return self

    def __aiter__(self):
        self._iter = iter(self.docs)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class FakeSessionsCollection:
    def __init__(self, docs=None):
        self.docs = list(docs or [])
        self.last_update = None

    async def find_one(self, query):
        session_id = query.get("_id")
        return next((doc for doc in self.docs if doc.get("_id") == session_id), None)

    def find(self, _query, projection):
        projected = []
        for doc in self.docs:
            projected.append({key: doc[key] for key in projection if key in doc})
        return FakeCursor(projected)

    async def update_one(self, query, update, upsert=False):
        self.last_update = {"query": query, "update": update, "upsert": upsert}


class FakeDB:
    def __init__(self, user_doc=None, session_docs=None):
        self.user_doc = user_doc
        self.sessions = FakeSessionsCollection(session_docs)

    def get_collection(self, name):
        if name == "users":
            return FakeUsersCollection(self.user_doc)
        if name == "sessions":
            return self.sessions
        raise AssertionError(f"Unexpected collection: {name}")


def _test_user() -> User:
    return User(id="user-1", username="tester", role="user")


def _make_app(authenticated: bool = True) -> FastAPI:
    app = FastAPI()
    app.include_router(sessions_route.router, prefix="/api/v1")
    if authenticated:
        app.dependency_overrides[require_user] = _test_user
    return app


def _client(authenticated: bool = True) -> TestClient:
    return TestClient(_make_app(authenticated=authenticated))


class SessionsPasswordTests(unittest.TestCase):
    def setUp(self):
        session_store._sessions.clear()
        session_store._sessions_atime.clear()

    @staticmethod
    def _run_async(coro):
        return asyncio.run(coro)

    def test_password_endpoints_require_authenticated_user(self):
        with patch.object(settings, "auth_provider", "local"):
            response = _client(authenticated=False).post(
                "/api/v1/sessions/session-1/password",
                json={"password": "Abcd1"},
            )

        self.assertEqual(401, response.status_code)

    def test_set_password_hashes_password_clears_share_and_unlocks_session(self):
        session = FakeScienceSession(is_shared=True)
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=session),
        ):
            response = _client().post(
                "/api/v1/sessions/session-1/password",
                json={"password": "Abcd1", "hint": "memory"},
            )

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.json()["data"]["has_password"])
        self.assertTrue(session.saved)
        self.assertFalse(session.is_shared)
        self.assertEqual("memory", session.password_hint)
        self.assertIsNotNone(session.password_hash)
        self.assertNotEqual("Abcd1", session.password_hash)
        self.assertTrue(sessions_route._verify_session_password("Abcd1", session.password_hash))
        self.assertTrue(sessions_route._is_session_unlocked(session, _test_user()))
        self.assertNotIn("unlock_token", response.json()["data"])

    def test_set_password_rejects_weak_password(self):
        session = FakeScienceSession()
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=session),
        ):
            response = _client().post(
                "/api/v1/sessions/session-1/password",
                json={"password": "abcd"},
            )

        self.assertEqual(400, response.status_code)

    def test_session_password_fields_are_saved_and_restored(self):
        db = FakeDB()
        session = ScienceSession(
            session_id="session-1",
            thread_id="session-1",
            vm_root_dir=Path("/tmp/scienceclaw-session-1"),
            user_id="user-1",
            password_hash="hash-value",
            password_hint="hint-value",
        )

        with patch.object(session_store, "db", db):
            self.assertEqual({}, session.password_unlocked_by)
            self.assertIsNone(db.sessions.last_update)
            self._run_async(session.save())

        update_data = db.sessions.last_update["update"]["$set"]
        self.assertEqual("hash-value", update_data["password_hash"])
        self.assertEqual("hint-value", update_data["password_hint"])
        self.assertNotIn("password_unlocked_by", update_data)

    def test_get_and_list_restore_session_password_fields(self):
        doc = {
            "_id": "session-1",
            "thread_id": "session-1",
            "vm_root_dir": "/tmp/scienceclaw-session-1",
            "user_id": "user-1",
            "password_hash": "hash-value",
            "password_hint": "hint-value",
        }
        db = FakeDB(session_docs=[doc])

        with patch.object(session_store, "db", db):
            loaded = self._run_async(session_store.async_get_science_session("session-1"))
            session_store._sessions.clear()
            session_store._sessions_atime.clear()
            listed = self._run_async(session_store.async_list_science_sessions("user-1"))

        self.assertEqual("hash-value", loaded.password_hash)
        self.assertEqual("hint-value", loaded.password_hint)
        self.assertEqual("hash-value", listed[0].password_hash)

    def test_set_password_rejects_non_owner_and_missing_session(self):
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=FakeScienceSession(user_id="other-user")),
        ):
            non_owner = _client().post(
                "/api/v1/sessions/session-1/password",
                json={"password": "Abcd1"},
            )
        self.assertEqual(403, non_owner.status_code)

        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(side_effect=ScienceSessionNotFoundError("missing")),
        ):
            missing = _client().post(
                "/api/v1/sessions/session-1/password",
                json={"password": "Abcd1"},
            )
        self.assertEqual(404, missing.status_code)

    def test_get_session_returns_metadata_without_events_when_locked(self):
        session = FakeScienceSession(
            password_hash=sessions_route._hash_session_password("Abcd1"),
            password_hint="memory",
        )
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=session),
        ):
            response = _client().get("/api/v1/sessions/session-1")

        self.assertEqual(200, response.status_code)
        payload = response.json()["data"]
        self.assertTrue(payload["has_password"])
        self.assertTrue(payload["locked"])
        self.assertEqual([], payload["events"])
        self.assertNotIn("password_hint", payload)

    def test_verify_password_unlocks_and_then_get_session_returns_events(self):
        session = FakeScienceSession(password_hash=sessions_route._hash_session_password("Abcd1"))
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=session),
        ):
            wrong = _client().post(
                "/api/v1/sessions/session-1/verify-password",
                json={"password": "wrong"},
            )
            locked = _client().get("/api/v1/sessions/session-1")
            correct = _client().post(
                "/api/v1/sessions/session-1/verify-password",
                json={"password": "Abcd1"},
            )
            unlocked = _client().get(
                "/api/v1/sessions/session-1",
            )
            relock = _client().post(
                "/api/v1/sessions/session-1/password/lock",
            )
            locked_again = _client().get(
                "/api/v1/sessions/session-1",
            )

        self.assertFalse(wrong.json()["data"]["valid"])
        self.assertNotIn("unlock_token", wrong.json()["data"])
        self.assertTrue(locked.json()["data"]["locked"])
        self.assertTrue(correct.json()["data"]["valid"])
        self.assertNotIn("unlock_token", correct.json()["data"])
        self.assertFalse(unlocked.json()["data"]["locked"])
        self.assertEqual(session.events, unlocked.json()["data"]["events"])
        self.assertTrue(relock.json()["data"]["locked"])
        self.assertTrue(locked_again.json()["data"]["locked"])
        self.assertEqual([], locked_again.json()["data"]["events"])

    def test_update_and_remove_password_rotate_and_clear_fields(self):
        old_hash = sessions_route._hash_session_password("Oldpass1")
        session = FakeScienceSession(password_hash=old_hash, password_hint="old")
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=session),
        ):
            update = _client().put(
                "/api/v1/sessions/session-1/password",
                json={"old_password": "Oldpass1", "new_password": "Newpass1", "hint": "new"},
            )

        self.assertEqual(200, update.status_code)
        self.assertNotEqual(old_hash, session.password_hash)
        self.assertTrue(sessions_route._verify_session_password("Newpass1", session.password_hash))
        self.assertEqual("new", session.password_hint)

        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=session),
        ):
            remove = _client().post(
                "/api/v1/sessions/session-1/password/remove",
                json={"password": "Newpass1"},
            )

        self.assertEqual(200, remove.status_code)
        self.assertIsNone(session.password_hash)
        self.assertIsNone(session.password_hint)

    def test_reset_password_requires_account_password(self):
        session = FakeScienceSession(password_hash=sessions_route._hash_session_password("Oldpass1"))
        user_hash = sessions_route._hash_session_password("Account1")
        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=session),
        ), patch.object(sessions_route, "_db", FakeDB({"_id": "user-1", "password_hash": user_hash})):
            bad = _client().post(
                "/api/v1/sessions/session-1/reset-password",
                json={"account_password": "wrong", "new_password": "Newpass1"},
            )
            good = _client().post(
                "/api/v1/sessions/session-1/reset-password",
                json={"account_password": "Account1", "new_password": "Newpass1", "hint": "reset"},
            )

        self.assertEqual(400, bad.status_code)
        self.assertEqual(200, good.status_code)
        self.assertTrue(sessions_route._verify_session_password("Newpass1", session.password_hash))
        self.assertEqual("reset", session.password_hint)

    def test_list_sessions_exposes_has_password(self):
        sessions = [
            FakeScienceSession(session_id="plain"),
            FakeScienceSession(session_id="locked", password_hash="hash"),
        ]
        with patch.object(
            sessions_route,
            "async_list_science_sessions",
            new=AsyncMock(return_value=sessions),
        ):
            response = _client().get("/api/v1/sessions")

        self.assertEqual(200, response.status_code)
        items = response.json()["data"]["sessions"]
        self.assertFalse(items[0]["has_password"])
        self.assertTrue(items[1]["has_password"])

    def test_protected_resource_endpoints_reject_locked_session(self):
        session = FakeScienceSession(password_hash=sessions_route._hash_session_password("Abcd1"))
        endpoints = [
            ("post", "/api/v1/sessions/session-1/chat", {"message": ""}),
            ("post", "/api/v1/sessions/session-1/stop", None),
            ("post", "/api/v1/sessions/session-1/clear_unread_message_count", None),
            ("get", "/api/v1/sessions/session-1/files", None),
            ("get", "/api/v1/sessions/session-1/sandbox-file?path=/tmp/scienceclaw-session-1/a.txt", None),
            ("get", "/api/v1/sessions/session-1/sandbox-file/download?path=/tmp/scienceclaw-session-1/a.txt", None),
            ("post_file", "/api/v1/sessions/session-1/upload", None),
            ("post", "/api/v1/sessions/session-1/vnc/signed-url", {"expire_minutes": 15}),
            ("post", "/api/v1/sessions/session-1/share", None),
            ("delete", "/api/v1/sessions/session-1/share", None),
            ("post", "/api/v1/sessions/session-1/skills/save", {"skill_name": "demo"}),
            ("post", "/api/v1/sessions/session-1/tools/save", {"tool_name": "demo"}),
        ]

        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=session),
        ):
            client = _client()
            for method, url, json_body in endpoints:
                if method == "post_file":
                    response = client.post(url, files={"file": ("a.txt", b"secret", "text/plain")})
                else:
                    requester = getattr(client, method)
                    response = requester(url, json=json_body) if json_body is not None else requester(url)
                self.assertEqual(403, response.status_code, url)

    def test_password_protected_session_cannot_be_shared_even_after_unlock(self):
        session = FakeScienceSession(password_hash=sessions_route._hash_session_password("Abcd1"))
        sessions_route._mark_session_unlocked(session, _test_user())

        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=session),
        ):
            response = _client().post(
                "/api/v1/sessions/session-1/share",
            )

        self.assertEqual(400, response.status_code)

    def test_password_protected_shared_session_is_not_publicly_readable(self):
        session = FakeScienceSession(
            is_shared=True,
            password_hash=sessions_route._hash_session_password("Abcd1"),
        )

        with patch.object(
            sessions_route,
            "async_get_science_session",
            new=AsyncMock(return_value=session),
        ):
            response = _client(authenticated=False).get("/api/v1/sessions/shared/session-1")

        self.assertEqual(404, response.status_code)


if __name__ == "__main__":
    unittest.main()
