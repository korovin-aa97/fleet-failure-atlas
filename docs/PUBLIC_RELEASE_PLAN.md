# Fleet Failure Atlas — Public Release Plan

Status: private content draft. Target: a credible executable `v0.1` atlas.

## Release thesis

Teams building autonomous coding agents repeatedly rediscover the same failure
modes: stale evidence, deadlocked handoffs, unsafe queue merges, timezone drift,
and misleading success signals. The atlas converts field experience into safe,
reproducible fixtures and regression defenses.

Canonical public line:

> An executable field guide to autonomous coding-agent failures: reproduce the
> symptom, detect it, repair the invariant, and keep it from returning.

Portfolio signature:

> Built from operating a mixed Claude/Codex production fleet.

Do not launch as a prose-only awesome-list.

## Phase 0 — Inventory, classification, and safety

- [ ] Create `docs/INVENTORY.md` and classify every candidate pattern as:
      public as-is, public after abstraction, internal-only, or commercial
      topology/know-how that must not be published.
- [ ] Add `docs/PATTERN_SCHEMA.md` with the required fields from `AGENTS.md`.
- [ ] Define provenance labels: observed, externally reported, hypothetical.
- [ ] Define safe-fixture rules: isolation, bounded resources, no production or
      network mutation, no credentials, and clear cleanup.
- [ ] Search existing failure catalogs, agent benchmarks, incident collections,
      and research directly; record dated sources in `docs/RELATED_WORK.md`.
- [ ] Recheck the project name and decide licensing. A possible split is
      CC-BY-4.0 for prose and MIT for fixtures/tools, but confirm contributor and
      reuse implications before choosing.

## Phase 1 — Produce the first executable collection

- [ ] Convert the four existing drafts to the common schema.
- [ ] Implement a minimal fixture runner with explicit resource/time bounds.
- [ ] Make stale-green-CI reproducible with two commits and stale evidence.
- [ ] Make artifact-poll deadlock reproducible with mismatched result channels.
- [ ] Make concurrent queue loss reproducible with two stable-key operations.
- [ ] Add detectors and regression checks for at least those three patterns.
- [ ] Add a timezone-boundary fixture if it remains safe and clear.
- [ ] Turn `regression-review-checklist.md` into both Markdown and a generic
      agent `SKILL.md`, with drift checks keeping them semantically aligned.
- [ ] Have an independent reader reproduce all public fixtures from clean clone.

Exit gate: at least three entries run from symptom to regression proof without
private context or unsafe host actions.

## Phase 2 — Contribution and verification model

- [ ] Add a pattern proposal issue template and pull-request checklist.
- [ ] Require provenance, safe fixture, detector, defense, false positives, and
      sanitization review for executable entries.
- [ ] Add schema validation and fixture time/resource limits in CI.
- [ ] Add secret/PII/internal-topology scanning guidance.
- [ ] Define how externally reported incidents are cited without copying
      excessive copyrighted text or making unsupported accusations.
- [ ] Add maintainers' review policy for security-sensitive or destructive
      reproductions; reject unsafe fixtures even when technically interesting.

## Phase 3 — Package the repository and site

- [ ] README: problem, one animated fixture demo, browse-by-symptom table,
      quickstart, entry anatomy, contribution path, safety boundary, related
      work, roadmap, and portfolio signature.
- [ ] Add `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`,
      `CODE_OF_CONDUCT.md`, governance/licensing explanation, and templates.
- [ ] Add 3–5 real `good first issue`s for detectors, fixtures, or documentation.
- [ ] Build a static searchable index, preferably GitHub Pages from repository
      content, without requiring a separate hosted backend.
- [ ] Add `llms.txt` and an index consumable by agents.
- [ ] Add CI for schema, fixtures, links, secret patterns, and site build.
- [ ] Generate social preview and a short "failure -> detector -> regression"
      demo from an actual fixture.
- [ ] Use accurate topics such as `ai-agents`, `coding-agents`, `reliability`,
      `testing`, `incident-response`, `regression-testing`, and `field-guide`.

## Phase 4 — Pre-public editorial gate

- [ ] Run all fixtures from a clean clone in an isolated environment.
- [ ] Review every line for customer data, internal hosts/paths, branch names,
      incident IDs, personal data, credentials, proprietary architecture, and
      unsafe commands.
- [ ] Verify provenance and citations; label every remaining uncertainty.
- [ ] Confirm the site and Markdown render correctly and links are stable.
- [ ] Re-run related-work and name checks on launch day.
- [ ] Prepare release notes, Show HN maker comment, native community posts,
      dev.to technical story, Habr adaptation, and FAQ.

## Phase 5 — Owner-authorized public flip

Do not execute without explicit owner authorization.

1. [ ] Change GitHub visibility to public.
2. [ ] Immediately verify license, README/demo, description, topics, citations,
       and clean history.
3. [ ] Enable secret scanning, push protection, vulnerability reporting, and
       code scanning.
4. [ ] Upload social preview, pin the repository, and enable Discussions only if
       there is capacity to moderate it.
5. [ ] Tag `v0.1.0` and publish human release notes listing the executable set.
6. [ ] Enable GitHub Pages from the reviewed build and verify every page.
7. [ ] Submit to relevant awesome-agent, testing, reliability, and incident
       response lists; avoid directories that expect a software package.

## Phase 6 — Launch content, days 2–14

- [ ] Show HN only when the executable fixtures are real; link GitHub, not a
      marketing landing page, and explain sanitization and limitations.
- [ ] Publish different posts on different days for agent-builder, testing,
      DevOps/SRE, open-source, and programming communities.
- [ ] Story article: recurring ways autonomous coding fleets fail in practice.
- [ ] Technical deep dive: green CI is evidence only when bound to the change.
- [ ] Technical deep dive: how to build safe executable incident fixtures.
- [ ] Publish a careful Habr adaptation and submit to engineering newsletters.
- [ ] Invite new patterns, not stars or votes.

## Phase 7 — Curate after launch

- [ ] Respond to new pattern proposals within 24–48 hours initially.
- [ ] Maintain a high evidence bar; do not inflate the catalog with thin entries.
- [ ] Track external citations, cloned fixtures, contributions, and issues.
- [ ] Publish focused releases as new executable patterns land.
- [ ] Continue active investment if at least one external issue or pull request
      contributes a new pattern per quarter; otherwise maintain as a reference.

## Actions reserved for the owner

Visibility and release authorization, final disclosure judgment for patterns
derived from private operations, license approval, Pages/public account actions,
profile pinning/social preview if manual, and posting from personal accounts.
