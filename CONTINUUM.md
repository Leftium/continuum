---
continuum: 0.1.0
status: draft
---

# Continuum

This repository uses the Continuum multi-agent workflow.

## Start here

Humans:
- Issues: https://github.com/Leftium/continuum/issues
- Pull requests: https://github.com/Leftium/continuum/pulls
- Milestones: https://github.com/Leftium/continuum/milestones

Agents:
1. Read this file before coordinating or modifying work.
2. Inspect open Continuum issues and pull requests.
3. Do not modify repository files unless you hold the active write lease.
4. A draft implementation pull request represents the active write lease.
5. A ready pull request means writes have stopped and review/handoff may begin.
6. Live workflow state belongs in GitHub; do not duplicate mutable state in this file.

## Repository conventions

- The `continuum` label identifies Continuum workflow issues.
- GitHub milestones group larger outcomes.
- GitHub issues are the canonical units of work.
- Issue relationships express ordering and dependencies; avoid sequence numbers when possible.
- Create implementation branches and pull requests only when work actually starts.
- Prefer the GitHub connector when available. If a required operation is unavailable, give the human an exact `gh` CLI command.

## Write lease

The implementation PR is the lease signal.

- **Draft PR**: one agent may write to the implementation branch.
- **Ready PR**: no agent should write; review/handoff is pending.
- Before writing, verify the PR is draft and that the current handoff identifies you as the writer.
- Before releasing the lease, commit and push all intended changes, verify the branch state, update the handoff, then mark the PR ready.
- Agents that do not hold the lease may inspect and review but must not write.

This is initially a cooperative convention rather than an atomic distributed lock. If real write collisions appear, the protocol may add stronger lease mechanics without changing the human-visible Draft/Ready signal.

## Issue lifecycle

A Continuum issue should describe:
- goal;
- relevant context and durable decisions;
- constraints and preserved behavior;
- acceptance criteria;
- dependencies or blocking relationships;
- current handoff when active.

When implementation begins:
1. create a fresh branch from the accepted base;
2. create a draft PR linked to the issue;
3. record the current writer/handoff;
4. perform the work while the PR remains draft.

When implementation finishes:
1. verify the work;
2. update the PR and issue with durable results;
3. mark the PR ready;
4. review and merge;
5. close the issue when its acceptance criteria are satisfied.

## Recovery

When returning after an absence:
1. open the current GitHub milestone;
2. inspect its open Continuum issues;
3. identify blocked/ready work from issue relationships;
4. inspect any linked PR;
5. interpret Draft as active write ownership and Ready as review/handoff.

Branches are implementation artifacts, not the project dashboard.

## Bootstrap

If this repository is missing Continuum metadata, create the `continuum` label:

```sh
gh label create continuum \
  --description "Managed by the Continuum workflow" \
  --color 5319E7
```

Create GitHub milestones as needed:

```sh
gh api --method POST repos/{owner}/{repo}/milestones \
  -f title='Milestone title'
```

Prefer native GitHub issue dependency/sub-issue relationships when available through the current `gh` version.

## Protocol

The draft protocol specification for this repository lives at `specs/001-continuum.md`.
The installable template for other repositories lives at `templates/CONTINUUM.md`.
