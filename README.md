# Continuum

Continuum is a GitHub-native workflow for coordinating coding agents and humans across long-running software projects.

**0.4 keeps the current contract and implementation plan in the PR body.** Comments
carry run-scoped ownership, verification, review and recovery. A temporary
`AGENTS.md` pointer provides branch discovery and is removed after clean review.
Cleanup cannot delete the plan. Issues retain ordinary GitHub semantics.

Read the canonical [0.4 protocol](protocol/CONTINUUM.md) and
[reference client instructions](docs/client.md). The dependency-free client uses
Python 3.9+, Git and `gh`; other clients can perform the same transactions.
Stable release discovery pins an exact source commit and stops until a supported
stable 0.4 release exists. Explicit development pins support authorized testing.

The 0.4 protocol/client and optional PR-labeling implementation have merged.
This reference repository **remains governed by 0.3** until its gated migration.
The installed root protocol/templates/finalizer below are intentionally retained.
Removal requires the admission gate, full drain, stable 0.4 release and designated
final migration described in [migration instructions](docs/migration.md).
See the [release checklist](docs/release.md) for the 0.4.0 publication boundary.

## Retained 0.3 model

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

- `protocol/CONTINUUM.md` - canonical 0.4 protocol and interoperable wire formats.
- `scripts/continuum.py`, `scripts/continuum_core.py` - 0.4 client and offline primitives.
- `tests/` - digest/repair fixtures, lifecycle and temporary Git integration tests.
- `specs/002-pr-local-redesign.md` - accepted architecture and historical constraints.
- `CONTINUUM.md` - vendor-managed Continuum protocol file; installed copies should match the accepted reference exactly.
- `AGENTS.md` - managed Continuum discovery block plus any repository-owned policy outside the managed markers.
- `specs/001-continuum.md` - draft protocol specification.
- `templates/CONTINUUM.md` - installable copy of `CONTINUUM.md`; kept byte-identical by the self-check.
- `templates/PR-PLAN.md` - compact starter for the temporary per-PR root plan.
- `scripts/continuum-finalize-pr.sh` - safe final cleanup; run it with `bash scripts/continuum-finalize-pr.sh` after review is otherwise clean to delete only the temporary root plan, commit, and push.
- `templates/continuum-finalize-pr.sh` - installable copy of that finalizer.
- `scripts/check-continuum.sh` - self-hosting consistency check.

## Legacy installation proposal

The planned installer command is:

```sh
le add continuum
```

This unimplemented installation proposal belongs to 0.3. Version 0.4 uses portable
bootstrap instead of repository installation and does not create root protocol
or plan files. Its target repository needs no labels, settings changes or upstream
installed machinery.

Bootstrap offers optional `continuum` PR labeling and a separate backfill choice.
Label creation requires explicit consent; missing permissions or label failures
do not block bootstrap. See [client instructions](docs/client.md#bootstrap) for
noninteractive create/skip flags and `label sync`. Canonical PR-body metadata
remains authoritative.

If an agent's GitHub connector cannot perform a bootstrap operation, give the human the exact `gh` CLI command.

## Status

Run `bash scripts/check-continuum.sh` for both versions' checks, or
`python3 -m unittest discover -s tests` for the offline 0.4 suite. Tests do not
mutate live GitHub state. Implementing 0.4 does not publish, migrate or merge.
