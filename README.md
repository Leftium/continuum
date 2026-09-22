# Continuum

Continuum is a GitHub-native workflow for coordinating coding agents and humans across long-running software projects.

The protocol is currently a **draft**. The initial target is version **0.1.0**.

## Core model

- GitHub **milestones** group larger outcomes.
- GitHub **issues** are the canonical units of work.
- Work ordering is expressed by issue relationships rather than sequence numbers.
- An implementation branch and pull request are created only when work starts.
- A **draft pull request** signals an active write lease.
- A **ready pull request** signals that writes have stopped and review/handoff may begin.
- Live workflow state stays in GitHub. `CONTINUUM.md` defines how agents and humans interpret that state.

## Repository layout

- `CONTINUUM.md` - Continuum instructions for this repository.
- `AGENTS.md` - discovery pointer for coding agents.
- `specs/001-continuum.md` - draft protocol specification.
- `templates/CONTINUUM.md` - draft template intended for installation into other repositories.

## Installation direction

The intended installation path is:

```sh
le add continuum
```

That command should install or update `CONTINUUM.md` and add a small managed Continuum pointer to `AGENTS.md` without overwriting unrelated agent instructions.

GitHub bootstrap operations that are not available through an agent's GitHub connector can be delegated to a human with explicit `gh` CLI commands.

## Status

Draft 0.1.0. The protocol and installable template are expected to change before the first stable release.
