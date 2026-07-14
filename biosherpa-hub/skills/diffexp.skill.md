---
id: diffexp
name: Differential Expression Analysis
tool: diffexp
description: Unified differential expression analysis supporting DESeq2 (RNA-seq) and limma (microarray/normalized)
---

# Differential Expression Analysis

Unified differential expression pipeline supporting two methods:

- **DESeq2** -- for RNA-seq raw count data with biological replicates
- **limma** -- for microarray data or pre-normalized expression matrices

## Parameter Display Protocol

**Before calling `run_biosherpa_tool`, present the following parameter table to the user.**
Ask if they want to use defaults or specify custom values. This ensures the user
understands and agrees with all analysis settings.

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| method | string | deseq2 | DE method: `deseq2` (RNA-seq counts) or `limma` (microarray/normalized) |
| counts | path | (required) | Expression/count matrix (genes=rows, samples=cols) |
| metadata | path | (required) | Sample metadata file |
| design | string | ~condition | Design formula |
| contrast-variable | string | condition | Variable for contrast |
| treatment | string | (required) | Treatment group label |
| control | string | (required) | Control group label |
| output-dir | path | biosherpa_output | Output directory |
| pvalue-cutoff | float | 0.05 | P-value cutoff for DEG filtering |
| use-padj | flag | off | Use adjusted p-value (padj) instead of pvalue |
| lfc-threshold | float | 1.0 | Absolute log2 fold-change (1.0=2-fold; 0.585=1.5-fold with WARNING) |
| colors | string | "" | Custom comma-separated hex colors, or leave empty for defaults |
| pca-label | flag | off | Show sample text labels on PCA plot |

## Input Format

Supports CSV, TSV/TXT, and XLSX input files. Auto-detected by file extension.
Other formats must be converted to CSV first.

## Output Files (numbered by analysis order)

1. `1_PCA.png` / `1_PCA.pdf` -- PCA sample clustering
2. `2_volcano.png` / `2_volcano.pdf` -- Volcano plot
3. `3_{method}_results.tsv` -- Full DEG results table
4. `4_heatmap.png` / `4_heatmap.pdf` -- Top DEG heatmap (if >= 2 DEGs)
5. `5_summary.json` -- Summary statistics
6. `6_analysis_code.R` -- Reproducible analysis code
7. `7_report.html` / `7_report.md` -- Analysis report

## When to Use Each Method

- RNA-seq raw integer counts with >=3 replicates: **deseq2**
- Microarray data (any platform): **limma**
- Already-normalized expression (TPM/FPKM/RPKM): **limma**
- RNA-seq with 2 replicates: limma via empirical Bayes can handle small N

## log2FC Guidance

- 1.0 = 2-fold (standard, recommended)
- 0.585 = ~1.5-fold (relaxed -- use only with justification)
- 2.0 = 4-fold (stringent)