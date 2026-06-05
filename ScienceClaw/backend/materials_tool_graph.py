from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable

from backend.tooluniverse_allowlist import inventory_item


@dataclass(frozen=True)
class DataTypeRule:
    key: str
    label: str
    aliases: tuple[str, ...]


DATA_TYPE_RULES: tuple[DataTypeRule, ...] = (
    DataTypeRule("smiles", "SMILES", ("smiles", "canonical_smiles", "isomeric_smiles")),
    DataTypeRule("cid", "PubChem CID", ("cid", "pubchem cid", "compound id")),
    DataTypeRule("inchikey", "InChIKey", ("inchikey", "inchi key")),
    DataTypeRule("inchi", "InChI", ("inchi",)),
    DataTypeRule("chembl_id", "ChEMBL ID", ("chembl", "chembl_id", "chembl id")),
    DataTypeRule("compound", "Compound", ("compound", "molecule", "chemical", "ligand")),
    DataTypeRule("molecular_formula", "Molecular formula", ("formula", "molecular formula")),
    DataTypeRule("doi", "DOI", ("doi", "digital object identifier")),
    DataTypeRule("pmid", "PMID", ("pmid", "pubmed id")),
    DataTypeRule("paper", "Paper metadata", ("paper", "article", "publication", "citation")),
    DataTypeRule("file_path", "File path", ("file_path", "filepath", "path", "filename", "file name")),
    DataTypeRule("pdf", "PDF", ("pdf",)),
    DataTypeRule("markdown", "Markdown", ("markdown", "md")),
    DataTypeRule("dataset", "Dataset", ("dataset", "data set", "dataframe", "table")),
    DataTypeRule("model", "Model", ("model", "checkpoint", "huggingface")),
    DataTypeRule("python_package", "Python package", ("package", "library", "pypi", "python package")),
    DataTypeRule("wikidata_entity", "Wikidata entity", ("wikidata", "qid", "entity id")),
    DataTypeRule("sparql", "SPARQL query", ("sparql",)),
    DataTypeRule("crystal_structure", "Crystal structure", ("crystal", "cif", "structure", "lattice")),
    DataTypeRule("material_descriptor", "Material descriptor", ("descriptor", "fingerprint", "embedding")),
    DataTypeRule("sequence", "Sequence", ("sequence", "fasta")),
    DataTypeRule("url", "URL", ("url", "uri", "link")),
)

_WORD_RE = re.compile(r"[^a-z0-9_./:-]+")
_TOKEN_BOUNDARY_RE = re.compile(r"[a-z0-9]")


def build_materials_tool_graph(
    tool_specs: Iterable[dict[str, Any]],
    *,
    include_isolated: bool = True,
    min_score: int = 60,
) -> dict[str, Any]:
    """Build a local compatibility graph for the curated materials ToolUniverse subset.

    The graph is deterministic and scoped to the supplied tool specs. It does not call
    ToolUniverse compose tools, LLM analyzers, or dependency auto-loaders.
    """
    analyzed = [_analyze_tool(tool) for tool in tool_specs if isinstance(tool, dict) and tool.get("name")]
    allowed_names = {tool["name"] for tool in analyzed}

    edges: list[dict[str, Any]] = []
    for source in analyzed:
        for target in analyzed:
            if source["name"] == target["name"]:
                continue
            shared = sorted(set(source["output_types"]) & set(target["input_types"]))
            if not shared:
                continue
            score = _edge_score(shared, source, target)
            if score < min_score:
                continue
            edges.append(
                {
                    "source": source["name"],
                    "target": target["name"],
                    "score": score,
                    "data_types": shared,
                    "data_type_labels": [_label_for_type(item) for item in shared],
                    "reason": _edge_reason(source["name"], target["name"], shared),
                }
            )

    connected = {edge["source"] for edge in edges} | {edge["target"] for edge in edges}
    nodes = [
        _node_payload(tool)
        for tool in analyzed
        if include_isolated or tool["name"] in connected
    ]
    visible_names = {node["id"] for node in nodes}
    edges = [
        edge
        for edge in edges
        if edge["source"] in visible_names and edge["target"] in visible_names and edge["source"] in allowed_names
    ]

    by_type = Counter(data_type for edge in edges for data_type in edge["data_types"])
    return {
        "nodes": nodes,
        "edges": sorted(edges, key=lambda item: (-item["score"], item["source"], item["target"])),
        "data_types": [
            {"key": rule.key, "label": rule.label, "edge_count": by_type.get(rule.key, 0)}
            for rule in DATA_TYPE_RULES
            if by_type.get(rule.key, 0)
        ],
        "stats": {
            "tools": len(analyzed),
            "nodes": len(nodes),
            "edges": len(edges),
            "isolated": len([node for node in nodes if node["id"] not in connected]),
            "min_score": min_score,
            "mode": "local_schema_heuristic",
        },
    }


def _analyze_tool(tool: dict[str, Any]) -> dict[str, Any]:
    name = str(tool.get("name") or "")
    description = str(tool.get("description") or "")
    parameters = tool.get("parameter") or tool.get("parameters") or {}
    return_schema = tool.get("return_schema") or {}
    inv = inventory_item(name)

    input_blob = _schema_blob(parameters)
    output_blob = " ".join(
        [
            name,
            description,
            _schema_blob(return_schema),
            _output_hints_from_name(name),
        ]
    )
    return {
        "name": name,
        "description": description,
        "category": tool.get("category") or tool.get("type") or "",
        "inventory_main_category": inv.main_category if inv else "",
        "inventory_sub_category": inv.sub_category if inv else "",
        "input_types": sorted(_detect_data_types(input_blob)),
        "output_types": sorted(_detect_data_types(output_blob)),
        "required_params": _required_params(parameters),
        "parameter_count": _parameter_count(parameters),
    }


def _node_payload(tool: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": tool["name"],
        "name": tool["name"],
        "description": tool["description"],
        "category": tool["inventory_sub_category"] or tool["category"],
        "main_category": tool["inventory_main_category"],
        "input_types": tool["input_types"],
        "output_types": tool["output_types"],
        "required_params": tool["required_params"],
        "parameter_count": tool["parameter_count"],
    }


def _schema_blob(schema: Any) -> str:
    if isinstance(schema, dict):
        parts: list[str] = []
        for key, value in schema.items():
            parts.append(str(key))
            parts.append(_schema_blob(value))
        return " ".join(parts)
    if isinstance(schema, list):
        return " ".join(_schema_blob(item) for item in schema)
    return str(schema or "")


def _required_params(parameters: Any) -> list[str]:
    if not isinstance(parameters, dict):
        return []
    required = parameters.get("required") or []
    return [str(item) for item in required if isinstance(item, str)]


def _parameter_count(parameters: Any) -> int:
    if not isinstance(parameters, dict):
        return 0
    props = parameters.get("properties") or {}
    return len(props) if isinstance(props, dict) else 0


def _detect_data_types(text: str) -> set[str]:
    normalized = _normalize(text)
    found: set[str] = set()
    for rule in DATA_TYPE_RULES:
        if any(_contains_alias(normalized, alias) for alias in rule.aliases):
            found.add(rule.key)

    # InChIKey includes "inchi"; keep both when explicitly present in text, but
    # avoid inferring plain InChI from InChIKey alone.
    if "inchikey" in found and not _contains_alias(normalized, "inchi "):
        found.discard("inchi")
    return found


def _normalize(text: str) -> str:
    lowered = str(text or "").lower().replace("-", "_")
    return f" {_WORD_RE.sub(' ', lowered)} "


def _contains_alias(normalized: str, alias: str) -> bool:
    needle = _normalize(alias).strip()
    if not needle:
        return False
    if _TOKEN_BOUNDARY_RE.search(needle):
        return f" {needle} " in normalized
    return needle in normalized


def _output_hints_from_name(name: str) -> str:
    lower = name.lower()
    hints: list[str] = []
    if "_get_cid" in lower or "cid_by" in lower:
        hints.append("cid pubchem cid")
    if "smiles" in lower:
        hints.append("smiles")
    if "doi" in lower:
        hints.append("doi")
    if "dataset" in lower:
        hints.append("dataset")
    if "pdf" in lower:
        hints.append("pdf file_path")
    if "markdown" in lower:
        hints.append("markdown file_path")
    return " ".join(hints)


def _edge_score(shared: list[str], source: dict[str, Any], target: dict[str, Any]) -> int:
    score = 60 + min(30, 10 * len(shared))
    if source["inventory_main_category"] == target["inventory_main_category"]:
        score += 5
    if any(item in {"smiles", "cid", "doi", "file_path", "dataset"} for item in shared):
        score += 10
    return min(score, 100)


def _edge_reason(source: str, target: str, data_types: list[str]) -> str:
    labels = ", ".join(_label_for_type(item) for item in data_types)
    return f"{source} can provide {labels} consumed by {target}."


def _label_for_type(key: str) -> str:
    for rule in DATA_TYPE_RULES:
        if rule.key == key:
            return rule.label
    return key
