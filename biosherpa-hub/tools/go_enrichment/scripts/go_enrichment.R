#!/usr/bin/env Rscript
suppressPackageStartupMessages({library(clusterProfiler);library(optparse)})
option_list=list(make_option("--deg-file",type="character"),make_option("--organism",type="character",default="org.Hs.eg.db"),make_option("--output-dir",type="character"),make_option("--pvalue-cutoff",type="double",default=0.05),make_option("--qvalue-cutoff",type="double",default=0.2))
opts=parse_args(OptionParser(option_list=option_list))
suppressPackageStartupMessages(library(opts$organism,character.only=TRUE))
deg=read.csv(opts[["deg-file"]],stringsAsFactors=FALSE)
sig=deg[deg$padj<opts[["pvalue-cutoff"]]&abs(deg$log2FoldChange)>0.5,]
genes=as.character(sig[[1]])
if(length(genes)<5){cat("Too few significant genes\n");quit(status=0)}
suppressPackageStartupMessages(library(enrichplot))
ego_bp=enrichGO(gene=genes,OrgDb=get(opts$organism),ont="BP",pvalueCutoff=opts[["pvalue-cutoff"]],qvalueCutoff=opts[["qvalue-cutoff"]])
ego_mf=enrichGO(gene=genes,OrgDb=get(opts$organism),ont="MF",pvalueCutoff=opts[["pvalue-cutoff"]],qvalueCutoff=opts[["qvalue-cutoff"]])
ego_cc=enrichGO(gene=genes,OrgDb=get(opts$organism),ont="CC",pvalueCutoff=opts[["pvalue-cutoff"]],qvalueCutoff=opts[["qvalue-cutoff"]])
dir.create(opts[["output-dir"]],showWarnings=FALSE,recursive=TRUE)
out=opts[["output-dir"]]
write.csv(as.data.frame(ego_bp),file.path(out,"go_enrichment_bp.csv"),row.names=FALSE)
write.csv(as.data.frame(ego_mf),file.path(out,"go_enrichment_mf.csv"),row.names=FALSE)
write.csv(as.data.frame(ego_cc),file.path(out,"go_enrichment_cc.csv"),row.names=FALSE)
if(nrow(ego_bp)>0){png(file.path(out,"go_barplot.png"),width=2400,height=2000,res=300);print(barplot(ego_bp,showCategory=15,title="GO BP Enrichment"));dev.off();png(file.path(out,"go_dotplot.png"),width=2400,height=2000,res=300);print(dotplot(ego_bp,showCategory=15,title="GO BP Enrichment"));dev.off()}
cat("GO enrichment complete\n")
