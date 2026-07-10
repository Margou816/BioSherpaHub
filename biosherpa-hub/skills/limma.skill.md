---
id: limma
name: limma Differential Expression
tool: limma_analysis
description: limma-based differential expression for microarray or normalized expression data
---

# limma Differential Expression

Use this skill for **microarray data** or **already-normalized expression matrices**.

## When to Use limma (vs other methods)

- Microarray data (any platform): **USE limma**
- Already-normalized expression matrix (TPM, FPKM, RPKM): **USE limma**
- Raw RNA-seq count data with replicates (>=3): use DESeq2 instead
- Raw RNA-seq count data (2 replicates): consider edgeR instead
- Single-cell RNA-seq: requires a different agent

## Input Format

### Expression File
- Format: CSV (comma-separated)
- Rows: genes/probes (gene ID in first column)
- Columns: samples (matching metadata)
- Values: normalized expression values (log2 or linear scale)
- limma works with any continuous expression measure -- no special normalization applied

### Metadata File
- Format: CSV (comma-separated)
- One row per sample, must match expression matrix column names exactly
- Must include the grouping variable(s) used in the design formula
- Example header: `sample,condition,batch`

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| expr_file | path | (required) | Normalized expression matrix CSV |
| metadata_file | path | (required) | Sample metadata CSV |
| design_formula | string | ~condition | R formula, variable of interest LAST |
| contrast_variable | string | condition | Variable name for the contrast |
| treatment_group | string | (required) | Treatment/experimental group label |
| control_group | string | (required) | Control/reference group label |
| pvalue_cutoff | float | 0.05 | Adjusted p-value cutoff |
| lfc_cutoff | float | 1.0 | Absolute log2 fold-change threshold |
| output_dir | path | biosherpa_output | Where to save results |

## Design Formula Guidelines

- Simple two-group: `~condition`
- With batch effect: `~batch + condition`
- **Variable of interest goes LAST** for coefficient extraction

## How limma Works

Unlike DESeq2, limma:
- Works on any continuous expression values (not just counts)
- Uses linear models + empirical Bayes moderation (lmFit + eBayes)
- Does NOT perform normalization -- you must provide normalized data
- More robust for small sample sizes than standard t-tests

## Output Files

- `limma_results.csv` -- Full results: logFC, AveExpr, t, P.Value, adj.P.Val, B
- `volcano.png` -- Volcano plot (red=up, blue=down)
- `summary.json` -- Up/down gene counts

## Common Issues

- Expression matrix must be normalized BEFORE running limma
- Sample names must match exactly between expression and metadata files
- If using array data, ensure probe-to-gene mapping is done beforehand