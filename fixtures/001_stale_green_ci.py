#!/usr/bin/env python3
"""Safe synthetic fixture for FFA-001."""

import json
import sys

PATTERN_ID = "FFA-001"
OLD_SHA = "1" * 40
HEAD_SHA = "2" * 40


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def result(mode: str) -> dict[str, object]:
    changed = ["src/api.py"]
    covered = ["src/api.py"]
    fresh_receipt_sha = HEAD_SHA
    fresh_covered = ["src/api.py"]
    vulnerable_accepts = True
    stale = OLD_SHA != HEAD_SHA
    uncovered = changed if stale else sorted(set(changed) - set(covered))
    repaired_accepts = not stale and not uncovered
    fresh_receipt_accepts = fresh_receipt_sha == HEAD_SHA and not (
        set(changed) - set(fresh_covered)
    )
    evidence: dict[str, object] = {
        "candidate_sha": HEAD_SHA,
        "receipt_sha": OLD_SHA,
        "vulnerable_gate_accepts": vulnerable_accepts,
    }
    if mode == "reproduce":
        require(vulnerable_accepts and stale, "stale successful receipt was not reproduced")
        evidence["failure"] = "a successful receipt for an older commit was accepted"
    elif mode == "detect":
        require(stale and bool(uncovered), "detector did not find stale or unbound evidence")
        evidence["detector_findings"] = ["head_sha_mismatch", "coverage_not_bound_to_head"]
    elif mode == "regress":
        require(not repaired_accepts, "repaired gate accepted the stale receipt")
        require(fresh_receipt_accepts, "repaired gate rejected a matching fresh receipt")
        evidence["repaired_gate_accepts"] = repaired_accepts
        evidence["fresh_receipt_accepts"] = fresh_receipt_accepts
        evidence["invariant"] = "receipt SHA and changed-surface coverage must match the candidate"
    else:
        raise SystemExit(f"unsupported mode: {mode}")
    return {"pattern_id": PATTERN_ID, "mode": mode, "status": "pass", "evidence": evidence}


if __name__ == "__main__":
    print(json.dumps(result(sys.argv[1] if len(sys.argv) > 1 else "reproduce"), sort_keys=True))
