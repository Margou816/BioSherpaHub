---
id: deseq2
name: DESeq2 Differential Expression
tool: deseq2_analysis
description: DESeq2-based differential expression for RNA-seq raw count data
---

# DESeq2 Differential Expression

Use this skill for RNA-seq data with **raw integer count matrices**.

## When to Use DESeq2 (vs other methods)

- RNA-seq data with >=3 biological replicates per group: **USE DESeq2**
- RNA-seq with 2 replicates: consider edgeR instead
- Microarray or already-normalized data: use limma instead
- Single-cell RNA-seq: requires a different agent entirely

## Input Format Requirements

### Counts File
- Format: CSV (comma-separated)
- Rows: genes (gene ID in first column)
- Columns: samples (matching metadata)
- Values: **raw integer counts** -- NOT TPM, FPKM, RPKM, or normalized data
- DESeq2 performs its own normalization (median-of-ratios)

### Metadata File
- Format: CSV (comma-separated)
- One row per sample, must match count matrix column names exactly
- Must include the grouping variable(s) used in the design formula
- Example header: `sample,condition,batch`

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| counts_file | path | (required) | Raw gene count matrix CSV |
| metadata_file | path | (required) | Sample metadata CSV |
| design_formula | string | ~condition | R formula, variable of interest LAST |
| contrast_variable | string | condition | Variable name for the contrast |
| treatment_group | string | (required) | Treatment/experimental group label |
| control_group | string | (required) | Control/reference group label |
| alpha | float | 0.05 | Adjusted p-value cutoff (0.01 stricter, 0.1 exploratory) |
| lfc_threshold | float | 1.0 | Absolute log2 fold-change (1.0=2-fold, 0.585=1.5-fold) |
| output_dir | path | biosherpa_output | Where to save results |

## Design Formula Guidelines

- Simple two-group: `~condition`
- With batch effect: `~batch + condition`
- **Variable of interest goes LAST** (DESeq2 defaults to the last variable for results)

## Output Files

- `deseq2_results.csv` -- Full results: baseMean, log2FoldChange, lfcSE, stat, pvalue, padj
- `volcano.png` -- EnhancedVolcano plot (red=up, blue=down)
- `pca.png` -- PCA sample clustering
- `ma.png` -- MA plot (mean expression vs log2FC)
- `summary.json` -- Up/down gene counts