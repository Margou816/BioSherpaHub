---
name: biosherpa-mcp
description: BioSherpa -- bioinformatics analysis platform using the Model Context Protocol. Use when the user requests RNA-seq, deseq2, limma, differential expression, GO, KEGG, GSEA, PPI, single-cell (Seurat, CellChat, Monocle), spatial transcriptomics, pathway enrichment, PubMed literature search, or any bioinformatics analysis. Supports three-level navigation: find an agent -> load a skill -> run a tool.
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
        - python
        - Rscript
---

# BioSherpa MCP Server

Bioinformatics analysis platform with a three-level Agent-Skill-Tool architecture.

## Architecture

- **Agent** -- Bioinformatics engineer persona. Guides the conversation, clarifies your intent, and chooses the right analysis method based on your data type.
- **Skill** -- Domain-specific module. Provides detailed parameter guidance, file format requirements, thresholds, and tells you which tool to call.
- **Tool** -- Fixed R or Python pipeline. Executes the actual analysis and returns results.

## How It Works

1. OpenClaw starts the MCP server
2. Server fetches available agents from the GitHub registry
3. Call `find_biosherpa_agent` with keywords describing your analysis need
4. The agent persona helps you clarify requirements
5. Call `load_biosherpa_skill` to get parameter guidance for a specific method
6. Call `run_biosherpa_tool` with the parameters to execute the analysis
7. Results are saved to your workspace

## Available Agents

| Agent | Description | Skills          |
| transcriptome | Bulk RNA-seq / microarray differential expression | deseq2, limma     || pubmed | PubMed literature search | pubmed |

## Configuration

- **python** -- for the MCP server and agent execution
- **Rscript** -- for R-based analysis tools
- **pyyaml** -- for registry parsing (`pip install pyyaml`)
- **R packages** -- DESeq2, EnhancedVolcano, ggplot2, clusterProfiler, org.Hs.eg.db, enrichplot, optparse (in R_LIBS_USER)