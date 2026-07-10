---
id: pubmed
name: PubMed Literature Search
tool: pubmed_search
description: PubMed search via NCBI E-utilities (no API key required)
---

# PubMed Literature Search

Searches PubMed for articles related to genes, pathways, or keywords.

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| query | string | (required) | Search query (gene symbols + disease terms) |
| max_results | int | 20 | Maximum articles to return |
| output_dir | path | biosherpa_output | Output directory |

## Search Tips

- Combine gene symbols with disease context: `"BRCA1 breast cancer"`
- Use MeSH terms for precision: `"inflammation"[MeSH] AND TNF`
- Use AND/OR/NOT operators for complex queries

## Output

- `pubmed_results.csv` -- Title, Authors (first 5), Journal, Year, Abstract (500 chars), PMID, DOI

## Rate Limits

NCBI E-utilities allow 3 requests/second without an API key.
A 400ms delay is built in to comply.