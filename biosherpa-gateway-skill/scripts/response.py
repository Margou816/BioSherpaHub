"""Response formatter — Result to dict for JSON output."""
from __future__ import annotations
from typing import Any, Dict
from biosherpa_core.context.result import Result, ResultStatus
def format_response(result: Result) -> Dict[str, Any]:
 return {"status":{ResultStatus.SUCCESS:"success",ResultStatus.PARTIAL:"partial",
  ResultStatus.FAILED:"failed",ResultStatus.CANCELLED:"cancelled"}.get(result.status,"unknown"),
  "summary":result.summary or "","artifacts":[str(a.path) for a in result.artifacts if a.path],
  "artifact_details":[{"name":a.name,"type":a.artifact_type.name,"path":str(a.path),
  "description":a.description} for a in result.artifacts],
  "errors":result.errors,"workflow":result.workflow.tool_sequence if result.workflow else[]}
def format_no_match() -> Dict[str, Any]:
 return {"status":"no_match","summary":"No Matching Agent","artifacts":[],"errors":[]}
