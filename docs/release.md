# Preparing Continuum 0.4.1

PR #27 prepares 0.4.1 and includes the merged PR #26 event-comment presentation:
human-readable summaries, collapsed metadata and compact event JSON. The
`continuum/0.4`, `continuum-event/0.4` and `continuum-pointer/0.4` schemas and
markers stay unchanged, as do lifecycle, leases, parser/replay, cleanup and
recovery semantics.

The canonical artifact front matter, reference client and release-discovery
fixtures support 0.4.1. Stable discovery accepts `v0.4.1` or `0.4.1`, rejects
draft/prerelease or mismatched sources, and pins the resolved exact commit.
This candidate cannot bootstrap from the currently published 0.4.0 release;
use a trusted 0.4.0 checkout until 0.4.1 is published.

## Preparation and publication boundaries

1. Run `bash scripts/check-continuum.sh` and required documentation CI on the
   preparation HEAD. Record check evidence on PR #27.
2. Obtain clean independent review through the normal 0.4 Ready workflow.
3. After review, acquire cleanup ownership, remove only the owned temporary
   pointer, and confirm required checks on the cleanup HEAD.
4. Merge only with separate human merge authority. Identify and verify the exact
   resulting release commit on `main`; changed content requires fresh review.
5. Obtain separate human authorization after merge before creating the immutable
   `v0.4.1` tag and publishing a stable GitHub release at that exact commit.
6. After authorized publication, verify the tag resolves to that commit, the
   latest release is neither draft nor prerelease, and artifact metadata matches.

This preparation PR creates no tag or release and authorizes no deployment.

## Historical 0.4.0 publication

Stable [v0.4.0](https://github.com/Leftium/continuum/releases/tag/v0.4.0) was
published under the owner's authority in issue #19 at exact commit
`76fed3f2fb03df0d7121fc8e026644431de16203`. PR #20 prepared the independently
reviewed candidate. The release is neither draft nor prerelease; its tag resolves
to that commit. Published tags must not move.

Publication and repository migration are separate boundaries. PR #24 removes
the retained 0.3 installation; new work uses stable 0.4 only after its merge.
See [migration.md](migration.md). This document preserves the original 0.4.0
publication procedure and release-note inputs; it authorizes no new release.

## Release contract

The canonical release artifact is `protocol/CONTINUUM.md`, with version `0.4.0`
and artifact path in its front matter. The reference client, contract fixtures,
and documented supported version must agree. At publication, root
`CONTINUUM.md` and its templates remained at 0.3.0 as migration infrastructure.
PR #24 removes them; they were never the 0.4 release artifact.

Stable bootstrap queries `repos/Leftium/continuum/releases/latest`, accepts
`v0.4.0` or `0.4.0`, rejects draft/prerelease results, and resolves the tag via
`repos/Leftium/continuum/commits/{tag}`. It validates the full commit SHA and
artifact metadata, then retains that immutable source pin in the PR contract
and recovery journal. It never substitutes `main`, an older protocol, or an
unapproved development pin. Publication uses the tag `v0.4.0`.

## Historical 0.4.0 publication checklist

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

After publication, the owner established the admission gate in #21 / PR #23.
Issue #22 / PR #24 performs the designated final migration after the full 0.3
drain described in [migration.md](migration.md). The docs-site work in issue #16
follows that merge boundary.

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
