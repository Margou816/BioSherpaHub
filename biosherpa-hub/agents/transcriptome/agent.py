"""TranscriptomeAgent â€?DESeq2 differential expression via fixed pipeline."""
from __future__ import annotations
import json
from pathlib import Path
from typing import List
from core_types import (
    BaseAgent, Request, Result, ResultStatus, WorkflowPlan,
    Artifact, ArtifactType,
)
from .tool_runner import run_deseq2

_TRANSCRIPTOME_KEYWORDS = frozenset({
    "rna", "rnaseq", "rna-seq", "transcriptome", "transcriptomics",
    "deseq2", "deseq", "differential expression", "differentially expressed",
    "deg", "degs", "count matrix", "gene expression", "volcano", "ma plot",
    "pca", "transcriptom",
})

class TranscriptomeAgent(BaseAgent):
    name: str = "transcriptome"
    version: str = "0.0.1"
    description: str = "DESeq2-based differential expression analysis"

    def can_handle(self, request: Request) -> bool:
        return any(kw in request.query.lower() for kw in _TRANSCRIPTOME_KEYWORDS)

    def plan(self, request: Request) -> WorkflowPlan:
        wf = WorkflowPlan(name="DESeq2 Differential Expression")
        wf.add_step(tool="deseq2_analysis", params={
            "counts_file": request.user_parameters.get("counts_file", ""),
            "metadata_file": request.user_parameters.get("metadata_file", ""),
            "design_formula": request.user_parameters.get("design_formula", "~condition"),
            "contrast_variable": request.user_parameters.get("contrast_variable", "condition"),
            "treatment_group": request.user_parameters.get("treatment_group", ""),
            "control_group": request.user_parameters.get("control_group", ""),
            "output_dir": request.user_parameters.get("output_dir", "."),
            "alpha": request.user_parameters.get("alpha", 0.05),
            "lfc_threshold": request.user_parameters.get("lfc_threshold", 1.0),
        }, description="DESeq2 analysis")
        return wf

    def execute(self, request: Request, plan: WorkflowPlan) -> Result:
        errors: List[str] = []
        artifacts: List[Artifact] = []
        for step in plan.steps:
            if step.tool != "deseq2_analysis":
                errors.append(f"Unknown tool: {step.tool}")
                continue
            try:
                step_artifacts = run_deseq2(
                    params=step.params,
                    r_libs_user=request.metadata.get("r_libs_user"),
                )
                artifacts.extend(step_artifacts)
            except Exception as exc:
                errors.append(f"DESeq2 failed: {exc}")
                return Result.failure(errors=errors)
        summary = self.summarize(Result(artifacts=artifacts, status=ResultStatus.SUCCESS))
        return Result.success(artifacts=artifacts, summary=summary)

    def summarize(self, result: Result) -> str:
        if not result.artifacts:
            return "DESeq2 produced no artifacts."
        parts = ["## DESeq2 Differential Expression Analysis\n"]
        for a in result.artifacts:
            if a.name == "summary.json" and a.path:
                try:
                    data = json.loads(a.path.read_text(encoding="utf-8", errors="replace"))
                    parts.append(f"DESeq2: {data.get('significant',0)} of {data.get('total_genes',0)} DEGs "
                                 f"({data.get('upregulated',0)} up, {data.get('downregulated',0)} down)")
                except Exception: pass
        for a in result.artifacts:
            if a.artifact_type == ArtifactType.TABLE and a.path:
                parts.append(f"Results: `{a.path}`")
            elif a.artifact_type == ArtifactType.IMAGE and a.path:
                parts.append(f"Plot: `{a.path}`")
        return "\n".join(parts)
