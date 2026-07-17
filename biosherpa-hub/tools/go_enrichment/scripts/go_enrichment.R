 #!/usr/bin/env Rscript
 # ---------------------------------------------------------------------------
 # BioSherpa GO Enrichment — clusterProfiler GO (BP/MF/CC) with PDF+PNG output
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
               help="OrgDb package (org.Hs.eg.db, org.Mm.eg.db, …)"),
   make_option("--output-dir", type="character", default=".", help="Output directory"),
   make_option("--pvalue-cutoff", type="double", default=0.05, help="P-value cutoff"),
   make_option("--qvalue-cutoff", type="double", default=0.2, help="Q-value cutoff")
 )
 opts <- parse_args(OptionParser(option_list=option_list))
 
 # ——— Read input: auto-detect format —————————————————————————————————
 ext <- tolower(tools::file_ext(opts[["deg-file"]]))
 if (ext == "csv") {
   deg <- read.csv(opts[["deg-file"]], stringsAsFactors=FALSE, check.names=FALSE)
 } else {
   deg <- read.delim(opts[["deg-file"]], stringsAsFactors=FALSE, check.names=FALSE)
 }
 
 # ——— Determine input mode ———————————————————————————————————————————
 cat(sprintf("Input: %d rows × %d cols\n", nrow(deg), ncol(deg)))
 cat(sprintf("Columns: %s\n", paste(colnames(deg), collapse=", ")))
 is_gene_list <- ncol(deg) == 1 ||
   (!"log2FoldChange" %in% colnames(deg) && !any(c("pvalue", "padj") %in% colnames(deg)))
 if (is_gene_list) {
   gene_symbols <- na.omit(as.character(deg[[1]]))
   gene_symbols <- gene_symbols[gene_symbols != ""]
   cat(sprintf("Gene list mode: %d symbols loaded\n", length(gene_symbols)))
 } else {
   fc_col <- "log2FoldChange"
   if (!fc_col %in% colnames(deg))
     stop("No fold-change column found (need logFC or log2FoldChange)")
   pval_col <- intersect(c("pvalue", "padj"), colnames(deg))[1]
   if (is.na(pval_col))
     stop("No p-value column found (need pvalue or padj)")
   sig <- deg[!is.na(deg[[pval_col]]) & deg[[pval_col]] < opts[["pvalue-cutoff"]] &
              !is.na(deg[[fc_col]]) & abs(deg[[fc_col]]) > 0.5, ]
   gene_symbols <- na.omit(as.character(sig[[1]]))
   gene_symbols <- gene_symbols[gene_symbols != ""]
   cat(sprintf("DEG mode: %d significant genes\n", length(gene_symbols)))
 }
 
 if (length(gene_symbols) < 3) {
   cat("WARNING: Fewer than 3 genes for GO enrichment\n")
   if (length(gene_symbols) == 0) quit(status=0)
 }
 
 # ——— Dynamic OrgDb loading ——————————————————————————————————————————
 orgdb_name <- opts[["organism"]]
 cat(sprintf("Loading organism database: %s\n", orgdb_name))
 if (!requireNamespace(orgdb_name, quietly=TRUE)) {
   stop(sprintf("OrgDb package '%s' not installed. Install: BiocManager::install('%s')",
                orgdb_name, orgdb_name))
 }
 suppressPackageStartupMessages(library(orgdb_name, character.only=TRUE))
 orgdb <- get(orgdb_name)
 
 # ——— SYMBOL → ENTREZID conversion ————————————————————————————————
 entrez_result <- tryCatch(
   bitr(gene_symbols, fromType="SYMBOL", toType="ENTREZID", OrgDb=orgdb),
   error=function(e) {
     cat(sprintf("bitr conversion failed: %s\n", e$message)); return(NULL)
   }
 )
 
 if (is.null(entrez_result) || nrow(entrez_result) == 0) {
   cat("ERROR: No genes could be converted to ENTREZ IDs.\n")
   cat(sprintf("  Input symbols: %d\n", length(gene_symbols)))
   cat(sprintf("  Check that gene symbols match %s.\n", orgdb_name))
   quit(status=0)
 }
 
 entrez_ids <- unique(entrez_result$ENTREZID)
 conv_rate <- round(length(entrez_ids) / length(gene_symbols) * 100, 1)
 cat(sprintf("SYMBOL→ENTREZID: %d/%d genes converted (%.1f%%)\n",
             length(entrez_ids), length(gene_symbols), conv_rate))
 
 if (conv_rate < 30) {
   cat("WARNING: Low conversion rate. Check organism database and gene symbols.\n")
 }
 
 # ——— Run GO enrichment for BP, MF, CC ——————————————————————————————
 dir.create(opts[["output-dir"]], showWarnings=FALSE, recursive=TRUE)
 out <- opts[["output-dir"]]
 ontologies <- c("BP", "MF", "CC")
 results <- list()
 file_n <- 0
 
 for (ont in ontologies) {
   cat(sprintf("Running GO %s enrichment…\n", ont))
   ego <- tryCatch(
     enrichGO(gene=entrez_ids, OrgDb=orgdb, ont=ont, keyType="ENTREZID",
              pvalueCutoff=opts[["pvalue-cutoff"]],
              qvalueCutoff=opts[["qvalue-cutoff"]]),
     error=function(e) {
       cat(sprintf("  GO %s failed: %s\n", ont, e$message)); return(NULL)
     }
   )
   results[[ont]] <- ego
 
   if (is.null(ego)) {
     cat(sprintf("GO %s: execution error\n", ont))
     next
   }
   if (nrow(ego) == 0) {
     cat(sprintf("GO %s: no enriched terms\n", ont))
     next
   }
 
   ont_lower <- tolower(ont)
 
   # —— CSV ——
   file_n <- file_n + 1
   csv_path <- file.path(out, sprintf("%d_go_%s.csv", file_n, ont_lower))
   write.csv(as.data.frame(ego), csv_path, row.names=FALSE)
 
   # —— Bar plot (PDF + PNG) ——
   bp <- barplot(ego, showCategory=min(15, nrow(ego)),
                 title=sprintf("GO %s Enrichment", ont))
   file_n <- file_n + 1
   ggsave(file.path(out, sprintf("%d_go_%s_barplot.pdf", file_n, ont_lower)),
          bp, width=10, height=7)
   ggsave(file.path(out, sprintf("%d_go_%s_barplot.png", file_n, ont_lower)),
          bp, width=10, height=7, dpi=150)
 
   # —— Dot plot (PDF + PNG) ——
   dp <- dotplot(ego, showCategory=min(15, nrow(ego)),
                 title=sprintf("GO %s Enrichment", ont))
   file_n <- file_n + 1
   ggsave(file.path(out, sprintf("%d_go_%s_dotplot.pdf", file_n, ont_lower)),
          dp, width=10, height=7)
   ggsave(file.path(out, sprintf("%d_go_%s_dotplot.png", file_n, ont_lower)),
          dp, width=10, height=7, dpi=150)
 
   # —— cnetplot (gene-term network) ——
   if (nrow(ego) >= 2) {
     tryCatch({
       file_n <- file_n + 1
       cp <- cnetplot(ego, showCategory=min(5, nrow(ego)))
       pdf(file.path(out, sprintf("%d_go_%s_cnetplot.pdf", file_n, ont_lower)),
           width=12, height=10)
       print(cp)
       dev.off()
       ggsave(file.path(out, sprintf("%d_go_%s_cnetplot.png", file_n, ont_lower)),
              cp, width=12, height=10, dpi=150)
     }, error=function(e) cat(sprintf("  GO %s cnetplot failed: %s\n", ont, e$message)))
 
     # —— chord diagram (circular cnetplot, requires circlize) ——
     if (requireNamespace("circlize", quietly=TRUE)) {
       tryCatch({
         file_n <- file_n + 1
         cp2 <- cnetplot(ego, showCategory=min(5, nrow(ego)),
                         circular=TRUE, colorEdge=TRUE)
         pdf(file.path(out, sprintf("%d_go_%s_chord.pdf", file_n, ont_lower)),
             width=10, height=10)
         print(cp2)
         dev.off()
         ggsave(file.path(out, sprintf("%d_go_%s_chord.png", file_n, ont_lower)),
                cp2, width=10, height=10, dpi=150)
       }, error=function(e) cat(sprintf("  GO %s chord failed: %s\n", ont, e$message)))
     }
   }
 
   cat(sprintf("GO %s: %d terms saved\n", ont, nrow(ego)))
 }
 
 # ——— Summary ————————————————————————————————————————————————————————
 total_terms <- sum(sapply(results, function(x) if (is.null(x)) 0 else nrow(x)))
 active_onts <- sum(sapply(results, function(x) !is.null(x) && nrow(x) > 0))
 cat(sprintf("GO enrichment complete: %d terms across %d ontologies\n",
             total_terms, active_onts))
 
 # ——— Generate reproducible code —————————————————————————————————————
 code_lines <- c(
   "#!/usr/bin/env Rscript",
   paste("# Generated:", Sys.time()),
   "suppressPackageStartupMessages({library(clusterProfiler); library(enrichplot); library(ggplot2)})",
   sprintf("library(%s)", orgdb_name),
   sprintf('deg_file <- "%s"', opts[["deg-file"]]),
   sprintf('outdir <- "%s"', out),
   sprintf("orgdb <- %s", orgdb_name),
   'deg <- read.csv(deg_file, stringsAsFactors=FALSE)',
   'gene_symbols <- na.omit(as.character(deg[[1]]))',
   'entrez_result <- bitr(gene_symbols, fromType="SYMBOL", toType="ENTREZID", OrgDb=orgdb)',
   'entrez_ids <- unique(entrez_result$ENTREZID)',
   'for (ont in c("BP","MF","CC")) {',
   '  ego <- enrichGO(gene=entrez_ids, OrgDb=orgdb, ont=ont, keyType="ENTREZID",',
   sprintf('               pvalueCutoff=%s, qvalueCutoff=%s)',
           opts[["pvalue-cutoff"]], opts[["qvalue-cutoff"]]),
   '  if (!is.null(ego) && nrow(ego) > 0) {',
   '    write.csv(as.data.frame(ego),',
   '              file.path(outdir, paste0("go_", tolower(ont), ".csv")),',
   '              row.names=FALSE)',
   '    ggsave(file.path(outdir, paste0("go_", tolower(ont), "_barplot.png")),',
   '           barplot(ego, showCategory=15), width=10, height=7, dpi=150)',
   '    ggsave(file.path(outdir, paste0("go_", tolower(ont), "_dotplot.png")),',
   '           dotplot(ego, showCategory=15), width=10, height=7, dpi=150)',
   '  }',
   '}',
   'cat("GO enrichment complete\\n")'
 )
 code_str <- paste(code_lines, collapse="\n")
 file_n <- file_n + 1
 code_path <- file.path(out, sprintf("%d_analysis_code.R", file_n))
 writeLines(code_str, code_path)
 cat("Reproducible code written to:", code_path, "\n")
