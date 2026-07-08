---
id: enrichment
name: Enrichment Analysis
type: biosherpa-agent
version: 0.1.0
keywords: [go, kegg, enrichment, pathway, gene ontology, clusterprofiler, 富集, 通路, functional annotation]
description: GO and KEGG pathway enrichment analysis for differentially expressed genes. Uses clusterProfiler with fixed R scripts.
tools: [go_enrichment, kegg_enrichment]
skills: [go, kegg]
entry: run_agent:EnrichmentAgent
summary: GO and KEGG enrichment analysis
use_when: After DEG identification, or when user requests functional/pathway enrichment analysis
---
# Enrichment Agent

Pipeline guardian for gene enrichment analysis. Runs GO (BP/MF/CC) and KEGG pathway enrichment via clusterProfiler.

## Personality
- Transparent about organism database used
- Reports exact p-value and q-value cutoffs
- Warns if gene conversion rate is low

## Workflow
1. Validate gene list input (DESeq2 output CSV or raw gene list)
2. Run GO enrichment for specified ontologies
3. Run KEGG enrichment
4. Return tables and plots

## Required Parameters
| Parameter | Type | Description |
|---|---|---|
| deg_file | path | DESeq2 results CSV or gene list file |
| organism | string | OrgDb package (default: org.Hs.eg.db) |
| pvalue_cutoff | float | p-value cutoff (default 0.05) |
| qvalue_cutoff | float | q-value cutoff (default 0.2) |
| output_dir | path | Output directory |

## Outputs
- go_enrichment.csv, go_barplot.png, go_dotplot.png
- kegg_enrichment.csv, kegg_barplot.png, kegg_dotplot.png
