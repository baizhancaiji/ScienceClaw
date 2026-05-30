import asyncio
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.mongodb.db import MongoDB  # noqa: E402


class FakeCollection:
    def __init__(self):
        self.indexes = []

    async def create_index(self, keys, **kwargs):
        self.indexes.append((keys, kwargs))
        return "ok"


class FakeDatabase:
    def __init__(self):
        self._collections = {}

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._collections.setdefault(name, FakeCollection())


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


if __name__ == "__main__":
    unittest.main()
