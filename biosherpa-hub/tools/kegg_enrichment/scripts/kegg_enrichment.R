#!/usr/bin/env Rscript
# ---------------------------------------------------------------------------
# BioSherpa KEGG Pathway Enrichment -- clusterProfiler with PDF+PNG output
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
  make_option("--organism", type="character", default="hsa",
              help="KEGG organism code (hsa, mmu, rno, ...)"),
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

# --- Determine input mode ---
is_gene_list <- ncol(deg) == 1 || !"log2FoldChange" %in% colnames(deg) && !any(c("pvalue","padj") %in% colnames(deg))
if (is_gene_list) {
  gene_symbols <- na.omit(as.character(deg[[1]]))
  gene_symbols <- gene_symbols[gene_symbols != ""]
  cat(sprintf("Gene list mode: %d symbols loaded\n", length(gene_symbols)))
} else {
  fc_col <- intersect("log2FoldChange", colnames(deg))
  if (is.na(fc_col)) stop("No fold-change column found (need logFC or log2FoldChange)")
  pval_col <- intersect(c("pvalue", "padj"), colnames(deg))[1]
  if (is.na(pval_col)) stop("No p-value column found (need pvalue or padj)")
  sig <- deg[!is.na(deg[[pval_col]]) & deg[[pval_col]] < opts[["pvalue-cutoff"]] &
             !is.na(deg[[fc_col]]) & abs(deg[[fc_col]]) > 0.5, ]
  gene_symbols <- na.omit(as.character(sig[[1]]))
  gene_symbols <- gene_symbols[gene_symbols != ""]
  cat(sprintf("DEG mode: %d significant genes\n", length(gene_symbols)))
}

if (length(gene_symbols) < 3) {
  cat("WARNING: Fewer than 3 genes for KEGG enrichment\n")
  if (length(gene_symbols) == 0) quit(status=0)
}

# --- SYMBOL to ENTREZID conversion ---
suppressPackageStartupMessages(library(org.Hs.eg.db))
entrez_result <- tryCatch(
  bitr(gene_symbols, fromType="SYMBOL", toType="ENTREZID", OrgDb=org.Hs.eg.db),
  error=function(e) { cat(sprintf("bitr conversion failed: %s\n", e$message)); return(NULL) }
)

if (is.null(entrez_result) || nrow(entrez_result) == 0) {
  cat("ERROR: No genes could be converted to ENTREZ IDs.\n")
  cat(sprintf("  Input symbols: %d\n", length(gene_symbols)))
  cat("  Check that gene symbols match the organism database.\n")
  quit(status=0)
}

entrez_ids <- unique(entrez_result$ENTREZID)
conv_rate <- round(length(entrez_ids) / length(gene_symbols) * 100, 1)
cat(sprintf("SYMBOL->ENTREZID: %d/%d genes converted (%.1f%%)\n",
            length(entrez_ids), length(gene_symbols), conv_rate))

if (conv_rate < 30) {
  cat("WARNING: Low conversion rate. Check organism code and gene symbols.\n")
}

# --- Run KEGG enrichment with retry (KEGG API may be unreachable in some regions) ---
cat(sprintf("Running KEGG enrichment (organism=%s)...\n", opts$organism))
max_attempts <- 3
ekegg <- NULL
for (attempt in 1:max_attempts) {
  cat(sprintf("  KEGG attempt %d/%d...\n", attempt, max_attempts))
  ekegg <- tryCatch(
    enrichKEGG(gene=entrez_ids, organism=opts$organism,
               pvalueCutoff=opts[["pvalue-cutoff"]],
               qvalueCutoff=opts[["qvalue-cutoff"]]),
    error=function(e) { cat(sprintf("  KEGG attempt %d failed: %s\n", attempt, e$message)); return(NULL) }
  )
  if (!is.null(ekegg)) break
  if (attempt < max_attempts) {
    delay <- attempt * 10
    cat(sprintf("  Retrying in %ds... (KEGG API may be slow/unreachable)\n", delay))
    Sys.sleep(delay)
  }
}

# ReactomePA fallback if KEGG failed or returned no results
if (is.null(ekegg) || (is.data.frame(ekegg) && nrow(ekegg) == 0)) {
  cat("KEGG enrichment failed or returned no results.\n")
  if (requireNamespace("ReactomePA", quietly=TRUE)) {
    cat("Trying ReactomePA as fallback...\n")
    ekegg <- tryCatch(
      ReactomePA::enrichPathway(gene=entrez_ids, organism="human",
                 pvalueCutoff=opts[["pvalue-cutoff"]],
                 qvalueCutoff=opts[["qvalue-cutoff"]],
                 readable=TRUE),
      error=function(e) { cat(sprintf("ReactomePA failed: %s\n", e$message)); return(NULL) }
    )
    if (!is.null(ekegg)) cat("ReactomePA enrichment succeeded.\n")
  } else {
    cat("ReactomePA not installed. Install: BiocManager::install('ReactomePA')\n")
    cat("Note: reactome.db is ~415MB and requires checkmate package.\n")
  }
}

# --- Save results ---
dir.create(opts[["output-dir"]], showWarnings=FALSE, recursive=TRUE)
out <- opts[["output-dir"]]

if (is.null(ekegg)) {
  cat("KEGG enrichment produced no results (execution error).\n")
} else if (nrow(ekegg) == 0) {
  csv_path <- file.path(out, "kegg_enrichment.csv")
  write.csv(data.frame(Note="No enriched KEGG pathways found"), csv_path, row.names=FALSE)
  cat("KEGG enrichment: 0 pathways enriched.\n")
  cat(sprintf("  Input genes: %d, converted to ENTREZ: %d\n",
              length(gene_symbols), length(entrez_ids)))
  cat("  Possible reasons: no pathways passed p/q thresholds, or organism mismatch.\n")
} else {
  # CSV
  csv_path <- file.path(out, "kegg_enrichment.csv")
  write.csv(as.data.frame(ekegg), csv_path, row.names=FALSE)
  # Bar plot (PDF + PNG)
  bp <- barplot(ekegg, showCategory=min(15, nrow(ekegg)),
                title="KEGG Pathway Enrichment")
  ggsave(file.path(out, "kegg_barplot.pdf"), bp, width=10, height=7)
  ggsave(file.path(out, "kegg_barplot.png"), bp, width=10, height=7, dpi=150)
  # Dot plot (PDF + PNG)
  dp <- dotplot(ekegg, showCategory=min(15, nrow(ekegg)),
                title="KEGG Pathway Enrichment")
  ggsave(file.path(out, "kegg_dotplot.pdf"), dp, width=10, height=7)
  ggsave(file.path(out, "kegg_dotplot.png"), dp, width=10, height=7, dpi=150)
  # cnetplot (gene-pathway network)
  if (nrow(ekegg) >= 2) {
    tryCatch({
      cp <- cnetplot(ekegg, showCategory=min(5, nrow(ekegg)))
      ggsave(file.path(out, "kegg_cnetplot.pdf"), cp, width=12, height=10)
      ggsave(file.path(out, "kegg_cnetplot.png"), cp, width=12, height=10, dpi=150)
    }, error=function(e) cat(sprintf("KEGG cnetplot failed: %s\n", e$message)))
    # chord diagram (circular cnetplot, requires circlize)
    if (requireNamespace("circlize", quietly=TRUE)) {
      tryCatch({
        cp2 <- cnetplot(ekegg, showCategory=min(5, nrow(ekegg)), circular=TRUE, colorEdge=TRUE)
        ggsave(file.path(out, "kegg_chord.pdf"), cp2, width=10, height=10)
        ggsave(file.path(out, "kegg_chord.png"), cp2, width=10, height=10, dpi=150)
      }, error=function(e) cat(sprintf("KEGG chord failed: %s\n", e$message)))
    }
  }
  cat(sprintf("KEGG enrichment: %d pathways saved\n", nrow(ekegg)))
}