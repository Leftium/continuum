# PR Plan

Issue: #17

## Goal

Make the optional `continuum` PR label discoverable during 0.4 bootstrap, with explicit user-controlled label creation and safe backfill of existing Continuum PRs.

## Scope

- Keep this PR governed by the repository's current Continuum 0.3 workflow until migration.
- If the `continuum` label exists, apply it best-effort to a newly bootstrapped Continuum PR.
- If the label is missing and creation is possible, surface an explicit create/skip choice; never create repository labels silently.
- Missing permissions, declining creation, or label-application failure must not block bootstrap.
- After creating the label, offer a one-time backfill for existing open 0.4 Continuum PRs identified by the canonical PR-body marker.
- Add an explicit/idempotent label-sync path; never remove unrelated labels.
- Do not heuristically infer old 0.3 PRs from titles or branch names.
- Keep labels non-authoritative: protocol correctness and discovery continue to rely on canonical Continuum metadata.
- Update protocol/client/getting-started documentation and focused tests.
- Do not publish a release, perform repository migration, or merge in this implementation run.

## Checkpoints

1. Define the normative optional-label/bootstrap/backfill behavior and client UX.
2. Implement reference-client label discovery/create/apply/sync behavior with permission-safe fallbacks.
3. Add focused tests and documentation; run full retained 0.3 + 0.4 checks and prepare independent review.

Checkpoints are durable savepoints within an active writing run, not default handoffs.

## Verify

- Existing label is applied to a new Continuum PR when permitted.
- Missing label produces explicit create/skip behavior, not silent creation.
- Decline/no-permission/application-failure paths continue bootstrap.
- Newly created label is applied to the current PR.
- Open 0.4 Continuum PR backfill uses canonical body markers, is idempotent, and preserves unrelated labels.
- Noninteractive behavior is explicit rather than inferred.
- Run `bash scripts/check-continuum.sh` and focused unit/integration coverage.
- Review staged/unstaged diffs and safe Git/GitHub destinations before each checkpoint push.
- Release the write lease and mark Ready when implementation is complete. Do not merge or remove this temporary 0.3 plan until independent review and authorized finalization.
