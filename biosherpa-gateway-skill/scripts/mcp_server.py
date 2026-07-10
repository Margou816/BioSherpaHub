#!/usr/bin/env python
"""BioSherpa MCP Server -- Agent-Skill-Tool three-level navigation over JSON-RPC stdio.

Exposes 3 MCP tools:
  find_biosherpa_agent  -- search registry keywords, return agent.md persona
  load_biosherpa_skill  -- load skill.md for a specific agent+skill
  run_biosherpa_tool    -- execute a tool via the agent dispatcher

Set BIOSHERPA_LOCAL=1 to use local F:\BioSherpa\RD files instead of GitHub.
"""
from __future__ import annotations
import json, sys, subprocess, io, os, zipfile, urllib.request, shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

REGISTRY_URL = "https://raw.githubusercontent.com/Margou816/BioSherpaHub/main/registry/registry.yaml"
LOCAL_HUB = Path(__file__).resolve().parent.parent.parent / "biosherpa-hub"
LOCAL_REGISTRY = Path(__file__).resolve().parent.parent.parent / "registry" / "registry.yaml"
CACHE_ROOT = Path.home() / ".biosherpa" / "cache"
AGENT_TIMEOUT = 600

_LOCAL = bool(os.environ.get("BIOSHERPA_LOCAL", ""))


def fetch_registry() -> List[Dict[str, Any]]:
    if _LOCAL and LOCAL_REGISTRY.is_file():
        import yaml
        return yaml.safe_load(LOCAL_REGISTRY.read_text(encoding="utf-8")).get("entries", [])
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
    if dest.exists():
        shutil.rmtree(dest)
    tmp = CACHE_ROOT / f"dl_{aid}"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    repo_url = "https://github.com/Margou816/BioSherpaHub"
    zurl = f"{repo_url}/archive/refs/heads/main.zip"
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
        if "run_agent.py" in fs:
            return Path(rp) / "run_agent.py"
    raise FileNotFoundError(f"No run_agent.py in {pkg}")


def _read_local_md(subdir: str, filename: str) -> Optional[Path]:
    if not _LOCAL or not LOCAL_HUB.is_dir():
        return None
    path = LOCAL_HUB / subdir / filename
    return path if path.is_file() else None


def _find_md(pkg: Path, subdir: str, filename: str) -> Optional[Path]:
    local = _read_local_md(subdir, filename)
    if local:
        return local
    for rp, _, fs in os.walk(str(pkg)):
        target = Path(rp) / subdir / filename
        if target.is_file():
            return target
        direct = Path(rp) / filename
        if direct.is_file() and subdir in str(rp):
            return direct
    for rp, _, fs in os.walk(str(pkg)):
        if filename in fs:
            return Path(rp) / filename
    return None


def build_tools() -> List[Dict[str, Any]]:
    return [
        {
            "name": "find_biosherpa_agent",
            "description": "Search for a BioSherpa agent matching your bioinformatics needs. Returns the agent persona (agent.md) which describes what the agent can do, available skills, and how to interact with it.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query matching agent keywords (e.g. 'rna-seq differential expression', 'go enrichment', 'pubmed literature')"}
                },
                "required": ["query"]
            },
        },
        {
            "name": "load_biosherpa_skill",
            "description": "Load a skill module for a specific agent. The skill provides detailed parameter guidance, file format requirements, and tells you which tool to call.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "Agent id from find_biosherpa_agent result (e.g. 'transcriptome', 'enrichment', 'pubmed')"},
                    "skill_name": {"type": "string", "description": "Skill name listed in the agent persona (e.g. 'deseq2', 'go', 'kegg', 'pubmed')"}
                },
                "required": ["agent_id", "skill_name"]
            },
        },
        {
            "name": "run_biosherpa_tool",
            "description": "Execute a bioinformatics analysis tool. The tool name comes from the skill's documentation. Provide all required parameters from the skill's parameter table.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "Agent id (e.g. 'transcriptome', 'enrichment', 'pubmed')"},
                    "tool_name": {"type": "string", "description": "Tool name from the skill documentation (e.g. 'deseq2_analysis', 'go_enrichment', 'kegg_enrichment', 'pubmed_search')"},
                    "params": {"type": "object", "description": "Tool parameters as specified in the skill's parameter table"},
                    "output_dir": {"type": "string", "description": "Output directory (default: biosherpa_output)"},
                    "workspace": {"type": "string", "description": "OpenClaw workspace directory"}
                },
                "required": ["agent_id", "tool_name", "params"]
            },
        },
    ]


def handle_find_agent(query: str) -> List[Dict[str, Any]]:
    entries = fetch_registry()
    query_lower = query.lower()
    matches = []
    for entry in entries:
        keywords = entry.get("keywords", [])
        if any(kw in query_lower for kw in keywords):
            matches.append(entry)
    if not matches:
        available = ", ".join(f"{e['id']} ({e.get('name','')})" for e in entries)
        return [{"type": "text", "text": (
            f"No agent found for query: '{query}'.\n\n"
            f"Available agents: {available}\n\n"
            f"Try a broader query or use one of the agent ids directly."
        )}]
    items: List[Dict[str, Any]] = []
    for entry in matches:
        if _LOCAL and LOCAL_HUB.is_dir():
            pkg = LOCAL_HUB
        else:
            pkg = get_cached(entry["id"], entry["version"])
            if pkg is None:
                pkg = download_agent(entry.get("repository", ""), entry["id"], entry["version"])
        agent_md = _find_md(pkg, "agents", f"{entry['id']}.agent.md")
        if agent_md:
            text = agent_md.read_text(encoding="utf-8", errors="replace")
            items.append({"type": "text", "text": f"=== Agent: {entry['id']} ({entry.get('name','')}) v{entry.get('version','')} ===\n{text}"})
        else:
            items.append({"type": "text", "text": json.dumps(entry, indent=2)})
    return items


def handle_load_skill(agent_id: str, skill_name: str) -> List[Dict[str, Any]]:
    for entry in fetch_registry():
        if entry["id"] != agent_id:
            continue
        skills = entry.get("skills", [])
        if skill_name not in skills:
            return [{"type": "text", "text": json.dumps({
                "status": "no_match",
                "summary": f"Skill '{skill_name}' not available for agent '{agent_id}'. Available: {skills}"
            })}]
        if _LOCAL and LOCAL_HUB.is_dir():
            pkg = LOCAL_HUB
        else:
            pkg = get_cached(entry["id"], entry["version"]) or download_agent(entry.get("repository", ""), entry["id"], entry["version"])
        skill_md = _find_md(pkg, "skills", f"{skill_name}.skill.md")
        if skill_md:
            return [{"type": "text", "text": skill_md.read_text(encoding="utf-8", errors="replace")}]
        return [{"type": "text", "text": json.dumps({
            "status": "no_match",
            "summary": f"Skill file '{skill_name}.skill.md' not found"
        })}]
    return [{"type": "text", "text": json.dumps({
        "status": "no_match",
        "summary": f"Agent '{agent_id}' not found in registry"
    })}]


def handle_run_tool(agent_id: str, tool_name: str, params: Dict[str, Any],
                    workspace: str = "", output_dir: str = "biosherpa_output") -> List[Dict[str, Any]]:
    for entry in fetch_registry():
        if entry["id"] != agent_id:
            continue
        if _LOCAL and LOCAL_HUB.is_dir():
            pkg = LOCAL_HUB
            runner = LOCAL_HUB / "run_agent.py"
        else:
            pkg = get_cached(entry["id"], entry["version"])
            if pkg is None:
                pkg = download_agent(entry.get("repository", ""), entry["id"], entry["version"])
            runner = find_run_agent(pkg)
        outdir = Path(output_dir)
        # Merge output_dir from params if not explicitly passed at top level
        if output_dir == "biosherpa_output" and "output_dir" in params:
            output_dir = str(params["output_dir"])
            outdir = Path(output_dir)
        if "workspace" not in params and workspace:
            params["workspace"] = workspace
        # Resolve relative input file paths against workspace
        _file_keys = ["counts_file", "metadata_file", "expr_file", "deg_file"]
        for key in _file_keys:
            val = params.get(key, "")
            if val and not Path(val).is_absolute() and workspace:
                params[key] = str(Path(workspace) / val)
        # Recalculate outdir after potential param merge
        outdir = Path(output_dir)
        if workspace and not outdir.is_absolute():
            outdir = Path(workspace) / outdir
        outdir.mkdir(parents=True, exist_ok=True)
        params["output_dir"] = str(outdir)
        cmd = [
            sys.executable, str(runner),
            "--agent", agent_id, "--tool", tool_name,
            "--params", json.dumps(params),
        ]
        r_libs = os.environ.get("R_LIBS_USER", "")
        if r_libs:
            cmd.extend(["--r-libs-user", r_libs])
        result = subprocess.run(cmd, capture_output=True, timeout=AGENT_TIMEOUT, cwd=str(pkg))
        stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
        items = collect_outputs(outdir)
        if stderr:
            items.insert(0, {"type": "text", "text": f"=== DIAGNOSTIC (stderr) ===\n{stderr}"})
        if result.returncode != 0:
            items.insert(0, {"type": "text", "text": f"Exit code: {result.returncode}"})
        items.append({"type": "text", "text": _location_summary(outdir)})
        return items
    return [{"type": "text", "text": json.dumps({
        "status": "no_match", "summary": f"Agent '{agent_id}' not found in registry"
    })}]


def collect_outputs(outdir: Path) -> List[Dict[str, Any]]:
    import base64
    items: List[Dict[str, Any]] = []
    for f in sorted(outdir.iterdir()):
        if not f.is_file():
            continue
        if f.suffix == ".csv":
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
            total = len(lines)
            preview = "\n".join(lines[:20])
            suffix = f"\n... ({total - 20} more rows)" if total > 20 else ""
            items.append({"type": "text", "text": (
                f"=== {f.name} ({total} rows, {f.stat().st_size:,} bytes) ===\n"
                f"[Full path: {f.resolve()}]\n{preview}{suffix}"
            )})
        elif f.suffix == ".png":
            b64 = base64.b64encode(f.read_bytes()).decode("ascii")
            items.append({"type": "image", "data": b64, "mimeType": "image/png"})
        elif f.suffix == ".json":
            text = f.read_text(encoding="utf-8", errors="replace")
            preview = text[:500]
            suffix = "..." if len(text) > 500 else ""
            items.append({"type": "text", "text": (
                f"=== {f.name} ({f.stat().st_size:,} bytes) ===\n"
                f"[Full path: {f.resolve()}]\n{preview}{suffix}"
            )})
        else:
            items.append({"type": "text", "text": (
                f"Output: {f.name} ({f.stat().st_size:,} bytes) -> {f.resolve()}"
            )})
    return items


def _location_summary(outdir: Path) -> str:
    files = sorted(f for f in outdir.iterdir() if f.is_file())
    if not files:
        return f"[BioSherpa] No output files found in {outdir.resolve()}"
    lines = [f"[BioSherpa] {len(files)} output file(s) saved to {outdir.resolve()}:"]
    for f in files:
        lines.append(f"  - {f.name} ({f.stat().st_size:,} bytes)")
    return "\n".join(lines)


def execute_tool(tool_name: str, args: Dict[str, Any]) -> List[Dict[str, Any]]:
    if tool_name == "find_biosherpa_agent":
        return handle_find_agent(args.get("query", ""))
    elif tool_name == "load_biosherpa_skill":
        return handle_load_skill(args.get("agent_id", ""), args.get("skill_name", ""))
    elif tool_name == "run_biosherpa_tool":
        params = args.get("params", {})
        if isinstance(params, str):
            params = json.loads(params)
        return handle_run_tool(
            args.get("agent_id", ""), args.get("tool_name", ""), params,
            workspace=args.get("workspace", ""),
            output_dir=args.get("output_dir", "biosherpa_output"),
        )
    return [{"type": "text", "text": json.dumps({"status": "no_match", "summary": f"Unknown tool: {tool_name}"})}]


def handle_request(req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    rid = req.get("id")
    method = req.get("method", "")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "biosherpa-mcp", "version": "0.1.0"}}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": build_tools()}}
    if method == "tools/call":
        p = req.get("params", {})
        content = execute_tool(p.get("name", ""), p.get("arguments", {}))
        return {"jsonrpc": "2.0", "id": rid, "result": {"content": content}}
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Unknown method: {method}"}}


def main() -> None:
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try: request = json.loads(line)
        except json.JSONDecodeError: continue
        response = handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
