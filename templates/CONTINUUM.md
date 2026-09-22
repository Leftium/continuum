---
continuum: 0.1.0
status: draft
---

# Continuum

This repository uses the Continuum multi-agent workflow.

## Start here

Humans:
- Issues: {{issues_url}}
- Pull requests: {{pull_requests_url}}
- Milestones: {{milestones_url}}

Agents:
1. Read this file before coordinating or modifying work.
2. Inspect open Continuum issues and pull requests.
3. Treat current Git/GitHub state plus tracked project policy as authoritative over stale or private handoff prose.
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

A lease is scoped to one implementation branch/PR. Independent draft PRs may coexist.

- **Acquiring**: before a PR exists, record the intended writer in the issue. That claim authorizes creating the branch, first commit, push, and draft PR.
- **Abandoned acquisition**: before a draft PR exists, the recorded writer or a human may release or reassign the claim by recording that change on the issue.
- **Draft PR**: one recorded writer may modify that implementation branch. The draft PR supersedes the acquisition claim as the lease signal.
- **Ready PR**: writes to that implementation branch have stopped; review/handoff may proceed.
- Agents that do not hold a branch's lease may inspect and review it but must not write to it.
- Concurrent leases are allowed unless issue dependencies or project policy make the work unsafe to overlap.

Before releasing a lease, commit and push all intended changes, verify the branch state, update the durable handoff, then mark the PR ready.

If review requests changes, record the writer and convert that PR back to draft before modifying its branch. Other implementation PRs are unaffected.

This is a cooperative convention rather than an atomic distributed lock. Stronger mechanics may be added later without changing Draft/Ready as the human-visible signal.

## Issue lifecycle

A Continuum issue should describe the goal, relevant durable context and decisions, constraints, acceptance criteria, dependencies, and current handoff when active.

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
3. identify blocked/ready work from issue relationships;
4. inspect linked PRs;
5. interpret each Draft PR as an active branch-scoped lease and each Ready PR as write-stopped review/handoff state.

Branches are implementation artifacts, not the project dashboard.

## Bootstrap

If this repository is missing Continuum metadata, create the `continuum` label:

```sh
gh label create continuum \
  --description "Managed by the Continuum workflow" \
  --color 5319E7
```

Create GitHub milestones only when useful for grouping:

```sh
gh api --method POST repos/{owner}/{repo}/milestones \
  -f title='Milestone title'
```

Prefer native GitHub issue dependency/sub-issue relationships when available through the current `gh` version.

## Protocol

For the protocol specification and migration guidance, see:
https://github.com/Leftium/continuum/blob/main/specs/001-continuum.md
