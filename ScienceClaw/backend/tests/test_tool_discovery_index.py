import sqlite3
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from backend.tool_discovery.index_store import ToolIndexStore  # noqa: E402
from backend.tool_discovery.schemas import ToolIndexItem  # noqa: E402


def _item(**overrides):
    data = {
        "tool_ref": "tooluniverse:PubMed_search_articles",
        "source_type": "tooluniverse",
        "name": "PubMed_search_articles",
        "display_name": "PubMed_search_articles",
        "description": "Search biomedical literature articles",
        "description_zh": "搜索生物医学论文",
        "category_zh": "学术文献",
        "aliases": ["论文", "医学论文", "PubMed", "article"],
        "keywords": ["literature", "pubmed"],
        "provider": "ToolUniverse",
        "schema_status": "available",
        "has_examples": True,
    }
    data.update(overrides)
    return ToolIndexItem(**data)


class ToolDiscoveryIndexTests(unittest.TestCase):
    def test_sqlite_fts5_is_available(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE VIRTUAL TABLE x USING fts5(name)")
        conn.close()

    def test_search_matches_chinese_aliases_and_filters(self):
        store = ToolIndexStore()
        store.rebuild(
            [
                _item(),
                _item(
                    tool_ref="tooluniverse:FAERS_count_reactions_by_drug_event",
                    name="FAERS_count_reactions_by_drug_event",
                    display_name="FAERS_count_reactions_by_drug_event",
                    description="Count drug adverse event reactions",
                    description_zh="统计药物不良反应",
                    category_zh="药物与化合物",
                    aliases=["药物毒性", "药物安全", "FAERS"],
                    keywords=["drug", "toxicity", "faers"],
                ),
                _item(
                    tool_ref="https_mcp:tool-1",
                    source_type="https_mcp",
                    name="mcp__github__search",
                    display_name="GitHub search",
                    description="Search repositories",
                    description_zh="",
                    category_zh="网页与外部服务",
                    aliases=["MCP", "网页", "搜索"],
                    keywords=["github", "mcp"],
                    provider="GitHub MCP",
                ),
                _item(
                    tool_ref="external:pdf_convert",
                    source_type="external_python_tool",
                    name="pdf_convert",
                    display_name="pdf_convert",
                    description="Convert PDF documents to Markdown",
                    description_zh="将 PDF 文档转换为 Markdown",
                    category_zh="文档处理",
                    aliases=["PDF", "PDF 转换", "文档"],
                    keywords=["pdf", "document", "markdown"],
                    provider="Tools",
                ),
            ]
        )

        literature = store.search("医学论文", limit=5)
        self.assertEqual("tooluniverse:PubMed_search_articles", literature[0].item.tool_ref)
        self.assertIn("aliases", literature[0].hit_fields)

        toxicity = store.search("药物毒性", limit=5)
        self.assertEqual("tooluniverse:FAERS_count_reactions_by_drug_event", toxicity[0].item.tool_ref)

        mcp_only = store.search("搜索", source_type="https_mcp", limit=5)
        self.assertEqual(["https_mcp:tool-1"], [hit.item.tool_ref for hit in mcp_only])

        pdf = store.search("PDF 转换", limit=5)
        self.assertEqual("external:pdf_convert", pdf[0].item.tool_ref)

    def test_rebuild_is_idempotent_and_respects_enabled_blocked_filters(self):
        store = ToolIndexStore()
        store.rebuild([_item()])
        store.rebuild([
            _item(enabled=False),
            _item(tool_ref="external:custom", source_type="external_python_tool", name="custom", blocked=True),
        ])

        self.assertEqual([], store.search("论文", limit=5))


if __name__ == "__main__":
    unittest.main()
