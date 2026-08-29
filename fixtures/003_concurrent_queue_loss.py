#!/usr/bin/env python3
"""Safe in-memory fixture for FFA-003."""

import json
import sys

PATTERN_ID = "FFA-003"


def apply(items: list[dict], operation: dict) -> list[dict]:
    current = {item["id"]: dict(item) for item in items}
    if operation["type"] == "remove":
        current.pop(operation["id"], None)
    elif operation["type"] == "append":
        current[operation["item"]["id"]] = dict(operation["item"])
    return [current[key] for key in sorted(current)]


def result(mode: str) -> dict:
    initial = [{"id": "job-a", "state": "open"}, {"id": "job-b", "state": "open"}]
    remove = {"type": "remove", "id": "job-a"}
    append = {"type": "append", "item": {"id": "job-c", "state": "open"}}
    remover_snapshot = apply(initial, remove)
    producer_snapshot = apply(initial, append)
    naive_merge = remover_snapshot
    accepted_ids = {item["id"] for item in producer_snapshot}
    merged_ids = {item["id"] for item in naive_merge}
    lost = sorted((accepted_ids - {"job-a", "job-b"}) - merged_ids)
    evidence = {"initial_ids": ["job-a", "job-b"], "naive_merge_ids": sorted(merged_ids)}
    if mode == "reproduce":
        assert lost == ["job-c"]
        evidence["lost_ids"] = lost
        evidence["failure"] = "whole-file conflict resolution discarded an accepted append"
    elif mode == "detect":
        assert lost
        evidence["detector_findings"] = [f"accepted_operation_missing:{item}" for item in lost]
    elif mode == "regress":
        replayed = apply(apply(initial, remove), append)
        replayed_ids = sorted(item["id"] for item in replayed)
        assert replayed_ids == ["job-b", "job-c"]
        evidence["replayed_ids"] = replayed_ids
        evidence["invariant"] = "replay stable-key operations against the latest state"
    else:
        raise SystemExit(f"unsupported mode: {mode}")
    return {"pattern_id": PATTERN_ID, "mode": mode, "status": "pass", "evidence": evidence}


if __name__ == "__main__":
    print(json.dumps(result(sys.argv[1] if len(sys.argv) > 1 else "reproduce"), sort_keys=True))
