# PR Plan

Issue: #12

## Goal

Make installed `CONTINUUM.md` a vendor-managed exact-copy protocol file and move repository-specific workflow policy to project-owned `AGENTS.md` content outside the managed Continuum markers.

## Scope

- Genericize root `CONTINUUM.md` so it contains no repository-specific URLs or project-policy inserts.
- Make root `CONTINUUM.md` and `templates/CONTINUUM.md` byte-identical.
- Update the managed `AGENTS.md` block to explicitly separate managed Continuum instructions from project-owned policy.
- Update README and protocol spec to document the exact-copy installation/update contract.
- Simplify `scripts/check-continuum.sh` to enforce exact root/template equality rather than placeholder normalization.
- Do not change lease, checkpoint, finalizer, or safety semantics.

## Checkpoint A — installation contract

- Genericize the Start Here human links in `CONTINUUM.md`.
- Add protocol guidance that `CONTINUUM.md` is vendor-managed and repository-specific policy belongs in project-owned `AGENTS.md` / docs.
- Make `templates/CONTINUUM.md` exactly equal to root.
- Update the managed `AGENTS.md` block with the project-policy boundary.
- Update README/spec documentation.
- Commit and non-force-push the coherent checkpoint, then continue without yielding.

## Checkpoint B — self-check

- Replace URL placeholder normalization with direct root/template comparison.
- Add assertions for the exact-copy/project-policy contract.
- Keep finalizer/template checks and finalizer regressions unchanged.
- Commit and non-force-push the coherent checkpoint, then continue without yielding.

## Checkpoint C — verification

- Confirm root/template byte equality.
- Run/observe Continuum self-check and finalizer regressions.
- Inspect the complete diff for unrelated workflow-semantic changes.
- Record rollout implications for Continuum #9 and Vee PR #116.
- Release the lease and mark Ready for independent review.

## Verify

- `cmp CONTINUUM.md templates/CONTINUUM.md`
- `bash scripts/check-continuum.sh`
- GitHub Actions `Continuum`
- no repository-specific URL placeholders remain
- managed `AGENTS.md` block still matches the documented update contract

The user controls final merge.
