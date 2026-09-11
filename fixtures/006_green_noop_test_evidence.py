#!/usr/bin/env python3
"""Safe in-memory fixture for FFA-006."""

import json
import sys
from typing import TypedDict

PATTERN_ID = "FFA-006"
HEAD_SHA = "6" * 40


class Applicability(TypedDict):
    status: str
    producer: str
    reason_code: str


class TestCounts(TypedDict):
    expected: int
    passed: int
    failed: int
    skipped: int


class Report(TypedDict):
    head_sha: str
    job_name: str
    conclusion: str
    applicability: Applicability
    tests: TestCounts


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def vulnerable_gate(report: Report) -> bool:
    return report["head_sha"] == HEAD_SHA and report["conclusion"] == "success"


def repaired_gate(report: Report) -> bool:
    if report["head_sha"] != HEAD_SHA or report["conclusion"] != "success":
        return False

    applicability = report["applicability"]
    tests = report["tests"]
    status = applicability["status"]
    expected = tests["expected"]
    passed = tests["passed"]
    failed = tests["failed"]
    skipped = tests["skipped"]

    if status == "applicable":
        executed = passed + failed
        return (
            expected > 0
            and executed == expected
            and passed == expected
            and failed == 0
            and skipped == 0
        )

    if status == "not_applicable":
        return (
            applicability.get("producer") == "test-applicability"
            and applicability.get("reason_code") == "documentation-only-change"
            and expected == 0
            and passed == 0
            and failed == 0
            and skipped == 0
        )

    return False


def no_op_report() -> Report:
    return {
        "head_sha": HEAD_SHA,
        "job_name": "integration-tests",
        "conclusion": "success",
        "applicability": {
            "status": "evidence_unavailable",
            "producer": "integration-tests",
            "reason_code": "required-prerequisite-missing",
        },
        "tests": {"expected": 2, "passed": 0, "failed": 0, "skipped": 2},
    }


def result(mode: str) -> dict[str, object]:
    report = no_op_report()
    tests = report["tests"]
    applicability = report["applicability"]

    expected = tests["expected"]
    passed = tests["passed"]
    failed = tests["failed"]
    skipped = tests["skipped"]
    executed = passed + failed
    vulnerable_accepts = vulnerable_gate(report)
    evidence: dict[str, object] = {
        "candidate_sha": HEAD_SHA,
        "job_name": report["job_name"],
        "conclusion": report["conclusion"],
        "applicability": applicability["status"],
        "reason_code": applicability["reason_code"],
        "expected": expected,
        "executed": executed,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
    }

    if mode == "reproduce":
        require(vulnerable_accepts and executed == 0, "green no-op evidence was not reproduced")
        evidence["vulnerable_gate_accepts"] = vulnerable_accepts
        evidence["failure"] = "an exact-head successful job was accepted after executing no tests"
    elif mode == "detect":
        findings: list[str] = []
        if expected > 0 and executed == 0:
            findings.append("zero_executed_tests")
        if skipped > 0:
            findings.append("required_tests_skipped")
        if applicability["status"] == "evidence_unavailable" and report["conclusion"] == "success":
            findings.append("evidence_unavailable_reported_success")
        require(
            findings
            == [
                "zero_executed_tests",
                "required_tests_skipped",
                "evidence_unavailable_reported_success",
            ],
            "detector did not identify green no-op evidence",
        )
        evidence["detector_findings"] = findings
    elif mode == "regress":
        complete_report: Report = {
            "head_sha": HEAD_SHA,
            "job_name": "integration-tests",
            "conclusion": "success",
            "applicability": {
                "status": "applicable",
                "producer": "test-applicability",
                "reason_code": "required-surface-changed",
            },
            "tests": {"expected": 2, "passed": 2, "failed": 0, "skipped": 0},
        }
        not_applicable_report: Report = {
            "head_sha": HEAD_SHA,
            "job_name": "test-applicability",
            "conclusion": "success",
            "applicability": {
                "status": "not_applicable",
                "producer": "test-applicability",
                "reason_code": "documentation-only-change",
            },
            "tests": {"expected": 0, "passed": 0, "failed": 0, "skipped": 0},
        }
        repaired_accepts_no_op = repaired_gate(report)
        repaired_accepts_complete = repaired_gate(complete_report)
        repaired_accepts_not_applicable = repaired_gate(not_applicable_report)
        require(not repaired_accepts_no_op, "repaired gate accepted unavailable evidence")
        require(repaired_accepts_complete, "repaired gate rejected a complete required suite")
        require(
            repaired_accepts_not_applicable,
            "repaired gate rejected an independently classified non-applicable change",
        )
        evidence["repaired_gate_accepts_no_op"] = repaired_accepts_no_op
        evidence["repaired_gate_accepts_complete"] = repaired_accepts_complete
        evidence["repaired_gate_accepts_not_applicable"] = repaired_accepts_not_applicable
        evidence["invariant"] = (
            "required work has positive complete counts; unavailable evidence fails; "
            "non-applicability needs a named decision and reason"
        )
    else:
        raise SystemExit(f"unsupported mode: {mode}")

    return {
        "pattern_id": PATTERN_ID,
        "mode": mode,
        "status": "pass",
        "evidence": evidence,
    }


if __name__ == "__main__":
    print(
        json.dumps(
            result(sys.argv[1] if len(sys.argv) > 1 else "reproduce"),
            sort_keys=True,
        )
    )
