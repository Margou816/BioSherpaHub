---
id: report
name: Analysis Report Generation
tool: report
description: Generate combined HTML/Markdown analysis report from diffexp and enrichment results
---

# Analysis Report Generation

Generates a comprehensive HTML report combining all analysis results.

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| diffexp_dir | path | "" | Diffexp output directory |
| enrichment_dir | path | "" | GO/KEGG enrichment output directory |
| pubmed_dir | path | "" | PubMed search output directory (optional) |
| output_dir | path | (required) | Where to save the report |

## When to Use

Call this tool ONLY after the user confirms all analyses are complete.
Do NOT call it automatically -- always ask the user first.