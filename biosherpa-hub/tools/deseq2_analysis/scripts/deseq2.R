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
    library(FactoMineR)
    library(factoextra)
    library(ggrepel)
    library(pheatmap)
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
# opts <- parse_args(parser)

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
# PCA plot
# ---------------------------------------------------------------------------

# vst transformation
vsd <- if (nrow(dds) >= 50) {
  vst(dds, blind = TRUE)
} else {
  varianceStabilizingTransformation(dds, blind = TRUE)
}

# Extract transformed expression matrix
expr_vsd <- assay(vsd)

# PCA input:
# rows = samples
# columns = genes
pca_data <- as.data.frame(t(expr_vsd))

# Run PCA
data.pca <- PCA(pca_data, graph = FALSE)

# Group information
group_list <- metadata[[contrast_var]]

colors <- c("#CA2C2C", "#194E7A", "#ED6356", "#41A98E", "#00B4D7", 
            "#EFA73B", "#AC3282", "#A99A5A", "#65619D", "#F4EE72")


# PCA plot
pca_plot <- fviz_pca_ind(
  data.pca, 
  geom.ind = "point",
  palette = colors[1:length(unique(metadata$Group))],
  # sample colors
  col.ind = group_list,
  # point settings
  pointsize = 1.3,
  alpha.ind = 0.6,
  # confidence ellipse
  addEllipses = TRUE,
  ellipse.level = 0.95,
  alpha.ellipse = 0.3,
  # sample labels
  repel = TRUE,
  legend.title = contrast_var
) +
  theme_bw() +
  ggtitle("PCA Plot") +
  theme(
    plot.title = element_text(hjust = 0.5, size = 16, face = "bold"),
    axis.title = element_text(size = 14),
    axis.text = element_text(size = 12),
    legend.text = element_text(size = 12),
    legend.title = element_text(size = 13)
  )


# Save PCA figure

pca_path <- file.path(opts[["output-dir"]], "1_PCA.pdf")

ggsave(
  filename = pca_path,
  plot = pca_plot,
  width = 5.5,
  height = 4
)


cat("PCA plot written to:", pca_path, "\n")

# ---------------------------------------------------------------------------
# DESeq2 pipeline
# ---------------------------------------------------------------------------
dds <- DESeqDataSetFromMatrix(
    countData = counts,
    colData   = metadata,
    design    = design_formula
)

# Pre-filter: Filter all 0 genes
dds <- dds[rowSums(counts(dds)) > 0, ]

dds <- DESeq(dds)

# ---------------------------------------------------------------------------
# Extract results for the specified contrast
# ---------------------------------------------------------------------------
# contrast_var <- opts[["contrast-variable"]]
# treat <- opts$treatment
# ctrl  <- opts$control

res <- results(dds)

# 设置 FC 和 p 值阈值
logFC_threshold <- opts$`lfc-threshold`
pval_threshold <- opts$alpha

# 筛选差异基因
res <- as.data.frame(res)
res$gene_id <- rownames(res)
res$Regulation <- "ns"
res$Regulation[(res$pvalue < pval_threshold) & (res$log2FoldChange < -logFC_threshold)] <- "Down"
res$Regulation[(res$pvalue < pval_threshold) & (res$log2FoldChange > logFC_threshold)] <- "Up"

# 添加 FoldChange 列
res$FoldChange <- 2^res$log2FoldChange


# Sort by adjusted p-value
res_ordered <- res[order(res$pvalue), c("gene_id", "FoldChange", "log2FoldChange", "pvalue", "padj", "Regulation", "baseMean", "lfcSE", "stat")]

# ---------------------------------------------------------------------------
# Ensure output directory exists
# ---------------------------------------------------------------------------
dir.create(opts[["output-dir"]], showWarnings = FALSE, recursive = TRUE)

# ---------------------------------------------------------------------------
# Write results TSV
# ---------------------------------------------------------------------------
tsv_path <- file.path(opts[["output-dir"]], "2_deseq2_results.tsv")
write.table(as.data.frame(res_ordered), file = tsv_path, row.names = FALSE, sep = '\t', quote = F)
cat("Results written to:", tsv_path, "\n")

# ---------------------------------------------------------------------------
# Volcano plot
# ---------------------------------------------------------------------------
# 选取上调和下调的前5个基因
top_up <- res_ordered[res_ordered$Regulation == "Up", ]
top_up <- top_up[order(-top_up$log2FoldChange), ][1:5, ]

top_down <- res_ordered[res_ordered$Regulation == "Down", ]
top_down <- top_down[order(top_down$log2FoldChange), ][1:5, ]

# 合并top基因
top_genes <- rbind(top_up, top_down)

# 获取Down和Up的数量
up_count <- nrow(res_ordered[res_ordered$Regulation == "Up", ])
down_count <- nrow(res_ordered[res_ordered$Regulation == "Down", ])

p2 <- ggplot(res_ordered, aes(x = log2FoldChange, y = -log10(pvalue), colour = Regulation)) +
  geom_point(alpha = 0.8, size = 3) +
  geom_vline(xintercept = c(-opts[["lfc-threshold"]], opts[["lfc-threshold"]]), lty = 4, col = "black", lwd = 0.8) +
  geom_hline(yintercept = -log10(opts$alpha), lty = 4, col = "black", lwd = 0.8) +
  labs(title = paste(treat, "vs", ctrl), x = "log2FoldChange", y = "-log10(P.Value)") +
  theme_bw() +
  scale_color_manual(values = c("Down" = "#194E7A", "ns" = "#BCBCBC", "Up" = "#CA2C2C"),
                     labels = c(paste0("Down(", down_count, ")"), "NS", paste0("Up(", up_count, ")"))) +
  scale_x_continuous(limits = c(-5, 5), oob = scales::squish) +
  scale_y_continuous(limits = c(0, 10), oob = scales::squish) +
  geom_text_repel(data = top_genes, aes(label = gene_id), size = 5, color = "black",
                  max.overlaps = 100, box.padding = 1, point.padding = 0.3,
                  segment.size = 0.6, segment.alpha = 0.5, min.segment.length = 0) +
  theme(plot.title = element_text(hjust = 0.5, size = 16, face = "bold"),
        axis.title = element_text(size = 18),
        axis.text = element_text(size = 16),
        legend.text = element_text(size = 14),
        legend.title = element_blank())

volcano_path <- file.path(opts[["output-dir"]], "volcano.pdf")
ggsave(filename = volcano_path, plot = p2, width = 8, height = 6)
cat("Volcano plot written to:", volcano_path, "\n")

# ---------------------------------------------------------------------------
# Heatmap
# ---------------------------------------------------------------------------
# 提取上下调基因

up_genes <- res_ordered[res_ordered$Regulation == "Up", ]
down_genes <- res_ordered[res_ordered$Regulation == "Down", ]

# 分别按 logFC 排序，选取 Top10
top10_up <- up_genes[order(-up_genes$log2FoldChange), ][1:10, "gene_id"]
top10_down <- down_genes[order(down_genes$log2FoldChange), ][1:10, "gene_id"]

# 合并 Top10 上下调基因
selected_genes <- c(top10_up, top10_down)

heatmap_data <- assay(vsd)[selected_genes, ]

annotation_col <- data.frame(Group = metadata[[contrast_var]])
rownames(annotation_col) <- colnames(heatmap_data)

annotation_colors <- list(Group = c("Control" = "#40A6A0", "LN" = "#EE4420"))

heatmap_path <- file.path(opts[["output-dir"]], "heatmap.pdf")

pdf(heatmap_path, width = 8, height = 6)

pheatmap(mat = heatmap_data,
         scale = "row",
         annotation_col = annotation_col,
         annotation_colors = annotation_colors,
         cluster_rows = TRUE,
         cluster_cols = TRUE,
         show_rownames = TRUE,
         show_colnames = FALSE,
         border_color = "black",
         fontsize = 12,
         fontsize_row = 10,
         color = colorRampPalette(c("#194E7A", "white", "#CA2C2C"))(50))

dev.off()

cat("Heatmap written to:", heatmap_path, "\n")

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
