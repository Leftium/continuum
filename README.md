# Continuum

Continuum is a GitHub-native workflow for coordinating coding agents and humans across long-running software projects.

The protocol is currently a **draft**. The initial target is version **0.1.0**.

## Core model

- GitHub **issues** are the canonical units of work.
- GitHub **milestones** optionally group larger outcomes.
- Work ordering is expressed by issue relationships rather than sequence numbers.
- An implementation branch and pull request are created only when work starts.
- A **draft pull request** means implementation is still open; it may rest unleased between writing runs.
- A **write lease** is run-scoped: one writer acquires it before branch writes and releases it before yielding or ending normally.
- If required human approval blocks commit or push, the lease may be explicitly **suspended** across that approval pause; ownership does not transfer.
- Multiple independent draft PRs may coexist, each leased or unleased.
- A **ready pull request** is unleased and write-stopped so review or handoff may begin.
- Live workflow state stays in GitHub. `CONTINUUM.md` defines how agents and humans interpret that state.

## Repository layout

- `CONTINUUM.md` - Continuum instructions for this repository.
- `AGENTS.md` - discovery pointer for coding agents.
- `specs/001-continuum.md` - draft protocol specification.
- `templates/CONTINUUM.md` - draft template intended for installation into other repositories.
- `scripts/check-continuum.sh` - self-hosting consistency check.

## Planned installation

The planned installer command is:

```sh
le add continuum
```

This command is not implemented yet. When implemented, it should install or update `CONTINUUM.md` and add a small managed Continuum pointer to `AGENTS.md` without overwriting unrelated agent instructions.

If an agent's GitHub connector cannot perform a bootstrap operation, give the human the exact `gh` CLI command.

## Status

This repository is the reference self-hosted Continuum installation: changes to the protocol should remain valid under the workflow they define.
