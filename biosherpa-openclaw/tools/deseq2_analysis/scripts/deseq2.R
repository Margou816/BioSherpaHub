#!/usr/bin/env Rscript
# ------------------------------------------------------------------------------
# BioSherpa DESeq2 Differential Expression Analysis -- fixed pipeline.
#
# This script performs a DESeq2 analysis on RNA-seq count data.
# It is NOT dynamically generated; all logic is fixed and auditable.
#
# Outputs (written to --output-dir):
#   deseq2_results.csv   Full results table (baseMean, log2FC, pvalue, padj)
#   volcano.png          EnhancedVolcano plot
#   pca.png              PCA plot (vst-transformed)
#   ma.png               MA plot (DESeq2::plotMA)
#   summary.json         Up/down gene counts
# ------------------------------------------------------------------------------

suppressPackageStartupMessages({
    library(optparse)
    library(DESeq2)
    library(ggplot2)
    library(EnhancedVolcano)
})

# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------
option_list <- list(
    make_option("--counts", type = "character", help = "Gene count matrix CSV"),
    make_option("--metadata", type = "character", help = "Sample metadata CSV"),
    make_option("--design", type = "character", help = "Design formula, e.g. '~ condition'"),
    make_option("--contrast-variable", type = "character", help = "Variable name for contrast"),
    make_option("--treatment", type = "character", help = "Treatment group label"),
    make_option("--control", type = "character", help = "Control group label"),
    make_option("--output-dir", type = "character", help = "Output directory"),
    make_option("--alpha", type = "double", default = 0.05, help = "Adjusted p-value cutoff"),
    make_option("--lfc-threshold", type = "double", default = 1.0, help = "log2FC threshold")
)

parser <- OptionParser(option_list = option_list)
opts <- parse_args(parser)

opts$alpha <- as.numeric(opts$alpha)
opts[["lfc-threshold"]] <- as.numeric(opts[["lfc-threshold"]])

# ---------------------------------------------------------------------------
# Load and validate input data
# ---------------------------------------------------------------------------
counts_raw <- read.csv(opts$counts, row.names = 1, check.names = FALSE)
metadata  <- read.csv(opts$metadata, row.names = 1, check.names = FALSE)

# Ensure all sample columns in counts exist as rows in metadata
samples_in_counts <- colnames(counts_raw)
samples_in_meta   <- rownames(metadata)
if (!all(samples_in_counts %in% samples_in_meta)) {
    missing <- setdiff(samples_in_counts, samples_in_meta)
    stop("Samples in count matrix not found in metadata: ", paste(missing, collapse = ", "))
}

# Reorder metadata to match counts column order
metadata <- metadata[samples_in_counts, , drop = FALSE]

# Integer conversion
counts <- as.matrix(counts_raw)
storage.mode(counts) <- "integer"

# Parse design formula
design_formula <- as.formula(opts$design)

# ---------------------------------------------------------------------------
# DESeq2 pipeline
# ---------------------------------------------------------------------------
dds <- DESeqDataSetFromMatrix(
    countData = counts,
    colData   = metadata,
    design    = design_formula
)

# Pre-filter: keep genes with at least 10 reads total
dds <- dds[rowSums(counts(dds)) >= 10, ]

dds <- DESeq(dds)

# ---------------------------------------------------------------------------
# Extract results for the specified contrast
# ---------------------------------------------------------------------------
contrast_var <- opts[["contrast-variable"]]
treat <- opts$treatment
ctrl  <- opts$control

res <- results(
    dds,
    contrast      = c(contrast_var, treat, ctrl),
    alpha         = opts$alpha,
    lfcThreshold  = opts[["lfc-threshold"]]
)

# Sort by adjusted p-value
res_ordered <- res[order(res$padj), ]

# ---------------------------------------------------------------------------
# Ensure output directory exists
# ---------------------------------------------------------------------------
dir.create(opts[["output-dir"]], showWarnings = FALSE, recursive = TRUE)

# ---------------------------------------------------------------------------
# Write results CSV
# ---------------------------------------------------------------------------
csv_path <- file.path(opts[["output-dir"]], "deseq2_results.csv")
write.csv(as.data.frame(res_ordered), file = csv_path, row.names = TRUE)
cat("Results written to:", csv_path, "\n")

# ---------------------------------------------------------------------------
# Volcano plot
# ---------------------------------------------------------------------------
volcano_path <- file.path(opts[["output-dir"]], "volcano.png")
png(volcano_path, width = 2400, height = 2400, res = 300)
suppressMessages(
    print(
        EnhancedVolcano(
            res_ordered,
            lab          = rownames(res_ordered),
            x            = "log2FoldChange",
            y            = "padj",
            title        = paste(treat, "vs", ctrl),
            pCutoff      = opts$alpha,
            FCcutoff     = opts[["lfc-threshold"]],
            pointSize    = 1.5,
            labSize      = 3.0,
            legendPosition = "right",
            drawConnectors = TRUE,
            max.overlaps  = 15
        )
    )
)
invisible(dev.off())
cat("Volcano plot written to:", volcano_path, "\n")

# ---------------------------------------------------------------------------
# PCA plot
# ---------------------------------------------------------------------------
vsd <- if (nrow(dds) >= 50) vst(dds, blind = TRUE) else varianceStabilizingTransformation(dds, blind = TRUE)
pca_data <- plotPCA(vsd, intgroup = contrast_var, returnData = TRUE)
percent_var <- round(100 * attr(pca_data, "percentVar"))

pca_plot <- ggplot(pca_data, aes(x = PC1, y = PC2, color = .data[[contrast_var]])) +
    geom_point(size = 3) +
    xlab(paste0("PC1: ", percent_var[1], "% variance")) +
    ylab(paste0("PC2: ", percent_var[2], "% variance")) +
    ggtitle("PCA Plot") +
    theme_bw(base_size = 14) +
    theme(legend.title = element_blank())

pca_path <- file.path(opts[["output-dir"]], "pca.png")
ggsave(pca_path, plot = pca_plot, width = 7, height = 6, dpi = 300)
cat("PCA plot written to:", pca_path, "\n")

# ---------------------------------------------------------------------------
# MA plot
# ---------------------------------------------------------------------------
ma_path <- file.path(opts[["output-dir"]], "ma.png")
png(ma_path, width = 2000, height = 2000, res = 300)
plotMA(res_ordered, ylim = c(-5, 5), main = paste("MA Plot:", treat, "vs", ctrl))
invisible(dev.off())
cat("MA plot written to:", ma_path, "\n")

# ---------------------------------------------------------------------------
# Summary JSON
# ---------------------------------------------------------------------------
valid <- which(!is.na(res_ordered$padj))
sig   <- valid[res_ordered$padj[valid] < opts$alpha]
sig_lfc <- which(abs(res_ordered$log2FoldChange) > opts[["lfc-threshold"]])
sig   <- intersect(sig, sig_lfc)
up    <- sig[res_ordered$log2FoldChange[sig] >  opts[["lfc-threshold"]]]
down  <- sig[res_ordered$log2FoldChange[sig] < -opts[["lfc-threshold"]]]

summary_list <- list(
    treatment       = treat,
    control         = ctrl,
    alpha           = opts$alpha,
    lfc_threshold   = opts[["lfc-threshold"]],
    total_genes     = nrow(res_ordered),
    significant     = length(sig),
    upregulated     = length(up),
    downregulated   = length(down)
)

summary_json <- jsonlite::toJSON(summary_list, auto_unbox = TRUE, pretty = TRUE)
summary_path <- file.path(opts[["output-dir"]], "summary.json")
writeLines(summary_json, summary_path)
cat("Summary written to:", summary_path, "\n")

# ---------------------------------------------------------------------------
# Session info for reproducibility
# ---------------------------------------------------------------------------
cat("\n--- Session Info ---\n")
sessionInfo()
