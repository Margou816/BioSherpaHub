"""TranscriptomeAgent -- DESeq2 differential expression powered by BioSherpa Core.

This agent implements the BaseAgent contract and delegates tool execution
to the existing handler.py -> deseq2.R pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from biosherpa_core import (
    BaseAgent,
    Request,
    Result,
    ResultStatus,
    WorkflowPlan,
    Artifact,
    ArtifactType,
)

from .tool_runner import run_deseq2

# Keywords that trigger this agent
_TRANSCRIPTOME_KEYWORDS = frozenset({
    "rna", "rnaseq", "rna-seq", "transcriptome", "transcriptomics",
    "deseq2", "deseq", "differential expression", "differentially expressed",
    "deg", "degs", "count matrix", "gene expression", "volcano", "ma plot",
    "pca", "transcriptom", "transcriptome",
})


class TranscriptomeAgent(BaseAgent):
    """DESeq2-based transcriptome differential expression agent."""

    name: str = "transcriptome"
    version: str = "0.0.1"
    description: str = (
        "DESeq2-based differential expression analysis for RNA-seq count data. "
        "Produces CSV results, volcano plot, PCA plot, and MA plot."
    )

    # ------------------------------------------------------------------
    # BaseAgent lifecycle
    # ------------------------------------------------------------------

    def can_handle(self, request: Request) -> bool:
        """Return True if the query relates to transcriptome analysis."""
        query_lower = request.query.lower()
        return any(kw in query_lower for kw in _TRANSCRIPTOME_KEYWORDS)

    def plan(self, request: Request) -> WorkflowPlan:
        """Build a single-step DESeq2 workflow.

        If the user has provided all required parameters, they are
        attached to the plan step.  Otherwise defaults (alpha=0.05,
        lfc_threshold=1.0) are used and the caller (runtime) is
        expected to fill in file paths before execution.
        """
        wf = WorkflowPlan(
            name="DESeq2 Differential Expression",
            description="Run DESeq2 analysis on RNA-seq count data.",
        )
        wf.add_step(
            tool="deseq2_analysis",
            params={
                "counts_file": request.user_parameters.get("counts_file", ""),
                "metadata_file": request.user_parameters.get("metadata_file", ""),
                "design_formula": request.user_parameters.get("design_formula", "~condition"),
                "contrast_variable": request.user_parameters.get("contrast_variable", "condition"),
                "treatment_group": request.user_parameters.get("treatment_group", ""),
                "control_group": request.user_parameters.get("control_group", ""),
                "output_dir": request.user_parameters.get("output_dir", ""),
                "alpha": request.user_parameters.get("alpha", 0.05),
                "lfc_threshold": request.user_parameters.get("lfc_threshold", 1.0),
            },
            description="DESeq2 differential expression analysis",
        )
        return wf

    def execute(self, request: Request, plan: WorkflowPlan) -> Result:
        """Execute the DESeq2 workflow and collect artifacts."""
        errors: List[str] = []
        artifacts: List[Artifact] = []

        for step in plan.steps:
            if step.tool != "deseq2_analysis":
                errors.append(f"Unknown tool: {step.tool}")
                continue

            # Merge parameters: step params have priority over defaults
            try:
                step_artifacts = run_deseq2(
                    params=step.params,
                    r_libs_user=request.metadata.get("r_libs_user"),
                )
                artifacts.extend(step_artifacts)
            except Exception as exc:
                errors.append(f"DESeq2 failed: {exc}")
                return Result.failure(errors=errors, workflow=plan)

        summary = self.summarize(Result(status=ResultStatus.SUCCESS, artifacts=artifacts))
        return Result.success(
            artifacts=artifacts,
            summary=summary,
            workflow=plan,
            request_id=request.id,
        )

    def summarize(self, result: Result) -> str:
        """Produce a human-readable summary from the analysis artifacts."""
        if not result.artifacts:
            return "DESeq2 analysis produced no artifacts."

        summary_json = None
        csv_artifact = None
        image_artifacts = []

        for a in result.artifacts:
            if a.name == "summary.json":
                summary_json = a
            elif a.artifact_type == ArtifactType.TABLE:
                csv_artifact = a
            elif a.artifact_type == ArtifactType.IMAGE:
                image_artifacts.append(a)

        parts = ["## DESeq2 Differential Expression Analysis\n"]

        if summary_json:
            parts.append(summary_json.description)
            parts.append("")

        if csv_artifact and csv_artifact.path:
            parts.append(f"**Results table:** `{csv_artifact.path}`")

        if image_artifacts:
            parts.append(f"**Plots ({len(image_artifacts)}):**")
            for ia in image_artifacts:
                if ia.path:
                    parts.append(f"- `{ia.path}`")

        parts.append("\n---")
        parts.append("Analysis performed with BioSherpa Transcriptome Agent v0.0.1.")
        return "\n".join(parts)
