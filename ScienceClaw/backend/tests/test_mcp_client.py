import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.mcp import client  # noqa: E402


class FakeAsyncClient:
    last_instance = None

    def __init__(self, response=None, side_effect=None, **kwargs):
        self.response = response
        self.side_effect = side_effect
        self.kwargs = kwargs
        self.post = AsyncMock(side_effect=self._post)
        FakeAsyncClient.last_instance = self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def _post(self, *args, **kwargs):
        if self.side_effect:
            raise self.side_effect
        return self.response


def _response(status_code=200, body=None):
    return httpx.Response(status_code, json=body or {"jsonrpc": "2.0", "result": {}})


def _sse_response(status_code=200, text=""):
    return httpx.Response(
        status_code,
        content=text.encode("utf-8"),
        headers={"Content-Type": "text/event-stream"},
    )


class MCPClientTests(unittest.TestCase):
    def test_initialize_posts_jsonrpc_payload_with_default_headers_and_tls_verify(self):
        response = _response(
            body={
                "jsonrpc": "2.0",
                "id": "rpc-id",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "Remote MCP"},
                },
            }
        )

        with patch.object(
            client.httpx,
            "AsyncClient",
            lambda **kwargs: FakeAsyncClient(response=response, **kwargs),
        ):
            result = asyncio.run(
                client.initialize(
                    "https://example.com/mcp",
                    headers={"Authorization": "Bearer token"},
                    timeout_seconds=3,
                )
            )

        self.assertEqual("Remote MCP", result["serverInfo"]["name"])
        fake = FakeAsyncClient.last_instance
        self.assertTrue(fake.kwargs["verify"])
        self.assertEqual(3, fake.kwargs["timeout"].connect)
        args, kwargs = fake.post.await_args
        self.assertEqual(("https://example.com/mcp",), args)
        self.assertEqual("2.0", kwargs["json"]["jsonrpc"])
        self.assertEqual("initialize", kwargs["json"]["method"])
        self.assertEqual(client.MCP_PROTOCOL_VERSION, kwargs["json"]["params"]["protocolVersion"])
        self.assertEqual("ScienceClaw", kwargs["json"]["params"]["clientInfo"]["name"])
        self.assertEqual("application/json, text/event-stream", kwargs["headers"]["Accept"])
        self.assertEqual("application/json", kwargs["headers"]["Content-Type"])
        self.assertEqual("Bearer token", kwargs["headers"]["Authorization"])

    def test_rejects_non_https_or_pathless_endpoint_before_network(self):
        for endpoint_url in [
            "http://example.com/mcp",
            "ws://example.com/mcp",
            "wss://example.com/mcp",
            "example.com/mcp",
            "https://example.com",
        ]:
            with self.subTest(endpoint_url=endpoint_url):
                with patch.object(client.httpx, "AsyncClient") as async_client:
                    with self.assertRaises(client.MCPClientError) as captured:
                        asyncio.run(client.initialize(endpoint_url))

                self.assertEqual("invalid_mcp_endpoint", captured.exception.code)
                async_client.assert_not_called()

    def test_http_error_maps_to_structured_retryable_status(self):
        with patch.object(
            client.httpx,
            "AsyncClient",
            lambda **kwargs: FakeAsyncClient(response=_response(503), **kwargs),
        ):
            with self.assertRaises(client.MCPClientError) as captured:
                asyncio.run(client.initialize("https://example.com/mcp"))

        self.assertEqual(
            {
                "code": "remote_mcp_http_error",
                "message": "Remote MCP returned HTTP 503",
                "retryable": True,
                "status_code": 503,
            },
            captured.exception.to_dict(),
        )

    def test_timeout_maps_to_retryable_error(self):
        request = httpx.Request("POST", "https://example.com/mcp")

        with patch.object(
            client.httpx,
            "AsyncClient",
            lambda **kwargs: FakeAsyncClient(
                side_effect=httpx.TimeoutException("slow", request=request),
                **kwargs,
            ),
        ):
            with self.assertRaises(client.MCPClientError) as captured:
                asyncio.run(client.initialize("https://example.com/mcp"))

        self.assertEqual("remote_mcp_timeout", captured.exception.code)
        self.assertTrue(captured.exception.retryable)

    def test_tls_transport_error_maps_to_retryable_transport_error(self):
        request = httpx.Request("POST", "https://example.com/mcp")

        with patch.object(
            client.httpx,
            "AsyncClient",
            lambda **kwargs: FakeAsyncClient(
                side_effect=httpx.TransportError("certificate verify failed", request=request),
                **kwargs,
            ),
        ):
            with self.assertRaises(client.MCPClientError) as captured:
                asyncio.run(client.initialize("https://example.com/mcp"))

        self.assertEqual("remote_mcp_transport_error", captured.exception.code)
        self.assertTrue(captured.exception.retryable)

    def test_invalid_jsonrpc_response_is_non_retryable(self):
        with patch.object(
            client.httpx,
            "AsyncClient",
            lambda **kwargs: FakeAsyncClient(
                response=_response(body={"jsonrpc": "2.0", "result": []}),
                **kwargs,
            ),
        ):
            with self.assertRaises(client.MCPClientError) as captured:
                asyncio.run(client.initialize("https://example.com/mcp"))

        self.assertEqual("remote_mcp_invalid_response", captured.exception.code)
        self.assertFalse(captured.exception.retryable)

    def test_jsonrpc_error_maps_to_remote_mcp_error(self):
        with patch.object(
            client.httpx,
            "AsyncClient",
            lambda **kwargs: FakeAsyncClient(
                response=_response(
                    body={
                        "jsonrpc": "2.0",
                        "error": {"code": -32601, "message": "Method not found"},
                    }
                ),
                **kwargs,
            ),
        ):
            with self.assertRaises(client.MCPClientError) as captured:
                asyncio.run(client.initialize("https://example.com/mcp"))

        self.assertEqual("remote_mcp_error", captured.exception.code)
        self.assertEqual("Method not found", captured.exception.message)

    def test_list_tools_posts_tools_list_and_returns_standardized_tools(self):
        response = _response(
            body={
                "jsonrpc": "2.0",
                "id": "rpc-id",
                "result": {
                    "tools": [
                        {
                            "name": " search_repositories ",
                            "description": " Search repositories by query ",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"query": {"type": "string"}},
                                "required": ["query"],
                            },
                        },
                        {
                            "name": "ping",
                        },
                    ]
                },
            }
        )

        with patch.object(
            client.httpx,
            "AsyncClient",
            lambda **kwargs: FakeAsyncClient(response=response, **kwargs),
        ):
            tools = asyncio.run(client.list_tools("https://example.com/mcp"))

        self.assertEqual("search_repositories", tools[0].name)
        self.assertEqual("Search repositories by query", tools[0].description)
        self.assertEqual(
            {
                "name": "search_repositories",
                "description": "Search repositories by query",
                "input_schema_raw": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
            tools[0].to_dict(),
        )
        self.assertEqual({"type": "object", "properties": {}}, tools[1].input_schema_raw)
        _, kwargs = FakeAsyncClient.last_instance.post.await_args
        self.assertEqual("tools/list", kwargs["json"]["method"])
        self.assertEqual({}, kwargs["json"]["params"])

    def test_list_tools_accepts_jsonrpc_event_stream_response(self):
        response = _sse_response(
            text=(
                'event: message\n'
                'data: {"jsonrpc":"2.0","id":"rpc-id","result":{"tools":[{"name":"ask_question","description":"Ask","inputSchema":{"type":"object","properties":{"question":{"type":"string"}}}}]}}\n\n'
            )
        )

        with patch.object(
            client.httpx,
            "AsyncClient",
            lambda **kwargs: FakeAsyncClient(response=response, **kwargs),
        ):
            tools = asyncio.run(client.list_tools("https://example.com/mcp"))

        self.assertEqual(1, len(tools))
        self.assertEqual("ask_question", tools[0].name)
        self.assertEqual("Ask", tools[0].description)
        self.assertEqual(
            {"type": "object", "properties": {"question": {"type": "string"}}},
            tools[0].input_schema_raw,
        )

    def test_list_tools_rejects_missing_tools_array(self):
        with patch.object(
            client.httpx,
            "AsyncClient",
            lambda **kwargs: FakeAsyncClient(
                response=_response(body={"jsonrpc": "2.0", "result": {"tools": {}}}),
                **kwargs,
            ),
        ):
            with self.assertRaises(client.MCPClientError) as captured:
                asyncio.run(client.list_tools("https://example.com/mcp"))

        self.assertEqual("remote_mcp_invalid_tools", captured.exception.code)

    def test_list_tools_rejects_tool_without_name(self):
        with patch.object(
            client.httpx,
            "AsyncClient",
            lambda **kwargs: FakeAsyncClient(
                response=_response(
                    body={"jsonrpc": "2.0", "result": {"tools": [{"description": "missing"}]}}
                ),
                **kwargs,
            ),
        ):
            with self.assertRaises(client.MCPClientError) as captured:
                asyncio.run(client.list_tools("https://example.com/mcp"))

        self.assertEqual("remote_mcp_invalid_tools", captured.exception.code)

    def test_list_tools_rejects_non_object_input_schema(self):
        with patch.object(
            client.httpx,
            "AsyncClient",
            lambda **kwargs: FakeAsyncClient(
                response=_response(
                    body={
                        "jsonrpc": "2.0",
                        "result": {
                            "tools": [
                                {"name": "bad_schema", "inputSchema": []},
                            ]
                        },
                    }
                ),
                **kwargs,
            ),
        ):
            with self.assertRaises(client.MCPClientError) as captured:
                asyncio.run(client.list_tools("https://example.com/mcp"))

        self.assertEqual("remote_mcp_invalid_tools", captured.exception.code)

    def test_call_tool_posts_tools_call_with_name_and_arguments(self):
        response = _response(
            body={
                "jsonrpc": "2.0",
                "id": "rpc-id",
                "result": {
                    "content": [{"type": "text", "text": "done"}],
                    "structuredContent": {"ok": True},
                },
            }
        )

        with patch.object(
            client.httpx,
            "AsyncClient",
            lambda **kwargs: FakeAsyncClient(response=response, **kwargs),
        ):
            result = asyncio.run(
                client.call_tool(
                    "https://example.com/mcp",
                    " search ",
                    arguments={"query": "science"},
                    headers={"Authorization": "Bearer token"},
                )
            )

        self.assertEqual({"ok": True}, result["structuredContent"])
        _, kwargs = FakeAsyncClient.last_instance.post.await_args
        self.assertEqual("tools/call", kwargs["json"]["method"])
        self.assertEqual(
            {"name": "search", "arguments": {"query": "science"}},
            kwargs["json"]["params"],
        )
        self.assertEqual("Bearer token", kwargs["headers"]["Authorization"])

    def test_call_tool_rejects_empty_tool_name_before_network(self):
        with patch.object(client.httpx, "AsyncClient") as async_client:
            with self.assertRaises(client.MCPClientError) as captured:
                asyncio.run(client.call_tool("https://example.com/mcp", " "))

        self.assertEqual("invalid_mcp_tool_name", captured.exception.code)
        async_client.assert_not_called()

    def test_call_tool_maps_jsonrpc_error_to_client_error(self):
        with patch.object(
            client.httpx,
            "AsyncClient",
            lambda **kwargs: FakeAsyncClient(
                response=_response(
                    body={
                        "jsonrpc": "2.0",
                        "error": {"code": -32000, "message": "Tool failed"},
                    }
                ),
                **kwargs,
            ),
        ):
            with self.assertRaises(client.MCPClientError) as captured:
                asyncio.run(client.call_tool("https://example.com/mcp", "search"))

        self.assertEqual("remote_mcp_error", captured.exception.code)
        self.assertEqual("Tool failed", captured.exception.message)

    def test_call_tool_safely_returns_success_envelope(self):
        with patch.object(
            client.httpx,
            "AsyncClient",
            lambda **kwargs: FakeAsyncClient(
                response=_response(
                    body={"jsonrpc": "2.0", "result": {"content": []}},
                ),
                **kwargs,
            ),
        ):
            result = asyncio.run(client.call_tool_safely("https://example.com/mcp", "search"))

        self.assertTrue(result["ok"])
        self.assertFalse(result["is_error"])
        self.assertEqual({"content": []}, result["result"])

    def test_call_tool_safely_returns_standard_error_object(self):
        with patch.object(
            client.httpx,
            "AsyncClient",
            lambda **kwargs: FakeAsyncClient(response=_response(503), **kwargs),
        ):
            result = asyncio.run(client.call_tool_safely("https://example.com/mcp", "search"))

        self.assertFalse(result["ok"])
        self.assertTrue(result["is_error"])
        self.assertEqual("remote_mcp_http_error", result["error"]["code"])
        self.assertTrue(result["error"]["retryable"])
        self.assertEqual("remote_mcp_http_error: Remote MCP returned HTTP 503", result["text"])


if __name__ == "__main__":
    unittest.main()
