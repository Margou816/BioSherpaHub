"""EnrichmentAgent -- GO and KEGG pathway enrichment via clusterProfiler."""
from __future__ import annotations
import json
from pathlib import Path
from typing import List
from core_types import (
    BaseAgent, Request, Result, ResultStatus, WorkflowPlan,
    Artifact, ArtifactType,
)
from .tool_runner import run_go_enrichment, run_kegg_enrichment

_ENRICHMENT_KEYWORDS = frozenset({
    "go", "kegg", "enrichment", "pathway", "gene ontology",
    "clusterprofiler", "functional",
})

class EnrichmentAgent(BaseAgent):
    name: str = "enrichment"
    version: str = "0.1.0"
    description: str = "GO and KEGG pathway enrichment analysis"

    def can_handle(self, request: Request) -> bool:
        return any(kw in request.query.lower() for kw in _ENRICHMENT_KEYWORDS)

    def plan(self, request: Request) -> WorkflowPlan:
        wf = WorkflowPlan(name="Enrichment Analysis")
        wf.add_step(tool="go_enrichment", params={
            "deg_file": request.user_parameters.get("deg_file", ""),
            "organism": request.user_parameters.get("organism", "org.Hs.eg.db"),
            "pvalue_cutoff": request.user_parameters.get("pvalue_cutoff", 0.05),
            "qvalue_cutoff": request.user_parameters.get("qvalue_cutoff", 0.2),
            "output_dir": request.user_parameters.get("output_dir", "."),
        }, description="GO enrichment")
        wf.add_step(tool="kegg_enrichment", params={
            "deg_file": request.user_parameters.get("deg_file", ""),
            "organism": request.user_parameters.get("organism", "org.Hs.eg.db"),
            "pvalue_cutoff": request.user_parameters.get("pvalue_cutoff", 0.05),
            "qvalue_cutoff": request.user_parameters.get("qvalue_cutoff", 0.2),
            "output_dir": request.user_parameters.get("output_dir", "."),
        }, description="KEGG enrichment")
        return wf

    def execute(self, request: Request, plan: WorkflowPlan) -> Result:
        artifacts: List[Artifact] = []
        errors: List[str] = []
        runners = {"go_enrichment": run_go_enrichment, "kegg_enrichment": run_kegg_enrichment}
        for step in plan.steps:
            runner = runners.get(step.tool)
            if runner is None: errors.append(f"Unknown tool: {step.tool}"); continue
            try:
                step_artifacts = runner(params=step.params)
                artifacts.extend(step_artifacts)
            except Exception as exc:
                errors.append(f"{step.tool} failed: {exc}")
        if errors and not artifacts: return Result.failure(errors=errors)
        summary = self.summarize(Result(artifacts=artifacts, status=ResultStatus.SUCCESS))
        return Result.success(artifacts=artifacts, summary=summary)

    def summarize(self, result: Result) -> str:
        if not result.artifacts: return "Enrichment produced no results."
        parts = ["## Enrichment Analysis\n"]
        for a in result.artifacts:
            if a.artifact_type == ArtifactType.TABLE and a.path:
                parts.append(f"Table: `{a.path}`")
            elif a.artifact_type == ArtifactType.IMAGE and a.path:
                parts.append(f"Plot: `{a.path}`")
        return "\n".join(parts)
