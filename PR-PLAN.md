# PR Plan

Issue: #22
Designated migration claim: `continuum-0.4-final-migration`

## Goal

Perform the single final self-migration of the Continuum reference repository from its retained 0.3 installation to published stable Continuum 0.4.

This PR itself remains governed by Continuum 0.3 through review, plan-only finalization, and merge. New work uses 0.4 only after this PR lands.

## Preconditions already established

- Project-owned admission gate #21 / PR #23 is merged on `main`.
- Stable `v0.4.0` is published and resolves to exact commit `76fed3f2fb03df0d7121fc8e026644431de16203`.
- Fresh pre-bootstrap drain check found no other open PR, competing lease/acquisition claim, resumable closed-unmerged work, or orphan bootstrap work.
- This issue/PR is the sole post-gate exception under reserved claim identity `continuum-0.4-final-migration`.

Recheck the drain and release pin again before Ready/cleanup and immediately before merge.

## Migration scope

Remove only retained 0.3 installation/runtime machinery:

- root installed `CONTINUUM.md`;
- `templates/CONTINUUM.md`;
- `templates/PR-PLAN.md`;
- `scripts/continuum-finalize-pr.sh`;
- `templates/continuum-finalize-pr.sh`;
- `scripts/test-finalizer.sh`;
- the managed 0.3 block in `AGENTS.md`, preserving every byte of project-owned policy outside it.

Update the post-migration repository around those removals:

- remove obsolete retained-0.3 equality/finalizer checks from `scripts/check-continuum.sh` or replace the entry point with an equivalent 0.4-only check;
- keep CI invoking a valid post-migration check;
- update README/status/migration/release documentation so the repository is described as migrated and future work uses stable 0.4;
- preserve historical specs where they remain useful as design/history rather than active installed protocol.

Preserve the 0.4 implementation:

- `protocol/CONTINUUM.md`;
- `scripts/continuum.py`, `scripts/continuum_core.py`, `scripts/check-protocol.py`;
- tests and fixtures for 0.4;
- accepted design/spec history;
- project-owned migration-gate text in `AGENTS.md`;
- ordinary GitHub issues, labels, branches, and history.

Do not include docs-site work from #16, new protocol behavior, another release, deployment, or unrelated cleanup.

## Checkpoints

1. Re-read gate policy, issue #22, stable release, current base, and drain; inventory all retained 0.3-only files/checks.
2. Remove retained 0.3 installation files and only the managed `AGENTS.md` block.
3. Convert checks/CI and repository docs to the post-migration 0.4 state without changing protocol/client behavior.
4. Run full post-migration verification and inspect the complete diff for accidental project-owned/published-0.4 changes.
5. Commit/non-force-push coherent checkpoints, release the write lease, and mark Ready for independent review.

## Verify

- `v0.4.0` still resolves to `76fed3f2fb03df0d7121fc8e026644431de16203`.
- No competing 0.3 work is active/resumable.
- Root `CONTINUUM.md`, retained 0.3 templates/finalizer machinery, and managed `AGENTS.md` block are absent.
- Project-owned `AGENTS.md` gate/history text remains intact.
- Canonical `protocol/CONTINUUM.md`, 0.4 client/core, fixtures/tests, and accepted design history are preserved except for narrowly required status/reference updates.
- Post-migration checks and `git diff --check` pass.
- CI is valid for the post-migration tree.
- README/docs no longer tell future work to use the installed 0.3 workflow.
- #16 remains deferred until this PR merges.

## Finalization boundary

After independent review is otherwise clean, finalize this still-0.3 PR by removing only root `PR-PLAN.md`.

Because this migration may remove the branch-local 0.3 finalizer, use either:

1. the exact helper from the pinned accepted base, if available and safe; or
2. the documented plan-only fallback after verifying reviewed shared HEAD and push destination: delete only `PR-PLAN.md`, create cleanup-only commit `chore: remove temporary PR plan`, and non-force push.

Do not merge automatically. Final merge requires separate human authorization. Recheck the drain immediately before merge.
