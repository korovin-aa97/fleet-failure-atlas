#!/usr/bin/env python3
"""Safe in-memory fixture for FFA-003."""

import json
import sys
from typing import TypedDict

PATTERN_ID = "FFA-003"


class QueueItem(TypedDict):
    id: str
    state: str


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def apply(
    items: list[QueueItem],
    *,
    remove_id: str | None = None,
    append_item: QueueItem | None = None,
) -> list[QueueItem]:
    current: dict[str, QueueItem] = {
        item["id"]: {"id": item["id"], "state": item["state"]} for item in items
    }
    if remove_id:
        current.pop(remove_id, None)
    if append_item:
        current[append_item["id"]] = {
            "id": append_item["id"],
            "state": append_item["state"],
        }
    return [current[key] for key in sorted(current)]


def result(mode: str) -> dict[str, object]:
    initial: list[QueueItem] = [
        {"id": "job-a", "state": "open"},
        {"id": "job-b", "state": "open"},
    ]
    appended: QueueItem = {"id": "job-c", "state": "open"}
    remover_snapshot = apply(initial, remove_id="job-a")
    producer_snapshot = apply(initial, append_item=appended)
    naive_merge = remover_snapshot
    accepted_ids = {item["id"] for item in producer_snapshot}
    merged_ids = {item["id"] for item in naive_merge}
    lost = sorted((accepted_ids - {"job-a", "job-b"}) - merged_ids)
    evidence: dict[str, object] = {
        "initial_ids": ["job-a", "job-b"],
        "naive_merge_ids": sorted(merged_ids),
    }
    if mode == "reproduce":
        require(lost == ["job-c"], "accepted append was not lost")
        evidence["lost_ids"] = lost
        evidence["failure"] = "whole-file conflict resolution discarded an accepted append"
    elif mode == "detect":
        require(bool(lost), "detector did not identify the lost operation")
        evidence["detector_findings"] = [f"accepted_operation_missing:{item}" for item in lost]
    elif mode == "regress":
        replayed = apply(apply(initial, remove_id="job-a"), append_item=appended)
        replayed_ids = sorted(item["id"] for item in replayed)
        require(replayed_ids == ["job-b", "job-c"], "operation replay lost an item")
        evidence["replayed_ids"] = replayed_ids
        evidence["invariant"] = "replay stable-key operations against the latest state"
    else:
        raise SystemExit(f"unsupported mode: {mode}")
    return {"pattern_id": PATTERN_ID, "mode": mode, "status": "pass", "evidence": evidence}


if __name__ == "__main__":
    print(json.dumps(result(sys.argv[1] if len(sys.argv) > 1 else "reproduce"), sort_keys=True))
