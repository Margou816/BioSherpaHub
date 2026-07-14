"""diffexp handler -- thin dispatch to diffexp.R (DESeq2 or limma)."""
from __future__ import annotations
import argparse, subprocess, sys, os
from pathlib import Path
import os


def _find_rscript():
    """Find a working Rscript. Collects ALL candidates, then tests each.
    Priority: explicit RSCRIPT_PATH, then PATH, Registry, disk scan, R_HOME.
    Each candidate is verified with --version before being returned."""
    import subprocess as _sp
    import shutil as _sh

    def _test(rscript):
        """Smoke test: does this Rscript actually run?"""
        try:
            r = _sp.run([rscript, "--version"], capture_output=True, timeout=15)
            return r.returncode == 0
        except Exception:
            return False

    candidates = []

    # 1. Explicit RSCRIPT_PATH
    env_r = os.environ.get("RSCRIPT_PATH", "")
    if env_r and os.path.isfile(env_r) and env_r not in candidates:
        candidates.append(env_r)

    # 2. PATH (user active R, highest implicit priority)
    found = _sh.which("Rscript") or _sh.which("Rscript.exe")
    if found and found not in candidates:
        candidates.append(found)

    # 3. Windows Registry (all hives, both bitness)
    try:
        import winreg
        for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            for key_path in [r"SOFTWARE\R-core\R", r"SOFTWARE\WOW6432Node\R-core\R"]:
                try:
                    with winreg.OpenKey(hive, key_path) as key:
                        ip, _ = winreg.QueryValueEx(key, "InstallPath")
                        rs = os.path.join(ip, "bin", "Rscript.exe")
                        if os.path.isfile(rs) and rs not in candidates:
                            candidates.append(rs)
                except (OSError, FileNotFoundError):
                    continue
    except ImportError:
        pass

    # 4. Disk scan: all drives
    import string as _str
    for drive in [d + ":" for d in _str.ascii_uppercase if os.path.exists(d + ":")]:
        for prog in ["Program Files", "Program Files (x86)"]:
            rdir = os.path.join(drive, os.sep, prog, "R")
            if not os.path.isdir(rdir):
                continue
            try:
                for ver in sorted(os.listdir(rdir), reverse=True):
                    rs = os.path.join(rdir, ver, "bin", "Rscript.exe")
                    if os.path.isfile(rs) and rs not in candidates:
                        candidates.append(rs)
            except OSError:
                continue

    # 5. R_HOME
    r_home = os.environ.get("R_HOME", "")
    if r_home:
        rs = os.path.join(r_home, "bin", "Rscript.exe")
        if os.path.isfile(rs) and rs not in candidates:
            candidates.append(rs)

    if not candidates:
        raise FileNotFoundError(
            "Rscript.exe not found. Install R from https://cran.r-project.org"
        )

    # Test each candidate, return first working one
    failed = []
    for rs in candidates:
        if _test(rs):
            return rs
        failed.append(rs)

    raise FileNotFoundError(
        "No working R installation found. Tested candidates:\n" +
        "\n".join("  [FAILED] " + rs for rs in failed) +
        "\n\nAll failed --version check. Check R installation integrity."
    )
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

    cmd = [_find_rscript(), str(_DIFFEXP_R),
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
        r_stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
        r_stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
        if r_stdout:
            print(r_stdout)
        if r_stderr:
            print(r_stderr, file=sys.stderr)
        # Also print a combined diagnostic to stderr for agent capture
        if result.returncode != 0 and (r_stdout or r_stderr):
            print(f"\n[Rscript exit {result.returncode}]", file=sys.stderr)
            if r_stderr:
                print(r_stderr, file=sys.stderr)
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"diffexp analysis timed out after {_DEFAULT_TIMEOUT}s", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())