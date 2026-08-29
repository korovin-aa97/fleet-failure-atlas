---
id: FFA-002
slug: artifact-poll-deadlock
title: Result-channel mismatch
lifecycle: orchestration, handoff
symptoms: timeout, phantom-wait, ignored-result
architectures: background-workers, multi-agent-orchestration
provenance: hypothetical
status: executable
fixture: fixtures/002_artifact_poll_deadlock.py
---

# Result-channel mismatch

## Scope and affected architecture

Applies to orchestrators that start a background worker and wait for completion,
especially when results can travel through both an orchestration protocol and a
filesystem artifact.

## Symptom and observable signature

The worker has completed and returned a valid result, while the parent remains
active until a timeout because it is polling a different channel.

- worker state is complete;
- an inline or protocol result is available;
- the parent repeatedly checks an undeclared artifact path;
- downstream work is blocked despite an idle worker.

## Root mechanism

Producer and consumer do not share one result contract. The worker returns JSON
through the supported channel, while the parent invents `result.json` as an
implicit second protocol.

## Minimal safe fixture

The fixture creates an inline result and performs three bounded existence checks
for a file the worker never promised to create. It demonstrates the mismatch
without sleeping, starting a process, or leaving a file behind.

```console
python3 atlas.py run FFA-002 --mode reproduce
```

## Deterministic detector

Flag a run when the declared worker channel contains a terminal result while the
parent is still waiting on an absent, undeclared artifact.

```console
python3 atlas.py run FFA-002 --mode detect
```

## Repair invariant

Each job has one declared authoritative result channel. The consumer validates
and consumes it once. Missing or malformed results terminate with a bounded
error instead of opening another polling path.

## Regression check

The repaired fixture consumes the inline JSON result directly and asserts the
job identity without consulting the filesystem.

```console
python3 atlas.py run FFA-002 --mode regress
```

## False positives and non-applicable cases

Polling is not inherently wrong. A durable artifact can be the authoritative
contract when its exact path, schema, atomic-write behavior, deadline, and
cleanup are declared before the worker starts.

## Provenance

**Hypothetical.** The names, identifiers, and control flow are synthetic. The
entry describes a generic protocol mismatch and makes no external incident
claim.
