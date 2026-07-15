"""BioSherpa shared utilities -- find_rscript, dispatch_tool.
Used by handlers, agents, and mcp_server to avoid code duplication.
"""
from __future__ import annotations
import os, subprocess, sys, shutil, string
from pathlib import Path
from typing import Any, Dict, List, Optional

IS_WINDOWS = sys.platform == "win32"


# ---------------------------------------------------------------------------
# Rscript discovery (one implementation, shared by all callers)
# ---------------------------------------------------------------------------

def _test_rscript(rscript: str) -> bool:
    """Smoke test: does this Rscript actually run?"""
    try:
        r = subprocess.run([rscript, "--version"], capture_output=True, timeout=15)
        return r.returncode == 0
    except Exception:
        return False


def find_rscript() -> str:
    """Find a working Rscript. Collects ALL candidates, then tests each.
    Priority: RSCRIPT_PATH > PATH > Registry > disk scan > R_HOME.
    Each candidate is verified with --version before being returned.
    """
    candidates: List[str] = []

    # 1. Explicit RSCRIPT_PATH
    env_r = os.environ.get("RSCRIPT_PATH", "")
    if env_r and os.path.isfile(env_r) and env_r not in candidates:
        candidates.append(env_r)

    # 2. PATH (user's active R, highest implicit priority)
    found = shutil.which("Rscript") or (shutil.which("Rscript.exe") if IS_WINDOWS else None)
    if found and found not in candidates:
        candidates.append(found)

    # 3. Windows Registry (all hives, both bitness)
    if IS_WINDOWS:
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

    # 4. Disk scan: all drives, Program Files / Program Files (x86)
    if IS_WINDOWS:
        for drive in [f"{d}:" for d in string.ascii_uppercase if os.path.exists(f"{d}:")]:
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

    # 5. R_HOME environment variable
    r_home = os.environ.get("R_HOME", "")
    if r_home:
        rs = os.path.join(r_home, "bin", "Rscript.exe" if IS_WINDOWS else "Rscript")
        if os.path.isfile(rs) and rs not in candidates:
            candidates.append(rs)

    if not candidates:
        raise FileNotFoundError(
            "Rscript not found. Install R from https://cran.r-project.org\n"
            "Or set RSCRIPT_PATH to the full path of Rscript."
        )

    # Test each candidate, return first working one
    failed: List[str] = []
    for rs in candidates:
        if _test_rscript(rs):
            return rs
        failed.append(rs)

    raise FileNotFoundError(
        f"No working R installation found among {len(candidates)} candidates:\n"
        + "\n".join(f"  [FAILED] {rs}" for rs in failed)
        + "\n\nAll failed --version check. Check R installation integrity."
    )


# ---------------------------------------------------------------------------
# Generic tool dispatcher (one implementation shared by all agents)
# ---------------------------------------------------------------------------

def dispatch_tool(
    agent_name: str,
    tools: Dict[str, Path],
    param_map: Dict[str, Dict[str, str]],
    tool_name: str,
    params: Dict[str, Any],
    timeout: int = 600,
    env_extra: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Dispatch a tool call to its handler and return status JSON.
    
    Args:
        agent_name: Agent id for error messages.
        tools: Dict mapping tool_name -> handler path.
        param_map: Dict mapping tool_name -> {param_key: --cli-flag}.
        tool_name: Name of the tool to run.
        params: Parameter dict from user.
        timeout: Subprocess timeout in seconds.
        env_extra: Extra env vars (e.g., {"R_LIBS_USER": "..."}) added to os.environ.
    
    Returns:
        {"status": "success"|"error", "summary": "...", "stderr": "...", "errors": [...]}
    """
    if tool_name not in tools:
        return {
            "status": "error",
            "summary": f"Unknown tool: {tool_name}",
            "errors": [f"Tool '{tool_name}' not in {agent_name} agent"],
        }

    handler = tools[tool_name]
    mapping = param_map.get(tool_name, {})
    cmd = [sys.executable, str(handler)]

    for key, flag in mapping.items():
        val = params.get(key, "")
        if isinstance(val, bool):
            if val:
                cmd.append(flag)
        elif val != "" and val is not None:
            cmd.extend([flag, str(val)])

    # Ensure output directory exists
    outdir = params.get("output_dir", "biosherpa_output")
    Path(outdir).mkdir(parents=True, exist_ok=True)

    # Build environment
    env = os.environ.copy()
    if env_extra:
        for k, v in env_extra.items():
            if v:
                env[k] = v

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout, env=env)
        stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
        return {
            "status": "success",
            "summary": f"{tool_name} completed (exit {result.returncode})",
            "stderr": stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "summary": f"Tool {tool_name} timed out",
            "errors": [f"Timeout after {timeout}s"],
        }
    except Exception as exc:
        return {"status": "error", "summary": str(exc), "errors": [str(exc)]}