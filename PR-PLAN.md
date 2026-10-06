# PR Plan

Issue: #14

## Goal

Refine the PR-local Continuum redesign until its ownership, recovery, trust, migration, and historical rationale are explicit enough for a second independent design review.

## Scope

- Keep PR #15 under the existing Continuum 0.3 lifecycle; do not self-migrate this active PR implicitly.
- Record the historical relationship to the pre-Continuum temporary milestone-plan workflow and the reasons Continuum moved away from that system.
- Incorporate the first T3 review into a concrete design proposal covering the durable PR contract, PR marker/discovery, bootstrap ownership and retry behavior, file collisions, finalization/reopening, protocol integrity and policy precedence, fork/head/base identity, blockers, and 0.3 migration.
- Treat the PR body as the durable design contract for this PR; use this file only as temporary 0.3 implementation/review working memory.
- Do not implement the normative 0.4 protocol until the revised design receives another independent review.

## Verify

- T3 can review `specs/002-pr-local-redesign.md` and the PR body without this chat context.
- The proposal explicitly answers every numbered finding from the first T3 review.
- The proposal preserves the useful post-milestone Continuum properties: create branches only when work starts, Draft/Ready lifecycle, run-scoped leases, checkpoint continuation, approval suspension, safe workspace handling, independent review, and recoverable cleanup.
- Acceptance scenarios cover fresh-agent recovery, uncertain bootstrap, collision/stacking, forks, source integrity, concurrent changes, post-cleanup fixes, and 0.3 migration.
- No normative 0.4 implementation, tests, or release/tag publication occurs before the second design review.
- Before eventual merge, promote accepted durable protocol knowledge to its final normative/docs locations and remove this temporary root `PR-PLAN.md` through the current 0.3 finalizer.
