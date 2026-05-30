import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.mcp import service  # noqa: E402
from backend.mcp.crypto import decrypt_secret  # noqa: E402
from backend.mcp.schemas import (  # noqa: E402
    CreateMCPServerRequest,
    MCPHeaderSecret,
    UpdateMCPServerRequest,
)


class MCPServerServiceTests(unittest.TestCase):
    def test_create_server_normalizes_slug_and_encrypts_bearer_secret(self):
        captured = {}

        async def create_server(doc):
            captured.update(doc)
            return dict(doc)

        request = CreateMCPServerRequest(
            name="  GitHub MCP  ",
            endpoint_url="https://example.com/mcp",
            auth_mode="bearer",
            bearer_token="token-value",
        )

        with patch.object(service.repository, "create_server", new=create_server):
            result = asyncio.run(service.create_server("user-1", request, "key"))

        self.assertEqual("user-1", captured["user_id"])
        self.assertEqual("github_mcp", captured["slug"])
        self.assertEqual("https", captured["transport"])
        self.assertEqual("unknown", captured["verify_status"])
        self.assertNotEqual("token-value", captured["auth_config"]["bearer_token_encrypted"])
        self.assertEqual(
            "token-value",
            decrypt_secret(captured["auth_config"]["bearer_token_encrypted"], "key"),
        )
        self.assertEqual("github_mcp", result.slug)
        self.assertTrue(result.has_bearer_token)

    def test_create_server_rejects_secret_without_encryption_key(self):
        request = CreateMCPServerRequest(
            name="GitHub MCP",
            endpoint_url="https://example.com/mcp",
            auth_mode="bearer",
            bearer_token="token-value",
        )

        with self.assertRaises(ValueError):
            asyncio.run(service.create_server("user-1", request, ""))

    def test_create_server_encrypts_header_secrets_and_returns_masked_headers(self):
        captured = {}

        async def create_server(doc):
            captured.update(doc)
            return dict(doc)

        request = CreateMCPServerRequest(
            name="Header MCP",
            endpoint_url="https://example.com/mcp",
            auth_mode="headers",
            headers=[MCPHeaderSecret(name="X-Org-Id", value="org-secret")],
        )

        with patch.object(service.repository, "create_server", new=create_server):
            result = asyncio.run(service.create_server("user-1", request, "key"))

        encrypted_header = captured["auth_config"]["headers_encrypted"][0]
        self.assertEqual("X-Org-Id", encrypted_header["name"])
        self.assertEqual("org-secret", decrypt_secret(encrypted_header["value_encrypted"], "key"))
        self.assertEqual("X-Org-Id", result.masked_headers[0].name)
        self.assertEqual("********", result.masked_headers[0].masked_value)

    def test_list_and_get_servers_return_response_models_without_raw_auth_config(self):
        doc = {
            "_id": "server-1",
            "name": "GitHub MCP",
            "slug": "github_mcp",
            "transport": "https",
            "endpoint_url": "https://example.com/mcp",
            "auth_mode": "bearer",
            "auth_config": {"bearer_token_encrypted": "encrypted"},
            "enabled": True,
            "verify_status": "unknown",
            "created_at": 1,
            "updated_at": 2,
        }

        with (
            patch.object(service.repository, "list_servers", new=AsyncMock(return_value=[doc])),
            patch.object(service.repository, "get_server", new=AsyncMock(return_value=doc)),
        ):
            listed = asyncio.run(service.list_servers("user-1"))
            detail = asyncio.run(service.get_server("server-1", "user-1"))

        self.assertEqual("server-1", listed[0].id)
        self.assertTrue(listed[0].has_bearer_token)
        self.assertFalse(hasattr(listed[0], "auth_config"))
        self.assertEqual(1, detail.created_at)
        self.assertEqual(2, detail.updated_at)

    def test_update_server_preserves_existing_secret_when_not_changed(self):
        existing = {
            "_id": "server-1",
            "user_id": "user-1",
            "name": "Old",
            "slug": "old",
            "transport": "https",
            "endpoint_url": "https://example.com/mcp",
            "auth_mode": "bearer",
            "auth_config": {"bearer_token_encrypted": "encrypted-token"},
            "enabled": True,
            "verify_status": "healthy",
            "verify_error": "",
        }
        updated = {**existing, "name": "Renamed", "slug": "renamed", "updated_at": 5}
        update_server = AsyncMock(return_value=updated)

        with (
            patch.object(service.repository, "get_server", new=AsyncMock(return_value=existing)),
            patch.object(service.repository, "update_server", new=update_server),
        ):
            result = asyncio.run(
                service.update_server(
                    "server-1",
                    "user-1",
                    UpdateMCPServerRequest(name="Renamed"),
                    "key",
                )
            )

        patch_doc = update_server.await_args.args[2]
        self.assertEqual("Renamed", patch_doc["name"])
        self.assertEqual("renamed", patch_doc["slug"])
        self.assertNotIn("auth_config", patch_doc)
        self.assertEqual("Renamed", result.name)

    def test_update_server_reencrypts_changed_bearer_secret_and_resets_verify_status(self):
        existing = {
            "_id": "server-1",
            "user_id": "user-1",
            "name": "Old",
            "slug": "old",
            "transport": "https",
            "endpoint_url": "https://example.com/mcp",
            "auth_mode": "none",
            "auth_config": {},
            "enabled": True,
            "verify_status": "healthy",
            "verify_error": "",
        }

        async def update_server(server_id, user_id, patch_doc):
            return {**existing, **patch_doc}

        with (
            patch.object(service.repository, "get_server", new=AsyncMock(return_value=existing)),
            patch.object(service.repository, "update_server", new=update_server),
        ):
            result = asyncio.run(
                service.update_server(
                    "server-1",
                    "user-1",
                    UpdateMCPServerRequest(auth_mode="bearer", bearer_token="new-token"),
                    "key",
                )
            )

        self.assertEqual("unknown", result.verify_status)
        encrypted = result.model_dump()
        self.assertNotIn("new-token", str(encrypted))

    def test_delete_server_delegates_to_repository_only(self):
        delete_server = AsyncMock()

        with patch.object(service.repository, "delete_server", new=delete_server):
            asyncio.run(service.delete_server("server-1", "user-1"))

        delete_server.assert_awaited_once_with("server-1", "user-1")


if __name__ == "__main__":
    unittest.main()
