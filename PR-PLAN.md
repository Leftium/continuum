# PR Plan

Issue: #14

## Goal

Refine the PR-native Continuum 0.4 design until canonical PR-body ownership, temporary AGENTS pointer safety, live target reconciliation, stacking exclusion, cleanup recovery, and the 0.3 migration boundary are explicit enough for another independent design review.

## Scope

- Keep PR #15 governed by Continuum 0.3; do not self-migrate it implicitly.
- Preserve the architecture: PR body = canonical contract/current plan, PR comments = workflow history, Git = product history, temporary AGENTS block = bootstrap/discovery only.
- Extend cooperative ownership to the Continuum-controlled PR-body section with revision/digest checks and evidence binding.
- Define the temporary block/workflow as valid only during exact bootstrap or on the associated open PR head; stale appearances elsewhere warn the developer and grant no authority.
- Tighten AGENTS whole-file cleanup so permanent/foreign content always survives.
- Add general target/head reconciliation, canonical stacking detection, and an exclusive cleanup claim/retry state machine.
- Add a durable 0.3 migration admission gate and explicit post-migration reopening/conversion path.
- Do not implement normative 0.4 until the revised design receives another independent review.

## Verify

- Every finding from T3's third design review has an explicit rule, state transition, or deliberate limitation.
- Checkpoints/review/cleanup bind to an accepted contract revision/digest + HEAD + target tuple.
- A human or concurrent body edit cannot be silently overwritten by a cooperating writer.
- Cleanup cannot delete a base-owned or permanent Continuum-only AGENTS file.
- Retargeting/head changes stop and reconcile in Draft, Ready, and cleanup states.
- A cleaned-up unmerged Continuum parent is still rejected as an unsupported stacked base.
- Cleanup ownership is mutually exclusive with implementation leases and has defined failed/uncertain-push recovery.
- Migration blocks new/in-flight 0.3 admission, drains resumable work, and requires explicit 0.4 handling for reopened old PRs.
- No normative 0.4 implementation, tests, release/tag publication, or actual 0.4 pointer is added in this design checkpoint.
- Before eventual merge, accepted durable design knowledge is promoted to final normative/docs locations and this temporary 0.3 `PR-PLAN.md` is removed under 0.3 cleanup.
