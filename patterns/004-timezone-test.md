---
id: FFA-004
slug: timezone-dependent-test
title: Timezone-dependent test
lifecycle: testing, verification
symptoms: environment-drift, midnight-failure, flaky-test
architectures: test-suites, scheduled-agents
provenance: hypothetical
status: executable
fixture: fixtures/004_timezone_test.py
---

# Timezone-dependent test

## Scope and affected architecture

Applies to tests and scheduled automation that translate instants into calendar
dates without declaring the intended timezone.

## Symptom and observable signature

The same test passes in one environment and fails in another, commonly near UTC
midnight or a daylight-saving boundary.

- datetime literals lack an offset or zone;
- assertions compare dates derived under different host settings;
- rerunning with a different `TZ` changes the result;
- failures cluster near day, month, year, or daylight-saving transitions.

## Root mechanism

An instant and a local calendar time are different concepts. A naive datetime or
implicit host timezone lets the environment choose which date a test means.

## Minimal safe fixture

The fixture maps the stable instant `2026-01-01T23:30:00+00:00` to UTC and
Europe/Madrid using its explicit UTC+01:00 offset at that winter instant. The
dates differ, deterministically reproducing the boundary without relying on the
host timezone database.

```console
python3 atlas.py run FFA-004 --mode reproduce
```

## Deterministic detector

Reject naive datetime fixtures and any calendar-date assertion that lacks a
declared timezone. The fixture demonstrates both findings without reading the
host clock.

```console
python3 atlas.py run FFA-004 --mode detect
```

## Repair invariant

Represent an instant with an offset or UTC, declare the calendar timezone at the
conversion boundary, and test named boundary cases directly.

## Regression check

The regression mode asserts the same instant becomes
`2026-01-02T00:30:00+01:00` in Europe/Madrid.

```console
python3 atlas.py run FFA-004 --mode regress
```

## False positives and non-applicable cases

A naive datetime is acceptable for a deliberately timezone-free domain value,
such as a store's recurring opening time, when no instant conversion occurs.
Pinning everything to UTC is insufficient when the product rule is explicitly
about a local civil date.

## Provenance

**Hypothetical.** The instant and assertion are constructed for this fixture.
No named test suite or external incident is implied.
