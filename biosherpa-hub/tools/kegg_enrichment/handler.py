"""KEGG enrichment handler -- thin dispatch to kegg_enrichment.R."""
from __future__ import annotations
import argparse, subprocess, sys, os
from pathlib import Path


def _find_rscript():
    """Locate Rscript.exe using multiple strategies across all possible install locations."""
    import shutil
    # 1. Explicit RSCRIPT_PATH env var (highest priority)
    env_r = os.environ.get("RSCRIPT_PATH", "")
    if env_r and os.path.isfile(env_r):
        return env_r

    # 2. Windows Registry -- R writes InstallPath to HKLM\SOFTWARE\R-core\R
    try:
        import winreg
        for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            for key_path in [r"SOFTWARE\R-core\R", r"SOFTWARE\WOW6432Node\R-core\R"]:
                try:
                    with winreg.OpenKey(hive, key_path) as key:
                        install_path, _ = winreg.QueryValueEx(key, "InstallPath")
                        rscript = os.path.join(install_path, "bin", "Rscript.exe")
                        if os.path.isfile(rscript):
                            return rscript
                except (OSError, FileNotFoundError):
                    continue
    except ImportError:
        pass  # winreg not available on non-Windows

    # 3. Scan all drives for R in Program Files and Program Files (x86)
    import string
    for drive in [f"{d}:" for d in string.ascii_uppercase if os.path.exists(f"{d}:")]:
        for prog in ["Program Files", "Program Files (x86)"]:
            rdir = os.path.join(drive, os.sep, prog, "R")
            if not os.path.isdir(rdir):
                continue
            try:
                versions = sorted(os.listdir(rdir), reverse=True)
            except OSError:
                continue
            for ver in versions:
                rscript = os.path.join(rdir, ver, "bin", "Rscript.exe")
                if os.path.isfile(rscript):
                    return rscript

    # 4. R_HOME environment variable (set by R during installation)
    r_home = os.environ.get("R_HOME", "")
    if r_home:
        rscript = os.path.join(r_home, "bin", "Rscript.exe")
        if os.path.isfile(rscript):
            return rscript

    # 5. PATH fallback
    found = shutil.which("Rscript") or shutil.which("Rscript.exe")
    if found:
        return found

    raise FileNotFoundError(
        "Rscript.exe not found. Install R from https://cran.r-project.org\n"
        "Alternatively, set RSCRIPT_PATH to the full path of Rscript.exe."
    )
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
    cmd = [_find_rscript(), str(_KEGG_R), "--deg-file", str(args.deg_file),
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
