# PR Plan

Issue: #7

## Goal

Ship Continuum 0.3.0-draft with two execution refinements:

1. a checkpoint is a durable savepoint, not a yield point; a leased writer continues through all planned checkpoints by default;
2. the cleanup finalizer pushes explicitly to the PR head branch and tolerates bounded GitHub PR-head propagation lag.

Also make standing authorization operational enough that agents stop asking for separate approval for routine tests, checks, builds, commits, non-force pushes, and continuation to the next planned checkpoint.

## Scope

- Bump protocol/template/spec/README references from 0.2.0-draft to 0.3.0-draft.
- Define checkpoint vs handoff/yield vs approval suspension.
- Strengthen managed `AGENTS.md` guidance and installation requirements.
- Update the PR-plan template so checkpoint sections are not interpreted as stop points.
- Harden the finalizer and keep its installable template byte-identical.
- Strengthen self-checks and add compact shell regression coverage for the finalizer if practical.
- Do not implement installer/update tooling or propagate 0.3.0 into other repositories in this PR.

## Checkpoint A — execution semantics

Update the protocol, self-hosted/template `CONTINUUM.md`, managed `AGENTS.md`, PR-plan template, and README so a leased run:

- continues through all planned checkpoints without asking to continue;
- commits and non-force-pushes coherent checkpoints as durable savepoints;
- runs plan-required formatting/tests/checks/builds without separate approval where repository policy can grant it;
- yields only for scope/product decisions, operations outside standing authorization, external blockers, or an ending harness/run;
- releases the lease only when actually yielding/ending or when implementation finishes.

Keep existing safety exclusions and higher-precedence restrictions.

Verify root/template synchronization and protocol-version consistency.

## Checkpoint B — finalizer hardening

Refactor `scripts/continuum-finalize-pr.sh` and its template so finalization:

- verifies current branch and open Ready PR state;
- obtains the PR head repository/branch;
- identifies a usable Git remote for the PR head repository;
- pushes with an explicit refspec rather than relying on upstream configuration;
- verifies the remote branch ref reached local HEAD;
- polls `gh pr view --json headRefOid` for a bounded interval;
- reports a clear propagation-lag error only after the remote ref is already correct.

Preserve cleanup-only behavior: tracked-clean worktree, exact current PR HEAD before deletion, only root `PR-PLAN.md` staged, one cleanup commit.

## Checkpoint C — regression checks

Strengthen `scripts/check-continuum.sh`.

Prefer a compact fake-`git`/`gh` shell harness that exercises the finalizer without network access. At minimum cover:

- no configured upstream / explicit push path;
- successful remote-ref update;
- stale PR head for several polls then convergence;
- genuine push failure;
- mismatched PR head/branch;
- dirty tracked worktree.

If a fake-command harness becomes disproportionately complex, keep static/syntax checks explicit and document the remaining integration boundary rather than building a framework.

## Checkpoint D — final verification and handoff

Run the repository self-check and any added focused finalizer tests. Inspect the complete diff for template drift and accidental weakening of safety exclusions.

Record verification and implementation decisions on the PR, release the lease, and mark Ready for independent review. Leave root `PR-PLAN.md` for review.

## Verify

- `bash scripts/check-continuum.sh`
- any focused finalizer regression script added by Checkpoint C
- `bash -n scripts/continuum-finalize-pr.sh`
- `cmp scripts/continuum-finalize-pr.sh templates/continuum-finalize-pr.sh`
- diff review for synchronized protocol/template semantics
