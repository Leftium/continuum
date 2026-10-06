# Publishing Continuum 0.4.0

Release preparation does not authorize publication. Issue #19 owns the publication
decision; PR #20 prepares the candidate for independent review. This repository
continues to use the retained 0.3 workflow until a separate gated migration.

## Release contract

The canonical release artifact is `protocol/CONTINUUM.md`, with version `0.4.0`
and artifact path in its front matter. The reference client, contract fixtures,
and documented supported version must agree. Root `CONTINUUM.md` and its
templates intentionally remain at 0.3.0; they are migration infrastructure,
not the 0.4 release artifact.

Stable bootstrap queries `repos/Leftium/continuum/releases/latest`, accepts
`v0.4.0` or `0.4.0`, rejects draft/prerelease results, and resolves the tag via
`repos/Leftium/continuum/commits/{tag}`. It validates the full commit SHA and
artifact metadata, then retains that immutable source pin in the PR contract
and recovery journal. It never substitutes `main`, an older protocol, or an
unapproved development pin. Publication uses the tag `v0.4.0`.

## Publication checklist

1. Run `bash scripts/check-continuum.sh` on the preparation candidate. Record its
   full commit SHA and check evidence in the preparation PR, not in this file.
2. Obtain clean independent review of that candidate against issue #19 and root
   `PR-PLAN.md`. Resolve findings through the normal Draft/write-lease workflow.
3. After review is otherwise clean, use the retained 0.3 finalizer to remove only
   root `PR-PLAN.md`. Confirm the cleanup commit has no substantive changes and
   run required checks on the final head before a separately authorized merge.
4. Identify the exact release commit on `main` after merge. Record the reviewed
   implementation SHA, cleanup SHA, and resulting `main` SHA in GitHub. If merge
   or intervening base changes alter the reviewed release content, obtain fresh
   verification/review before publication. Run the full check on the release
   commit; do not publish an unverified merge result.
5. Obtain separate human authorization to publish `v0.4.0` at that exact commit.
   Create a stable GitHub release, neither draft nor prerelease. Do not move or
   reuse the tag afterward; use immutable-release protections where available.
6. Verify the tag resolves to the authorized commit and GitHub's latest stable
   release reports `v0.4.0`. Confirm the artifact at that pin matches the reviewed
   source. A development pin or passing offline tests cannot establish publication.

After publication, establish the admission gate and full 0.3 drain described in
[migration.md](migration.md), then perform the designated final migration.
The docs-site work in issue #16 follows that boundary.

## Release-note inputs

- PR-native protocol: the PR body retains the current contract and implementation
  plan; comments carry run-scoped ownership, verification, review, and recovery.
- Portable bootstrap: target repositories need no installed protocol or finalizer.
  A temporary `AGENTS.md` discovery pointer preserves permanent instructions.
- Dependency-free reference client: Python 3.9+, Git, and authenticated `gh`, with
  interoperable wire formats that other clients or authorized humans can use.
- Stable source pinning: release discovery resolves the supported version to an
  exact commit; downloaded protocol text is read, never executed.
- Recovery and cleanup: suspension, explicit stopped-owner recovery, digest repair,
  and bounded pointer removal preserve ownership and plan history. Uncertain state
  stops writes; cleanup does not authorize merge.
- Optional `continuum` PR labeling and explicit backfill: labels aid discovery and
  have no authority over contracts or leases. Creation requires consent; failures
  do not block bootstrap.

This release does not migrate the reference repository or deploy the docs site.
