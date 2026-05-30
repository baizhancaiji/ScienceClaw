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
            asyncio.run(repository.update_server("server-1", "user-1", {"name": "New"}))
        with self.assertRaises(NotImplementedError):
            asyncio.run(repository.list_tools_by_server("server-1", "user-1"))


if __name__ == "__main__":
    unittest.main()
