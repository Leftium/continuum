# PR Plan

Issue: #21

## Goal

Establish the durable Continuum 0.3 admission gate required before the reference repository can bootstrap its one final 0.3 -> 0.4 migration PR.

## Scope

- Keep this PR governed by Continuum 0.3.
- Add project-owned migration-gate policy outside the managed Continuum block in `AGENTS.md`.
- Record the project-owner decision, stable `v0.4.0` prerequisite, and exact designated migration-only identity: issue #22 / claim `continuum-0.4-final-migration`.
- Record the drain inventory, including this gate PR as the only pre-gate implementation that must finish before #22 bootstraps.
- Ban new ordinary 0.3 starts, reopen-for-implementation, and implicit orphan adoption after the gate lands.
- Preserve the existing managed 0.3 block and all retained 0.3 machinery.
- Do not bootstrap or implement #22 in this PR.
- Do not modify the canonical 0.4 protocol/client or docs-site work.

## Checkpoints

1. Reverify publication, open PRs, historical branches/PRs, and active claim state.
2. Add the project-owned gate/inventory text to `AGENTS.md` without changing the managed block.
3. Verify the policy diff and repository checks, release the write lease, and mark Ready.

## Verify

- `v0.4.0` remains the latest stable release and resolves to `76fed3f2fb03df0d7121fc8e026644431de16203`.
- No other open/unmerged 0.3 PRs or active/resumable claims exist.
- Every non-main historical branch corresponds to merged work or is otherwise explicitly non-resumable.
- `AGENTS.md` managed block is byte-preserved.
- Project-owned gate text names only #22 / `continuum-0.4-final-migration` as the post-gate exception.
- `bash scripts/check-continuum.sh` and `git diff --check` pass.
- No retained 0.3 file is removed or modified except the project-owned addition outside the managed `AGENTS.md` block.
- Do not merge or finalize `PR-PLAN.md` until independent review is clean.
