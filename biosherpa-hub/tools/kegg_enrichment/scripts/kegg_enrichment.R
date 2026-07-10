#!/usr/bin/env Rscript
.libPaths(c(Sys.getenv('R_LIBS_USER'), .libPaths()))

suppressPackageStartupMessages({library(clusterProfiler);library(optparse)})
option_list=list(make_option("--deg-file",type="character"),make_option("--organism",type="character",default="hsa"),make_option("--output-dir",type="character"),make_option("--pvalue-cutoff",type="double",default=0.05),make_option("--qvalue-cutoff",type="double",default=0.2))
opts=parse_args(OptionParser(option_list=option_list))
deg=read.csv(opts[["deg-file"]],stringsAsFactors=FALSE)
suppressPackageStartupMessages(library(org.Hs.eg.db))
sig=deg[deg$padj<opts[["pvalue-cutoff"]]&abs(deg$log2FoldChange)>0.5,]
gene_symbols=as.character(sig[[1]])
suppressPackageStartupMessages(library(clusterProfiler))
entrez_ids=bitr(gene_symbols,fromType="SYMBOL",toType="ENTREZID",OrgDb=org.Hs.eg.db)
genes=unique(entrez_ids$ENTREZID)
if(length(genes)<5){cat("Too few significant genes for KEGG\n");quit(status=0)}
suppressPackageStartupMessages(library(enrichplot))
if(opts$organism=="org.Hs.eg.db"){library(org.Hs.eg.db)}
ekegg=enrichKEGG(gene=genes,organism=opts$organism,pvalueCutoff=opts[["pvalue-cutoff"]],qvalueCutoff=opts[["qvalue-cutoff"]])
dir.create(opts[["output-dir"]],showWarnings=FALSE,recursive=TRUE)
out=opts[["output-dir"]]
write.csv(as.data.frame(ekegg),file.path(out,"kegg_enrichment.csv"),row.names=FALSE)
if(!is.null(ekegg)&&nrow(ekegg)>0){png(file.path(out,"kegg_barplot.png"),width=2400,height=2000,res=300);print(barplot(ekegg,showCategory=15,title="KEGG Pathway Enrichment"));dev.off();png(file.path(out,"kegg_dotplot.png"),width=2400,height=2000,res=300);print(dotplot(ekegg,showCategory=15,title="KEGG Pathway Enrichment"));dev.off()}
cat("KEGG enrichment complete\n")
