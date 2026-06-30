---
name: biosherpa
description: BioSherpa bioinformatics agent hub. Routes bioinformatics requests (RNA-seq, differential expression, GO, KEGG, enrichment, PPI, single-cell, Seurat, CellChat, Monocle, trajectory) to the appropriate analysis agent via the BioSherpa Registry. Use when the user requests any kind of bioinformatics or computational biology analysis.
user-invocable: true
---

# BioSherpa -- Bioinformatics Agent Hub

BioSherpa is a dynamic agent hub that connects OpenClaw to bioinformatics analysis agents. It handles agent discovery, loading, execution, and cleanup automatically.

## When to Activate

Route the following requests to BioSherpa:

- **Transcriptome:** Bulk RNA-seq, differential expression (DESeq2), volcano plots, PCA, MA plots
- **Enrichment:** GO, KEGG, GSEA, pathway analysis
- **PPI:** Protein-protein interaction networks
- **Single-cell:** scRNA-seq, Seurat, CellChat, Monocle, trajectory analysis, marker detection, annotation
- **Spatial:** Spatial transcriptomics

Keywords that trigger this skill: rna-seq, rnaseq, deseq2, differential expression, deg, transcriptome, go, kegg, gsea, enrichment, ppi, single-cell, scrna-seq, seurat, cellchat, monocle, trajectory, spatial transcriptomics, marker gene, annotation, bulk rna, gene expression

## How It Works

1. Receive bioinformatics request from user
2. Search BioSherpa Registry for matching agent
3. Download agent package if needed (cached for reuse)
4. Load and execute agent in isolated sandbox
5. Return results (tables, plots, summaries) to user
6. Release agent resources after execution

## Running BioSherpa

```bash
python -c "
from pathlib import Path
import sys
sys.path.insert(0, r'F:\BioSherpa\RD')

from biosherpa_core.context.request import Request
from biosherpa_core.context.project import Project
from biosherpa_openclaw.gateway.dispatcher import Dispatcher

dispatcher = Dispatcher.from_github(repo_url='https://github.com/YOUR_ORG/biosherpa-registry')
result = dispatcher.dispatch('YOUR_QUERY', workspace_path=Path.cwd())
print(result)
"
```

## Configuration

- **Registry URL:** Configured in dispatcher initialization
- **Cache directory:** `~/.biosherpa/cache` (configurable)
- **R library path:** `C:/tmp/Rlib` (required for R-based agents)

## Important Notes

- BioSherpa agents NEVER generate code dynamically
- All analyses use fixed, auditable scripts
- Agents are stateless and released after execution
- The registry abstracts away backend details
