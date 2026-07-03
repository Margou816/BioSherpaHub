#!/usr/bin/env python3
"""BioSherpa Gateway — single entry point invoked by the OpenClaw skill.

Called via SKILL.md instructions:
    python main.py --query "user request" --workspace /path

Contains ZERO biological logic. Only routes to BioSherpa Core.
"""
from __future__ import annotations
import argparse, json, sys, gc
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE  # all modules co-located in scripts/
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import Config
from cache import SkillCache
from registry_client import RegistryClient
from loader import SkillLoader
from dispatcher import Dispatch
from response import format_response, format_no_match


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BioSherpa Gateway")
    parser.add_argument("--query", required=True, help="User request")
    parser.add_argument("--workspace", default=".", help="Workspace directory")
    parser.add_argument("--files", nargs="*", default=[], help="Input file paths")
    parser.add_argument("--registry-url", default=None, help="Override registry URL")
    parser.add_argument("--r-libs", default=None, help="Override R library path")
    parser.add_argument("--timeout", type=int, default=600, help="Timeout seconds")
    args = parser.parse_args(argv)

    config = Config()
    if args.registry_url: config.registry_url = args.registry_url
    if args.r_libs: config.r_libs_user = args.r_libs
    config.agent_timeout_seconds = args.timeout

    cache = SkillCache(cache_root=config.cache_path, ttl_seconds=config.cache_ttl_seconds)
    registry = RegistryClient(index_url=config.registry_url)
    loader = SkillLoader(cache=cache, timeout=config.agent_timeout_seconds)

    files = [Path(f) for f in (args.files or [])]
    dispatch = Dispatch(config=config, cache=cache, registry=registry, loader=loader)
    result = dispatch.run(args.query, Path(args.workspace), files)

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0 if result.get("status") not in ("error", "failed") else 1


if __name__ == "__main__":
    sys.exit(main())
