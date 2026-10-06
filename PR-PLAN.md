# PR Plan

Issue: #14

## Goal

Close the two remaining recovery gaps in the PR-native Continuum 0.4 design: repair of human-edited invalid contract metadata, and cleanup verification when a post-cleanup fix cycle intentionally leaves the optional AGENTS pointer absent.

## Scope

- Keep PR #15 governed by Continuum 0.3; do not self-migrate it implicitly.
- Preserve the current PR-native architecture.
- Add an exclusive contract-repair transition for invalid revision/digest metadata, including held-lease and unleased cases.
- Ensure repair accepts an exact authorized raw snapshot, restores valid metadata, preserves unrelated PR content, and blocks implementation until validation succeeds.
- Add verified no-op cleanup that separates historical pointer-removal provenance from current readiness/review evidence.
- Preserve fail-closed handling for genuinely unexplained pointer absence.
- Make the designated final migration PR's exemption from the 0.3 admission gate explicit.
- Do not implement normative 0.4 until another independent design review is clean.

## Verify

- A human can edit the canonical plan without manually calculating protocol metadata; the next client has an executable repair path.
- An invalid digest cannot be bypassed by normal lease acquisition, cleanup, or implementation writes.
- Repair ownership is exclusive and recoverable if its run terminates.
- A second Ready cycle after pointer cleanup can complete cleanup without restoring/removing the pointer again.
- No-op cleanup proves historical authorized removal while validating the new current tuple independently.
- Unexplained pointer absence still stops for human recovery.
- The final migration PR is the sole recorded exception to the no-new-0.3 gate.
- Acceptance scenarios cover unleased/held invalid-digest repair and pointer-free second Ready cleanup.
- No normative 0.4 implementation, tests, releases/tags, or actual 0.4 pointer changes occur in this design checkpoint.
- Before eventual merge, accepted durable design knowledge is promoted to final normative/docs locations and this temporary 0.3 `PR-PLAN.md` is removed under 0.3 cleanup.
