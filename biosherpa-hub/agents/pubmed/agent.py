"""PubMedAgent -- literature search via NCBI E-utilities."""
from __future__ import annotations
import json
from typing import List
from core_types import (
    BaseAgent, Request, Result, ResultStatus, WorkflowPlan,
    Artifact, ArtifactType,
)
from .tool_runner import run_pubmed_search
_KW = frozenset({"pubmed","literature","articles","ncbi","reference","citation","paper","journal"})
class PubMedAgent(BaseAgent):
    name="pubmed"; version="0.1.0"; description="PubMed literature search"
    def can_handle(self, request: Request) -> bool:
        return any(kw in request.query.lower() for kw in _KW)
    def plan(self, request: Request) -> WorkflowPlan:
        wf = WorkflowPlan(name="PubMed Search")
        wf.add_step(tool="pubmed_search", params={
            "query": request.user_parameters.get("query", request.query),
            "max_results": request.user_parameters.get("max_results", 20),
            "output_dir": request.user_parameters.get("output_dir", "."),
        }, description="PubMed literature search")
        return wf
    def execute(self, request: Request, plan: WorkflowPlan) -> Result:
        artifacts: List[Artifact] = []
        errors: List[str] = []
        for step in plan.steps:
            if step.tool != "pubmed_search":
                errors.append(f"Unknown: {step.tool}"); continue
            try:
                step_artifacts = run_pubmed_search(params=step.params)
                artifacts.extend(step_artifacts)
            except Exception as exc:
                errors.append(f"PubMed search failed: {exc}")
        if errors and not artifacts: return Result.failure(errors=errors)
        return Result.success(artifacts=artifacts, summary=self.summarize(Result(artifacts=artifacts, status=ResultStatus.SUCCESS)))
    def summarize(self, result: Result) -> str:
        if not result.artifacts: return "No PubMed results."
        parts = ["## PubMed Search Results\n"]
        for a in result.artifacts:
            if a.artifact_type == ArtifactType.TABLE and a.path:
                parts.append(f"Results: `{a.path}`")
        return "\n".join(parts)
