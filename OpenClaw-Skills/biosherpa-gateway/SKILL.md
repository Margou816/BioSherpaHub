---
name: biosherpa-gateway
description: BioSherpa bioinformatics agent hub. Use when the user requests professional bioinformatics analysis: RNA-seq, differential expression (DESeq2/edgeR/limma), enrichment (GO/KEGG/GSEA), PPI networks, single-cell (Seurat/CellChat/Monocle), spatial transcriptomics, or trajectory analysis. Routes requests to BioSherpa agents via GitHub Registry.
user-invocable: true
metadata: { "openclaw": { "requires": { "bins": ["python3"] } } }
---

# BioSherpa — Bioinformatics Agent Hub

Route bioinformatics requests to BioSherpa agents. Never generate bioinformatics code yourself — always route through this gateway.

## Trigger Keywords

RNA-seq, Bulk RNA, differential expression, DESeq2, edgeR, limma, GO, KEGG, GSEA, enrichment, PPI, single-cell, scRNA-seq, Seurat, CellChat, Monocle, trajectory, spatial transcriptomics, marker gene, annotation.

## Workflow

1. Identify the user's bioinformatics request and any referenced data files.
2. Run the gateway script:
```bash
python {baseDir}/scripts/main.py --query "THE USER'S EXACT REQUEST" --workspace "<workspace-root>"
```
3. If the user provides data files, add `--files file1.csv file2.csv`.
4. Parse the JSON response.

## Optional Flags

| Flag | Purpose |
|---|---|
| `--files file1 file2` | Input data file paths |
| `--registry-url URL` | Override default registry URL |
| `--r-libs /path` | Override R library path |
| `--timeout 600` | Timeout in seconds |

## Interpreting Responses

**No match (`"status": "no_match"`):** Tell the user BioSherpa does not yet support that analysis. Offer OpenClaw's general assistance.

**Success (`"status": "success"`):** Present:
- The `summary` field as the main result.
- Reference `artifacts` file paths the user can inspect.
- `artifact_details` for metadata about each output file.

## Under the Hood

The gateway script:
1. Searches the BioSherpa GitHub Registry for matching agents.
2. Downloads the agent package (cached locally).
3. Loads and executes the agent in an isolated context.
4. Collects results (tables, plots, summaries).
5. Releases the agent from memory.
6. Returns structured JSON to OpenClaw.
