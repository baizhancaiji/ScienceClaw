"""Task-service authentication and owner-isolation contract tests."""
from __future__ import annotations

import time
import unittest
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import tasks as tasks_api
from app.api import webhooks as webhooks_api
from app.auth import User, require_user
from app.core.db import db


class AsyncCursor:
    def __init__(self, docs: list[dict[str, Any]]):
        self._docs = list(docs)

    def sort(self, key: str, direction: int):
        reverse = direction < 0
        self._docs.sort(key=lambda d: d.get(key) or datetime.min.replace(tzinfo=timezone.utc), reverse=reverse)
        return self

    def skip(self, offset: int):
        self._docs = self._docs[offset:]
        return self

    def limit(self, limit: int):
        self._docs = self._docs[:limit]
        return self

    def __aiter__(self):
        self._iter = iter(self._docs)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class Result:
    def __init__(self, deleted_count: int = 0):
        self.deleted_count = deleted_count


class FakeCollection:
    def __init__(self, docs: list[dict[str, Any]] | None = None):
        self.docs = list(docs or [])

    @staticmethod
    def _matches(doc: dict[str, Any], query: dict[str, Any]) -> bool:
        return all(doc.get(key) == value for key, value in query.items())

    def find(self, query: dict[str, Any] | None = None, projection: dict[str, Any] | None = None):
        query = query or {}
        docs = [doc for doc in self.docs if self._matches(doc, query)]
        if projection:
            docs = [{key: doc[key] for key in projection if key in doc} for doc in docs]
        return AsyncCursor(docs)

    async def find_one(self, query: dict[str, Any]):
        for doc in self.docs:
            if self._matches(doc, query):
                return doc
        return None

    async def insert_one(self, doc: dict[str, Any]):
        self.docs.append(doc)

    async def update_one(self, query: dict[str, Any], update: dict[str, Any]):
        for doc in self.docs:
            if self._matches(doc, query):
                doc.update(update.get("$set", {}))
                return

    async def delete_one(self, query: dict[str, Any]):
        for index, doc in enumerate(self.docs):
            if self._matches(doc, query):
                del self.docs[index]
                return Result(deleted_count=1)
        return Result(deleted_count=0)

    async def update_many(self, query: dict[str, Any], update: dict[str, Any]):
        pull = update.get("$pull", {})
        for doc in self.docs:
            if all(value in doc.get(key, []) for key, value in query.items()):
                for key, value in pull.items():
                    doc[key] = [item for item in doc.get(key, []) if item != value]

    async def count_documents(self, query: dict[str, Any]):
        return len([doc for doc in self.docs if self._matches(doc, query)])


class FakeDB:
    def __init__(self):
        now = datetime.now(timezone.utc)
        self.collections = {
            "user_sessions": FakeCollection([
                {"_id": "token-user-1", "user_id": "user-1", "username": "alice", "role": "user", "expires_at": int(time.time()) + 60},
            ]),
            "tasks": FakeCollection([
                {"_id": "task-1", "name": "Mine", "prompt": "p", "schedule_desc": "daily", "crontab": "0 7 * * *", "status": "enabled", "user_id": "user-1", "created_at": now, "updated_at": now},
                {"_id": "task-2", "name": "Other", "prompt": "p", "schedule_desc": "daily", "crontab": "0 8 * * *", "status": "enabled", "user_id": "user-2", "created_at": now, "updated_at": now},
            ]),
            "task_runs": FakeCollection([
                {"_id": "run-1", "task_id": "task-1", "status": "success", "start_time": now},
                {"_id": "run-2", "task_id": "task-2", "status": "success", "start_time": now},
            ]),
            "webhooks": FakeCollection([
                {"_id": "hook-1", "name": "Mine", "type": "feishu", "url": "https://example.test/1", "user_id": "user-1", "created_at": now, "updated_at": now},
                {"_id": "hook-2", "name": "Other", "type": "feishu", "url": "https://example.test/2", "user_id": "user-2", "created_at": now, "updated_at": now},
            ]),
        }

    def get_collection(self, name: str):
        return self.collections[name]


class TaskServiceAuthIsolationTests(unittest.TestCase):
    def setUp(self):
        self.fake_db = FakeDB()
        self.original_get_collection = db.get_collection
        db.get_collection = self.fake_db.get_collection

        self.app = FastAPI()
        self.app.include_router(tasks_api.router)
        self.app.include_router(webhooks_api.router)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.app.dependency_overrides.clear()
        db.get_collection = self.original_get_collection

    def _as_user(self, user_id: str = "user-1", role: str = "user"):
        async def override_user():
            return User(id=user_id, username=user_id, role=role)

        self.app.dependency_overrides[require_user] = override_user

    def test_tasks_require_bearer_session(self):
        response = self.client.get("/tasks")
        self.assertEqual(response.status_code, 401)

        response = self.client.get("/tasks", headers={"Authorization": "Bearer token-user-1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], ["task-1"])

    def test_regular_user_cannot_access_other_users_task(self):
        self._as_user("user-1")
        self.assertEqual(self.client.get("/tasks/task-2").status_code, 404)
        self.assertEqual(self.client.delete("/tasks/task-2").status_code, 404)
        self.assertEqual(self.client.get("/tasks/task-2/runs").status_code, 404)

    def test_admin_can_list_all_tasks(self):
        self._as_user("admin-1", role="admin")
        response = self.client.get("/tasks")
        self.assertEqual(response.status_code, 200)
        self.assertEqual({item["id"] for item in response.json()}, {"task-1", "task-2"})

    def test_created_task_is_owned_by_regular_user(self):
        self._as_user("user-1")
        response = self.client.post(
            "/tasks",
            json={
                "name": "Created",
                "prompt": "p",
                "schedule_desc": "daily",
                "crontab": "0 9 * * *",
                "status": "enabled",
                "user_id": "user-2",
            },
        )
        self.assertEqual(response.status_code, 200)
        created = self.fake_db.get_collection("tasks").docs[-1]
        self.assertEqual(created["user_id"], "user-1")

    def test_webhooks_are_filtered_by_owner(self):
        self._as_user("user-1")
        response = self.client.get("/webhooks")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], ["hook-1"])
        self.assertEqual(self.client.get("/webhooks/hook-2").status_code, 404)

    def test_admin_can_list_all_webhooks(self):
        self._as_user("admin-1", role="admin")
        response = self.client.get("/webhooks")
        self.assertEqual(response.status_code, 200)
        self.assertEqual({item["id"] for item in response.json()}, {"hook-1", "hook-2"})

    def test_created_webhook_is_owned_by_current_user(self):
        self._as_user("user-1")
        response = self.client.post(
            "/webhooks",
            json={"name": "Created", "type": "feishu", "url": "https://example.test/new"},
        )
        self.assertEqual(response.status_code, 200)
        created = self.fake_db.get_collection("webhooks").docs[-1]
        self.assertEqual(created["user_id"], "user-1")


if __name__ == "__main__":
    unittest.main()
