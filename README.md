# BioSherpa

BioSherpa is a bioinformatics AI Agent platform built as an OpenClaw Plugin. It provides reproducible, auditable analysis pipelines for transcriptome data.

## Version 0.0.1 (Current)

Transcriptome differential expression analysis via DESeq2.

**Outputs:** Differential expression CSV, Volcano plot, PCA plot, MA plot, Summary JSON

## Architecture

```
Agent (reasoning) -> Tool (OpenAPI schema) -> Handler (dispatch) -> Script (fixed R)
```

- **Agent** understands user intent and selects the right tool.
- **Skill** provides domain expertise as an OpenClaw skill file.
- **Handler** validates inputs and dispatches to the R script.
- **Script** is a fixed, auditable R pipeline — never AI-generated.

## Project Structure

```
biosherpa-openclaw/
  agents/transcriptome/    Agent personality, prompt, config, skills
  tools/deseq2_analysis/   Tool schema, handler, fixed R script
  examples/transcriptome/  Example input data
  tests/                   Unit tests
```

## Prerequisites

- Python >= 3.10
- R >= 4.2 with Rscript on PATH
- R packages: DESeq2, EnhancedVolcano, ggplot2, optparse, jsonlite (via renv)

## Quick Start

```bash
cd tools/deseq2_analysis/scripts
Rscript -e 'renv::restore()'
cd ../..
python tools/deseq2_analysis/handler.py \
  --counts-file examples/transcriptome/counts.csv \
  --metadata-file examples/transcriptome/metadata.csv \
  --design-formula "~ condition" \
  --contrast-variable condition \
  --treatment-group treated \
  --control-group control \
  --output-dir ./output
```

## OpenClaw Integration

1. Copy skill to `~/.openclaw/plugin-skills/biosherpa-differential-expression/`
2. The agent uses `prompt.md` as its system prompt
3. Tools invoke via shell: `python handler.py ...`
