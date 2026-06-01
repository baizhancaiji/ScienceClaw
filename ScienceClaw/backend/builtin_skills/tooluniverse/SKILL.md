---
name: tooluniverse
description: "Access ToolUniverse scientific tools for drug discovery, protein analysis, genomics, literature search, clinical data, ADMET prediction, molecular docking, and more. Use the three-step tool discovery workflow instead of requesting a full catalog."
---

# ToolUniverse Scientific Tools

You have access to **ToolUniverse**, a unified ecosystem of scientific tools that covers the full spectrum of biomedical research. ToolUniverse is a searchable catalog, not a list to inject into context.

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

- **Drug Discovery**: target identification, compound screening, ADMET prediction, drug safety, drug-drug interactions, drug repurposing
- **Protein Analysis**: structure retrieval (PDB/AlphaFold), function lookup (UniProt), interaction networks (STRING/BioGRID), therapeutic design
- **Genomics**: gene expression, GWAS analysis, variant interpretation (ACMG), enrichment analysis, single-cell RNA-seq
- **Literature Search**: multi-source paper search (PubMed/PubTator/EuropePMC/Semantic Scholar/OpenAlex), systematic reviews
- **Clinical**: trial matching, guidelines, pharmacovigilance, precision oncology, rare disease diagnosis
- **Molecular**: docking (Boltz2), SMILES-based property prediction, compound similarity, molecular visualization
- **Omics**: transcriptomics, proteomics, metabolomics, multi-omics integration, spatial transcriptomics

## Three-Step Workflow

**Always follow this sequence: Search → Info → Run**

### Step 1: Search for tools

```
tooluniverse_search(query="protein structure prediction", limit=5)
```

This returns a list of matching tools with names and descriptions. Use natural language to describe what you need.

You can also use the generic discovery entry:

```
tool_search(query="protein structure prediction", source_type="tooluniverse", limit=5)
```

### Step 2: Check tool specification

```
tooluniverse_info(tool_name="UniProt_get_function_by_accession")
```

This returns the full parameter schema (required/optional args, types, descriptions). **Always check this before running a tool** to ensure you provide correct arguments.

Generic equivalent:

```
tool_info(tool_ref="tooluniverse:UniProt_get_function_by_accession")
```

### Step 3: Execute the tool

```
tooluniverse_run(
    tool_name="UniProt_get_function_by_accession",
    arguments='{"accession": "P05067"}'
)
```

The `arguments` parameter is a **JSON string** containing the tool's parameters.

Generic equivalent:

```
tool_run(
    tool_ref="tooluniverse:UniProt_get_function_by_accession",
    arguments='{"accession": "P05067"}'
)
```

## Common Tool Examples

### Protein & Gene
| Tool | Arguments Example |
|------|-------------------|
| `UniProt_get_function_by_accession` | `{"accession": "P05067"}` |
| `UniProt_get_entry_by_accession` | `{"accession": "P05067"}` |

### Drug Safety
| Tool | Arguments Example |
|------|-------------------|
| `FAERS_count_reactions_by_drug_event` | `{"medicinalproduct": "aspirin"}` |

### Disease-Target
| Tool | Arguments Example |
|------|-------------------|
| `OpenTargets_get_associated_targets_by_disease_efoId` | `{"efoId": "EFO_0000685"}` |

### Literature
| Tool | Arguments Example |
|------|-------------------|
| `PubTator_search_publications` | `{"query": "CRISPR cancer therapy", "limit": 10}` |

### ADMET Prediction
| Tool | Arguments Example |
|------|-------------------|
| `ADMETAI_predict_BBB_penetrance` | `{"smiles": ["CCO"]}` |
| `ADMETAI_predict_toxicity` | `{"smiles": ["CCO"]}` |

### Molecular Docking
| Tool | Arguments Example |
|------|-------------------|
| `boltz2_docking` | `{"protein_id": "1ABC", "ligand_smiles": "CCO"}` |

## Multi-Step Research Patterns

### Drug Safety Profile
1. `tooluniverse_search("drug adverse events")` → find FAERS tools
2. `tooluniverse_run("FAERS_count_reactions_by_drug_event", ...)` → get adverse events
3. `tooluniverse_run("FAERS_get_drug_label_info", ...)` → get drug label

### Disease Target Discovery
1. `tooluniverse_run("OpenTargets_get_associated_targets_by_disease_efoId", ...)` → targets
2. `tooluniverse_run("UniProt_get_entry_by_accession", ...)` → protein details
3. `tooluniverse_run("PubTator_search_publications", ...)` → supporting literature

### Compound Property Analysis
1. `tooluniverse_search("ADMET prediction")` → find prediction tools
2. Run multiple ADMET predictions (BBB, toxicity, bioavailability, solubility)
3. Synthesize results into a compound profile

## Tips

- **Tool names follow a pattern**: `Database_action_description` (e.g., `UniProt_get_entry_by_accession`)
- **First call may be slow** (~30s) as ToolUniverse initializes; subsequent calls are fast
- **Results can be large**: focus on the most relevant fields for the user's question
- **When unsure about tool name**: use `tool_search` or `tooluniverse_search` with a broad query first
- **Chain multiple tools** for comprehensive analysis — combine data from different sources
- **API keys are optional**: most tools work without keys, but some (NVIDIA, HuggingFace) may need them for specific functionality
