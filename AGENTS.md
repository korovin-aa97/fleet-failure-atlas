# Fleet Failure Atlas — Agent Bootstrap

Last updated: 2026-08-29. Repository status: **private content draft**.

Read this file first, then `README.md`, `regression-review-checklist.md`, every
existing pattern, and `docs/PUBLIC_RELEASE_PLAN.md`.

## Product in one sentence

Fleet Failure Atlas is an executable field guide showing how autonomous coding
agent systems fail, how to recognize each failure, and how to prevent it from
returning.

## Positioning

This must become more useful than a blog or awesome-list. A complete entry has a
minimal reproduction, observable signature, detector, repair contract, and
regression check. Stories without reusable evidence may live in articles but do
not qualify as atlas entries.

## Current state

- Private and unpublished.
- Contains a generic regression-review checklist and four sanitized draft
  patterns: stale green CI, artifact-poll deadlock, concurrent queue loss, and
  timezone-dependent tests.
- The patterns have `Fixture TODO` sections; no executable fixtures or detectors
  exist yet.
- There is no schema, contribution process, license, site, validation harness,
  or release workflow.

## Non-negotiable boundaries

- Clean-room every entry. Remove organization names, hostnames, paths, branch
  names, customer data, credentials, incident IDs, and commercial topology.
- Preserve the technical mechanism while changing identifying details.
- Never publish an alleged failure as fact without reproducible evidence or a
  clearly labelled hypothetical status.
- Do not disclose operational techniques that materially reveal a private
  orchestration product. Abstract the invariant, not the entire fleet design.
- Avoid blame. Entries describe system mechanisms and defenses, not individual
  mistakes.
- Keep executable fixtures safe: no destructive host actions, external writes,
  real credentials, production access, or uncontrolled resource consumption.

## Required pattern format

Every public pattern must include:

1. title and stable ID;
2. scope and affected architecture;
3. symptom and observable signature;
4. root mechanism;
5. minimal safe fixture;
6. deterministic detector;
7. repair invariant;
8. regression check;
9. false positives and non-applicable cases;
10. provenance category: observed, externally reported, or hypothetical.

## Next work, in order

1. Add `docs/PATTERN_SCHEMA.md` and an inventory/classification worksheet.
2. Convert the four drafts into the required schema.
3. Build safe executable fixtures and detectors for at least three entries.
4. Turn the regression checklist into a reusable agent skill plus plain Markdown.
5. Add contribution validation, templates, and a small fixture runner.
6. Decide the docs/code licensing split and build a browsable static index.
7. Complete `docs/PUBLIC_RELEASE_PLAN.md`; publish only with explicit approval.

## v0.1 definition of done

- At least three patterns run end-to-end from reproduction to regression proof.
- Every claim has provenance and every fixture is isolated and safe.
- The regression-review checklist is usable without knowledge of its source
  fleet and is available in a machine-readable agent format.
- Contributors have a template, safety rules, and a local validation command.
- Search/index pages group failures by lifecycle stage and symptom.
- README includes a short demo and explains what the atlas deliberately omits.
- Community, security, changelog, licensing, and release materials are complete.

## Working rules for future agents

- Prefer small fixtures over long prose.
- Generalize names, not causal mechanics.
- Add one automated detector and regression check with each new executable entry.
- Label unverified hypotheses and never invent incident statistics.
- Review entries for secrets, personal data, internal topology, and unsafe steps.
- Re-check related public failure catalogs and research on launch day.

## Success criterion

After launch, seek at least one external issue or pull request contributing a
new pattern per quarter. If the project attracts only passive reading, keep it
as a curated reference rather than expanding into a framework.

## Release authority

Agents can inventory, sanitize, implement fixtures, generate the site, and
draft launch content. Visibility changes and any public publication require an
explicit owner instruction in the active session.
