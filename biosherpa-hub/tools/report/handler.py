"""Report generation handler -- combines diffexp + enrichment results into HTML report."""
from __future__ import annotations
import argparse, sys, os, json, shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="BioSherpa Analysis Report Generator")
    parser.add_argument("--diffexp-dir", type=str, default="", help="Diffexp output directory")
    parser.add_argument("--enrichment-dir", type=str, default="", help="Enrichment output directory")
    parser.add_argument("--pubmed-dir", type=str, default="", help="PubMed output directory")
    parser.add_argument("--output-dir", type=str, required=True, help="Output directory for report")
    args = parser.parse_args(argv)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# BioSherpa Analysis Report",
        f"Generated: {now}",
        "",
        "## 1. Differential Expression Analysis",
    ]

    # Diffexp section
    de_dir = Path(args.diffexp_dir) if args.diffexp_dir else None
    if de_dir and de_dir.is_dir():
        summary_file = de_dir / "5_summary.json"
        if summary_file.is_file():
            summary = json.loads(summary_file.read_text(encoding="utf-8"))
            lines += [
                f"- Method: {summary.get('method', 'N/A')}",
                f"- Treatment: {summary.get('treatment', 'N/A')} vs Control: {summary.get('control', 'N/A')}",
                f"- Total genes: {summary.get('total_genes', 'N/A')}",
                f"- Significant DEGs: {summary.get('significant', 'N/A')}",
                f"  - Upregulated: {summary.get('upregulated', 'N/A')}",
                f"  - Downregulated: {summary.get('downregulated', 'N/A')}",
                f"- P-value cutoff: {summary.get('pvalue_cutoff', 'N/A')}",
                f"- |log2FC| threshold: {summary.get('lfc_threshold', 'N/A')}",
            ]
        # Copy key figures
        for fname in ["1_PCA.png", "2_volcano.png", "4_heatmap.png"]:
            src = de_dir / fname
            if src.is_file():
                shutil.copy2(src, out / f"de_{fname}")
                lines.append(f"\n![{fname}](de_{fname})")
        lines.append("")

    # Enrichment section
    en_dir = Path(args.enrichment_dir) if args.enrichment_dir else None
    if en_dir and en_dir.is_dir():
        lines.append("## 2. GO/KEGG Enrichment Analysis")
        for fname in sorted(en_dir.iterdir()):
            if fname.suffix == ".csv" and fname.stat().st_size > 50:
                text = fname.read_text(encoding="utf-8", errors="replace")
                row_count = len(text.strip().split("\n")) - 1
                if "Note" not in text[:100]:
                    lines.append(f"- {fname.stem}: {row_count} terms")
        for fname in sorted(en_dir.iterdir()):
            if fname.suffix in (".png", ".pdf"):
                dest = out / f"en_{fname.name}"
                shutil.copy2(fname, dest)
                lines.append(f"\n![{fname.name}](en_{fname.name})")
        lines.append("")

    # PubMed section
    pm_dir = Path(args.pubmed_dir) if args.pubmed_dir else None
    if pm_dir and pm_dir.is_dir():
        lines.append("## 3. PubMed Literature Search")
        csv_file = pm_dir / "pubmed_results.csv"
        if csv_file.is_file():
            text = csv_file.read_text(encoding="utf-8", errors="replace")
            row_count = max(0, len(text.strip().split("\n")) - 1)
            lines.append(f"- Articles found: {row_count}")
        lines.append("")

    # Discussion
    lines += [
        "## 4. Discussion",
        "The differential expression analysis identified significantly regulated genes.",
        "GO/KEGG enrichment reveals the biological functions and pathways involved.",
        "PubMed search provides literature context for the key findings.",
        "",
        "For detailed results, refer to the output files in the analysis directories.",
    ]

    md_path = out / "analysis_report.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    # Try HTML conversion
    html_path = out / "analysis_report.html"
    try:
        import subprocess as sp
        rscript = shutil.which("Rscript") or shutil.which("Rscript.exe")
        if rscript:
            sp.run([rscript, "-e",
                f'if(requireNamespace("rmarkdown",quietly=TRUE)) rmarkdown::render("{md_path}",output_file="{html_path.name}",output_dir="{out}",quiet=TRUE)'],
                capture_output=True, timeout=60)
    except Exception:
        pass

    if html_path.is_file():
        print(f"HTML report: {html_path}")
    print(f"Markdown report: {md_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())