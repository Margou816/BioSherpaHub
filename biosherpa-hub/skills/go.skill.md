---
id: go
name: GO Enrichment
tool: go_enrichment
description: Gene Ontology (BP/MF/CC) enrichment via clusterProfiler
---

# GO Enrichment Analysis

Functional enrichment against Gene Ontology databases.

## Input

- DEG list from DESeq2 output CSV or a plain gene symbol list file (one per line)
- The R script reads the first column as gene symbols

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| deg_file | path | (required) | DEG result CSV or gene list file |
| organism | string | org.Hs.eg.db | OrgDb package: org.Hs.eg.db (human), org.Mm.eg.db (mouse) |
| pvalue_cutoff | float | 0.05 | P-value cutoff for enrichment |
| qvalue_cutoff | float | 0.2 | Q-value cutoff (clusterProfiler default) |
| output_dir | path | biosherpa_output | Output directory |

## Ontologies

- BP: Biological Process -- what the genes *do*
- MF: Molecular Function -- what the gene products *bind/act on*
- CC: Cellular Component -- where the gene products are *located*

## Output Files

- `go_enrichment_bp.csv`, `go_enrichment_mf.csv`, `go_enrichment_cc.csv`
- `go_barplot.png`, `go_dotplot.png`

## Interpretation

- GeneRatio: proportion of your DEGs annotated to the term
- padj: Benjamini-Hochberg adjusted p-value
- Bar plot: top enriched terms by gene count

## Common Issues

- Fewer than 5 significant DEGs may produce no enrichment
- Gene symbol conversion rate depends on OrgDb coverage
- Always confirm the organism database matches your species