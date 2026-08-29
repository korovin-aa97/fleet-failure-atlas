# Contributing

Fleet Failure Atlas values a small number of strong, safe entries over a large
catalogue of anecdotes. Start with a pattern proposal issue before building a
fixture.

## A qualifying entry

A contribution must include:

- one stable failure mechanism and observable signature;
- provenance labelled `observed`, `externally-reported`, or `hypothetical`;
- a deterministic, offline, bounded fixture using synthetic data;
- `reproduce`, `detect`, and `regress` modes;
- a repair invariant, false-positive boundary, and regression proof;
- a sanitization statement covering secrets, personal data, names, paths,
  identifiers, and proprietary topology.

Read the [schema](docs/PATTERN_SCHEMA.md) and
[safety model](docs/SAFETY_AND_PROVENANCE.md) before writing code.

## Local workflow

Python 3.11 or newer is required. The project has no third-party runtime or test
dependencies.

1. Copy an existing pattern and fixture.
2. Allocate the next unused `FFA-NNN` ID; never renumber published entries.
3. Keep the fixture under `fixtures/` and inside the runner's temporary working
   directory.
4. Regenerate the static index with `python3 atlas.py build-site`.
5. Run `python3 atlas.py check` and `python3 -m unittest discover -v`.
6. Open a focused pull request using the repository template.

## Fixture safety

Do not access a network, real repository, credential, user file, host service,
or production environment. Do not require containers, privilege changes,
background persistence, destructive actions, deliberate resource exhaustion, or
writes outside the current temporary directory. The five-second timeout is a
ceiling, not a target.

If a mechanism cannot be safely reproduced, propose a defensive documented
entry and explain why. Maintainers may still decline it.

## External reports and copyright

Cite primary sources and link to the exact page supporting the claim. Paraphrase
in your own words; do not copy incident reports or datasets into the repository.
Clearly separate what a source reports from your inference. Never identify a
private party or publish material received under confidentiality.

## Review standard

Maintainers review technical determinism, safety, evidence language, detector
quality, regression value, false positives, and duplication. A pattern is not
accepted merely because it happened in practice. All contributions are licensed
under the repository's MIT License.
