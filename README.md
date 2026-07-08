# BioSherpa

Bioinformatics Agent Hub -- reproducible, auditable analysis pipelines via MCP (Model Context Protocol) and fixed scripts.

## Current Version: 0.0.2

### Agents

| Agent | Analysis | Tools | Status |
|---|---|---|---|
| Transcriptome | DESeq2 differential expression | `deseq2_analysis` | ✅ v0.0.1 |
| Enrichment | GO + KEGG pathway enrichment | `go_enrichment`, `kegg_enrichment` | ✅ v0.1.0 |
| PubMed | Literature search | `pubmed_search` | ✅ v0.1.0 |

### Outputs

| Agent | Output Files |
|---|---|
| Transcriptome | `deseq2_results.csv`, `volcano.png`, `pca.png`, `ma.png`, `summary.json` |
| Enrichment | `go_enrichment_bp/mf/cc.csv`, `kegg_enrichment.csv`, bar plots, dot plots |
| PubMed | `pubmed_results.csv` (Title, Authors, Journal, Abstract, PMID, DOI) |

## Architecture

```
OpenClaw (MCP Client)
  |  JSON-RPC over stdio
  v
biosherpa-gateway-skill/scripts/mcp_server.py   (MCP Server)
  |  tools/list -> fetch from GitHub Registry
  |  tools/call -> download agent -> run_agent.py
  v
biosherpa-hub/agents/{agent}/agent.py            (Agent = Pipeline Guardian)
  |  validate -> plan -> execute -> summarize
  v
biosherpa-hub/tools/{tool}/handler.py            (Thin dispatch)
  |  subprocess -> Rscript
  v
biosherpa-hub/tools/{tool}/scripts/{script}.R    (Fixed pipeline)
```

### Design Principles

- **Agent** = validates, executes, summarizes. Never generates code.
- **Skill** = on-demand playbook loaded by LLM only when needed.
- **Handler** = thin wrapper, no analysis logic.
- **Script** = fixed, auditable R/Python pipeline.
- **Registry** = GitHub-hosted YAML index, no hardcoded agent names.

## Project Structure

```
F:\BioSherpa\RD\
├── biosherpa-gateway-skill/      MCP Gateway for OpenClaw
│   ├── SKILL.md                  Skill trigger + MCP config
│   └── scripts/mcp_server.py     JSON-RPC MCP Server
├── biosherpa-hub/                Agent + Tool Repository
│   ├── core_types.py             Self-contained type system
│   ├── run_agent.py              Subprocess agent entry point
│   ├── manifest.yaml
│   ├── agents/
│   │   ├── transcriptome.agent.md    Agent definition (single file)
│   │   ├── enrichment.agent.md
│   │   ├── pubmed.agent.md
│   │   ├── transcriptome/           agent.py + tool_runner.py
│   │   ├── enrichment/              
│   │   └── pubmed/
│   ├── tools/
│   │   ├── deseq2_analysis/         handler.py + deseq2.R
│   │   ├── go_enrichment/            handler.py + go_enrichment.R
│   │   ├── kegg_enrichment/          handler.py + kegg_enrichment.R
│   │   └── pubmed_search/            handler.py (pure Python)
│   └── skills/
│       ├── deseq2.skill.md
│       ├── go.skill.md
│       ├── kegg.skill.md
│       └── pubmed.skill.md
└── registry/registry.yaml         Agent index (public)
```

## Prerequisites

- Python >= 3.10 + pyyaml
- R >= 4.2 with Rscript on PATH
- R packages: DESeq2, EnhancedVolcano, ggplot2, clusterProfiler, org.Hs.eg.db, enrichplot, optparse, jsonlite

## OpenClaw Integration

1. Place `biosherpa-gateway-skill/` in OpenClaw skills directory
2. SKILL.md auto-discovers the MCP server via metadata
3. Register MCP: `openclaw mcp add biosherpa`
4. Tools appear automatically: transcriptome, enrichment, pubmed, load_biosherpa_skill

## Quick Test

```bash
# Test DESeq2 directly
cd biosherpa-hub
python run_agent.py --agent transcriptome \
  --params '{"counts_file":"examples/transcriptome/counts.csv","metadata_file":"examples/transcriptome/metadata.csv","design_formula":"~condition","contrast_variable":"condition","treatment_group":"treated","control_group":"control","output_dir":"./output"}'

# Test PubMed search
python run_agent.py --agent pubmed \
  --params '{"query":"BRCA1 breast cancer","max_results":10,"output_dir":"./pubmed_out"}'
```
