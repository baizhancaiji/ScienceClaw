import asyncio
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.mongodb.db import MongoDB  # noqa: E402
from backend.mcp import repository  # noqa: E402


class FakeCollection:
    def __init__(self):
        self.indexes = []
        self.documents = []

    async def create_index(self, keys, **kwargs):
        self.indexes.append((keys, kwargs))
        return "ok"

    async def insert_one(self, doc):
        self.documents.append(dict(doc))
        return None

    async def find_one(self, query):
        for doc in self.documents:
            if all(doc.get(key) == value for key, value in query.items()):
                return dict(doc)
        return None

    def find(self, query):
        docs = [
            dict(doc)
            for doc in self.documents
            if all(doc.get(key) == value for key, value in query.items())
        ]
        return FakeCursor(docs)

    async def update_one(self, query, update):
        for doc in self.documents:
            if all(doc.get(key) == value for key, value in query.items()):
                doc.update(update.get("$set", {}))
                return None
        return None

    async def delete_one(self, query):
        self.documents = [
            doc
            for doc in self.documents
            if not all(doc.get(key) == value for key, value in query.items())
        ]
        return None

    async def delete_many(self, query):
        await self.delete_one(query)
        return None


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    async def to_list(self, length=None):
        return list(self.docs)


class FakeDatabase:
    def __init__(self):
        self._collections = {}

    def __getitem__(self, name):
        return self._collections.setdefault(name, FakeCollection())

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self[name]


class MCPMongoIndexTests(unittest.TestCase):
    def setUp(self):
        self.original_db = MongoDB.db
        self.fake_db = FakeDatabase()
        MongoDB.db = self.fake_db

    def tearDown(self):
        MongoDB.db = self.original_db

    def test_init_indexes_registers_mcp_collection_indexes(self):
        asyncio.run(MongoDB.init_indexes())

        self.assertEqual(
            [
                ([("user_id", 1), ("updated_at", -1)], {}),
                ([("user_id", 1), ("enabled", 1), ("verify_status", 1)], {}),
                ([("user_id", 1), ("slug", 1)], {"unique": True}),
                ([("user_id", 1), ("endpoint_url", 1)], {}),
            ],
            self.fake_db.mcp_servers.indexes,
        )
        self.assertEqual(
            [
                ([("server_id", 1), ("original_name", 1)], {"unique": True}),
                ([("user_id", 1), ("canonical_name", 1)], {"unique": True}),
                ([("user_id", 1), ("enabled", 1), ("updated_at", -1)], {}),
                (
                    [("user_id", 1), ("enabled", 1), ("removed", 1), ("updated_at", -1)],
                    {},
                ),
                ([("user_id", 1), ("server_id", 1), ("last_seen_at", -1)], {}),
            ],
            self.fake_db.mcp_tools.indexes,
        )

    def test_init_indexes_can_run_repeatedly(self):
        asyncio.run(MongoDB.init_indexes())
        asyncio.run(MongoDB.init_indexes())

        self.assertEqual(8, len(self.fake_db.mcp_servers.indexes))
        self.assertEqual(10, len(self.fake_db.mcp_tools.indexes))


class MCPRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.original_db = MongoDB.db
        self.fake_db = FakeDatabase()
        MongoDB.db = self.fake_db

    def tearDown(self):
        MongoDB.db = self.original_db

    def test_create_get_and_list_servers_are_user_scoped(self):
        first = {
            "_id": "server-1",
            "user_id": "user-1",
            "name": "First",
            "slug": "first",
        }
        second = {
            "_id": "server-2",
            "user_id": "user-2",
            "name": "Second",
            "slug": "second",
        }

        created = asyncio.run(repository.create_server(first))
        asyncio.run(repository.create_server(second))

        self.assertEqual(first, created)
        self.assertEqual(first, asyncio.run(repository.get_server("server-1", "user-1")))
        self.assertIsNone(asyncio.run(repository.get_server("server-1", "user-2")))
        self.assertEqual([first], asyncio.run(repository.list_servers("user-1")))

    def test_later_batch_methods_are_declared_but_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            asyncio.run(repository.list_enabled_tools_by_user("user-1"))

    def test_update_server_is_user_scoped_and_preserves_unpatched_secrets(self):
        server = {
            "_id": "server-1",
            "user_id": "user-1",
            "name": "First",
            "slug": "first",
            "auth_config": {"bearer_token_encrypted": "encrypted-token"},
        }
        asyncio.run(repository.create_server(server))

        updated = asyncio.run(
            repository.update_server("server-1", "user-1", {"name": "Renamed"})
        )
        blocked = asyncio.run(
            repository.update_server("server-1", "user-2", {"name": "Wrong User"})
        )

        self.assertIsNone(blocked)
        self.assertEqual("Renamed", updated["name"])
        self.assertEqual(
            {"bearer_token_encrypted": "encrypted-token"},
            updated["auth_config"],
        )

    def test_delete_server_is_user_scoped_and_deletes_owned_tools(self):
        server = {
            "_id": "server-1",
            "user_id": "user-1",
            "name": "First",
            "slug": "first",
        }
        other = {
            "_id": "server-1",
            "user_id": "user-2",
            "name": "Other",
            "slug": "other",
        }
        asyncio.run(repository.create_server(server))
        asyncio.run(repository.create_server(other))
        self.fake_db.mcp_tools.documents.extend(
            [
                {"_id": "tool-1", "server_id": "server-1", "user_id": "user-1"},
                {"_id": "tool-2", "server_id": "server-1", "user_id": "user-2"},
            ]
        )

        asyncio.run(repository.delete_server("server-1", "user-1"))

        self.assertIsNone(asyncio.run(repository.get_server("server-1", "user-1")))
        self.assertEqual(other, asyncio.run(repository.get_server("server-1", "user-2")))
        self.assertEqual(
            [{"_id": "tool-2", "server_id": "server-1", "user_id": "user-2"}],
            self.fake_db.mcp_tools.documents,
        )

    def test_upsert_tools_from_remote_adds_and_updates_without_overwriting_enabled(self):
        existing_tool = {
            "_id": "tool-1",
            "server_id": "server-1",
            "user_id": "user-1",
            "original_name": "search",
            "canonical_name": "mcp__server__search",
            "description": "old",
            "enabled": False,
            "removed": True,
            "created_at": 1,
            "updated_at": 1,
        }
        self.fake_db.mcp_tools.documents.append(existing_tool)

        diff = asyncio.run(
            repository.upsert_tools_from_remote(
                "server-1",
                "user-1",
                [
                    {
                        "_id": "ignored-new-id",
                        "server_id": "server-1",
                        "user_id": "user-1",
                        "original_name": "search",
                        "canonical_name": "mcp__server__search",
                        "description": "new",
                        "enabled": True,
                        "removed": False,
                        "created_at": 99,
                        "updated_at": 2,
                    },
                    {
                        "_id": "tool-2",
                        "server_id": "server-1",
                        "user_id": "user-1",
                        "original_name": "read",
                        "canonical_name": "mcp__server__read",
                        "description": "read",
                        "enabled": True,
                        "removed": False,
                        "created_at": 2,
                        "updated_at": 2,
                    },
                ],
            )
        )

        self.assertEqual({"added": 1, "updated": 1}, diff)
        tools = asyncio.run(repository.list_tools_by_server("server-1", "user-1"))
        search = next(tool for tool in tools if tool["original_name"] == "search")
        self.assertEqual("tool-1", search["_id"])
        self.assertEqual("new", search["description"])
        self.assertFalse(search["enabled"])
        self.assertFalse(search["removed"])
        self.assertEqual(1, search["created_at"])

    def test_upsert_tools_from_remote_does_not_count_seen_only_refresh_as_update(self):
        self.fake_db.mcp_tools.documents.append(
            {
                "_id": "tool-1",
                "server_id": "server-1",
                "user_id": "user-1",
                "original_name": "search",
                "canonical_name": "mcp__server__search",
                "description": "same",
                "input_schema_raw": {},
                "enabled": True,
                "removed": False,
                "created_at": 1,
                "last_seen_at": 1,
                "updated_at": 1,
            }
        )

        diff = asyncio.run(
            repository.upsert_tools_from_remote(
                "server-1",
                "user-1",
                [
                    {
                        "_id": "new-id",
                        "server_id": "server-1",
                        "user_id": "user-1",
                        "original_name": "search",
                        "canonical_name": "mcp__server__search",
                        "description": "same",
                        "input_schema_raw": {},
                        "enabled": True,
                        "removed": False,
                        "created_at": 2,
                        "last_seen_at": 2,
                        "updated_at": 2,
                    },
                ],
            )
        )

        self.assertEqual({"added": 0, "updated": 0}, diff)

    def test_mark_removed_tools_marks_only_owned_present_tools_once(self):
        self.fake_db.mcp_tools.documents.extend(
            [
                {
                    "_id": "tool-1",
                    "server_id": "server-1",
                    "user_id": "user-1",
                    "original_name": "gone",
                    "removed": False,
                },
                {
                    "_id": "tool-2",
                    "server_id": "server-1",
                    "user_id": "user-1",
                    "original_name": "already_gone",
                    "removed": True,
                },
                {
                    "_id": "tool-3",
                    "server_id": "server-1",
                    "user_id": "user-2",
                    "original_name": "gone",
                    "removed": False,
                },
            ]
        )

        removed = asyncio.run(
            repository.mark_removed_tools(
                "server-1",
                "user-1",
                ["gone", "already_gone", "missing"],
            )
        )

        self.assertEqual(1, removed)
        owned = asyncio.run(repository.list_tools_by_server("server-1", "user-1"))
        self.assertTrue(next(tool for tool in owned if tool["original_name"] == "gone")["removed"])
        other = asyncio.run(repository.list_tools_by_server("server-1", "user-2"))
        self.assertFalse(other[0]["removed"])


if __name__ == "__main__":
    unittest.main()
