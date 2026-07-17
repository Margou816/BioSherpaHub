"""GO enrichment handler -- thin dispatch to go_enrichment.R."""
from __future__ import annotations
import argparse, subprocess, sys, os
from pathlib import Path
import sys as _sys
_HUB = __import__("pathlib").Path(__file__).resolve().parent.parent.parent
_sys.path.insert(0, str(_HUB))
from shared import find_rscript
del _sys



from typing import List, Optional

_SCRIPT_DIR = Path(__file__).resolve().parent
_GO_R = _SCRIPT_DIR / "scripts" / "go_enrichment.R"
_DEFAULT_TIMEOUT = 600

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="GO Enrichment Handler")
    parser.add_argument("--deg-file", required=True, type=Path)
    parser.add_argument("--organism", default="org.Hs.eg.db")
    parser.add_argument("--pvalue-cutoff", type=float, default=0.05)
    parser.add_argument("--qvalue-cutoff", type=float, default=0.2)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    cmd = [find_rscript(), str(_GO_R), "--deg-file", str(args.deg_file),
           "--organism", args.organism, "--output-dir", str(out),
           "--pvalue-cutoff", str(args.pvalue_cutoff),
           "--qvalue-cutoff", str(args.qvalue_cutoff)]
    try:
        result = subprocess.run(cmd, capture_output=True, encoding="utf-8",
                            errors="replace", timeout=_DEFAULT_TIMEOUT,
                            env={**os.environ, "R_LIBS_USER": os.environ.get("R_LIBS_USER", "C:/tmp/Rlib")})
        if result.stdout: print(result.stdout)
        if result.stderr: print(result.stderr, file=sys.stderr)
        return 0
    except subprocess.CalledProcessError as exc:
        print(exc.stderr.decode("utf-8", errors="replace"), file=sys.stderr)
        return exc.returncode

if __name__ == "__main__": sys.exit(main())
