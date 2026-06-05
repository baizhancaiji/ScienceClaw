---
name: tooluniverse
description: "Access the ScienceClaw-curated ToolUniverse subset for materials research, chemistry, scientific Python package information, literature metadata, web/file utilities, statistics, data storage, visualization, and knowledge graph queries. Use the three-step tool discovery workflow instead of requesting a full catalog."
---

# ToolUniverse Scientific Tools

You have access to the ScienceClaw-curated **ToolUniverse** subset for materials science, chemistry, and general research utilities. The runtime only loads tools retained in `docs/final_materials_chemistry_tools_inventory.md`; tools outside that inventory are treated as unavailable. ToolUniverse is a searchable catalog, not a list to inject into context.

Use either the generic workflow:

```text
tool_search -> tool_info -> tool_run
```

or the compatibility workflow:

```text
tooluniverse_search -> tooluniverse_info -> tooluniverse_run
```

Do not request the full ToolUniverse catalog. Search for a short candidate list, inspect one selected tool's schema, then run it with structured arguments.

## When to Use

Use ToolUniverse tools when the user needs:

- **Materials Research**: materials ML package information, atomistic simulation libraries, graph neural network tooling, and molecular/material descriptors
- **Chemistry**: ChEMBL, PubChem, vendor compound lookup, SMILES/CID conversion, molecular visualization, synthetic accessibility, and reaction metadata
- **Scientific Python Packages**: package information for numerical computing, visualization, data processing, machine learning, and cheminformatics libraries
- **Literature and Metadata**: DOI/OpenAlex/Semantic Scholar/Crossref/DataCite metadata and citation-oriented workflows
- **General Research Utilities**: web retrieval, file download, document conversion, Python execution, statistics, data storage/retrieval, Wikidata, and visualization helpers

## Three-Step Workflow

**Always follow this sequence: Search → Info → Run**

### Step 1: Search for tools

```
tooluniverse_search(query="SMILES to PubChem CID", limit=5)
```

This returns a list of matching tools with names and descriptions. Use natural language to describe what you need.

You can also use the generic discovery entry:

```
tool_search(query="materials machine learning descriptors", source_type="tooluniverse", limit=5)
```

### Step 2: Check tool specification

```
tooluniverse_info(tool_name="PubChem_get_CID_by_SMILES")
```

This returns the full parameter schema (required/optional args, types, descriptions). **Always check this before running a tool** to ensure you provide correct arguments.

Generic equivalent:

```
tool_info(tool_ref="tooluniverse:PubChem_get_CID_by_SMILES")
```

### Step 3: Execute the tool

```
tooluniverse_run(
    tool_name="PubChem_get_CID_by_SMILES",
    arguments='{"smiles": "CCO"}'
)
```

The `arguments` parameter is a **JSON string** containing the tool's parameters.

Generic equivalent:

```
tool_run(
    tool_ref="tooluniverse:PubChem_get_CID_by_SMILES",
    arguments='{"smiles": "CCO"}'
)
```

## Common Tool Examples

### Materials Libraries
| Tool | Arguments Example |
|------|-------------------|
| `get_dscribe_info` | `{}` |
| `get_ase_info` | `{}` |
| `get_schnetpack_info` | `{}` |

### Chemistry
| Tool | Arguments Example |
|------|-------------------|
| `PubChem_get_CID_by_SMILES` | `{"smiles": "CCO"}` |
| `ChEMBL_get_molecule` | `{"molecule_chembl_id": "CHEMBL25"}` |
| `visualize_molecule_2d` | `{"smiles": "CCO"}` |

### Compound Sources
| Tool | Arguments Example |
|------|-------------------|
| `Enamine_get_compound` | `{"compound_id": "Z1234567890"}` |
| `ZINC_get_compound` | `{"zinc_id": "ZINC000000000001"}` |

### Literature and Metadata
| Tool | Arguments Example |
|------|-------------------|
| `Crossref_get_work` | `{"doi": "10.1038/s41586-020-2649-2"}` |
| `openalex_get_work_by_doi` | `{"doi": "10.1038/s41586-020-2649-2"}` |

### Utilities
| Tool | Arguments Example |
|------|-------------------|
| `get_webpage_title` | `{"url": "https://example.com"}` |
| `convert_to_markdown` | `{"uri": "https://example.com/paper.pdf"}` |

## Multi-Step Research Patterns

### Compound Identity and Vendor Check
1. `tooluniverse_search("SMILES CID compound vendor")` -> find PubChem/vendor tools
2. `tooluniverse_run("PubChem_get_CID_by_SMILES", ...)` -> resolve compound identifiers
3. `tooluniverse_run("Enamine_get_compound", ...)` or another retained vendor tool -> inspect availability

### Materials ML Library Selection
1. `tooluniverse_search("materials machine learning descriptor package")` -> find package info tools
2. Inspect `get_dscribe_info`, `get_schnetpack_info`, or `get_torch_geometric_info`
3. Compare scope, dependencies, and fit for the user's materials workflow

### Paper Metadata Enrichment
1. `tooluniverse_search("DOI metadata citations")` -> find Crossref/OpenAlex/Semantic Scholar tools
2. Run one DOI metadata tool after checking its schema
3. Summarize title, venue, authors, citations, and links relevant to the materials question

## Tips

- **Tool names follow a pattern**: `Database_action_description` (e.g., `PubChem_get_CID_by_SMILES`)
- **First call may be slow** (~30s) as ToolUniverse initializes; subsequent calls are fast
- **Results can be large**: focus on the most relevant fields for the user's question
- **When unsure about tool name**: use `tool_search` or `tooluniverse_search` with a broad query first
- **Chain multiple tools** for comprehensive analysis — combine data from different sources
- **Inventory is authoritative**: if a tool is not in `docs/final_materials_chemistry_tools_inventory.md`, treat it as unavailable
- **API keys are optional**: most retained tools work without keys, but some provider-backed tools may require credentials
