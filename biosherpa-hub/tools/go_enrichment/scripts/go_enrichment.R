#!/usr/bin/env Rscript
# ---------------------------------------------------------------------------
# BioSherpa GO Enrichment -- clusterProfiler GO (BP/MF/CC) with PDF+PNG output
# Supports: DEG result files (logFC or log2FoldChange) or plain gene lists
# ---------------------------------------------------------------------------
.libPaths(unique(c(.libPaths(), Sys.getenv("R_LIBS_USER"))))

suppressPackageStartupMessages({
  library(optparse)
  library(clusterProfiler)
  library(enrichplot)
  library(ggplot2)
})

option_list <- list(
  make_option("--deg-file", type="character", help="DEG results TSV/CSV or gene list file"),
  make_option("--organism", type="character", default="org.Hs.eg.db",
              help="OrgDb package (org.Hs.eg.db, org.Mm.eg.db, ...)"),
  make_option("--output-dir", type="character", default=".", help="Output directory"),
  make_option("--pvalue-cutoff", type="double", default=0.05, help="P-value cutoff"),
  make_option("--qvalue-cutoff", type="double", default=0.2, help="Q-value cutoff")
)
opts <- parse_args(OptionParser(option_list=option_list))

# --- Read input: auto-detect format ---
ext <- tolower(tools::file_ext(opts[["deg-file"]]))
if (ext == "csv") {
  deg <- read.csv(opts[["deg-file"]], stringsAsFactors=FALSE, check.names=FALSE)
} else {
  deg <- read.delim(opts[["deg-file"]], stringsAsFactors=FALSE, check.names=FALSE)
}

# --- Determine input mode: gene list vs DEG table ---
is_gene_list <- ncol(deg) == 1 || !"log2FoldChange" %in% colnames(deg) && !any(c("pvalue","padj") %in% colnames(deg))
if (is_gene_list) {
  genes <- na.omit(as.character(deg[[1]]))
  genes <- genes[genes != ""]
  cat(sprintf("Gene list mode: %d genes loaded\n", length(genes)))
} else {
  # Find fold-change column (logFC from diffexp, log2FoldChange from standard DESeq2)
  fc_col <- intersect("log2FoldChange", colnames(deg))
  if (is.na(fc_col)) stop("No fold-change column found (logFC or log2FoldChange)")
  pval_col <- intersect(c("pvalue", "padj"), colnames(deg))[1]
  if (is.na(pval_col)) stop("No p-value column found (pvalue or padj)")
  sig <- deg[!is.na(deg[[pval_col]]) & deg[[pval_col]] < opts[["pvalue-cutoff"]] &
             !is.na(deg[[fc_col]]) & abs(deg[[fc_col]]) > 0.5, ]
  genes <- na.omit(as.character(sig[[1]]))
  genes <- genes[genes != ""]
  cat(sprintf("DEG mode: %d significant genes (col=%s, pval<%s)\n",
              length(genes), fc_col, opts[["pvalue-cutoff"]]))
}

if (length(genes) < 3) {
  cat("WARNING: Fewer than 3 genes -- enrichment may not produce meaningful results\n")
  if (length(genes) == 0) {
    cat("No genes to analyze. Check input file and cutoff values.\n")
    quit(status=0)
  }
}

# --- Load organism database ---
suppressPackageStartupMessages(library(opts$organism, character.only=TRUE))

# --- Run GO enrichment for BP, MF, CC ---
ontologies <- c("BP", "MF", "CC")
results <- list()

for (ont in ontologies) {
  cat(sprintf("Running GO %s enrichment...\n", ont))
  ego <- tryCatch(
    enrichGO(gene=genes, OrgDb=get(opts$organism), ont=ont, keyType="SYMBOL",
             pvalueCutoff=opts[["pvalue-cutoff"]], qvalueCutoff=opts[["qvalue-cutoff"]]),
    error=function(e) { cat(sprintf("  GO %s failed: %s\n", ont, e$message)); return(NULL) }
  )
  results[[ont]] <- ego
}

# --- Save results ---
dir.create(opts[["output-dir"]], showWarnings=FALSE, recursive=TRUE)
out <- opts[["output-dir"]]
total_terms <- 0

for (ont in ontologies) {
  ego <- results[[ont]]
  if (is.null(ego) || nrow(ego) == 0) {
    cat(sprintf("GO %s: no enriched terms\n", ont))
    next
  }
  # CSV
  csv_path <- file.path(out, sprintf("go_enrichment_%s.csv", tolower(ont)))
  write.csv(as.data.frame(ego), csv_path, row.names=FALSE)
  # Bar plot (PDF + PNG)
  bp <- barplot(ego, showCategory=min(15, nrow(ego)),
                title=sprintf("GO %s Enrichment", ont))
  pdf_path <- file.path(out, sprintf("go_barplot_%s.pdf", tolower(ont)))
  png_path <- file.path(out, sprintf("go_barplot_%s.png", tolower(ont)))
  ggsave(pdf_path, bp, width=10, height=7)
  ggsave(png_path, bp, width=10, height=7, dpi=150)
  # Dot plot (PDF + PNG)
  dp <- dotplot(ego, showCategory=min(15, nrow(ego)),
                title=sprintf("GO %s Enrichment", ont))
  pdf_path2 <- file.path(out, sprintf("go_dotplot_%s.pdf", tolower(ont)))
  png_path2 <- file.path(out, sprintf("go_dotplot_%s.png", tolower(ont)))
  ggsave(pdf_path2, dp, width=10, height=7)
  ggsave(png_path2, dp, width=10, height=7, dpi=150)
  # cnetplot (gene-term network)
  if (nrow(ego) >= 2) {
    tryCatch({
      cp <- cnetplot(ego, showCategory=min(5, nrow(ego)))
      ggsave(file.path(out, sprintf("go_cnetplot_%s.pdf", tolower(ont))), cp, width=12, height=10)
      ggsave(file.path(out, sprintf("go_cnetplot_%s.png", tolower(ont))), cp, width=12, height=10, dpi=150)
    }, error=function(e) cat(sprintf("  GO %s cnetplot failed: %s\n", ont, e$message)))
    # chord diagram (circular cnetplot, requires circlize)
    if (requireNamespace("circlize", quietly=TRUE)) {
      tryCatch({
        cp2 <- cnetplot(ego, showCategory=min(5, nrow(ego)), circular=TRUE, colorEdge=TRUE)
        ggsave(file.path(out, sprintf("go_chord_%s.pdf", tolower(ont))), cp2, width=10, height=10)
        ggsave(file.path(out, sprintf("go_chord_%s.png", tolower(ont))), cp2, width=10, height=10, dpi=150)
      }, error=function(e) cat(sprintf("  GO %s chord failed: %s\n", ont, e$message)))
    }
  }
  total_terms <- total_terms + nrow(ego)
  cat(sprintf("GO %s: %d terms saved\n", ont, nrow(ego)))
}

cat(sprintf("GO enrichment complete: %d total enriched terms across %d ontologies\n",
            total_terms, length(ontologies)))