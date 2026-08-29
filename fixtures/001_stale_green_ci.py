#!/usr/bin/env python3
"""Safe synthetic fixture for FFA-001."""

import json
import sys

PATTERN_ID = "FFA-001"
OLD_SHA = "1" * 40
HEAD_SHA = "2" * 40


def result(mode: str) -> dict:
    receipt = {"name": "tests", "conclusion": "success", "head_sha": OLD_SHA, "covered": ["src/api.py"]}
    candidate = {"head_sha": HEAD_SHA, "changed": ["src/api.py"]}
    vulnerable_accepts = receipt["conclusion"] == "success"
    stale = receipt["head_sha"] != candidate["head_sha"]
    uncovered = sorted(set(candidate["changed"]) - set(receipt["covered"])) if not stale else candidate["changed"]
    repaired_accepts = not stale and not uncovered and receipt["conclusion"] == "success"
    evidence = {
        "candidate_sha": candidate["head_sha"],
        "receipt_sha": receipt["head_sha"],
        "vulnerable_gate_accepts": vulnerable_accepts,
    }
    if mode == "reproduce":
        assert vulnerable_accepts and stale
        evidence["failure"] = "a successful receipt for an older commit was accepted"
    elif mode == "detect":
        assert stale and uncovered
        evidence["detector_findings"] = ["head_sha_mismatch", "coverage_not_bound_to_head"]
    elif mode == "regress":
        assert not repaired_accepts
        evidence["repaired_gate_accepts"] = repaired_accepts
        evidence["invariant"] = "receipt SHA and changed-surface coverage must match the candidate"
    else:
        raise SystemExit(f"unsupported mode: {mode}")
    return {"pattern_id": PATTERN_ID, "mode": mode, "status": "pass", "evidence": evidence}


if __name__ == "__main__":
    print(json.dumps(result(sys.argv[1] if len(sys.argv) > 1 else "reproduce"), sort_keys=True))
