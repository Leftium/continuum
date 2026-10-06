# PR Plan

Issue: #14

## Goal

Refine the Continuum redesign into a PR-native protocol whose canonical contract and implementation plan live on the pull request, with only a temporary discovery/bootstrap pointer in `AGENTS.md`.

## Scope

- Keep PR #15 governed by Continuum 0.3; do not self-migrate it implicitly.
- Replace the proposed temporary root `CONTINUUM.md` with PR-body canonical state + PR-comment workflow history.
- Use a small temporary, non-authoritative `AGENTS.md` pointer only to create/bootstrap the branch and help agents locate the PR.
- Incorporate all remaining findings from T3's second design review, including exact lease transitions, resumable bootstrap identity, cleanup ownership, and a strict active-0.3 migration boundary.
- Preserve the historical constraint against prepared future branches.
- Do not implement the normative 0.4 protocol until another independent design review is clean.

## Verify

- T3 can review `specs/002-pr-local-redesign.md` and the PR body without chat context.
- The new architecture makes deleted-plan recovery and root `CONTINUUM.md` collision findings obsolete rather than adding compensating complexity.
- Every remaining T3 finding has an explicit rule or state transition.
- PR body remains the current canonical plan; significant contract changes also leave durable PR comments.
- The pointer cannot override base policy and cleanup can remove only the exact owned block.
- Acceptance walkthroughs include deferred future planning, uncertain bootstrap, lease failures, post-cleanup fixes, AGENTS conflicts, forks, and 0.3 migration.
- No normative 0.4 implementation, tests, release/tag publication, or actual 0.4 AGENTS pointer is added in this design-only checkpoint.
- Before eventual merge, accepted durable design knowledge is promoted to final normative/docs locations and this temporary 0.3 `PR-PLAN.md` is removed under 0.3 cleanup.
