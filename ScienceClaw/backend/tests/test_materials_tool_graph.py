import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.materials_tool_graph import build_materials_tool_graph  # noqa: E402


class MaterialsToolGraphTests(unittest.TestCase):
    def test_builds_directed_edges_from_shared_data_types(self):
        graph = build_materials_tool_graph(
            [
                {
                    "name": "PubChem_get_CID_by_SMILES",
                    "description": "Retrieve PubChem CID from a SMILES string.",
                    "parameter": {
                        "type": "object",
                        "properties": {"smiles": {"type": "string", "description": "SMILES"}},
                    },
                    "return_schema": {"type": "object", "properties": {"cid": {"type": "integer"}}},
                },
                {
                    "name": "PubChem_get_compound_synonyms_by_CID",
                    "description": "Get compound synonyms by PubChem CID.",
                    "parameter": {
                        "type": "object",
                        "properties": {"cid": {"type": "integer", "description": "PubChem CID"}},
                    },
                    "return_schema": {"type": "object", "properties": {"synonyms": {"type": "array"}}},
                },
            ],
            include_isolated=False,
        )

        self.assertEqual(2, graph["stats"]["nodes"])
        self.assertEqual(1, graph["stats"]["edges"])
        self.assertEqual("PubChem_get_CID_by_SMILES", graph["edges"][0]["source"])
        self.assertEqual("PubChem_get_compound_synonyms_by_CID", graph["edges"][0]["target"])
        self.assertIn("cid", graph["edges"][0]["data_types"])

    def test_omits_isolated_nodes_when_requested(self):
        graph = build_materials_tool_graph(
            [
                {
                    "name": "get_dscribe_info",
                    "description": "Package information for DScribe.",
                    "parameter": {"type": "object", "properties": {}},
                }
            ],
            include_isolated=False,
        )

        self.assertEqual([], graph["nodes"])
        self.assertEqual([], graph["edges"])


if __name__ == "__main__":
    unittest.main()
