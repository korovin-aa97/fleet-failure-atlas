---
id: FFA-001
slug: stale-green-ci
title: Stale green CI evidence
lifecycle: verification, merge
symptoms: misleading-success, stale-evidence, coverage-gap
architectures: continuous-integration, automated-review
provenance: hypothetical
status: executable
fixture: fixtures/001_stale_green_ci.py
---

# Stale green CI evidence

## Scope and affected architecture

Applies when a coding agent or automated reviewer uses CI results to authorize a
merge. The pattern is platform-independent: the dangerous assumption is that a
successful check name is sufficient evidence by itself.

## Symptom and observable signature

A merge candidate appears green even though the evidence belongs to an older
revision or never exercised the changed surface.

- the check receipt SHA differs from the candidate SHA;
- source changed after the latest successful receipt was produced;
- the receipt has no changed-surface coverage declaration;
- a job reports success after skipping every relevant command.

## Root mechanism

The gate validates the conclusion but not the identity or scope of the evidence.
This turns a mutable status label into a capability to merge unrelated code.

## Minimal safe fixture

The fixture constructs two synthetic 40-character commit identities. A green
receipt is attached to the first; the merge candidate points at the second. The
vulnerable gate checks only `conclusion == success` and therefore accepts it.

```console
python3 atlas.py run FFA-001 --mode reproduce
```

It uses no repository, network, token, or external CI system.

## Deterministic detector

Compare the receipt's exact `head_sha` with the candidate SHA, then verify that
every changed path maps to a check the receipt actually ran. Missing identity or
coverage data is itself a finding.

```console
python3 atlas.py run FFA-001 --mode detect
```

## Repair invariant

A merge is allowed only when a successful receipt is bound to the exact
candidate revision and explicitly covers every changed surface under an
independently controlled policy.

## Regression check

The regression mode sends the stale receipt through the repaired predicate and
proves it is rejected.

```console
python3 atlas.py run FFA-001 --mode regress
```

## False positives and non-applicable cases

Some CI systems intentionally reuse content-addressed results. That is safe only
when the receipt also proves the relevant inputs, environment, and policy are
identical. A human-readable branch name or check name is not such proof.

## Provenance

**Hypothetical.** This is a clean-room synthetic reproduction of a general
evidence-binding failure, not a claim about a named organization or incident.
GitHub's public Checks API documents `head_sha` as part of a check-run receipt;
see the [related-work notes](https://github.com/korovin-aa97/fleet-failure-atlas/blob/main/docs/RELATED_WORK.md).
