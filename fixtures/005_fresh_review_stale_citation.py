#!/usr/bin/env python3
"""Safe in-memory fixture for FFA-005."""

import hashlib
import json
import sys

PATTERN_ID = "FFA-005"
HEAD_SHA = "5" * 40
RULE_ID = "api-route-format"
RULE_TEXT = "RULE api-route-format: new API route paths use kebab-case."

ORIGINAL_DOCUMENT = (
    "# Project policy",
    "",
    RULE_TEXT,
    "RULE tests-required: changed behavior needs a regression test.",
)
CURRENT_DOCUMENT = (
    "# Project policy",
    "",
    "## Generated context",
    "Review the complete change before applying these rules.",
    "",
    "## Rules",
    RULE_TEXT,
    "RULE tests-required: changed behavior needs a regression test.",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def rule_line(document: tuple[str, ...], rule_id: str) -> int:
    prefix = f"RULE {rule_id}:"
    matches = [index for index, line in enumerate(document, start=1) if line.startswith(prefix)]
    if len(matches) != 1:
        raise RuntimeError(f"expected one stable rule anchor, found {len(matches)}")
    return matches[0]


def cited_text(document: tuple[str, ...], start_line: int, end_line: int) -> str:
    if start_line < 1 or end_line < start_line or end_line > len(document):
        return ""
    return "\n".join(document[start_line - 1 : end_line])


def citation_matches(
    document: tuple[str, ...], start_line: int, end_line: int, content_sha256: str
) -> bool:
    value = cited_text(document, start_line, end_line)
    return bool(value) and digest(value) == content_sha256


def result(mode: str) -> dict[str, object]:
    stored_line = rule_line(ORIGINAL_DOCUMENT, RULE_ID)
    current_line = rule_line(CURRENT_DOCUMENT, RULE_ID)
    expected_digest = digest(RULE_TEXT)
    review_head_sha = HEAD_SHA
    candidate_head_sha = HEAD_SHA
    review_sha_matches = review_head_sha == candidate_head_sha
    stored_citation_matches = citation_matches(
        CURRENT_DOCUMENT, stored_line, stored_line, expected_digest
    )
    vulnerable_accepts = review_sha_matches
    evidence: dict[str, object] = {
        "review_head_sha": review_head_sha,
        "candidate_head_sha": candidate_head_sha,
        "review_sha_matches": review_sha_matches,
        "rule_id": RULE_ID,
        "stored_line": stored_line,
        "actual_line": current_line,
    }

    if mode == "reproduce":
        require(vulnerable_accepts, "fresh review receipt was not accepted")
        require(not stored_citation_matches, "stored citation unexpectedly stayed valid")
        evidence["vulnerable_gate_accepts"] = vulnerable_accepts
        evidence["stored_citation_text"] = cited_text(CURRENT_DOCUMENT, stored_line, stored_line)
        evidence["failure"] = "a fresh review receipt was accepted with a stale internal citation"
    elif mode == "detect":
        findings: list[str] = []
        if review_sha_matches and not stored_citation_matches:
            findings.append("citation_content_mismatch")
        if stored_line != current_line:
            findings.append("citation_line_drift")
        require(
            findings == ["citation_content_mismatch", "citation_line_drift"],
            "detector did not identify stale citation evidence",
        )
        evidence["detector_findings"] = findings
    elif mode == "regress":
        rendered_line = rule_line(CURRENT_DOCUMENT, RULE_ID)
        repaired_accepts = review_sha_matches and citation_matches(
            CURRENT_DOCUMENT, rendered_line, rendered_line, expected_digest
        )
        require(repaired_accepts, "anchor-based citation did not resolve at the head")
        evidence["repaired_gate_accepts"] = repaired_accepts
        evidence["rendered_line"] = rendered_line
        evidence["content_sha256"] = expected_digest
        evidence["invariant"] = (
            "stable rule identity selects exact-head content; line ranges are rendered afterward"
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
