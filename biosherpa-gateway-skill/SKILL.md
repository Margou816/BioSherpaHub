---
name: biosherpa-gateway
description: BioSherpa bioinformatics agent hub. Use when the user requests RNA-seq, differential expression (DESeq2/edgeR/limma), enrichment (GO/KEGG/GSEA), PPI, single-cell (Seurat/CellChat/Monocle), spatial transcriptomics, or trajectory analysis. Routes to BioSherpa agents via GitHub Registry.
user-invocable: true
metadata:
  openclaw:
    requires:
      bins:
        - python3
---

# BioSherpa Gateway

This skill routes bioinformatics requests to BioSherpa agents. Never generate bioinformatics code yourself — always route through this gateway.

## Triggers

RNA-seq | rnaseq | DESeq2 | edgeR | limma | differential expression | DEG | transcriptome | GO | KEGG | GSEA | enrichment | PPI | single-cell | scRNA-seq | Seurat | CellChat | Monocle | trajectory | spatial | marker gene | annotation | bulk RNA | gene expression

## Workflow

1. Receive bioinformatics request from user
2. Call the gateway script with the user's query and workspace
3. If response `status` is `no_match`, tell the user the analysis type is not yet supported
4. If `status` is `success`, present the `summary` and reference `artifact_details`
5. If `status` is `error`, relay the error to the user

## Usage

```bash
python {baseDir}/scripts/main.py --query "THE USER'S REQUEST" --workspace "WORKSPACE_PATH"
```

### Optional flags

| Flag | Description |
|---|---|
| `--files f1.csv f2.csv` | Input data files |
| `--registry-url URL` | Override registry URL |
| `--r-libs /path/to/R/lib` | Override R library path |
| `--timeout 600` | Timeout in seconds |

## Response Format

The gateway returns JSON:

```json
{
  "status": "success|no_match|error",
  "summary": "Human-readable result",
  "artifacts": ["/path/to/file.csv", "/path/to/plot.png"],
  "artifact_details": [
    {"name": "deseq2_results.csv", "type": "TABLE", "path": "...", "description": "..."}
  ],
  "errors": [],
  "workflow": ["deseq2_analysis"]
}
```

## Under the Hood

1. Searches BioSherpa GitHub Registry for matching agents
2. Downloads agent package (cached locally)
3. Loads and executes the agent in isolated context
4. Collects results (tables, plots, summaries)
5. Releases agent from memory — no persistent state
6. Returns structured JSON to OpenClaw
