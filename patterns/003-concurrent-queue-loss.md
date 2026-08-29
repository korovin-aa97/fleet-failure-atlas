---
id: FFA-003
slug: concurrent-queue-loss
title: Concurrent queue update loss
lifecycle: coordination, persistence
symptoms: lost-update, silent-data-loss, clean-history
architectures: file-backed-queues, concurrent-workers
provenance: hypothetical
status: executable
fixture: fixtures/003_concurrent_queue_loss.py
---

# Concurrent queue update loss

## Scope and affected architecture

Applies when several workers mutate a queue or registry stored as one file, then
merge snapshots through a version-control system or shared filesystem.

## Symptom and observable signature

One worker closes an item while another appends a new item. Both operations
report success, the file remains syntactically valid, and the appended item is
missing after the snapshots are reconciled.

- successful operations overlap in time;
- the missing stable ID appears in a producer receipt but not final state;
- conflict resolution selected an entire file from one side;
- repository history is clean, so ordinary conflict checks do not warn.

## Root mechanism

The system merges snapshots instead of logical operations. Choosing the
remover's complete file silently discards the producer's append.

## Minimal safe fixture

The fixture creates two in-memory snapshots from the same two-item queue. One
removes `job-a`; the other adds `job-c`. A whole-snapshot merge reproduces the
loss without processes, locks, disk writes, or nondeterministic timing.

```console
python3 atlas.py run FFA-003 --mode reproduce
```

## Deterministic detector

Compare acknowledged stable-key operations with the merged state. Any accepted
append absent from the result becomes `accepted_operation_missing:<id>`.

```console
python3 atlas.py run FFA-003 --mode detect
```

## Repair invariant

Persist stable-key operations, apply them to the latest state, and publish with
compare-and-swap semantics. On rejection, reload and replay the same idempotent
operation; never force-push a stale snapshot.

## Regression check

The regression mode replays remove and append against current state. It proves
the final IDs are exactly `job-b` and `job-c`.

```console
python3 atlas.py run FFA-003 --mode regress
```

## False positives and non-applicable cases

A whole-file merge can be correct when there is a single writer or when the file
is derived from an authoritative operation log. A missing ID is also legitimate
when a later acknowledged removal targets that same ID.

## Provenance

**Hypothetical.** This is a synthetic lost-update fixture. It does not disclose
or attribute a real queue, repository, organization, or incident.
