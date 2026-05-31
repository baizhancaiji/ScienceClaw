import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from backend.route import sessions


class SkillDescriptionTests(unittest.IsolatedAsyncioTestCase):
    def test_parse_description_zh_from_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "example"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                """---
name: example
description: Use when drafting reports.
description_zh: 撰写报告时使用。
---
""",
                encoding="utf-8",
            )

            meta = sessions._parse_skill_frontmatter(skill_dir)

        self.assertEqual(meta["name"], "example")
        self.assertEqual(meta["description"], "Use when drafting reports.")
        self.assertEqual(meta["description_zh"], "撰写报告时使用。")

    def test_parse_description_i18n_zh_from_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "example"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                """---
name: example
description: Use when drafting reports.
description_i18n:
  zh: 撰写报告时使用。
---
""",
                encoding="utf-8",
            )

            meta = sessions._parse_skill_frontmatter(skill_dir)

        self.assertEqual(meta["description_zh"], "撰写报告时使用。")

    def test_parse_metadata_without_frontmatter_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "example"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                """name: example
description: Use when drafting reports.
description_zh: 撰写报告时使用。

# Example
""",
                encoding="utf-8",
            )

            meta = sessions._parse_skill_frontmatter(skill_dir)

        self.assertEqual(meta["name"], "example")
        self.assertEqual(meta["description"], "Use when drafting reports.")
        self.assertEqual(meta["description_zh"], "撰写报告时使用。")

    def test_strip_skill_metadata_text(self):
        content = """---
name: example
description: Use when drafting reports.
---

# Example

Body
"""

        self.assertEqual(sessions._strip_skill_metadata_text(content), "# Example\n\nBody\n")

    async def test_populate_description_zh_uses_existing_chinese_text(self):
        skills = [{
            "name": "weather",
            "description": "查询天气预报。",
            "description_zh": "",
        }]

        await sessions._populate_skill_description_zh(skills, "user-1")

        self.assertEqual(skills[0]["description_zh"], "查询天气预报。")

    async def test_populate_description_zh_translates_english_dominant_mixed_text(self):
        cursor = _AsyncCursor([{"_id": "cache-key", "description_zh": "论文全文阅读技能。"}])
        collection = _FakeCollection(cursor)
        skills = [{
            "name": "nature-reader",
            "description": "Build full-paper Markdown readers. Triggers: 全文翻译, 论文解读.",
            "description_zh": "",
        }]

        with patch.object(sessions, "_skill_description_cache_key", return_value="cache-key"), \
             patch.object(sessions._db, "get_collection", return_value=collection), \
             patch.object(sessions, "_resolve_skill_translation_model_config", new=AsyncMock()) as resolve_model:
            await sessions._populate_skill_description_zh(skills, "user-1")

        self.assertEqual(skills[0]["description_zh"], "论文全文阅读技能。")
        resolve_model.assert_not_called()

    async def test_populate_description_zh_uses_cache_before_llm(self):
        cursor = _AsyncCursor([{"_id": "cache-key", "description_zh": "缓存译文。"}])
        collection = _FakeCollection(cursor)
        skills = [{
            "name": "copywriting",
            "description": "Use when writing marketing copy.",
            "description_zh": "",
        }]

        with patch.object(sessions, "_skill_description_cache_key", return_value="cache-key"), \
             patch.object(sessions._db, "get_collection", return_value=collection), \
             patch.object(sessions, "_resolve_skill_translation_model_config", new=AsyncMock()) as resolve_model:
            await sessions._populate_skill_description_zh(skills, "user-1")

        self.assertEqual(skills[0]["description_zh"], "缓存译文。")
        resolve_model.assert_not_called()


class _AsyncCursor:
    def __init__(self, docs):
        self._iter = iter(docs)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


class _FakeCollection:
    def __init__(self, cursor):
        self.cursor = cursor

    def find(self, *_args, **_kwargs):
        return self.cursor


if __name__ == "__main__":
    unittest.main()
