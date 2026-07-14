"""diffexp handler -- thin dispatch to diffexp.R (DESeq2 or limma)."""
from __future__ import annotations
import argparse, subprocess, sys, os
from pathlib import Path
from typing import List, Optional

_SCRIPT_DIR = Path(__file__).resolve().parent
_DIFFEXP_R = _SCRIPT_DIR / "scripts" / "diffexp.R"
_DEFAULT_TIMEOUT = 600

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Unified Differential Expression Handler (DESeq2 / limma)")
    parser.add_argument("--method", type=str, default="deseq2", help="DE method: deseq2 or limma")
    parser.add_argument("--counts", type=str, required=True, help="Expression/count matrix file")
    parser.add_argument("--metadata", type=str, required=True, help="Sample metadata file")
    parser.add_argument("--design", type=str, default="~condition", help="Design formula")
    parser.add_argument("--contrast-variable", type=str, default="condition", help="Contrast variable")
    parser.add_argument("--treatment", type=str, required=True, help="Treatment group label")
    parser.add_argument("--control", type=str, required=True, help="Control group label")
    parser.add_argument("--output-dir", type=str, required=True, help="Output directory")
    parser.add_argument("--pvalue-cutoff", type=float, default=0.05, help="P-value cutoff")
    parser.add_argument("--use-padj", action="store_true", default=False, help="Use adjusted p-value")
    parser.add_argument("--lfc-threshold", type=float, default=1.0, help="log2FC threshold")
    parser.add_argument("--colors", type=str, default="", help="Custom color palette (comma-separated)")
    parser.add_argument("--pca-label", action="store_true", default=False, help="Show labels on PCA")
    args = parser.parse_args(argv)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    cmd = ["Rscript", str(_DIFFEXP_R),
           "--method", args.method,
           "--counts", args.counts,
           "--metadata", args.metadata,
           "--design", args.design,
           "--contrast-variable", args.contrast_variable,
           "--treatment", args.treatment,
           "--control", args.control,
           "--output-dir", str(out),
           "--pvalue-cutoff", str(args.pvalue_cutoff),
           "--lfc-threshold", str(args.lfc_threshold),
           "--colors", args.colors]
    if args.use_padj:
        cmd.append("--use-padj")
    if args.pca_label:
        cmd.append("--pca-label")

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=_DEFAULT_TIMEOUT,
                                env={**os.environ, "R_LIBS_USER": os.environ.get("R_LIBS_USER", "C:/tmp/Rlib")})
        if result.stdout:
            print(result.stdout.decode("utf-8", errors="replace"))
        if result.stderr:
            print(result.stderr.decode("utf-8", errors="replace"), file=sys.stderr)
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"diffexp analysis timed out after {_DEFAULT_TIMEOUT}s", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())