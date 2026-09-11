---
id: FFA-006
slug: green-noop-test-evidence
title: Green no-op test evidence
lifecycle: testing, verification, merge
symptoms: misleading-success, skipped-tests, evidence-unavailable
architectures: continuous-integration, integration-testing
provenance: externally-reported
status: executable
fixture: fixtures/006_green_noop_test_evidence.py
---

# Green no-op test evidence

## Scope and affected architecture

Applies when a required CI producer can finish successfully without executing
the checks that make its result useful. The skip decision may live inside a
test process, so the surrounding job keeps its expected name and green
conclusion even though required evidence was never produced.

## Symptom and observable signature

The exact candidate revision has a successful required job, but its structured
test result reports zero executed tests.

- expected test work is positive;
- every required test is skipped or filtered out;
- the job conclusion is still `success`;
- a missing prerequisite is described as a skip instead of unavailable evidence.

## Root mechanism

The gate validates the outer producer identity and conclusion but not the
applicability decision or the producer's structured counts. One process acts as
both test runner and applicability judge, yet only the runner has a check name.
Consequently, “the contract passed” and “the contract was not evaluated” have
the same external status.

## Minimal safe fixture

The fixture builds one in-memory receipt for the exact synthetic head SHA. It
records two expected tests, zero executed tests, two skipped tests, and an
unavailable prerequisite while the outer job reports success. A conclusion-only
gate accepts it.

```console
python3 atlas.py run FFA-006 --mode reproduce
```

The fixture is offline, deterministic, and uses only synthetic identities and
test counts. It does not read environment variables or credentials.

## Deterministic detector

Validate a normalized structured test report in a separate required check.
For an applicable required suite, require `expected > 0`, `executed == expected`,
`failed == 0`, and `skipped == 0`. Report unavailable evidence separately when
a required prerequisite is absent; a green outer conclusion cannot override it.

```console
python3 atlas.py run FFA-006 --mode detect
```

The fixture emits stable findings for zero executed tests, required skips, and
unavailable evidence incorrectly paired with success.

## Repair invariant

Applicability and execution are independently visible evidence. Required work
has positive, complete structured counts. Missing prerequisites fail closed as
`evidence_unavailable`. A genuinely non-applicable change is accepted only when
an independently controlled named decision records `not_applicable` with a
policy-approved reason.

## Regression check

Regression mode rejects the green no-op receipt, accepts a complete two-test
receipt, and accepts an explicit documentation-only non-applicability decision.
The positive cases prevent an always-deny predicate from masquerading as the
repair.

```console
python3 atlas.py run FFA-006 --mode regress
```

## False positives and non-applicable cases

Zero executed tests are not automatically a failure when policy proves that no
required test surface applies. That decision must be separate from a producer
whose own work is being judged, name the deciding check, and carry a bounded
reason. Optional tests may be skipped if they are outside the required set.
Structured counts prove that declared work ran; they do not prove test quality
or that a producer reported its own behavior honestly.

## Provenance

**Externally reported.** A public
[DEV comment](https://dev.to/to21as/comment/3ehnm) described a required test job
that exited successfully after its suites selected an internal skip path because
a prerequisite was missing. A second public
[analysis](https://dev.to/pm25coder/comment/3ei6l) proposed making applicability
nameable and validating structured test counts independently. The fixture is an
independent clean-room model with generic counts and synthetic identities. It
copies no code or repository data and makes no claim about frequency, impact,
or the internal design of any named test framework.
