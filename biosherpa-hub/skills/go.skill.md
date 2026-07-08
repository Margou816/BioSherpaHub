# GO Enrichment Skill

## Input: DEG list from DESeq2 output CSV or gene symbol list

## Parameters
- pvalue_cutoff: 0.05 standard, 0.01 strict
- qvalue_cutoff: 0.2 standard (clusterProfiler default)
- organism: org.Hs.eg.db (human), org.Mm.eg.db (mouse)

## Ontologies
- BP: Biological Process
- MF: Molecular Function
- CC: Cellular Component

## Outputs
- go_enrichment_bp.csv, go_enrichment_mf.csv, go_enrichment_cc.csv
- go_barplot.png, go_dotplot.png

## Interpretation
- GeneRatio: proportion of DEGs annotated to the GO term
- Count: number of DEGs in the term
- padj: Benjamini-Hochberg adjusted p-value
- Bar plot shows top enriched terms by count

## Common Issues
- Fewer than 5 significant genes blocks enrichment
- Gene symbol conversion rate depends on OrgDb coverage
- Verify organism database matches your species
