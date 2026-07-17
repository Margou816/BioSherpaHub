"""DESeq2 analysis handler -- thin dispatch layer.

Validates inputs, constructs the Rscript command, invokes the fixed R script,
and collects output file paths. Contains no analysis logic.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
import sys as _sys
_HUB = __import__("pathlib").Path(__file__).resolve().parent.parent.parent
_sys.path.insert(0, str(_HUB))
from shared import find_rscript
del _sys



from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DESEQ2_R = Path("scripts") / "deseq2.R"
_DEFAULT_TIMEOUT = 600  # seconds

_EXPECTED_OUTPUTS = [
    "deseq2_results.csv",
    "volcano.png",
    "pca.png",
    "ma.png",
    "summary.json",
]

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_inputs(
    counts_file: Path,
    metadata_file: Path,
    output_dir: Path,
    alpha: float,
    lfc_threshold: float,
) -> Dict[str, Path]:
    """Validate input paths and parameters. Returns resolved absolute paths.

    Raises FileNotFoundError if any required input file is missing.
    Raises ValueError if numeric parameters are out of range.
    """
    counts = counts_file.resolve()
    metadata = metadata_file.resolve()
    output = output_dir.resolve()

    if not counts.is_file():
        raise FileNotFoundError(f"Counts file not found: {counts}")
    if not metadata.is_file():
        raise FileNotFoundError(f"Metadata file not found: {metadata}")

    if not (0 < alpha <= 1):
        raise ValueError(f"alpha must be in (0, 1], got {alpha}")
    if lfc_threshold < 0:
        raise ValueError(f"lfc_threshold must be >= 0, got {lfc_threshold}")

    # Quick header check -- count matrix first col should be gene IDs
    _check_counts_header(counts)
    _check_metadata_header(metadata)

    return {"counts": counts, "metadata": metadata, "output": output}

def _check_counts_header(path: Path) -> None:
    """Verify the counts file (CSV or TSV) has at least a gene-id column + one sample column."""
    with path.open("r", encoding="utf-8") as fh:
        header = fh.readline().strip()
    delim = "\t" if "\t" in header else ","
    cols = [c.strip().strip('"') for c in header.split(delim)]
    if len(cols) < 2:
        raise ValueError(
            f"Counts file header has only {len(cols)} column(s); "
            f"expected gene-id column + at least one sample column. Detected delimiter: {repr(delim)}"
        )

def _check_metadata_header(path: Path) -> None:
    """Verify the metadata file (CSV or TSV) has at least a sample-id column + one grouping column."""
    with path.open("r", encoding="utf-8") as fh:
        header = fh.readline().strip()
    delim = "\t" if "\t" in header else ","
    cols = [c.strip().strip('"') for c in header.split(delim)]
    if len(cols) < 2:
        raise ValueError(
            f"Metadata file header has only {len(cols)} column(s); "
            "expected sample-id column + at least one grouping column."
        )

# ---------------------------------------------------------------------------
# Command building
# ---------------------------------------------------------------------------

def build_command(
    counts_file: Path,
    metadata_file: Path,
    design_formula: str,
    contrast_variable: str,
    treatment_group: str,
    control_group: str,
    output_dir: Path,
    alpha: float,
    lfc_threshold: float,
) -> List[str]:
    """Construct the Rscript command-line argument list."""
    # Resolve script path relative to BIOSHERPA_HOME or the handler's tool directory
    biosherpa_home = Path(__file__).resolve().parent.parent.parent
    script_path = biosherpa_home / "tools" / "deseq2_analysis" / _DESEQ2_R
    return [
        "Rscript",
        str(script_path),
        "--counts", str(counts_file),
        "--metadata", str(metadata_file),
        "--design", design_formula,
        "--contrast-variable", contrast_variable,
        "--treatment", treatment_group,
        "--control", control_group,
        "--output-dir", str(output_dir),
        "--alpha", str(alpha),
        "--lfc-threshold", str(lfc_threshold),
    ]

# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def run_analysis(
    cmd: List[str],
    timeout: int = _DEFAULT_TIMEOUT,
    encoding: str = "utf-8",
    errors: str = "replace",
) -> subprocess.CompletedProcess:
    """Run the DESeq2 R script via subprocess with UTF-8 encoding."""
    return subprocess.run(
        cmd,
        capture_output=True,
        encoding=encoding,
        errors=errors,
        text=False,
        timeout=timeout
    )

# ---------------------------------------------------------------------------
# Output collection
# ---------------------------------------------------------------------------

def collect_outputs(output_dir: Path) -> Dict[str, Path]:
    """Scan output_dir for expected outputs and return a name -> Path mapping.

    Raises FileNotFoundError if any expected output is missing.
    """
    result: Dict[str, Path] = {}
    for fname in _EXPECTED_OUTPUTS:
        fpath = output_dir / fname
        if not fpath.is_file():
            raise FileNotFoundError(
                f"Expected output file not produced: {fpath}"
            )
        result[fname] = fpath

    # Optionally read summary.json and attach its content
    summary_path = output_dir / "summary.json"
    if summary_path.is_file():
        with summary_path.open("r", encoding="utf-8") as fh:
            try:
                summary_data = json.load(fh)
                result["_summary"] = summary_data  # type: ignore[assignment]
            except json.JSONDecodeError:
                pass

    return result

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="BioSherpa DESeq2 differential expression analysis handler"
    )
    parser.add_argument(
        "--counts-file", required=True, type=Path,
        help="Path to gene count matrix CSV (genes=rows, samples=columns)"
    )
    parser.add_argument(
        "--metadata-file", required=True, type=Path,
        help="Path to sample metadata CSV"
    )
    parser.add_argument(
        "--design-formula", required=True, type=str,
        help="DESeq2 design formula, e.g. '~ condition'"
    )
    parser.add_argument(
        "--contrast-variable", required=True, type=str,
        help="Variable name for the contrast"
    )
    parser.add_argument(
        "--treatment-group", required=True, type=str,
        help="Treatment/experimental group label"
    )
    parser.add_argument(
        "--control-group", required=True, type=str,
        help="Control/reference group label"
    )
    parser.add_argument(
        "--output-dir", required=True, type=Path,
        help="Directory for output files"
    )
    parser.add_argument(
        "--alpha", type=float, default=0.05,
        help="Adjusted p-value cutoff (default: 0.05)"
    )
    parser.add_argument(
        "--lfc-threshold", type=float, default=1.0,
        help="Absolute log2FC threshold (default: 1.0)"
    )

    args = parser.parse_args(argv)

    try:
        # 1. Validate inputs
        paths = validate_inputs(
            counts_file=Path(args.counts_file),
            metadata_file=Path(args.metadata_file),
            output_dir=Path(args.output_dir),
            alpha=args.alpha,
            lfc_threshold=args.lfc_threshold,
        )

        # 2. Ensure output directory exists
        paths["output"].mkdir(parents=True, exist_ok=True)

        # 3. Build command
        cmd = build_command(
            counts_file=paths["counts"],
            metadata_file=paths["metadata"],
            design_formula=args.design_formula,
            contrast_variable=args.contrast_variable,
            treatment_group=args.treatment_group,
            control_group=args.control_group,
            output_dir=paths["output"],
            alpha=args.alpha,
            lfc_threshold=args.lfc_threshold,
        )

        print(f"[BioSherpa] Running: {' '.join(cmd)}")

        # 4. Run analysis
        result = run_analysis(cmd, encoding="utf-8", errors="replace")
        stdout_text = result.stdout or ""
        stderr_text = result.stderr or ""
        if stdout_text:
            print(stdout_text)
        if stderr_text:
            print(stderr_text, file=sys.stderr)

        # 5. Collect outputs
        outputs = collect_outputs(paths["output"])
        print(f"\n[BioSherpa] Analysis complete. Outputs:")
        for name, fpath in outputs.items():
            if name == "_summary":
                print(f"  summary: {fpath}")
            else:
                print(f"  {name}: {fpath}")

        return 0

    except (FileNotFoundError, ValueError) as exc:
        print(f"[BioSherpa] Error: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"[BioSherpa] R script failed (exit {exc.returncode}):", file=sys.stderr)
        stdout_text = exc.stdout.decode("utf-8", errors="replace") if exc.stdout else ""
        stderr_text = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""
        if stdout_text:
            print(stdout_text, file=sys.stderr)
        if stderr_text:
            print(stderr_text, file=sys.stderr)
        return exc.returncode
    except subprocess.TimeoutExpired as exc:
        print(f"[BioSherpa] Analysis timed out after {exc.timeout}s", file=sys.stderr)
        if exc.stdout:
            print(exc.stdout.decode("utf-8", errors="replace"), file=sys.stderr)
        if exc.stderr:
            print(exc.stderr.decode("utf-8", errors="replace"), file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
