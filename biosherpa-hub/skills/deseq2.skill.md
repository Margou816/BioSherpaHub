---
id: deseq2
name: DESeq2 Skill
description: DESeq2 parameter guidance, input validation rules, and result interpretation for differential expression analysis
---
# DESeq2 Skill — Pipeline Guardian Playbook

This skill is loaded on-demand when detailed DESeq2 guidance is needed.
It does NOT run analysis — that is the agent's job.

## Input Format Requirements

### Counts File
- Rows: genes (gene ID in first column)
- Columns: samples
- Values: **raw integer counts** — NOT TPM, FPKM, or normalized data
- DESeq2 performs its own normalization (median-of-ratios)

### Metadata File
- One row per sample, matching count matrix column names
- Must include the grouping variable(s) used in the design formula
- Example: sample,condition,batch

## Parameter Selection

### Design Formula
- Simple two-group: ~condition
- With batch: ~batch + condition
- Variable of interest LAST for default results extraction

### Alpha
- 0.05 standard. 0.01 stricter. 0.1 exploratory.

### LFC Threshold
- 1.0 = 2-fold (standard)
- 0.585 = ~1.5-fold (sensitive)
- 2.0 = 4-fold (stringent)

## Output Interpretation

### CSV: deseq2_results.csv
- baseMean: mean normalized count
- log2FoldChange: positive = higher in treatment
- padj: Benjamini-Hochberg FDR

### Volcano Plot
- X: log2FC, Y: -log10(padj)
- Red = significantly up, Blue = significantly down

### PCA Plot
- Shows sample clustering by treatment
- Good quality = distinct group separation

### MA Plot
- X: mean expression, Y: log2FC
- Should be symmetric around y=0

## Common Mistakes

1. Using TPM/FPKM instead of raw counts → DESeq2 normalization is wrong
2. Sample name mismatch between counts and metadata → analysis fails
3. Design formula ordering: variable of interest should be last
4. Insufficient replicates: minimum 2-3 per group recommended
