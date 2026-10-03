# Continuum

Continuum is a GitHub-native workflow for coordinating coding agents and humans across long-running software projects.

The protocol is a **draft** targeting version **0.3.0**.

## Core model

- GitHub **issues** are the canonical units of work.
- GitHub **milestones** optionally group larger outcomes.
- Work ordering is expressed by issue relationships rather than sequence numbers.
- An implementation branch and pull request are created only when work starts.
- Every implementation branch starts with a temporary root **`PR-PLAN.md`** that carries the implementation contract through coding and review, then is deleted by the standard finalizer before merge.
- A leased Continuum PR grants standing approval for routine in-scope, non-destructive repository work unless project or higher-precedence policy narrows it.
- A **checkpoint is a savepoint, not a yield point**: verify, commit, and push each coherent checkpoint, then continue through the plan without asking whether to proceed.
- Agents prefer the existing project worktree and switch it to the PR branch when that is safe; separate worktrees are a fallback for dirty/conflicting or concurrent work.
- A **draft pull request** means implementation is still open; it may rest unleased between writing runs.
- A **write lease** is run-scoped: one writer acquires it before branch writes and releases it before yielding or ending normally.
- If required human approval blocks commit or push, the lease may be explicitly **suspended** across that approval pause; ownership does not transfer.
- Multiple independent draft PRs may coexist, each leased or unleased.
- A **ready pull request** is unleased and write-stopped for implementation. The cleanup-only plan finalizer may still run after review.
- Live workflow state stays in GitHub. `CONTINUUM.md` defines how agents and humans interpret that state.
- Installed `CONTINUUM.md` is vendor-managed protocol text copied verbatim from the accepted Continuum reference; repository-specific workflow policy lives in project-owned `AGENTS.md` content outside the managed Continuum markers or in referenced project docs/specs.

## Repository layout

- `CONTINUUM.md` - vendor-managed Continuum protocol file; installed copies should match the accepted reference exactly.
- `AGENTS.md` - managed Continuum discovery block plus any repository-owned policy outside the managed markers.
- `specs/001-continuum.md` - draft protocol specification.
- `templates/CONTINUUM.md` - installable copy of `CONTINUUM.md`; kept byte-identical by the self-check.
- `templates/PR-PLAN.md` - compact starter for the temporary per-PR root plan.
- `scripts/continuum-finalize-pr.sh` - safe final cleanup; run it with `bash scripts/continuum-finalize-pr.sh` after review is otherwise clean to delete only the temporary root plan, commit, and push.
- `templates/continuum-finalize-pr.sh` - installable copy of that finalizer.
- `scripts/check-continuum.sh` - self-hosting consistency check.

## Planned installation

The planned installer command is:

```sh
le add continuum
```

This command is not implemented yet. When implemented, it should install or update `CONTINUUM.md` as an exact copy of the accepted Continuum reference, make the `PR-PLAN.md` starter and finalizer available, and synchronize only the managed Continuum block in `AGENTS.md`. Repository-specific policy and unrelated agent instructions outside the managed markers must be preserved unchanged. The installer must not create a root `PR-PLAN.md` on the integration branch; that temporary file is created only when an implementation PR starts.

If an agent's GitHub connector cannot perform a bootstrap operation, give the human the exact `gh` CLI command.

## Status

This repository is the reference self-hosted Continuum installation: changes to the protocol should remain valid under the workflow they define.
