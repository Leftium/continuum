# PR Plan

Issue: #19

## Goal

Prepare the exact Continuum 0.4.0 release candidate on `main` without publishing the release or performing the repository's 0.3 -> 0.4 self-migration.

## Scope

- Keep this PR governed by the repository's current Continuum 0.3 workflow.
- Remove or update stale transitional wording that describes already-merged implementation PRs as still active.
- Verify `protocol/CONTINUUM.md`, the reference client, fixtures/tests, and docs consistently identify version 0.4.0.
- Verify stable bootstrap discovery accepts the supported `v0.4.0` / `0.4.0` release name and resolves it to an immutable commit.
- Review README, client, and migration guidance against the actual post-#15/#18 repository state.
- Before fresh independent review, perform the human-authorized editorial pass on `protocol/CONTINUUM.md`: clarify the normal lifecycle, separate exceptional recovery, consolidate redundancy, and relocate non-normative client mechanics to `docs/client.md`. Preserve every requirement, wire format, normalization rule, transition, permission, guarantee, migration boundary, and observable client behavior. Leave uncertain simplifications unchanged.
- Preserve all retained 0.3 root protocol/templates/finalizer/managed AGENTS machinery needed for the later designated migration PR.
- Run the full retained 0.3 + 0.4 verification suite.
- Record the exact reviewed release-candidate commit and release-note inputs.
- Do not create a tag or GitHub release in this PR.
- Do not perform self-migration, docs-site deployment, or unrelated feature work.

## Checkpoints

1. Audit release/version/documentation consistency and make only release-preparation corrections.
2. Verify stable-discovery assumptions and full retained 0.3 + 0.4 checks.
3. Record the exact release candidate, release notes/checklist, release the lease, and mark Ready for independent review.

Checkpoints are durable savepoints within an active writing run, not default handoffs.

## Verify

- `protocol/CONTINUUM.md` metadata, client version, fixtures/tests, and documentation agree on 0.4.0.
- README/client/migration docs do not describe merged PRs as still active.
- Stable bootstrap discovery behavior remains pinned to a stable release and exact commit.
- Retained 0.3 migration/finalization machinery remains intact.
- Record before/after protocol line and whitespace-delimited word counts. Audit the editorial diff against the preceding candidate for semantic preservation, including literal wire blocks and event transitions.
- Existing scripts, fixtures, and tests remain unchanged during the editorial pass.
- `bash scripts/check-continuum.sh` and `git diff --check` pass.
- Review staged/unstaged diffs and safe Git/GitHub destinations before each checkpoint push.
- Release the write lease and mark Ready when preparation is complete.
- Do not publish `v0.4.0`, migrate the repository, merge, or remove this temporary 0.3 plan until independently reviewed and separately authorized.
