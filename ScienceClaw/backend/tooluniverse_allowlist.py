from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Iterable, NamedTuple


class ToolInventoryItem(NamedTuple):
    tool_name: str
    display_name: str
    main_category: str
    sub_category: str
    availability: str
    reason: str


_PACKAGE_INVENTORY_PATH = Path(__file__).resolve().parent / "tooluniverse_materials_inventory.tsv"
_MARKDOWN_INVENTORY_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "final_materials_chemistry_tools_inventory.md"
)
_TOOL_ROW_RE = re.compile(r"^\|\s*([A-Za-z0-9_]+)\s*\|")
_MAIN_CATEGORY_RE = re.compile(r"^### 2\.\d+\s+(.+?)\s*\(")
_SUB_CATEGORY_RE = re.compile(r"^####\s+(.+?)\s*\(")
_MARKDOWN_ROW_RE = re.compile(
    r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$"
)


@lru_cache(maxsize=1)
def inventory_items() -> dict[str, ToolInventoryItem]:
    if _PACKAGE_INVENTORY_PATH.exists():
        return _load_tsv_inventory(_PACKAGE_INVENTORY_PATH)
    if _MARKDOWN_INVENTORY_PATH.exists():
        return _load_markdown_inventory(_MARKDOWN_INVENTORY_PATH)
    return {}


@lru_cache(maxsize=1)
def allowed_tool_names() -> frozenset[str]:
    """Return ToolUniverse tool names retained for materials/chemistry work."""
    return frozenset(inventory_items())


def is_allowed_tool_name(tool_name: str) -> bool:
    return tool_name in allowed_tool_names()


def inventory_item(tool_name: str) -> ToolInventoryItem | None:
    return inventory_items().get(tool_name)


def inventory_sub_category(tool_name: str, fallback: str = "其他") -> str:
    item = inventory_item(tool_name)
    return item.sub_category if item and item.sub_category else fallback


def is_allowed_tool_result(result: object) -> bool:
    if not isinstance(result, dict):
        return True
    candidates = (
        result.get("name"),
        result.get("tool_name"),
        result.get("tool"),
        result.get("function"),
    )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            return is_allowed_tool_name(candidate)
    return False


def filter_allowed_tool_specs(tools: Iterable[dict]) -> list[dict]:
    allowed = allowed_tool_names()
    return [
        tool
        for tool in tools
        if isinstance(tool, dict) and str(tool.get("name") or "") in allowed
    ]


def _load_tsv_inventory(path: Path) -> dict[str, ToolInventoryItem]:
    items: dict[str, ToolInventoryItem] = {}
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 6:
            continue
        item = ToolInventoryItem(
            tool_name=parts[0].strip(),
            display_name=parts[1].strip(),
            main_category=parts[2].strip(),
            sub_category=parts[3].strip(),
            availability=parts[4].strip(),
            reason=parts[5].strip(),
        )
        if item.tool_name:
            items[item.tool_name] = item
    return items


def _load_markdown_inventory(path: Path) -> dict[str, ToolInventoryItem]:
    items: dict[str, ToolInventoryItem] = {}
    main_category = ""
    sub_category = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        main_match = _MAIN_CATEGORY_RE.match(line)
        if main_match:
            main_category = main_match.group(1).strip()
            continue
        sub_match = _SUB_CATEGORY_RE.match(line)
        if sub_match:
            sub_category = sub_match.group(1).strip()
            continue
        row_match = _MARKDOWN_ROW_RE.match(line)
        if not row_match:
            continue
        tool_name = row_match.group(1).strip()
        if tool_name == "工具名" or not _TOOL_ROW_RE.match(f"| {tool_name} |"):
            continue
        item = ToolInventoryItem(
            tool_name=tool_name,
            display_name=row_match.group(2).strip(),
            main_category=main_category,
            sub_category=sub_category,
            availability=row_match.group(4).strip(),
            reason=row_match.group(5).strip(),
        )
        items[item.tool_name] = item
    return items
