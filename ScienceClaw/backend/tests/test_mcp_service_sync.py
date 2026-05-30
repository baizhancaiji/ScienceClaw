import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.mcp import service  # noqa: E402
from backend.mcp.client import MCPClientError, MCPRemoteTool  # noqa: E402
from backend.mcp.crypto import encrypt_secret  # noqa: E402


def _server_doc(**overrides):
    data = {
        "_id": "server-1",
        "user_id": "user-1",
        "name": "GitHub MCP",
        "slug": "github_mcp",
        "transport": "https",
        "endpoint_url": "https://example.com/mcp",
        "auth_mode": "none",
        "auth_config": {},
        "enabled": True,
        "verify_status": "unknown",
        "verify_error": "",
        "tool_count": 0,
        "last_verified_at": None,
        "created_at": 1,
        "updated_at": 1,
    }
    data.update(overrides)
    return data


class MCPVerifyServiceTests(unittest.TestCase):
    def test_verify_server_marks_healthy_and_records_tool_count(self):
        existing = _server_doc()
        update_server = AsyncMock(
            side_effect=lambda server_id, user_id, patch: {**existing, **patch}
        )
        remote_tools = [
            MCPRemoteTool(name="search", description="", input_schema_raw={}),
            MCPRemoteTool(name="read", description="", input_schema_raw={}),
        ]

        with (
            patch.object(service.repository, "get_server", new=AsyncMock(return_value=existing)),
            patch.object(service.repository, "update_server", new=update_server),
            patch.object(service.client, "initialize", new=AsyncMock(return_value={})),
            patch.object(service.client, "list_tools", new=AsyncMock(return_value=remote_tools)),
        ):
            result = asyncio.run(service.verify_server("server-1", "user-1", "key"))

        self.assertEqual("healthy", result.verify_status)
        self.assertEqual("", result.verify_error)
        self.assertEqual(2, result.tool_count)
        self.assertGreaterEqual(result.duration_ms, 0)
        patch_doc = update_server.await_args.args[2]
        self.assertEqual("healthy", patch_doc["verify_status"])
        self.assertEqual(2, patch_doc["tool_count"])
        self.assertIsInstance(patch_doc["last_verified_at"], int)

    def test_verify_server_marks_error_and_summarizes_client_failure(self):
        existing = _server_doc(verify_status="healthy", verify_error="")
        update_server = AsyncMock(
            side_effect=lambda server_id, user_id, patch: {**existing, **patch}
        )
        failure = MCPClientError(
            code="remote_mcp_timeout",
            message="Remote MCP request timed out",
            retryable=True,
        )

        with (
            patch.object(service.repository, "get_server", new=AsyncMock(return_value=existing)),
            patch.object(service.repository, "update_server", new=update_server),
            patch.object(service.client, "initialize", new=AsyncMock(side_effect=failure)),
            patch.object(service.client, "list_tools", new=AsyncMock()) as list_tools,
        ):
            result = asyncio.run(service.verify_server("server-1", "user-1", "key"))
            list_tools.assert_not_awaited()

        self.assertEqual("error", result.verify_status)
        self.assertEqual("remote_mcp_timeout: Remote MCP request timed out", result.verify_error)
        patch_doc = update_server.await_args.args[2]
        self.assertEqual("error", patch_doc["verify_status"])
        self.assertNotIn("tool_count", patch_doc)

    def test_verify_server_returns_none_when_server_not_found(self):
        update_server = AsyncMock()

        with (
            patch.object(service.repository, "get_server", new=AsyncMock(return_value=None)),
            patch.object(service.repository, "update_server", new=update_server),
            patch.object(service.client, "initialize", new=AsyncMock()) as initialize,
            patch.object(service.client, "list_tools", new=AsyncMock()),
        ):
            result = asyncio.run(service.verify_server("missing", "user-1", "key"))
            initialize.assert_not_awaited()

        self.assertIsNone(result)
        update_server.assert_not_awaited()

    def test_verify_server_decrypts_bearer_secret_for_remote_headers(self):
        existing = _server_doc(
            auth_mode="bearer",
            auth_config={"bearer_token_encrypted": encrypt_secret("token-value", "key")},
        )

        async def update_server(_server_id, _user_id, patch):
            return {**existing, **patch}

        with (
            patch.object(service.repository, "get_server", new=AsyncMock(return_value=existing)),
            patch.object(service.repository, "update_server", new=update_server),
            patch.object(service.client, "initialize", new=AsyncMock(return_value={})) as initialize,
            patch.object(service.client, "list_tools", new=AsyncMock(return_value=[])) as list_tools,
        ):
            asyncio.run(service.verify_server("server-1", "user-1", "key"))
            self.assertEqual(
                {"Authorization": "Bearer token-value"},
                initialize.await_args.kwargs["headers"],
            )
            self.assertEqual(
                {"Authorization": "Bearer token-value"},
                list_tools.await_args.kwargs["headers"],
            )

    def test_verify_server_decrypts_static_headers_for_remote_headers(self):
        existing = _server_doc(
            auth_mode="headers",
            auth_config={
                "headers_encrypted": [
                    {
                        "name": "X-Api-Key",
                        "value_encrypted": encrypt_secret("header-secret", "key"),
                    }
                ]
            },
        )

        async def update_server(_server_id, _user_id, patch):
            return {**existing, **patch}

        with (
            patch.object(service.repository, "get_server", new=AsyncMock(return_value=existing)),
            patch.object(service.repository, "update_server", new=update_server),
            patch.object(service.client, "initialize", new=AsyncMock(return_value={})) as initialize,
            patch.object(service.client, "list_tools", new=AsyncMock(return_value=[])),
        ):
            asyncio.run(service.verify_server("server-1", "user-1", "key"))
            self.assertEqual(
                {"X-Api-Key": "header-secret"},
                initialize.await_args.kwargs["headers"],
            )

    def test_verify_server_marks_error_when_secret_decryption_fails(self):
        existing = _server_doc(
            auth_mode="bearer",
            auth_config={"bearer_token_encrypted": encrypt_secret("token-value", "right-key")},
        )

        async def update_server(_server_id, _user_id, patch):
            return {**existing, **patch}

        with (
            patch.object(service.repository, "get_server", new=AsyncMock(return_value=existing)),
            patch.object(service.repository, "update_server", new=update_server),
            patch.object(service.client, "initialize", new=AsyncMock()) as initialize,
        ):
            result = asyncio.run(service.verify_server("server-1", "user-1", "wrong-key"))
            initialize.assert_not_awaited()

        self.assertEqual("error", result.verify_status)
        self.assertTrue(result.verify_error.startswith("mcp_auth_error:"))

    def test_verify_error_summary_is_truncated(self):
        existing = _server_doc()
        long_failure = MCPClientError(code="remote_mcp_error", message="x" * 500)

        async def update_server(_server_id, _user_id, patch):
            return {**existing, **patch}

        with (
            patch.object(service.repository, "get_server", new=AsyncMock(return_value=existing)),
            patch.object(service.repository, "update_server", new=update_server),
            patch.object(service.client, "initialize", new=AsyncMock(side_effect=long_failure)),
        ):
            result = asyncio.run(service.verify_server("server-1", "user-1", "key"))

        self.assertEqual(300, len(result.verify_error))
        self.assertTrue(result.verify_error.endswith("..."))


if __name__ == "__main__":
    unittest.main()
