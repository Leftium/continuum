# Continuum

Continuum is a GitHub-native workflow for coordinating coding agents and humans across long-running software projects.

**0.4 keeps the current contract and implementation plan in the PR body.** Comments
carry run-scoped ownership, verification, review and recovery. A temporary
`AGENTS.md` pointer provides branch discovery and is removed after clean review.
Cleanup cannot delete the plan. Issues retain ordinary GitHub semantics.

Read the canonical [0.4 protocol](protocol/CONTINUUM.md) and
[reference client instructions](docs/client.md). The dependency-free client uses
Python 3.9+, Git and authenticated `gh`; other clients can perform the same
transactions. Stable bootstrap resolves the supported release to an exact source
commit and retains that pin in the PR contract.

Stable [v0.4.0](https://github.com/Leftium/continuum/releases/tag/v0.4.0) is
published at `76fed3f2fb03df0d7121fc8e026644431de16203`. This tree removes the
retained 0.3 installation. New implementation work uses stable 0.4 after the
[final migration PR #24](https://github.com/Leftium/continuum/pull/24) merges;
that PR itself remains governed by 0.3 through review, plan-only finalization
and merge. The project-owned admission gate in [AGENTS.md](AGENTS.md) remains
active through that boundary. See [migration instructions](docs/migration.md)
and the [publication record](docs/release.md).

## Starting work

Use portable bootstrap from a trusted client checkout. Version 0.4 needs no
installed root protocol, plan template or finalizer in the target repository.
The PR body stores the plan; a temporary pointer preserves existing `AGENTS.md`
instructions. Read selected-base policy and ordinary blockers before bootstrap,
then acquire run-scoped ownership before implementation writes.

A leased PR grants standing authority for routine in-scope, non-destructive work
where repository and higher-precedence policy allow it. Verify, commit and push
coherent checkpoints, then continue the plan. Release ownership before yielding
or ending normally; explicit approval suspension retains ownership. Ready PRs
are write-stopped for implementation and require clean independent review before
bounded pointer cleanup. Merge requires separate authority.

Bootstrap offers optional `continuum` PR labeling and a separate backfill choice.
Label creation requires explicit consent; missing permissions or label failures
do not block bootstrap. See [client instructions](docs/client.md#bootstrap) for
noninteractive create/skip flags and `label sync`. Canonical PR-body metadata
remains authoritative.

## Repository layout

- `protocol/CONTINUUM.md` - canonical 0.4 protocol and interoperable wire formats.
- `scripts/continuum.py`, `scripts/continuum_core.py` - reference client and offline primitives.
- `tests/` - digest/repair fixtures, lifecycle and temporary Git integration tests.
- `AGENTS.md` - project-owned workflow guidance and migration-gate history.
- `docs/` - client instructions, migration boundary and publication record.
- `specs/001-continuum.md` - historical 0.3 design specification, not active workflow guidance.
- `specs/002-pr-local-redesign.md` - accepted 0.4 architecture and historical constraints.
- `scripts/check-continuum.sh` - canonical source validation and offline client tests.

## Verification

Run `bash scripts/check-continuum.sh` for canonical source validation and the
full offline suite, or `python3 -m unittest discover -s tests` for tests alone.
Tests use fixtures and temporary local Git repositories; they do not mutate
live GitHub state. Checks do not publish releases, deploy or merge.
