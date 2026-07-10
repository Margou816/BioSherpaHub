---
id: kegg
name: KEGG Pathway Enrichment
tool: kegg_enrichment
description: KEGG pathway enrichment via clusterProfiler
---

# KEGG Pathway Enrichment

Maps DEGs to KEGG biological pathways.

## Input

- DEG list from DESeq2 output CSV or gene symbol list
- Gene symbols are auto-converted to ENTREZ IDs via `bitr()`

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| deg_file | path | (required) | DEG result CSV or gene list file |
| organism | string | hsa | KEGG code: hsa (human), mmu (mouse), rno (rat) |
| pvalue_cutoff | float | 0.05 | P-value cutoff |
| qvalue_cutoff | float | 0.2 | Q-value cutoff |
| output_dir | path | biosherpa_output | Output directory |

## Output Files

- `kegg_enrichment.csv`
- `kegg_barplot.png`, `kegg_dotplot.png`

## Common Issues

- KEGG organism code must match species exactly
- Some genes may not map to any KEGG pathway
- `bitr()` conversion requires the correct OrgDb package installed