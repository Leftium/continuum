# PR Plan

Issue: #14
Accepted design: `specs/002-pr-local-redesign.md` at `e55c8da75fe826656c2f3263497d0ac2211000e5`.
Clean design review: https://github.com/Leftium/continuum/pull/15#issuecomment-6021590514

## Goal

Implement the accepted PR-native Continuum 0.4 architecture with an interoperable normative protocol and dependency-free reference tooling.

## Scope

- Keep this PR under the existing 0.3 protocol, lease, and finalizer; no implicit self-migration.
- Add `protocol/CONTINUUM.md` and define canonical JSON contract digests, raw repair snapshots, UUID IDs, pointer bytes/provenance, and comment-event state transitions.
- Implement offline validation/repair/pointer primitives and a Git/GitHub CLI for bootstrap, status/validation, cooperative claims/events, and removal/no-op cleanup.
- Add focused fixtures and tests for wire interoperability, failed/concurrent state changes, surgical pointer handling, stale contexts, repair, cleanup, forks, and migration barriers.
- Update self-checks, CI, and user docs while retaining the operational 0.3 installation.
- Do not perform repository migration or publish/tag a release: the documented stable-0.4 prerequisite is not satisfied.

## Checkpoints

1. Normative protocol, schema/pointer/event primitives, and interoperable fixtures.
2. Git/GitHub orchestration, focused workflow tests, and documentation.
3. Full required checks and implementation review; release the 0.3 lease and mark Ready.

Checkpoints are durable savepoints within this writing run, not default handoffs.

## Verify

- Run the existing `bash scripts/check-continuum.sh` including legacy finalizer coverage.
- Run standard-library unit/integration tests against canonical fixtures and temporary Git repositories/fake GitHub adapters; use no live mutation tests.
- Exercise CLI help, validation, contract repair, pointer cleanup, and no-op cleanup.
- Review staged and unstaged diffs, documentation/source consistency, and safe Git destinations before each non-force checkpoint push.
- Preserve the accepted design as rationale; normative rules belong in `protocol/CONTINUUM.md`.
- Release the lease and mark Ready when complete. Do not merge or remove this temporary 0.3 plan until independent review and authorized finalization.
