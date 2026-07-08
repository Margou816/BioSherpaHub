# KEGG Pathway Enrichment Skill

## Input: DEG list from DESeq2 output CSV

## Parameters
- pvalue_cutoff: 0.05 standard
- qvalue_cutoff: 0.2 standard
- organism: hsa (human), mmu (mouse), rno (rat)

## Outputs
- kegg_enrichment.csv
- kegg_barplot.png, kegg_dotplot.png

## Note
enrichKEGG requires ENTREZ gene IDs. Gene symbols are auto-converted via bitr().

## Common Issues
- KEGG organism code must match species
- Some genes may not map to KEGG pathways
