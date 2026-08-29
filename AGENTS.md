# Fleet Failure Atlas — agent guide

Current release: **v0.1.2**. Repository: public, maintainer-led, MIT licensed.

Read this file, `README.md`, `docs/PATTERN_SCHEMA.md`,
`docs/SAFETY_AND_PROVENANCE.md`, and `CONTRIBUTING.md` before changing a pattern
or fixture.

## Product contract

Fleet Failure Atlas is an executable field guide to failures in autonomous
coding-agent systems. A complete entry has a bounded synthetic reproduction,
observable signature, deterministic detector, repair invariant, regression
proof, false-positive boundary, and explicit provenance.

Do not turn the repository into a prose-only awesome-list, incident rumor
catalogue, model leaderboard, or general orchestration framework.

## Safety and disclosure boundary

- Never add customer or organization names, hostnames, user paths, branch names,
  credentials, personal data, private incident IDs, or proprietary topology.
- Never present a failure as observed or externally reported without the
  corresponding provenance evidence.
- Keep fixtures offline, deterministic, bounded, non-destructive, and synthetic.
- Do not read credentials, user files, repository state, host services, or
  production systems.
- Reject unsafe reproductions even when the underlying mechanism is interesting.
- Describe system mechanisms and defenses without assigning blame.

## Repository map

- `atlas.py`: standard-library validator, safety scan, fixture runner, and site
  generator.
- `patterns/`: canonical human entries with validated metadata and sections.
- `fixtures/`: one executable fixture per pattern.
- `skills/regression-review/`: portable agent review skill.
- `docs/atlas.json`: generated machine-readable pattern index.
- `docs/index.html` and `docs/patterns/`: generated Pages site.
- `tests/`: release-contract tests.

## Change workflow

1. Allocate the next stable `FFA-NNN`; never renumber a released entry.
2. Add or update the pattern and its fixture together.
3. Support `reproduce`, `detect`, and `regress`, returning the documented JSON
   evidence object.
4. Add tests for runner or schema behavior when those contracts change.
5. Run `python3 atlas.py build-site` after any pattern metadata or body change.
6. Run `make check` before commit.
7. Review the complete diff and history for secrets, private identifiers,
   unsupported claims, and unsafe operations.

## Compatibility

Python 3.11+ is the supported runtime. Keep runtime and tests dependency-free
unless a future release has a compelling, documented reason to change that
promise. Treat fixture JSON, pattern IDs, metadata keys, CLI commands, and the
machine index as public contracts. Use semantic versioning for breaking changes.

## Release procedure

Use `docs/PUBLIC_RELEASE_PLAN.md` for the maintainer checklist. Do not change
repository visibility, publish a release, enable an external service, or post
social content unless the active user request explicitly authorizes it.

## Near-term work

- accept independent reproduction feedback on non-macOS platforms;
- add strong patterns only when they meet the executable evidence bar;
- improve detectors without importing product-specific orchestration details;
- keep the static site and agent index small, accessible, and dependency-free.
