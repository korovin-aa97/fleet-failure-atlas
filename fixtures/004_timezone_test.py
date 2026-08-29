#!/usr/bin/env python3
"""Safe deterministic timezone-boundary fixture for FFA-004."""

from datetime import datetime, timedelta, timezone
import json
import sys

PATTERN_ID = "FFA-004"


def result(mode: str) -> dict:
    instant = datetime(2026, 1, 1, 23, 30, tzinfo=timezone.utc)
    # Europe/Madrid is UTC+01:00 at this fixed winter instant. Keeping the
    # offset in the fixture avoids depending on a host-installed timezone DB.
    madrid_zone = timezone(timedelta(hours=1), name="Europe/Madrid@2026-01-01")
    madrid = instant.astimezone(madrid_zone)
    naive_literal = "2026-01-01T23:30:00"
    evidence = {"instant_utc": instant.isoformat(), "date_utc": str(instant.date()), "date_madrid": str(madrid.date())}
    if mode == "reproduce":
        assert instant.date() != madrid.date()
        evidence["failure"] = "one instant maps to different calendar dates across zones"
    elif mode == "detect":
        parsed = datetime.fromisoformat(naive_literal)
        assert parsed.tzinfo is None
        evidence["detector_findings"] = ["naive_datetime_literal", "calendar_date_without_declared_zone"]
    elif mode == "regress":
        expected = datetime(2026, 1, 2, 0, 30, tzinfo=madrid_zone)
        assert madrid == expected
        evidence["explicit_zone_result"] = expected.isoformat()
        evidence["invariant"] = "tests declare both the instant and the calendar timezone"
    else:
        raise SystemExit(f"unsupported mode: {mode}")
    return {"pattern_id": PATTERN_ID, "mode": mode, "status": "pass", "evidence": evidence}


if __name__ == "__main__":
    print(json.dumps(result(sys.argv[1] if len(sys.argv) > 1 else "reproduce"), sort_keys=True))
