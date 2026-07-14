"""KEGG enrichment handler -- thin dispatch to kegg_enrichment.R."""
from __future__ import annotations
import argparse, subprocess, sys, os
from pathlib import Path


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
