# PubMed Literature Search Skill

## Search Tips
- Use gene symbols combined with disease/condition: "BRCA1 breast cancer"
- Use MeSH terms for precision: "inflammation[MeSH] AND TNF"
- Limit with AND/OR/NOT operators

## Output: pubmed_results.csv
- Title, Authors (first 5), Journal, Year
- Abstract (first 500 chars), PMID, DOI

## Note
NCBI E-utilities require no API key but enforce rate limits (3/sec without key).
Add 400ms delay between requests to comply.
