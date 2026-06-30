---
name: differential-expression
description: DESeq2-based differential expression analysis for RNA-seq data. Provides expert guidance on when and how to use DESeq2, parameter selection, and result interpretation.
user-invocable: true
---

# Differential Expression Analysis (DESeq2)

Use this skill when the user requests differential expression analysis of RNA-seq count data, or asks about expression differences between experimental groups.

## When to Apply

- Bulk RNA-seq data with raw counts (not TPM/FPKM-normalized data; DESeq2 performs its own normalization)
- Two or more experimental groups with biological replicates (minimum 2-3 replicates per group)
- Simple or multi-factor designs (e.g., `~ condition`, `~ batch + condition`)

## When NOT to Apply

- Normalized expression data (use limma instead)
- Single-sample or no-replicate designs (DESeq2 can estimate dispersion without replicates but with very low power)
- Microarray data (use limma)
- Single-cell data (use the single-cell module, v0.0.3)

## Input Data Format

### Counts File (CSV)

- Rows: genes (gene ID in first column)
- Columns: samples
- Values: integer raw counts
- Example:

```
gene_id,sample1,sample2,sample3
BRCA1,1023,892,756
TP53,2341,2100,1987
```

### Metadata File (CSV)

- Must contain one row per sample, matching count matrix column names
- Must include the grouping variable(s) used in the design formula
- Example:

```
sample,condition,batch
sample1,treated,1
sample2,treated,1
sample3,control,1
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| counts_file | string | required | Path to gene count matrix CSV |
| metadata_file | string | required | Path to sample metadata CSV |
| design_formula | string | required | R formula, e.g. `~ condition` or `~ batch + condition` |
| contrast_variable | string | required | Variable name to contrast (must be in design formula) |
| treatment_group | string | required | Treatment/experimental group label |
| control_group | string | required | Control/reference group label |
| alpha | number | 0.05 | Adjusted p-value cutoff |
| lfc_threshold | number | 1.0 | Absolute log2 fold change threshold |
| output_dir | string | required | Output directory |

## Parameter Selection Guidance

### Design Formula

- Simple two-group comparison: `~ condition`
- With batch effect: `~ batch + condition`
- With covariates: `~ age + sex + condition`
- The variable of interest should be listed LAST for the default DESeq2 results extraction

### Alpha (padj cutoff)

- 0.05: Standard. Good balance of sensitivity and specificity for most experiments.
- 0.01: Stricter. Use when false positives are costly (e.g., validation experiments).
- 0.1: More relaxed. Use for exploratory/hypothesis-generating analyses.

### LFC Threshold

- 1.0: Standard (2-fold change). Recommended for most analyses.
- 0.585: ~1.5-fold. Use when expecting subtle expression changes.
- 2.0: Stringent (4-fold). Use for highly confident, large-effect DEGs.

## Output Interpretation

### deseq2_results.csv

Key columns:
- **baseMean**: Mean normalized count across all samples
- **log2FoldChange**: log2(treatment/control). Positive = higher in treatment.
- **lfcSE**: Standard error of log2FC
- **stat**: Wald test statistic
- **pvalue**: Raw p-value
- **padj**: Benjamini-Hochberg adjusted p-value (FDR)

### Volcano Plot

- X-axis: log2FoldChange
- Y-axis: -log10(padj)
- Red points: significantly upregulated (higher padj, higher log2FC)
- Blue points: significantly downregulated
- Grey points: not significant
- Top genes labelled

### PCA Plot

- Shows sample clustering based on top variable genes
- Good quality: treatment groups should form distinct clusters
- Batch effects or outliers will be visible as separate clusters or stray points

### MA Plot

- X-axis: mean normalized count (expression level)
- Y-axis: log2 fold change
- Red points: significant DEGs
- Should be roughly symmetric around y=0, with no strong dependence on expression level

## Common Pitfalls

1. **Counts vs normalized data**: Ensure input is raw integer counts, not TPM/FPKM.
2. **Sample name mismatch**: Sample names in counts columns must match metadata row names exactly.
3. **Design formula ordering**: The contrast variable should work with how DESeq2 names coefficients.
4. **Interpretation of log2FC direction**: Positive = upregulated in treatment vs control. This is the DESeq2 convention for `contrast = c(variable, treatment, control)`.
5. **Zero-count genes**: DESeq2 filters low-count genes. The total_genes in summary.json reflects post-filtering count.
