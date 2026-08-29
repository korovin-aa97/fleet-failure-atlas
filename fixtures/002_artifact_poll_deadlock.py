#!/usr/bin/env python3
"""Safe synthetic fixture for FFA-002; no real worker or unbounded wait."""

import json
import sys
from pathlib import Path

PATTERN_ID = "FFA-002"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def result(mode: str) -> dict[str, object]:
    worker_job_id = "demo-42"
    worker_state = "complete"
    guessed_artifact = Path("result.json")
    polls = 3
    artifact_seen = any(guessed_artifact.exists() for _ in range(polls))
    evidence: dict[str, object] = {
        "worker_state": worker_state,
        "artifact_seen": artifact_seen,
        "bounded_polls": polls,
    }
    if mode == "reproduce":
        require(worker_state == "complete" and not artifact_seen, "result mismatch not reproduced")
        evidence["failure"] = "parent waits on a path outside the worker result contract"
    elif mode == "detect":
        findings: list[str] = []
        if worker_state == "complete" and not artifact_seen:
            findings.append("completed_result_ignored_while_artifact_missing")
        require(bool(findings), "detector did not identify the result-channel mismatch")
        evidence["detector_findings"] = findings
    elif mode == "regress":
        consumed_job_id = worker_job_id if worker_state == "complete" else None
        require(consumed_job_id == "demo-42", "declared result channel was not consumed")
        evidence["consumed_result_channel"] = "inline-json"
        evidence["invariant"] = "producer and consumer share one declared result channel"
    else:
        raise SystemExit(f"unsupported mode: {mode}")
    return {"pattern_id": PATTERN_ID, "mode": mode, "status": "pass", "evidence": evidence}


if __name__ == "__main__":
    print(json.dumps(result(sys.argv[1] if len(sys.argv) > 1 else "reproduce"), sort_keys=True))
