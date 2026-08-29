# Pattern schema

Atlas entries are Markdown files in `patterns/` with deliberately simple front
matter. The validator parses `key: value` pairs without a YAML dependency.

## Required metadata

| Field | Contract |
| --- | --- |
| `id` | Stable `FFA-NNN` identifier; never reused. |
| `slug` | Unique lowercase URL slug. |
| `title` | Short mechanism-oriented name. |
| `lifecycle` | Comma-separated stages such as `verification, merge`. |
| `symptoms` | Comma-separated observable search terms. |
| `architectures` | Comma-separated affected system shapes. |
| `provenance` | `observed`, `externally-reported`, or `hypothetical`. |
| `status` | `executable` or `documented`. |
| `fixture` | Safe Python file directly under `fixtures/`, or `none` for a documented entry. |

## Required sections

Every entry must have all of these level-two headings:

1. Scope and affected architecture
2. Symptom and observable signature
3. Root mechanism
4. Minimal safe fixture
5. Deterministic detector
6. Repair invariant
7. Regression check
8. False positives and non-applicable cases
9. Provenance

## Executable result contract

A fixture accepts `reproduce`, `detect`, or `regress` as its first argument and
prints one JSON object to stdout:

```json
{
  "pattern_id": "FFA-001",
  "mode": "detect",
  "status": "pass",
  "evidence": {"detector_findings": ["head_sha_mismatch"]}
}
```

`pass` means the fixture proved the expected property. In reproduce mode that
property is the presence of the deliberately contained failure. The runner
provides a fresh temporary directory, removes it after the process exits, and
kills a fixture after five seconds or 64 KiB per output stream.

An `executable` entry must name an existing `.py` fixture and implement all
three modes. A defensive `documented` entry must use `fixture: none`; it appears
in the atlas but is skipped by `atlas.py run`. The validator requires at least
three executable entries in the collection.

## Provenance categories

- `observed`: maintainers directly observed the mechanism and can privately
  substantiate it. Publication must still use clean-room fixtures and must not
  imply frequency or impact without publishable evidence.
- `externally-reported`: a primary source publicly documents the event. Cite it,
  distinguish reported facts from inference, and avoid excessive quotation.
- `hypothetical`: a synthetic mechanism that is technically reproducible but is
  not presented as a real incident.

Provenance is about the claim, not fixture quality. A hypothetical pattern can
be fully executable; an observed story without a safe reproduction is not an
executable entry.

## Safety requirements

Fixtures must be deterministic, resource-bounded, offline, non-destructive, and
self-contained. They may use only synthetic identifiers and data. They must not
read credentials, user files, repository state, host services, or production
systems. Network calls, privilege changes, persistent background processes,
fork bombs, intentional secret material, and writes outside the runner's
temporary directory are prohibited.

Run `python3 atlas.py check` before proposing a pattern.
