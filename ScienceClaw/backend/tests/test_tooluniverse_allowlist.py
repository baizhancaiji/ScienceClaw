import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.deepagent import tooluniverse_tools  # noqa: E402
from backend.route import tooluniverse as tooluniverse_route  # noqa: E402
from backend.tool_discovery.providers import ToolUniverseProvider  # noqa: E402
from backend.tooluniverse_allowlist import allowed_tool_names, inventory_item, is_allowed_tool_name  # noqa: E402


def _invoke(tool_obj, args):
    return tool_obj.invoke(args)


def _run(coro):
    return asyncio.run(coro)


class FakeToolUniverse:
    def __init__(self):
        self.all_tools = [
            {
                "name": "PubChem_get_CID_by_SMILES",
                "description": "Allowed chemistry lookup",
                "category": "chemistry",
                "parameter": {"type": "object", "properties": {"smiles": {"type": "string"}}},
            },
            {
                "name": "PubMed_search_articles",
                "description": "Removed biomedical literature lookup",
                "category": "literature",
                "parameter": {"type": "object", "properties": {"query": {"type": "string"}}},
            },
        ]
        self.all_tool_dict = {tool["name"]: tool for tool in self.all_tools}

    def tool_specification(self, tool_name, format="default"):
        tool = self.all_tool_dict.get(tool_name)
        if not tool:
            return None
        return {
            "name": tool_name,
            "description": tool["description"],
            "parameters": tool["parameter"],
        }

    def run(self, payload):
        name = payload["name"]
        if name == "Tool_Finder_Keyword":
            return list(self.all_tools)
        return {"name": name, "arguments": payload["arguments"]}


class ToolUniverseAllowlistTests(unittest.TestCase):
    def setUp(self):
        self.fake_tu = FakeToolUniverse()

    def test_inventory_parses_expected_materials_chemistry_tools(self):
        names = allowed_tool_names()

        self.assertEqual(210, len(names))
        self.assertTrue(is_allowed_tool_name("PubChem_get_CID_by_SMILES"))
        self.assertTrue(is_allowed_tool_name("get_dscribe_info"))
        self.assertFalse(is_allowed_tool_name("OpenTopoData_get_elevation"))
        self.assertFalse(is_allowed_tool_name("ToolGraphComposer"))
        self.assertFalse(is_allowed_tool_name("PubMed_search_articles"))
        self.assertEqual("化学信息学", inventory_item("PubChem_get_CID_by_SMILES").sub_category)

    def test_rest_list_omits_tools_not_in_inventory(self):
        tools = tooluniverse_route._build_tools_list(self.fake_tu)

        self.assertEqual(["PubChem_get_CID_by_SMILES"], [tool["name"] for tool in tools])
        self.assertEqual("化学信息学", tools[0]["inventory_sub_category"])
        self.assertEqual("化学信息学", tools[0]["category_zh"])

    def test_rest_spec_and_run_reject_tools_not_in_inventory(self):
        with patch.object(tooluniverse_route, "_get_tu", return_value=self.fake_tu):
            with self.assertRaises(Exception):
                _run(tooluniverse_route.get_tool_spec("PubMed_search_articles", lang="en", _user=None))

            with self.assertRaises(Exception):
                _run(
                    tooluniverse_route.run_tool(
                        "PubMed_search_articles",
                        tooluniverse_route.ToolRunRequest(arguments={"query": "CRISPR"}),
                        _user=None,
                    )
                )

    def test_agent_search_filters_removed_tools_and_run_rejects_them(self):
        with patch.object(tooluniverse_tools, "_get_tu", return_value=self.fake_tu):
            search = _invoke(tooluniverse_tools.tooluniverse_search, {"query": "paper", "limit": 10})
            run = _invoke(
                tooluniverse_tools.tooluniverse_run,
                {"tool_name": "PubMed_search_articles", "arguments": '{"query":"CRISPR"}'},
            )

        self.assertEqual(["PubChem_get_CID_by_SMILES"], [tool["name"] for tool in search["tools"]])
        self.assertIn("Tool not found", run["error"])

    def test_discovery_provider_rejects_removed_tool_refs(self):
        provider = ToolUniverseProvider()

        with self.assertRaises(LookupError):
            _run(provider.get_info("tooluniverse:PubMed_search_articles", "user-1"))

        result = _run(provider.run("tooluniverse:PubMed_search_articles", {"query": "CRISPR"}, "user-1"))
        self.assertFalse(result.ok)
        self.assertIn("ToolUniverse tool not found", result.error or "")


if __name__ == "__main__":
    unittest.main()
