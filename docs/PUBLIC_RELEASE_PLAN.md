# Maintainer release checklist

Last exercised for v0.1.2 on 2026-08-30.

## Product gate

- [x] Every entry follows `docs/PATTERN_SCHEMA.md`.
- [x] At least three entries run end-to-end through reproduce, detect, and
  regress modes (v0.1.0 has four).
- [x] Fixtures are synthetic, offline, bounded to five seconds, and run in a
  fresh temporary directory.
- [x] Provenance and false-positive boundaries are explicit.
- [x] Human checklist and agent `SKILL.md` are semantically aligned.
- [x] Searchable static index and machine-readable JSON are generated.

## Safety and editorial gate

- [x] Inventory classifies the source material and publication boundary.
- [x] Current tree and history were reviewed for secrets, personal data,
  organization names, paths, incident identifiers, and private topology.
- [x] All current incident-like claims are labelled hypothetical.
- [x] Related work uses primary sources and records the check date.
- [x] Exact project-name search was repeated on launch day.
- [x] Unsafe reproduction classes and private reporting path are documented.

## Engineering gate

```bash
python3 atlas.py validate
python3 atlas.py safety
python3 -m unittest discover -v
python3 atlas.py run
python3 atlas.py build-site --check
actionlint
python3 -m pip install --requirement requirements-dev.txt
ruff check .
ruff format --check .
mypy
bandit -q -r atlas.py fixtures
```

- [x] All commands pass locally.
- [x] Python 3.12 and the current local Python pass the full release gate.
- [x] CI covers Python 3.11–3.14 on Linux and Python 3.11 on Windows.
- [x] A clean clone passes the release gate before visibility changes.
- [x] The Pages home, search interaction, pattern page, links, and responsive
  bounds were browser-checked.

## Packaging gate

- [x] README, short demo, limitations, contribution path, and roadmap exist.
- [x] MIT license, changelog, citation, conduct, governance, contribution, and
  security files exist.
- [x] Pattern proposal, bug report, and pull request templates exist.
- [x] CI and Pages workflows pin official actions to reviewed commit SHAs.
- [x] Animated fixture walkthrough, favicon, and 1280×640 social-preview asset
  are checked in.
- [x] Repository description and topics are accurate.

## Publication gate

Execute only with explicit owner authorization in the active session:

1. Push reviewed `main` while still private.
2. Confirm clean CI for the exact head SHA.
3. Change visibility to public and immediately verify README and license.
4. Enable private vulnerability reporting and useful public security features.
5. Publish an immutable semantic-version tag and GitHub Release notes.
6. Enable Pages from the reviewed workflow and verify the deployed URL.
7. Create only useful starter issues; do not post social content unless separately
   authorized.

## Ongoing curation

- Respond to substantive proposals promptly when maintainer capacity allows.
- Keep stable IDs and document runner/schema compatibility in the changelog.
- Re-run related-work and name checks for releases that materially change scope.
- Prefer a small evidence-backed reference over expansion for its own sake.
