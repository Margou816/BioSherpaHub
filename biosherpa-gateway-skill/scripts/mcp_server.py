#!/usr/bin/env python3
"""BioSherpa MCP Server ��?Zero biosherpa_core dependency. JSON-RPC over stdio."""
from __future__ import annotations
import json, sys, subprocess, io, os, zipfile, urllib.request, shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

REGISTRY_URL = "https://raw.githubusercontent.com/Margou816/BioSherpaHub/main/registry/registry.yaml"
CACHE_ROOT = Path.home() / ".biosherpa" / "cache"
AGENT_TIMEOUT = 600


def fetch_registry() -> List[Dict[str, Any]]:
    import yaml
    with urllib.request.urlopen(REGISTRY_URL, timeout=30) as r:
        data = yaml.safe_load(r.read().decode("utf-8"))
    return data.get("entries", [])


def cache_dir(aid: str, ver: str) -> Path:
    return CACHE_ROOT / f"{aid}@{ver}"


def get_cached(aid: str, ver: str) -> Optional[Path]:
    d = cache_dir(aid, ver)
    return d if (d / "manifest.yaml").exists() else None


def download_agent(repo: str, aid: str, ver: str) -> Path:
    dest = cache_dir(aid, ver)
    if dest.exists(): shutil.rmtree(dest)
    tmp = CACHE_ROOT / f"dl_{aid}"
    if tmp.exists(): shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    zurl = f"{repo.rstrip('/')}/archive/refs/heads/main.zip"
    with urllib.request.urlopen(zurl, timeout=120) as r:
        with zipfile.ZipFile(io.BytesIO(r.read())) as zf:
            zf.extractall(tmp)
    items = list(tmp.iterdir())
    src = items[0] if items else tmp
    shutil.copytree(src, dest)
    shutil.rmtree(tmp)
    return dest


def find_run_agent(pkg: Path) -> Path:
    for rp, _, fs in os.walk(str(pkg)):
        if "run_agent.py" in fs: return Path(rp) / "run_agent.py"
    raise FileNotFoundError(f"No run_agent.py in {pkg}")


def collect_outputs(outdir: Path) -> List[Dict[str, Any]]:
    """Read output files into MCP content items (not just paths).

    CSV files are returned as text content; PNG files as base64-encoded
    image content. This ensures results are visible even when the MCP
    subprocess runs inside a sandbox that isolates the filesystem.
    """
    import base64
    items: List[Dict[str, Any]] = []
    for f in sorted(outdir.iterdir()):
        if not f.is_file():
            continue
        if f.suffix == ".csv":
            text = f.read_text(encoding="utf-8", errors="replace")
            items.append({"type": "text", "text": f"=== {f.name} ===\n{text}"})
        elif f.suffix == ".png":
            b64 = base64.b64encode(f.read_bytes()).decode("ascii")
            items.append({"type": "image", "data": b64, "mimeType": "image/png"})
        elif f.suffix == ".json":
            text = f.read_text(encoding="utf-8", errors="replace")
            items.append({"type": "text", "text": f"=== {f.name} ===\n{text}"})
        else:
            items.append({"type": "text", "text": f"Output: {f.name} ({f.stat().st_size} bytes)"})
    return items
def build_tools() -> List[Dict[str, Any]]:
    tools = []
    for entry in fetch_registry():
        tools.append({
            "name": entry["id"].replace("-","_").replace(".","_"),
            "description": entry.get("description",""),
            "inputSchema": {"type":"object","properties":{
                "counts_file":{"type":"string","description":"Gene count matrix CSV path"},
                "metadata_file":{"type":"string","description":"Sample metadata CSV path"},
                "design_formula":{"type":"string","description":"e.g. ~condition"},
                "contrast_variable":{"type":"string","description":"Variable for contrast"},
                "treatment_group":{"type":"string","description":"Treatment group label"},
                "control_group":{"type":"string","description":"Control group label"},
                "output_dir":{"type":"string","description":"Output directory"},
                "workspace":{"type":"string","description":"OpenClaw workspace directory — output files are saved here"},
                "alpha":{"type":"number","description":"padj cutoff, default 0.05"},
                "lfc_threshold":{"type":"number","description":"log2FC threshold, default 1.0"},
            },"required":["counts_file","metadata_file","design_formula","contrast_variable","treatment_group","control_group","output_dir"]},
        })
        tools.append({
            "name": "load_biosherpa_skill",
            "description": "Load a BioSherpa skill playbook for parameter guidance and result interpretation. Available skills: deseq2.",
            "inputSchema": {"type":"object","properties":{
                "skill_name": {"type":"string","description":"Name of the skill to load (e.g. deseq2)"},
            },"required":["skill_name"]},
        })
    return tools


def execute_tool(tool_name: str, args: Dict[str, Any]) -> List[Dict[str, Any]]:
    if tool_name == "load_biosherpa_skill":
        return _load_skill(args.get("skill_name", ""))

    for entry in fetch_registry():
        mcp_name = entry["id"].replace("-","_").replace(".","_")
        if mcp_name != tool_name:
            continue
        pkg = get_cached(entry["id"], entry["version"])
        if pkg is None:
            pkg = download_agent(entry["repository"], entry["id"], entry["version"])
        runner = find_run_agent(pkg)
        params_json = json.dumps(args)
        # Resolve output_dir relative to workspace so files land on host
        outdir = Path(args.get("output_dir", "biosherpa_output"))
        ws = args.get("workspace", "")
        if ws and not outdir.is_absolute():
            outdir = Path(ws) / outdir
        args["output_dir"] = str(outdir)
        params_json = json.dumps(args)
        cmd = [sys.executable, str(runner),
               "--agent", entry["id"],
               "--params", params_json]
        env = os.environ.copy()
        subprocess.run(cmd, capture_output=True,
                                timeout=AGENT_TIMEOUT, env=env,
                                cwd=str(pkg))
        outdir = Path(args.get("output_dir", "biosherpa_output"))
        items = collect_outputs(outdir)
        items.append({"type": "text", "text": _build_save_script(outdir)})
        return items
    return [{"type":"text","text":json.dumps(
        {"status":"no_match","summary":"No agent found"})}]



def _load_skill(skill_name: str) -> List[Dict[str, Any]]:
    builtin = {"deseq2": "skills/deseq2.skill.md"}
    if skill_name not in builtin:
        return [{"type":"text","text":json.dumps(
            {"status":"no_match","summary":f"Skill '{skill_name}' not found"})}]
    for entry in fetch_registry():
        pkg = get_cached(entry["id"], entry["version"])
        if pkg is None:
            pkg = download_agent(entry["repository"], entry["id"], entry["version"])
        skill_path = pkg / builtin[skill_name]
        if skill_path.exists():
            return [{"type":"text","text":
                skill_path.read_text(encoding="utf-8", errors="replace")}]
    return [{"type":"text","text":json.dumps(
        {"status":"no_match","summary":f"Package for '{skill_name}' not found"})}]


def _build_save_script(outdir: Path) -> str:
    """Build a self-contained Python script with embedded file contents.

    The script does NOT reference sandbox paths — all file data is
    embedded directly. The LLM writes this to workspace via exec
    and runs it to materialize output files on the host.
    """
    import base64
    files = []
    for f in sorted(outdir.iterdir()):
        if not f.is_file(): continue
        if f.suffix in (".csv", ".json"):
            files.append({"n": f.name, "t": "text", "d": f.read_text(encoding="utf-8", errors="replace")})
        elif f.suffix == ".png":
            files.append({"n": f.name, "t": "png", "d": base64.b64encode(f.read_bytes()).decode("ascii")})
    payload = json.dumps(files, ensure_ascii=False)
    return f"""SAVE_SCRIPT (write to workspace as _save.py, then run: python _save.py)
import base64, json, pathlib, os
ws = os.environ.get("WORKSPACE", ".")
out = pathlib.Path(ws) / "biosherpa_output"
out.mkdir(parents=True, exist_ok=True)
files = json.loads(r'''{payload}''')
for f in files:
    p = out / f["n"]
    if f["t"] == "text":
        p.write_text(f["d"], encoding="utf-8")
    else:
        p.write_bytes(base64.b64decode(f["d"]))
print(f"Saved {{len(files)}} files to {{out}}")
"""


def handle_request(req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    rid = req.get("id"); method = req.get("method", "")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "biosherpa-mcp", "version": "0.1.0"}}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": build_tools()}}
    if method == "tools/call":
        p = req.get("params", {}); name = p.get("name", ""); args = p.get("arguments", {})
        content = execute_tool(name, args)
        return {"jsonrpc": "2.0", "id": rid, "result": {"content": content}}
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Unknown method: {method}"}}


def main() -> None:
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
