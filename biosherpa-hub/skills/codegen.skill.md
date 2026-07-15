---
id: codegen
name: Master Analysis Code Generation
tool: codegen
description: Assemble master_analysis.R from individual analysis output directories
---

# Master Analysis Code Generation

Combines code fragments and parameters from completed analyses into a single
`master_analysis.R` script that can reproduce the entire workflow.

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| diffexp-dir | path | "" | Diffexp output directory (with 5_summary.json + 6_analysis_code.R) |
| enrichment-dir | path | "" | Enrichment output directory |
| pubmed-dir | path | "" | PubMed output directory (optional) |
| output-dir | path | (required) | Where to save master_analysis.R |

## Output

- `master_analysis.R` -- runnable R script reproducing all analyses