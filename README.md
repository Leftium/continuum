# Continuum

Continuum is a GitHub-native workflow for coordinating coding agents and humans across long-running software projects.

The protocol is currently a **draft**. The initial target is version **0.1.0**.

## Core model

- GitHub **issues** are the canonical units of work.
- GitHub **milestones** optionally group larger outcomes.
- Work ordering is expressed by issue relationships rather than sequence numbers.
- An implementation branch and pull request are created only when work starts.
- A **draft pull request** signals one writer's lease on that implementation branch.
- Multiple independent draft PRs may coexist.
- A **ready pull request** signals that writes to its branch have stopped and review/handoff may begin.
- Live workflow state stays in GitHub. `CONTINUUM.md` defines how agents and humans interpret that state.

## Repository layout

- `CONTINUUM.md` - Continuum instructions for this repository.
- `AGENTS.md` - discovery pointer for coding agents.
- `specs/001-continuum.md` - draft protocol specification.
- `templates/CONTINUUM.md` - draft template intended for installation into other repositories.
- `scripts/check-continuum.sh` - self-hosting consistency check.

## Planned installation

The intended installation path is:

```sh
le add continuum
```

That command is not implemented yet. It is intended to install or update `CONTINUUM.md` and add a small managed Continuum pointer to `AGENTS.md` without overwriting unrelated agent instructions.

GitHub bootstrap operations that are not available through an agent's GitHub connector can be delegated to a human with explicit `gh` CLI commands.

## Status

Draft 0.1.0. This repository is also the reference self-hosted Continuum installation: changes to the protocol should remain valid under the workflow they define.
