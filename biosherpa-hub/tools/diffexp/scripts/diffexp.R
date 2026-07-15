#!/usr/bin/env Rscript
# ------------------------------------------------------------------------------
# BioSherpa diffexp.R -- Unified differential expression pipeline (DESeq2 + limma)
#
# --method deseq2  : RNA-seq raw count data
# --method limma   : microarray or normalized expression matrix
#
# All visualization (PCA, volcano, heatmap) is shared across methods.
# ------------------------------------------------------------------------------

.libPaths(unique(c(.libPaths(), Sys.getenv("R_LIBS_USER"))))

# --- Preflight: verify required R packages ---
cat(sprintf("R version: %s\n", R.version.string))
required_pkgs <- c("optparse", "ggplot2", "ggrepel", "pheatmap", "FactoMineR", "factoextra", "scales")
missing_pkgs <- required_pkgs[!sapply(required_pkgs, requireNamespace, quietly = TRUE)]
if (length(missing_pkgs) > 0) {
  cat("WARNING: Missing R packages:\n")
  for (p in missing_pkgs) cat(sprintf("  - %s\n", p))
  cat("Run: install.packages(missing_pkgs, repos='https://cran.r-project.org')\n")
}

suppressPackageStartupMessages({
  library(optparse)
  library(ggplot2)
  library(ggrepel)
  library(pheatmap)
  library(FactoMineR)
  library(factoextra)
  library(scales)
  # jsonlite loaded conditionally below
})

# --- Conditionally load optional packages (graceful degradation) ---
has_jsonlite <- requireNamespace("jsonlite", quietly = TRUE)
has_rmarkdown <- requireNamespace("rmarkdown", quietly = TRUE)
if (!has_jsonlite) {
  cat("NOTE: jsonlite not available, using base R for JSON output\n")
}
if (!has_rmarkdown) {
  cat("NOTE: rmarkdown not available, HTML report will be skipped (MD only)\n")
}

# ---------------------------------------------------------------------------
# CLI arguments
# ---------------------------------------------------------------------------
option_list <- list(
  make_option("--method", type="character", default="deseq2",
              help="DE method: deseq2 or limma"),
  make_option("--counts", type="character",
              help="Input expression/count matrix (genes=rows, samples=cols)"),
  make_option("--metadata", type="character",
              help="Sample metadata file"),
  make_option("--design", type="character", default="~condition",
              help="Design formula"),
  make_option("--contrast-variable", type="character", default="condition",
              help="Variable for contrast"),
  make_option("--treatment", type="character", help="Treatment group label"),
  make_option("--control", type="character", help="Control group label"),
  make_option("--output-dir", type="character", default=".",
              help="Output directory"),
  make_option("--pvalue-cutoff", type="double", default=0.05,
              help="P-value cutoff for DEG filtering"),
  make_option("--use-padj", action="store_true", default=FALSE,
              help="Use adjusted p-value (padj) instead of raw p-value"),
  make_option("--lfc-threshold", type="double", default=1.0,
              help="Absolute log2 fold-change threshold"),
  make_option("--colors", type="character", default="",
              help="Comma-separated custom color palette"),
  make_option("--pca-label", action="store_true", default=FALSE,
              help="Show sample labels on PCA plot")
)

parser <- OptionParser(option_list=option_list)
opts <- parse_args(parser)

opts[["pvalue-cutoff"]] <- as.numeric(opts[["pvalue-cutoff"]])
opts[["lfc-threshold"]]  <- as.numeric(opts[["lfc-threshold"]])

method        <- opts[["method"]]
input_file    <- opts[["counts"]]
metadata_file <- opts[["metadata"]]
design_formula <- as.formula(opts[["design"]])
contrast_var  <- opts[["contrast-variable"]]
treat         <- opts[["treatment"]]
ctrl          <- opts[["control"]]
outdir        <- opts[["output-dir"]]
pval_cut      <- opts[["pvalue-cutoff"]]
use_padj      <- opts[["use-padj"]]
lfc_thresh    <- opts[["lfc-threshold"]]
custom_colors <- opts[["colors"]]
pca_label     <- opts[["pca-label"]]

dir.create(outdir, showWarnings=FALSE, recursive=TRUE)

# ---------------------------------------------------------------------------
# #4 log2FC warning
# ---------------------------------------------------------------------------
if (lfc_thresh != 1.0) {
  cat(sprintf("WARNING: lfc_threshold=%.3f (~%.1f-fold). %s\n",
              lfc_thresh, 2^lfc_thresh,
              ifelse(lfc_thresh < 1.0, "This is a relaxed cutoff.", "")))
}

# ---------------------------------------------------------------------------
# #6 Parse custom colors or use defaults
# ---------------------------------------------------------------------------
default_colors <- c("#CA2C2C", "#194E7A", "#ED6356", "#41A98E", "#00B4D7",
                    "#EFA73B", "#AC3282", "#A99A5A", "#65619D", "#F4EE72")
if (nchar(custom_colors) > 0) {
  user_colors <- unlist(strsplit(custom_colors, ","))
  user_colors <- trimws(user_colors)
} else {
  user_colors <- default_colors
}

# ---------------------------------------------------------------------------
# #5 Multi-format input
# ---------------------------------------------------------------------------
read_data <- function(path) {
  ext <- tolower(tools::file_ext(path))
  if (ext == "csv") {
    return(read.csv(path, row.names=1, check.names=FALSE))
  } else if (ext %in% c("tsv", "txt")) {
    return(read.delim(path, row.names=1, check.names=FALSE))
  } else if (ext %in% c("xlsx", "xls")) {
    if (!requireNamespace("readxl", quietly=TRUE)) {
      stop("XLSX input requires the 'readxl' package. Install with: install.packages('readxl')")
    }
    df <- as.data.frame(readxl::read_xlsx(path))
    rownames(df) <- df[,1]
    df <- df[,-1, drop=FALSE]
    return(df)
  } else {
    stop(sprintf("Unsupported format '%s'. Use CSV, TSV, or XLSX.", ext))
  }
}

expr_data  <- read_data(input_file)
metadata   <- read_data(metadata_file)

# Ensure metadata row names exist
if (is.null(rownames(metadata)) || all(rownames(metadata) == as.character(1:nrow(metadata)))) {
  rownames(metadata) <- metadata[[1]]
}

# ---------------------------------------------------------------------------
# Align samples
# ---------------------------------------------------------------------------
samples_expr <- colnames(expr_data)
samples_meta <- rownames(metadata)
if (!all(samples_expr %in% samples_meta)) {
  missing <- setdiff(samples_expr, samples_meta)
  stop("Samples in expression matrix not found in metadata: ", paste(missing, collapse=", "))
}
expr_data <- expr_data[, samples_expr, drop=FALSE]
metadata  <- metadata[samples_expr, , drop=FALSE]

# ---------------------------------------------------------------------------
# #10 Get actual group levels from metadata
# ---------------------------------------------------------------------------
if (!contrast_var %in% colnames(metadata)) {
  stop(sprintf("Contrast variable '%s' not found in metadata columns: %s",
               contrast_var, paste(colnames(metadata), collapse=", ")))
}
group_levels <- unique(metadata[[contrast_var]])
group_list   <- metadata[[contrast_var]]
n_groups     <- length(group_levels)

# ---------------------------------------------------------------------------
# Color assignment for groups
# ---------------------------------------------------------------------------
group_colors <- setNames(user_colors[1:n_groups], group_levels)

# Volcano colors (Up/Down/NS)
# Fixed volcano colors (regulation direction, not group membership)
vol_up_col   <- "#CA2C2C"  # red for up-regulated
vol_down_col <- "#194E7A"  # blue for down-regulated
vol_ns_col   <- "#BCBCBC"  # grey for not significant

# Heatmap annotation colors
annotation_colors <- list()
annotation_colors[[contrast_var]] <- group_colors
names(annotation_colors) <- contrast_var

# ---------------------------------------------------------------------------
# #8 Method-specific DE analysis
# ---------------------------------------------------------------------------
if (method == "deseq2") {
  suppressPackageStartupMessages(library(DESeq2))
  counts <- as.matrix(expr_data)
  storage.mode(counts) <- "integer"
  dds <- DESeqDataSetFromMatrix(countData=counts, colData=metadata, design=design_formula)
  dds <- dds[rowSums(counts(dds)) > 0, ]
  dds <- DESeq(dds)
  res <- as.data.frame(results(dds))
  res$gene_id <- rownames(res)
  
  res$AveExpr <- res$baseMean
  # for PCA
  vsd <- if (nrow(dds) >= 50) vst(dds, blind=TRUE) else varianceStabilizingTransformation(dds, blind=TRUE)
  expr_transformed <- assay(vsd)
  method_label <- "DESeq2"

} else if (method == "limma") {
  suppressPackageStartupMessages(library(limma))
  design_mat <- model.matrix(design_formula, data=metadata)
  fit <- lmFit(expr_data, design_mat)
  fit <- eBayes(fit, trend=TRUE)
  contrast_cols <- grep(contrast_var, colnames(design_mat))
  if (length(contrast_cols) == 0) {
    stop(sprintf("Contrast variable '%s' not found in design columns", contrast_var))
  }
  coef_idx <- tail(contrast_cols, 1)
  res <- as.data.frame(topTable(fit, coef=coef_idx, number=Inf, adjust.method="BH"))
colnames(res)[colnames(res) == "logFC"] <- "log2FoldChange"  # normalize column name
  res$gene_id <- rownames(res)
  # for PCA
  expr_transformed <- as.matrix(expr_data)
  method_label <- "limma"

} else {
  stop(sprintf("Unknown method '%s'. Use 'deseq2' or 'limma'.", method))
}

# ---------------------------------------------------------------------------
# #2 pvalue/padj filtering
# ---------------------------------------------------------------------------
pval_col <- if (use_padj) "adj.P.Val" else "pvalue"
pval_label <- if (use_padj) "padj" else "pvalue"

res$Regulation <- "ns"
res$Regulation[(res[[pval_col]] < pval_cut) & (res$log2FoldChange < -lfc_thresh)] <- "Down"
res$Regulation[(res[[pval_col]] < pval_cut) & (res$log2FoldChange >  lfc_thresh)] <- "Up"
res$FoldChange <- 2^res$log2FoldChange

res_ordered <- res[order(res[[pval_col]]),
  c("gene_id","FoldChange","log2FoldChange","pvalue","padj","Regulation","AveExpr")]

# ---------------------------------------------------------------------------
# #3 results TSV
# ---------------------------------------------------------------------------
result_file <- file.path(outdir, paste0("3_", method, "_results.tsv"))
write.table(res_ordered, file=result_file, row.names=FALSE, sep="\t", quote=FALSE, fileEncoding="UTF-8")
cat("Results written to:", result_file, "\n")

# ---------------------------------------------------------------------------
# PCA plot
# ---------------------------------------------------------------------------
pca_data <- as.data.frame(t(expr_transformed))
data.pca <- PCA(pca_data, graph=FALSE)

# #7 PCA geom
pca_geom <- if (pca_label) c("point", "text") else "point"

pca_plot <- fviz_pca_ind(
  data.pca,
  geom.ind = pca_geom,
  col.ind = group_list,
  palette = as.vector(group_colors),
  pointsize = 1.3,
  alpha.ind = 0.6,
  addEllipses = TRUE,
  ellipse.level = 0.95,
  alpha.ellipse = 0.3,
  repel = TRUE,
  legend.title = contrast_var
) +
  theme_bw() +
  ggtitle(sprintf("PCA: %s vs %s (%s)", treat, ctrl, method_label)) +
  theme(
    plot.title = element_text(hjust=0.5, size=14, face="bold"),
    axis.title = element_text(size=12),
    legend.title = element_text(size=12)
  )

# #1 dual format
ggsave(file.path(outdir, "1_PCA.png"), pca_plot, width=5.5, height=4, dpi=150)
ggsave(file.path(outdir, "1_PCA.pdf"), pca_plot, width=5.5, height=4)
cat("PCA plot written to:", file.path(outdir, "1_PCA.png/pdf"), "\n")

# ---------------------------------------------------------------------------
# Volcano plot
# ---------------------------------------------------------------------------
up_count   <- sum(res_ordered$Regulation == "Up")
down_count <- sum(res_ordered$Regulation == "Down")

top_up   <- head(res_ordered[res_ordered$Regulation == "Up", ], 10)
top_down <- head(res_ordered[res_ordered$Regulation == "Down", ], 10)
top_genes <- rbind(top_up, top_down)

volcano_plot <- ggplot(res_ordered, aes(x=log2FoldChange, y=-log10(get(pval_col)), colour=Regulation)) +
  geom_point(alpha=0.8, size=2.5) +
  geom_vline(xintercept=c(-lfc_thresh, lfc_thresh), lty=4, col="black", lwd=0.8) +
  geom_hline(yintercept=-log10(pval_cut), lty=4, col="black", lwd=0.8) +
  labs(title=sprintf("%s vs %s (%s)", treat, ctrl, method_label),
       x="log2 Fold Change", y=paste0("-log10(", pval_label, ")")) +
  theme_bw() +
  scale_color_manual(
    values=c("Down"=vol_down_col, "ns"=vol_ns_col, "Up"=vol_up_col),
    labels=c(paste0("Down(",down_count,")"), "NS", paste0("Up(",up_count,")"))) +
  scale_x_continuous(limits=c(-5,5), oob=scales::squish) +
  geom_text_repel(data=top_genes, aes(label=gene_id), size=4, color="black",
                  max.overlaps=100, box.padding=0.8, show.legend=FALSE) +
  theme(plot.title=element_text(hjust=0.5, size=14, face="bold"),
        axis.title=element_text(size=13), legend.title=element_blank())

ggsave(file.path(outdir, "2_volcano.png"), volcano_plot, width=8, height=6, dpi=150)
ggsave(file.path(outdir, "2_volcano.pdf"), volcano_plot, width=8, height=6)
cat("Volcano plot written to:", file.path(outdir, "2_volcano.png/pdf"), "\n")

# ---------------------------------------------------------------------------
# #10 Heatmap -- dynamic annotation colors from input data
# ---------------------------------------------------------------------------
sig_genes <- res_ordered[res_ordered$Regulation %in% c("Up","Down"), ]
if (nrow(sig_genes) > 0) {
  top_up_hm   <- head(sig_genes[sig_genes$Regulation == "Up", "gene_id"], 10)
  top_down_hm <- head(sig_genes[sig_genes$Regulation == "Down", "gene_id"], 10)
  selected    <- c(top_up_hm, top_down_hm)
  selected    <- selected[selected %in% rownames(expr_transformed)]

  if (length(selected) >= 2) {
    hm_data <- expr_transformed[selected, , drop=FALSE]
    annot_col <- data.frame(row.names=colnames(hm_data))
    annot_col[[contrast_var]] <- metadata[colnames(hm_data), contrast_var]

    # Build annotation_colors dynamically from input data
    hm_color_list <- list()
    hm_color_list[[contrast_var]] <- group_colors

    hm_path_pdf <- file.path(outdir, "4_heatmap.pdf")
    hm_path_png <- file.path(outdir, "4_heatmap.png")

    pdf(hm_path_pdf, width=8, height=6)
    pheatmap(mat=hm_data, scale="row", annotation_col=annot_col,
             annotation_colors=hm_color_list,
             cluster_rows=TRUE, cluster_cols=TRUE,
             show_rownames=TRUE, show_colnames=FALSE,
             border_color="black", fontsize=12, fontsize_row=10,
             color=colorRampPalette(c("#194E7A","white","#CA2C2C"))(50))
    dev.off()

    png(hm_path_png, width=8, height=6, units="in", res=150)
    pheatmap(mat=hm_data, scale="row", annotation_col=annot_col,
             annotation_colors=hm_color_list,
             cluster_rows=TRUE, cluster_cols=TRUE,
             show_rownames=TRUE, show_colnames=FALSE,
             border_color="black", fontsize=12, fontsize_row=10,
             color=colorRampPalette(c("#194E7A","white","#CA2C2C"))(50))
    dev.off()
    cat("Heatmap written to:", hm_path_pdf, "and", hm_path_png, "\n")
  } else {
    cat("Not enough significant genes for heatmap (need >= 2)\n")
  }
} else {
  cat("No significant DEGs for heatmap\n")
}

# ---------------------------------------------------------------------------
# Summary JSON
# ---------------------------------------------------------------------------
sig <- which((res_ordered[[pval_col]] < pval_cut) & (abs(res_ordered$log2FoldChange) > lfc_thresh))
up  <- sig[res_ordered$log2FoldChange[sig] >  lfc_thresh]
down <- sig[res_ordered$log2FoldChange[sig] < -lfc_thresh]

summary_list <- list(
  method          = method,
  treatment       = treat,
  control         = ctrl,
  design          = opts[["design"]],
  pvalue_cutoff   = pval_cut,
  use_padj        = use_padj,
  lfc_threshold   = lfc_thresh,
  total_genes     = nrow(res_ordered),
  significant     = length(sig),
  upregulated     = length(up),
  downregulated   = length(down)
)
if (has_jsonlite) {
  writeLines(jsonlite::toJSON(summary_list, auto_unbox=TRUE, pretty=TRUE),
           file.path(outdir, "5_summary.json"))
} else {
  sink(file.path(outdir, "5_summary.json"))
  str(summary_list)
  sink()
}
cat("Summary written to:", file.path(outdir, "5_summary.json"), "\n")

# ---------------------------------------------------------------------------
# #9 Reproducible analysis code
# ---------------------------------------------------------------------------
cat("Generating reproducible analysis code...\n")
code_lines <- c(
  "#!/usr/bin/env Rscript",
  paste("# Generated:", Sys.time()),
  "",
  "suppressPackageStartupMessages({",
  if (method=="deseq2") "  library(DESeq2)" else "  library(limma)",
  "  library(ggplot2); library(ggrepel); library(pheatmap)",
  "  library(FactoMineR); library(factoextra)",
  "})",
  "",
  sprintf('method <- "%s"', method),
  sprintf('input_file <- "%s"', input_file),
  sprintf('metadata_file <- "%s"', metadata_file),
  sprintf('treat <- "%s"; ctrl <- "%s"', treat, ctrl),
  sprintf('outdir <- "%s"', outdir),
  sprintf('pval_cut <- %s; lfc_thresh <- %s; use_padj <- %s', pval_cut, lfc_thresh, use_padj),
  "",
  "# --- PCA plot ---",
  "pca_data <- as.data.frame(t(expr_transformed))",
  "data.pca <- PCA(pca_data, graph=FALSE)",
  sprintf("group_colors <- c(%s)", paste(sprintf('"%s"="%s"', names(group_colors), group_colors), collapse=", ")),
  sprintf("group_list <- metadata[['%s']]", contrast_var),
  sprintf("pca_plot <- fviz_pca_ind(data.pca, geom.ind=%s, col.ind=group_list, palette=group_colors, addEllipses=TRUE, repel=TRUE) + theme_bw() + ggtitle('%s vs %s')", deparse(pca_geom), treat, ctrl),
  sprintf("ggsave('%s', pca_plot, width=5.5, height=4, dpi=150)", file.path(outdir,"1_PCA.png")),
  sprintf("ggsave('%s', pca_plot, width=5.5, height=4)", file.path(outdir,"1_PCA.pdf")),
  "",
  "# --- Volcano plot ---",
  "up_count <- sum(res$Regulation == 'Up')",
  "down_count <- sum(res$Regulation == 'Down')",
  "top_up <- head(res[res$Regulation == 'Up', ], 10)",
  "top_down <- head(res[res$Regulation == 'Down', ], 10)",
  "top_genes <- rbind(top_up, top_down)",
  sprintf("pval_col <- if(use_padj) 'adj.P.Val' else 'pvalue'"),
  "volcano_plot <- ggplot(res, aes(x=log2FoldChange, y=-log10(get(pval_col)), colour=Regulation)) +",
  "  geom_point(alpha=0.8, size=2.5) +",
  "  geom_vline(xintercept=c(-lfc_thresh, lfc_thresh), lty=4, col='black') +",
  "  geom_hline(yintercept=-log10(pval_cut), lty=4, col='black') +",
  sprintf("  labs(title='%s vs %s', x='log2 Fold Change') +", treat, ctrl),
  "  theme_bw() + scale_color_manual(values=c('Down'='#194E7A','ns'='#BCBCBC','Up'='#CA2C2C')) +",
  "  geom_text_repel(data=top_genes, aes(label=gene_id), size=4, show.legend=FALSE) +",
  "  theme(legend.title=element_blank())",
  sprintf("ggsave('%s', volcano_plot, width=8, height=6, dpi=150)", file.path(outdir,"2_volcano.png")),
  sprintf("ggsave('%s', volcano_plot, width=8, height=6)", file.path(outdir,"2_volcano.pdf")),
  "",
  "# --- Heatmap ---",
  "sig_genes <- res[res$Regulation %in% c('Up','Down'), ]",
  "if (nrow(sig_genes) >= 2) {",
  "  selected <- c(head(sig_genes[sig_genes$Regulation=='Up','gene_id'],10),",
  "               head(sig_genes[sig_genes$Regulation=='Down','gene_id'],10))",
  "  hm_data <- expr_transformed[selected, , drop=FALSE]",
  sprintf("  annot_col <- data.frame(row.names=colnames(hm_data), %s=metadata[colnames(hm_data),'%s'])", contrast_var, contrast_var),
  sprintf("  hm_color_list <- list(); hm_color_list[['%s']] <- group_colors", contrast_var),
  sprintf("  pdf('%s', width=8, height=6)", file.path(outdir,"4_heatmap.pdf")),
  "  pheatmap(hm_data, scale='row', annotation_col=annot_col, annotation_colors=hm_color_list, cluster_rows=TRUE, cluster_cols=TRUE, show_rownames=TRUE, show_colnames=FALSE, border_color='black', color=colorRampPalette(c('#194E7A','white','#CA2C2C'))(50))",
  "  dev.off()",
  sprintf("  png('%s', width=8, height=6, units='in', res=150)", file.path(outdir,"4_heatmap.png")),
  "  pheatmap(hm_data, scale='row', annotation_col=annot_col, annotation_colors=hm_color_list, cluster_rows=TRUE, cluster_cols=TRUE, show_rownames=TRUE, show_colnames=FALSE, border_color='black', color=colorRampPalette(c('#194E7A','white','#CA2C2C'))(50))",
  "  dev.off()",
  "}",
  "",
  "# --- Summary ---",
  "sig <- which((res[[pval_col]] < pval_cut) & (abs(res$log2FoldChange) > lfc_thresh))",
  "summary_list <- list(method=method, treatment=treat, control=ctrl, pvalue_cutoff=pval_cut, lfc_threshold=lfc_thresh, total_genes=nrow(res), significant=length(sig), upregulated=sum(res$log2FoldChange[sig] > lfc_thresh), downregulated=sum(res$log2FoldChange[sig] < -lfc_thresh))",
  sprintf("if (requireNamespace('jsonlite', quietly=TRUE)) writeLines(jsonlite::toJSON(summary_list, auto_unbox=TRUE, pretty=TRUE), '%s')", file.path(outdir,"5_summary.json")),
  paste0("cat('Analysis complete\n')")
)
code_str <- paste(code_lines, collapse="\n")
code_path <- file.path(outdir, "6_analysis_code.R")
writeLines(code_str, code_path)
cat("Reproducible code written to:", code_path, "\n")

# ---------------------------------------------------------------------------
# #11 HTML report
# ---------------------------------------------------------------------------
report_lines <- c(
  "# Differential Expression Analysis Report",
  "",
  sprintf("## Analysis: %s vs %s (%s)", treat, ctrl, method_label),
  sprintf("Contrast: %s | Design: %s", contrast_var, deparse(design_formula)),
  "",
  sprintf("- Total genes: %d", nrow(res_ordered)),
  sprintf("- Significant DEGs: **%d**", length(sig)),
  sprintf("  - Upregulated: %d", length(up)),
  sprintf("  - Downregulated: %d", length(down)),
  sprintf("- P-value cutoff: %.3f (%s)", pval_cut, pval_label),
  sprintf("- |log2FC| threshold: %.2f", lfc_thresh),
  "",
  "## Output Files",
  "| # | File | Description |",
  "|---|---|---|",
  "| 1 | 1_PCA.png/pdf | PCA plot |",
  "| 2 | 2_volcano.png/pdf | Volcano plot |",
  sprintf("| 3 | 3_%s_results.tsv | Full DEG results |", method),
  "| 4 | 4_heatmap.png/pdf | Heatmap |",
  "| 5 | 5_summary.json | Summary stats |",
  "| 6 | 6_analysis_code.R | Reproducible code |",
  "| 7 | 7_report.html/md | This report |",
  "",
  "## Session Info",
  "",
  "```",
  paste(capture.output(sessionInfo()), collapse="\n"),
  "```"
)

report_md <- paste(unlist(report_lines), collapse="\n")
report_md_path <- file.path(outdir, "7_report.md")
writeLines(report_md, report_md_path)

if (has_rmarkdown) {
  tryCatch({
    rmarkdown::render(report_md_path, output_format="html_document",
                      output_file="7_report.html", output_dir=outdir, quiet=TRUE)
    cat("HTML report written to:", file.path(outdir, "7_report.html"), "\n")
  }, error=function(e) cat("rmarkdown failed, MD report at:", report_md_path, "\n"))
} else {
  cat("Markdown report written to:", report_md_path, "\n")
}

