#!/usr/bin/env python3
"""Safe synthetic fixture for FFA-002; no real worker or unbounded wait."""

import json
from pathlib import Path
import sys

PATTERN_ID = "FFA-002"


def result(mode: str) -> dict:
    worker_result = {"job_id": "demo-42", "state": "complete", "value": 7}
    guessed_artifact = Path("result.json")
    polls = 3
    artifact_seen = any(guessed_artifact.exists() for _ in range(polls))
    evidence = {"worker_state": worker_result["state"], "artifact_seen": artifact_seen, "bounded_polls": polls}
    if mode == "reproduce":
        assert worker_result["state"] == "complete" and not artifact_seen
        evidence["failure"] = "parent waits on a path outside the worker result contract"
    elif mode == "detect":
        findings = []
        if worker_result["state"] == "complete" and not artifact_seen:
            findings.append("completed_result_ignored_while_artifact_missing")
        assert findings
        evidence["detector_findings"] = findings
    elif mode == "regress":
        consumed = worker_result if worker_result.get("state") == "complete" else None
        assert consumed and consumed["job_id"] == "demo-42"
        evidence["consumed_result_channel"] = "inline-json"
        evidence["invariant"] = "producer and consumer share one declared result channel"
    else:
        raise SystemExit(f"unsupported mode: {mode}")
    return {"pattern_id": PATTERN_ID, "mode": mode, "status": "pass", "evidence": evidence}


if __name__ == "__main__":
    print(json.dumps(result(sys.argv[1] if len(sys.argv) > 1 else "reproduce"), sort_keys=True))
