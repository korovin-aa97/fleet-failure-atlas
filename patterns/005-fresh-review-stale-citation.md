---
id: FFA-005
slug: fresh-review-stale-citation
title: Fresh review, stale citation
lifecycle: review, verification
symptoms: citation-drift, misleading-freshness, stale-evidence
architectures: automated-review, policy-as-code
provenance: externally-reported
status: executable
fixture: fixtures/005_fresh_review_stale_citation.py
---

# Fresh review, stale citation

## Scope and affected architecture

Applies when an automated reviewer re-runs for a new revision but carries
human-readable citations forward from an earlier document layout. The outer
review receipt can be fresh while a line range inside its evidence no longer
identifies the claimed rule or code.

## Symptom and observable signature

The review names the current commit and reports a recent run, yet following one
of its citations opens unrelated content.

- the review receipt is bound to the current revision;
- a cited file still exists, but the claimed content moved;
- the displayed line range did not move with that content;
- another anchor generated from the same revision may point to the new line.

## Root mechanism

The producer stores a positional label and later rebuilds only the URL or commit
part of the citation. Commit freshness and citation freshness become separate
facts, but the consumer validates only the first. Line numbers are presentation
coordinates, not stable evidence identity.

## Minimal safe fixture

The fixture starts with a synthetic rule at line 3, inserts four harmless lines
above it, and models a new review receipt bound to the new synthetic head SHA.
The receipt keeps the old line number, so the vulnerable gate accepts a fresh
review whose citation now resolves to a heading instead of the rule.

```console
python3 atlas.py run FFA-005 --mode reproduce
```

The fixture is offline and uses only in-memory strings and synthetic commit
identities.

## Deterministic detector

Resolve every citation against the exact referenced revision and compare the
retrieved content with the stable rule ID or expected content digest. Report
both a content mismatch and positional drift when the anchor exists elsewhere
in the same file.

```console
python3 atlas.py run FFA-005 --mode detect
```

## Repair invariant

Stable rule identity or a content anchor selects evidence from the exact
referenced blob. File and line ranges are then rendered from that retrieval for
display; a cached range never serves as the identity of the rule.

## Regression check

The repaired fixture locates the stable rule ID in the current document,
verifies its content digest, and only then emits the current line number. It
proves that moving unchanged content does not detach the citation from its
meaning.

```console
python3 atlas.py run FFA-005 --mode regress
```

## False positives and non-applicable cases

A line range can be reliable when the cited blob itself is immutable and the
range was computed from that exact blob. Stable anchors can also be ambiguous;
duplicate or missing IDs must fail closed rather than selecting the first
match. The detector validates citation integrity, not whether the cited prose
is a correct or sufficiently precise policy.

## Provenance

**Externally reported.** A public
[DEV discussion](https://dev.to/pm25coder/comment/3eh4b) identified the split
between a fresh review and stale citations and linked a
[public reproduction pull request](https://github.com/dannwaneri/rules-demo-api/pull/2).
On 2026-09-10, the public review page said the review was updated through commit
`3ffacd9` while its body still displayed earlier line ranges for the cited rule
and source. The fixture above is an independent clean-room model with synthetic
text and identities; it copies no repository content and makes no claim about
frequency, impact, or cause inside the named review service.
