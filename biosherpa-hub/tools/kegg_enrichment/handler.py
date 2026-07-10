"""KEGG enrichment handler -- thin dispatch to kegg_enrichment.R."""
from __future__ import annotations
import argparse, subprocess, sys, os
from pathlib import Path
from typing import List, Optional
_SCRIPT_DIR = Path(__file__).resolve().parent
_KEGG_R = _SCRIPT_DIR / "scripts" / "kegg_enrichment.R"
def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="KEGG Enrichment Handler")
    parser.add_argument("--deg-file", required=True, type=Path)
    parser.add_argument("--organism", default="hsa")
    parser.add_argument("--pvalue-cutoff", type=float, default=0.05)
    parser.add_argument("--qvalue-cutoff", type=float, default=0.2)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    cmd = ["Rscript", str(_KEGG_R), "--deg-file", str(args.deg_file),
           "--organism", args.organism, "--output-dir", str(out),
           "--pvalue-cutoff", str(args.pvalue_cutoff),
           "--qvalue-cutoff", str(args.qvalue_cutoff)]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=600, env={**os.environ, "R_LIBS_USER": os.environ.get("R_LIBS_USER", "C:/tmp/Rlib")})
        if result.stdout: print(result.stdout.decode("utf-8", errors="replace"))
        return 0
    except subprocess.CalledProcessError as exc:
        print(exc.stderr.decode("utf-8", errors="replace"), file=sys.stderr)
        return exc.returncode
if __name__ == "__main__": sys.exit(main())
