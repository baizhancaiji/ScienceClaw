import sys
import unittest
from pathlib import Path

from pydantic import ValidationError


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.mcp.schemas import (  # noqa: E402
    CreateMCPServerRequest,
    MCPHeaderSecret,
    MCPMaskedHeader,
    MCPServerDetailItem,
    MCPServerListItem,
    ToggleMCPServerRequest,
    UpdateMCPServerRequest,
)


class MCPServerSchemaTests(unittest.TestCase):
    def test_create_server_request_normalizes_and_validates_https(self):
        request = CreateMCPServerRequest(
            name="  GitHub MCP  ",
            endpoint_url="  https://example.com/mcp  ",
            auth_mode="none",
        )

        self.assertEqual("GitHub MCP", request.name)
        self.assertEqual("https://example.com/mcp", request.endpoint_url)
        self.assertTrue(request.enabled)
        self.assertFalse(request.verify_now)

        with self.assertRaises(ValidationError):
            CreateMCPServerRequest(name="x", endpoint_url="https://example.com/mcp")
        with self.assertRaises(ValidationError):
            CreateMCPServerRequest(name="GitHub MCP", endpoint_url="http://example.com/mcp")

    def test_create_server_request_validates_auth_modes(self):
        bearer = CreateMCPServerRequest(
            name="GitHub MCP",
            endpoint_url="https://example.com/mcp",
            auth_mode="bearer",
            bearer_token="token-value",
        )
        headers = CreateMCPServerRequest(
            name="Header MCP",
            endpoint_url="https://example.com/mcp",
            auth_mode="headers",
            headers=[MCPHeaderSecret(name="X-Org-Id", value="org-1")],
        )

        self.assertEqual("bearer", bearer.auth_mode)
        self.assertEqual("headers", headers.auth_mode)
        with self.assertRaises(ValidationError):
            CreateMCPServerRequest(
                name="GitHub MCP",
                endpoint_url="https://example.com/mcp",
                auth_mode="bearer",
            )
        with self.assertRaises(ValidationError):
            CreateMCPServerRequest(
                name="Header MCP",
                endpoint_url="https://example.com/mcp",
                auth_mode="headers",
                headers=[],
            )

    def test_header_name_rejects_spaces_and_control_characters(self):
        self.assertEqual("X-Org-Id", MCPHeaderSecret(name=" X-Org-Id ", value="org").name)

        with self.assertRaises(ValidationError):
            MCPHeaderSecret(name="X Org", value="org")
        with self.assertRaises(ValidationError):
            MCPHeaderSecret(name="X-\nOrg", value="org")

    def test_update_server_request_allows_partial_changes(self):
        update = UpdateMCPServerRequest(name="  Renamed  ", endpoint_url=None)

        self.assertEqual("Renamed", update.name)
        self.assertIsNone(update.endpoint_url)
        with self.assertRaises(ValidationError):
            UpdateMCPServerRequest(endpoint_url="http://example.com/mcp")
        with self.assertRaises(ValidationError):
            UpdateMCPServerRequest(auth_mode="bearer", bearer_token="")

    def test_toggle_and_response_models_match_server_contract(self):
        toggle = ToggleMCPServerRequest(enabled=False)
        item = MCPServerListItem(
            id="server-1",
            name="GitHub MCP",
            slug="github_mcp",
            endpoint_url="https://example.com/mcp",
            auth_mode="bearer",
            enabled=True,
            verify_status="healthy",
            tool_count=18,
            has_bearer_token=True,
            masked_headers=[MCPMaskedHeader(name="X-Org-Id", masked_value="********")],
        )
        detail = MCPServerDetailItem(**item.model_dump(), created_at=1, updated_at=2)

        self.assertFalse(toggle.enabled)
        self.assertEqual("https", item.transport)
        self.assertEqual("********", item.masked_headers[0].masked_value)
        self.assertEqual(1, detail.created_at)
        self.assertEqual(2, detail.updated_at)


if __name__ == "__main__":
    unittest.main()
