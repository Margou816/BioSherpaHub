# BioSherpa Setup Guide

## Quick Start (Current Machine)

```bash
# 1. Set environment variable (add to system or .bashrc/.zshrc)
set BIOSHERPA_HOME=F:\BioSherpa\RD\biosherpa-openclaw

# 2. Install R packages
set R_LIBS_USER=C:/tmp/Rlib
cd %BIOSHERPA_HOME%\tools\deseq2_analysis\scripts
Rscript -e "if (!require('BiocManager', quietly=TRUE)) install.packages('BiocManager'); BiocManager::install(c('DESeq2','EnhancedVolcano','optparse','jsonlite','ggplot2','ggrepel'))"

# 3. Register OpenClaw skill
mkdir %USERPROFILE%\.openclaw\plugin-skills\biosherpa-differential-expression
copy %BIOSHERPA_HOME%\agents\transcriptome\skills\differential_expression.md %USERPROFILE%\.openclaw\plugin-skills\biosherpa-differential-expression\SKILL.md

# 4. Add to openclaw.json:
#    "biosherpa-differential-expression": {"enabled": true}

# 5. Restart OpenClaw
```

## New Machine Setup

When moving to a new computer:

### 1. Copy the project
Copy the entire `biosherpa-openclaw/` directory to the new machine. Any location works.

### 2. Set BIOSHERPA_HOME
```bash
# Windows (CMD)
setx BIOSHERPA_HOME "C:\path\to\biosherpa-openclaw"

# Windows (PowerShell)
[Environment]::SetEnvironmentVariable("BIOSHERPA_HOME", "C:\path\to\biosherpa-openclaw", "User")

# Linux/Mac
echo 'export BIOSHERPA_HOME=/path/to/biosherpa-openclaw' >> ~/.bashrc
```

### 3. Install R and packages
```bash
# Install R from https://cran.r-project.org/

# Install required packages
cd %BIOSHERPA_HOME%\tools\deseq2_analysis\scripts
Rscript -e "if (!require('BiocManager', quietly=TRUE)) install.packages('BiocManager'); BiocManager::install(c('DESeq2','EnhancedVolcano','optparse','jsonlite','ggplot2','ggrepel'))"
```

### 4. Register OpenClaw skill
```bash
mkdir ~/.openclaw/plugin-skills/biosherpa-differential-expression
cp $BIOSHERPA_HOME/agents/transcriptome/skills/differential_expression.md ~/.openclaw/plugin-skills/biosherpa-differential-expression/SKILL.md
```
Then add to `~/.openclaw/openclaw.json`:
```json
"skills": {
  "entries": {
    "biosherpa-differential-expression": {"enabled": true}
  }
}
```

### 5. Verify
```bash
# Run the example analysis
python %BIOSHERPA_HOME%\tools\deseq2_analysis\handler.py \
  --counts-file %BIOSHERPA_HOME%\examples\transcriptome\counts.csv \
  --metadata-file %BIOSHERPA_HOME%\examples\transcriptome\metadata.csv \
  --design-formula "~condition" \
  --contrast-variable condition \
  --treatment-group treated \
  --control-group control \
  --output-dir ./test_output

# Run tests
cd %BIOSHERPA_HOME%
pip install pytest
pytest tests/
```

## Architecture Files Mapping

| BioSherpa File | OpenClaw Equivalent | Purpose |
|---|---|---|
| `agents/transcriptome/soul.md` | Merged into SKILL.md | Agent personality |
| `agents/transcriptome/prompt.md` | SKILL.md (skill instructions) | System prompt / behavior |
| `agents/transcriptome/config.yaml` | openclaw.json skills.entries | Configuration |
| `agents/transcriptome/skills/*.md` | plugin-skills/*/SKILL.md | Domain expertise |
| `tools/*/handler.py` | Shell command invocation | Tool execution |
| `tools/*/scripts/*.R` | Called by handler | Fixed analysis |

## How It Works in OpenClaw

1. You enable the skill in openclaw.json
2. When you mention transcriptome analysis in OpenClaw, the skill activates
3. The SKILL.md content (personality + domain knowledge + tool instructions) becomes part of the agent's context
4. The agent follows the instructions to invoke handler.py via shell commands
5. handler.py validates inputs and calls the fixed deseq2.R script
6. Results (CSV + plots + summary) are written to the output directory
