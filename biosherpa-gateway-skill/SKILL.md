---
name: biosherpa-mcp
description: BioSherpa MCP Server — bioinformatics analysis via the Model Context Protocol. Use when the user requests RNA-seq, DESeq2, edgeR, limma, differential expression, GO, KEGG, GSEA, PPI, single-cell (Seurat, CellChat, Monocle), spatial transcriptomics, or trajectory analysis.
user-invocable: true
metadata:
  openclaw:
    mcpServer:
      command: python
      args:
        - "{baseDir}/scripts/mcp_server.py"
      env:
        R_LIBS_USER: C:/tmp/Rlib
    requires:
      bins:
        - python3
        - Rscript
---

# BioSherpa MCP Server

This skill provides bioinformatics analysis tools via the Model Context Protocol (MCP). The MCP server dynamically discovers available agents from the GitHub registry and exposes them as tools to OpenClaw.

## Supported Analysis

- **Transcriptome:** DESeq2 differential expression, volcano plots, PCA, MA plots
- **Enrichment:** GO, KEGG, GSEA (coming in next versions)
- **PPI:** Protein interaction networks (coming)
- **Single-cell:** Seurat, CellChat, Monocle (coming)

## How It Works

1. OpenClaw starts the MCP server as a subprocess
2. Server fetches available tools from the GitHub registry
3. Server exposes tools via JSON-RPC (MCP protocol over stdio)
4. When you call a tool, the server downloads the agent, runs the analysis, and returns results
5. All analysis is done via fixed pipelines — never dynamically generated code

## Configuration

OpenClaw auto-discovers the MCP server from the skill metadata. The server requires:

- **python3** — for the MCP server and agent execution
- **Rscript** — for DESeq2 analysis
- **pyyaml** — for registry parsing (`pip install pyyaml`)
- **R packages:** DESeq2, EnhancedVolcano, ggplot2 (in R_LIBS_USER)

## Tool Parameters

When OpenClaw calls a bioinformatics tool, provide:
- `counts_file` — gene count matrix CSV (genes=rows, samples=columns)
- `metadata_file` — sample metadata CSV
- `design_formula` — e.g. `~condition`
- `contrast_variable` — variable for contrast
- `treatment_group` — treatment group label
- `control_group` — control group label
- `output_dir` — directory for results
- `alpha` — padj cutoff (default 0.05)
- `lfc_threshold` — log2FC cutoff (default 1.0)
