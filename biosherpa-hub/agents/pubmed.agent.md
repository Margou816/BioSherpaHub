---
id: pubmed
name: PubMed Literature Search
type: biosherpa-agent
version: 0.1.0
keywords: [pubmed, literature, articles, ncbi, reference, citation]
description: Search PubMed for articles related to genes or keywords via NCBI E-utilities.
tools: [pubmed_search]
skills: [pubmed]
entry: agents.pubmed.agent:PubMedAgent
summary: PubMed literature search for gene-related research
use_when: After DEG or enrichment analysis, or when user requests literature background
---
# PubMed Agent
Searches PubMed for relevant literature. Uses NCBI E-utilities (no API key required).
## Parameters
| Parameter | Type | Description |
|---|---|---|
| query | string | Search query (gene names, keywords) |
| max_results | int | Max articles to return (default 20) |
| output_dir | path | Output directory |
## Outputs
- pubmed_results.csv -- Title, authors, journal, year, abstract, DOI, PMID
