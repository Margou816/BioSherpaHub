#!/usr/bin/env Rscript
# limma.R -- Fixed limma differential expression pipeline

.libPaths(c(Sys.getenv('R_LIBS_USER'), .libPaths()))
# Usage: Rscript limma.R --expr-file <csv> --metadata-file <csv> --design <formula> ...

suppressPackageStartupMessages({
  library(limma)
  library(optparse)
  library(ggplot2)
  library(jsonlite)
})

# Parse command-line arguments
option_list <- list(
  make_option("--expr-file", type="character", help="Normalized expression matrix CSV (genes=rows, samples=cols)"),
  make_option("--metadata-file", type="character", help="Sample metadata CSV"),
  make_option("--design", type="character", default="~condition", help="Design formula"),
  make_option("--contrast-variable", type="character", default="condition", help="Variable for contrast"),
  make_option("--treatment", type="character", help="Treatment group label"),
  make_option("--control", type="character", help="Control group label"),
  make_option("--output-dir", type="character", default=".", help="Output directory"),
  make_option("--pvalue-cutoff", type="double", default=0.05, help="Adjusted p-value cutoff"),
  make_option("--lfc-cutoff", type="double", default=1.0, help="Absolute log2FC threshold")
)
opt <- parse_args(OptionParser(option_list=option_list))

# Validate required arguments
if (is.null(opt$"expr-file") || is.null(opt$"metadata-file") ||
    is.null(opt$treatment) || is.null(opt$control)) {
  stop("Missing required arguments: --expr-file, --metadata-file, --treatment, --control")
}

# Read input data
expr <- read.csv(opt$"expr-file", row.names=1, check.names=FALSE)
metadata <- read.csv(opt$"metadata-file", row.names=NULL, check.names=FALSE)

# Use first column as sample ID for metadata
sample_col <- colnames(metadata)[1]
rownames(metadata) <- metadata[[sample_col]]

# Ensure sample order matches expression columns
common_samples <- intersect(colnames(expr), rownames(metadata))
if (length(common_samples) == 0) {
  stop("No matching sample names between expression matrix and metadata")
}
expr <- expr[, common_samples, drop=FALSE]
metadata <- metadata[common_samples, , drop=FALSE]

# Build design matrix
design_formula <- as.formula(opt$design)
design <- model.matrix(design_formula, data=metadata)

# Fit limma model
fit <- lmFit(expr, design)
fit <- eBayes(fit, trend=TRUE)

# Extract contrast coefficient
contrast_cols <- grep(opt$"contrast-variable", colnames(design))
if (length(contrast_cols) == 0) {
  stop(sprintf("Contrast variable '%s' not found in design columns: %s",
               opt$"contrast-variable", paste(colnames(design), collapse=", ")))
}
# Use the last matching column (variable of interest should be last in design)
coef_idx <- tail(contrast_cols, 1)

# Extract results
results <- topTable(fit, coef=coef_idx, number=Inf, adjust.method="BH")
results$significant <- results$adj.P.Val < opt$"pvalue-cutoff" &
                       abs(results$logFC) > opt$"lfc-cutoff"

# Save results CSV
write.csv(results, file.path(opt$"output-dir", "limma_results.csv"), row.names=TRUE)
cat("Results written to:", file.path(opt$"output-dir", "limma_results.csv"), "\n")

# Volcano plot
results$neg_log10_padj <- -log10(pmax(results$adj.P.Val, 1e-300))
results$direction <- "NS"
results$direction[results$significant & results$logFC > 0] <- "Up"
results$direction[results$significant & results$logFC < 0] <- "Down"

p <- ggplot(results, aes(x=logFC, y=neg_log10_padj, color=direction)) +
  geom_point(alpha=0.6, size=1.5) +
  scale_color_manual(values=c("Up"="red", "Down"="blue", "NS"="grey70")) +
  theme_minimal(base_size=12) +
  labs(x="log2 Fold Change", y="-log10 adjusted p-value",
       title=sprintf("limma: %s vs %s", opt$treatment, opt$control)) +
  geom_hline(yintercept=-log10(opt$"pvalue-cutoff"), linetype="dashed", color="grey50") +
  geom_vline(xintercept=c(-opt$"lfc-cutoff", opt$"lfc-cutoff"), linetype="dashed", color="grey50")

ggsave(file.path(opt$"output-dir", "volcano.png"), p, width=8, height=6, dpi=150)
cat("Volcano plot written to:", file.path(opt$"output-dir", "volcano.png"), "\n")

# Summary JSON
summary <- list(
  treatment = opt$treatment,
  control = opt$control,
  design = opt$design,
  pvalue_cutoff = opt$"pvalue-cutoff",
  lfc_cutoff = opt$"lfc-cutoff",
  total_genes = nrow(results),
  significant = sum(results$significant),
  upregulated = sum(results$significant & results$logFC > 0),
  downregulated = sum(results$significant & results$logFC < 0)
)
writeLines(toJSON(summary, auto_unbox=TRUE, pretty=TRUE),
           file.path(opt$"output-dir", "summary.json"))
cat("Summary written to:", file.path(opt$"output-dir", "summary.json"), "\n")

# Session info
cat("\n--- Session Info ---\n")
sessionInfo()