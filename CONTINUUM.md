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
3. Treat current Git and GitHub state, together with tracked project policy, as authoritative over stale or private handoff prose.
4. Do not modify an implementation branch unless you hold its write lease.
5. Live workflow state belongs in GitHub; do not duplicate mutable state in this file.

## Repository conventions

- The `continuum` label identifies Continuum workflow issues.
- GitHub issues are the canonical units of work.
- GitHub milestones optionally group larger outcomes.
- Issue relationships express ordering and dependencies; avoid sequence numbers when possible.
- Create implementation branches and pull requests only when work actually starts.
- Prefer the GitHub connector when available. If a required operation is unavailable, give the human an exact `gh` CLI command.

## Write leases

A lease is scoped to one implementation branch and its PR. Independent draft PRs may coexist.

- **Acquiring**: before a PR exists, record the intended writer in the issue. That claim authorizes creating the branch, first commit, push, and draft PR.
- **Abandoned acquisition**: before a draft PR exists, the recorded writer or a human may release or reassign the claim by recording that change on the issue.
- **Draft PR**: one recorded writer may modify that implementation branch. The draft PR supersedes the acquisition claim as the lease signal. Prefer a simple durable writer record such as `Writer: T3 / Codex`.
- **Draft-to-Draft transfer**: the current writer may hand implementation directly to another writer without marking the PR Ready. Push a coherent checkpoint, record the handoff and new writer, then stop writing; the new recorded writer may continue while the PR remains Draft.
- **Ready PR**: writes to that implementation branch have stopped; review or handoff may proceed.
- Agents that do not hold a branch's lease may inspect and review it but must not write to it.
- Concurrent leases are allowed unless issue dependencies or project policy make the work unsafe to overlap.

Before releasing a lease, commit and push all intended changes, verify the branch state, update the durable handoff, then mark the PR ready.

If review requests changes, record the writer and convert that PR back to draft before modifying its branch. Other implementation PRs are unaffected.

This is a cooperative convention rather than an atomic distributed lock. Stronger mechanics may be added later without changing the human-visible Draft and Ready signals.

## Issue lifecycle

A Continuum issue should describe the goal, relevant durable context and decisions, constraints, acceptance criteria, dependencies, and current handoff when active.

Prefer issue comments for durable product and scope decisions, blockers, dependencies, and acceptance changes. Prefer PR comments for implementation checkpoints, commit IDs, verification, review findings, and handoffs for fixes. Link between them instead of repeating long handoffs. Do not copy live GitHub fields, such as Draft/Ready or review status, into tracked files or long-lived PR prose.

When implementation begins:
1. record the intended writer in the issue;
2. create a fresh branch from the accepted base and make the initial commit;
3. create a draft PR linked to the issue;
4. continue work while that PR remains draft.

When implementation finishes:
1. verify the work;
2. update the PR and issue with durable results;
3. mark the PR ready;
4. review and merge;
5. close the issue when its acceptance criteria are satisfied.

## Recovery

When returning after an absence:
1. inspect open Continuum issues;
2. inspect milestone grouping when an issue has one;
3. identify blocked and ready work from issue relationships;
4. inspect linked PRs;
5. interpret each Draft PR as an active branch-scoped lease and each Ready PR as write-stopped and available for review or handoff.

Branches are implementation artifacts, not the project dashboard.

## Bootstrap

If this repository is missing Continuum metadata, create the `continuum` label:

```sh
gh label create continuum \
  --description "Managed by the Continuum workflow" \
  --color 5319E7
```

If the repository has multiple long-lived accepted integration bases, make Continuum discoverable from each base with compatible `AGENTS.md` / `CONTINUUM.md` files or an equally reliable project-policy discovery path.

Project policy may define risk-tiered verification for bounded fixes versus deployment/layout/persistence/runtime-boundary changes. For archaeology or restoration work, it may also require a behavior/semantics inventory before implementation starts.

Create GitHub milestones only when useful for grouping:

```sh
gh api --method POST repos/{owner}/{repo}/milestones \
  -f title='Milestone title'
```

Prefer native GitHub issue dependency and sub-issue relationships when available through the current `gh` version.

## Protocol

See the [Continuum protocol specification](https://github.com/Leftium/continuum/blob/main/specs/001-continuum.md) for protocol and migration guidance.
