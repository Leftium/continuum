# Continuum protocol 0.1.0-draft

## Status

Draft specification for a GitHub-native workflow that coordinates humans and coding agents across long-running software projects.

## Goals

Continuum should:
- make current project state reconstructable from repository and GitHub state after long absences;
- support multiple agents without requiring shared hidden context;
- support safe concurrent work on independent issues;
- make handoffs durable and explicit;
- use GitHub-native objects instead of parallel project-management files where practical;
- work with partial GitHub API access by falling back to exact `gh` CLI commands for humans;
- keep the protocol light enough to add to ordinary repositories.

## Non-goals

Continuum does not attempt to:
- replace GitHub Issues, Pull Requests, Milestones, or Projects;
- provide a fully atomic distributed lock in the initial version;
- prevent all merge conflicts between independently leased branches;
- require every repository to use GitHub Projects or milestones;
- encode mutable live project state in `CONTINUUM.md`;
- require a specific coding agent or model.

## Object model

### GitHub milestone

A GitHub milestone optionally represents a larger outcome or phase. It groups related Continuum issues when that grouping is useful.

Milestones should use descriptive names rather than ordinal identifiers whenever practical. Due dates should represent real target dates, not synthetic ordering.

### GitHub issue

A GitHub issue is the canonical Continuum unit of work.

An issue may represent implementation, investigation, modernization, comparison, documentation, or another bounded outcome. Issues should be ordered by native dependency and blocking relationships where available rather than by embedded sequence numbers.

### Agent run

A run is one agent taking responsibility for advancing an issue. Runs are conceptual; Continuum 0.1.0 does not require a dedicated GitHub object for them.

A run must leave a durable handoff in the issue or linked PR when responsibility changes. A run that writes to an implementation branch must acquire its write lease before writing and release it before yielding control or ending normally, except when the run is explicitly suspended while waiting for required human approval.

### Pull request

A PR represents implementation work for an issue.

Implementation branches and PRs should be created only when work starts. Future planned work should remain issues rather than pre-created branches.

### Write lease

A write lease grants one recorded writer exclusive permission to modify one implementation branch during an active writing run.

PR lifecycle state and write ownership are separate:

- Draft = implementation is still open. A Draft PR may be unleased between writing runs.
- Ready = implementation is write-stopped and available for review or handoff. A Ready PR must not have an active write lease.
- Write lease = one recorded writer may modify the Draft PR's branch for the current writing run.

Each lease is scoped to one implementation branch and its PR, not the repository. Multiple Draft implementation PRs may coexist when their work can safely proceed concurrently, and each may be either leased or unleased.

Before modifying an existing implementation branch, a writer must verify the current branch HEAD and durably acquire the lease. Prefer a simple explicit record such as `Writer: T3 / Codex`; the latest unreleased writer record is the cooperative lease-owner record unless project policy defines another representation. Non-owners may inspect and review the branch but must not write to it.

A writing run must release its lease before yielding control to the human or ending normally, even when implementation remains incomplete. Releasing a lease does not make a Draft PR Ready. The normal resting state for incomplete work is therefore Draft + no active lease.

The exception is an approval pause: if the writer cannot create the required durable checkpoint because commit, push, or another necessary write operation requires human approval, the run may yield while retaining the lease in a suspended state. A suspended lease still excludes other writers and is not a normal resting state.

Issue dependencies or tracked project policy may prohibit concurrency even when separate branches exist. Continuum does not attempt to lock files or subsystems across otherwise independent PRs.

#### Lease acquisition before a PR exists

Because a Draft PR normally requires a branch and commit first, an issue may carry a temporary acquisition claim:

1. verify the issue is ready to begin;
2. record the intended writer durably on the issue;
3. that claim authorizes only the bootstrap work needed to create the implementation branch, initial commit, push, and Draft PR;
4. once the Draft PR exists, the bootstrap claim ends; before further writes, acquire the PR branch's run-scoped lease.

The acquisition claim is issue-scoped. It must not be interpreted as repository-wide ownership. If acquisition is abandoned before a Draft PR exists, the recorded writer or a human may release or reassign the claim. The release or reassignment must be recorded durably on the issue before another writer proceeds.

#### Lease lifecycle on an existing Draft PR

A Draft PR may pass through many writing runs without becoming Ready for review.

To begin a writing run:

1. verify the PR is Draft and the branch HEAD is the expected checkpoint;
2. verify no other writer holds the lease;
3. durably record the writer and acquire the lease;
4. only then modify the implementation branch.

Before a normal run ends or yields control:

1. stop at a coherent checkpoint;
2. commit and push all intended checkpoint changes;
3. record a durable handoff when context is needed by the next run;
4. durably release the lease.

The PR remains Draft if implementation is incomplete. The same writer may reacquire it in a later run, or a different writer may acquire it after verifying the checkpoint. A transfer is therefore logically release + acquire, even if future tooling performs both operations atomically.

#### Approval pause

If a writer must obtain required human approval before it can commit, push, or perform another operation needed to create the durable checkpoint, it cannot satisfy the normal release sequence yet. In that case:

1. durably record that the lease is suspended for approval and identify the blocked operation;
2. retain the lease while yielding to the human;
3. do not make unrelated branch writes while suspended;
4. after approval, resume the same writing run, perform the approved operation, create the durable checkpoint, and release normally.

A suspended lease is still held by its recorded writer, so another writer must not acquire the branch. Approval itself does not transfer ownership.

If the human decides not to resume the suspended run, the human may explicitly abandon it and recover the lease. That recovery accepts that any uncommitted or unpushed work from the suspended run may be discarded; it must not be assumed to exist in shared GitHub state. Record the abandonment and resulting unleased or newly acquired state durably.

If a run terminates abnormally before releasing its lease, a human may recover an evidently stale lease after establishing that the recorded writer is no longer actively writing. The recovery and resulting ownership state must be recorded durably.

#### Requested changes

A Ready PR remains write-stopped during review.

When review requires fixes:

1. convert the PR back to Draft;
2. acquire a run-scoped write lease at the current branch HEAD;
3. apply and verify the fixes;
4. release the lease;
5. return the PR to Ready only when implementation is again complete.

Other PR-scoped leases are unaffected.

This convention is intentionally soft in 0.1.0. A future version may add an atomic ref-backed or API-backed lease while retaining Draft and Ready as the human-visible state.

## State model

Typical lifecycle for one issue:

```text
open ready issue
  -> acquisition claim; writer recorded
  -> branch + initial commit
  -> draft PR; no active lease
      -> writing run acquires lease at current HEAD
      -> write
          -> if approval blocks checkpoint: suspended lease
          -> approval -> resume same run
      -> commit / push / handoff
      -> writing run releases lease
      -> draft PR; no active lease
      -> repeat as needed
  -> implementation complete + verified
  -> ready PR; no active lease
      -> approved -> merged
      -> changes requested
          -> draft PR
          -> writing run acquires lease
          -> fixes / verify / release
          -> ready PR
  -> merged PR
  -> issue acceptance verified
  -> issue closed
```

Several issues may occupy the draft-PR state concurrently when dependencies and project policy permit.

Blocked work remains an open issue with native dependency and blocking relationships where possible.

## Authoritative state and inference

Continuum state should be reconstructable from shared repository and GitHub state plus tracked project policy. A private chat transcript or previous agent's prose summary may explain context, but it is not authoritative when it conflicts with current shared state.

The precedence is:

```text
Git and GitHub live state
  + tracked Continuum or project policy
  = authoritative workflow state

handoff prose
  = explanatory context
```

Tracked files and PR bodies should describe durable policy, scope, rationale, and facts instead of copying mutable GitHub state, such as Draft/Ready status, review stage, or the current writer. If prose becomes stale, live GitHub state and the latest durable writer record remain authoritative.

A fresh capable agent should normally be able to determine:
- the current workflow state;
- what work is complete, active, blocked, or pending;
- the next permitted or required action;
- which implementation branches currently have leases and who owns them;
- any project-policy constraint that applies to the next action.

Two agents observing the same authoritative state and policy should normally infer the same workflow state, constraints, and set of permitted next actions. Continuum does not impose a global priority rule among simultaneously actionable work; project-specific policy may refine the generic lifecycle.

### Roles belong to work, not agent identities

Implementation, investigation, review, verification, and similar terms describe work or workflow stages. Continuum does not permanently assign those roles to ChatGPT, T3, Codex, or another harness.

The human may choose any capable agent for a stage unless project policy imposes a constraint. Changing agents does not itself change workflow state.

### Generic next-action semantics

For the standard implementation lifecycle:

```text
open ready issue, no implementation PR
  -> record writer and acquire enough authority to create branch + draft PR

draft implementation PR, no lease
  -> implementation is incomplete and available for a writing run

draft implementation PR, active lease
  -> recorded writer may write until that run reaches a checkpoint

approval required before checkpoint can be made durable
  -> record suspended lease and blocked operation
  -> yield for approval while retaining ownership
  -> after approval, resume the same run and create the checkpoint

end of writing run
  -> push coherent checkpoint, record needed handoff, release lease
  -> remain Draft unless implementation is complete

ready implementation PR
  -> no active lease; branch is write-stopped and review or handoff may begin

review requests changes
  -> convert PR to Draft, acquire lease at current HEAD, implement fixes, verify, release lease, then return to Ready

merged implementation PR
  -> verify issue acceptance criteria; if they are satisfied, close the issue and reassess downstream dependencies
```

Blocked issues remain blocked regardless of agent availability. Project policy may add stages or constraints, but should do so durably so another agent can reach the same conclusion.

Project policy may also set verification by risk. A bounded parser or documentation fix may need fewer checks than a deployment, layout, persistence, or runtime-boundary change. The required checks must be explicit, and the branch must be verified before its lease is released.

For archaeology, restoration, or migration work that depends on historical behavior, project policy may require a behavior or semantics inventory before implementation. This is an optional readiness refinement, not a required Continuum lifecycle stage.

### Relational workflow constraints

Project policy may define constraints between runs rather than fixed agent assignments. For example, a project may require review by a run independent from the implementation run.

Such constraints should be represented as project policy or durable handoff state only when needed. They should not be encoded as permanent provider-specific role assignments.

## Handoffs

A durable handoff should include only information needed by the next agent:
- current goal;
- completed work and verified results;
- durable decisions and rationale;
- relevant constraints;
- exact next action;
- unresolved questions or blockers;
- linked issue, PR, or commit identifiers where useful.

Prefer putting durable product/scope decisions, blockers, dependencies, and acceptance changes on the issue. Prefer putting implementation checkpoints, commit identifiers, verification, review findings, and fix-pass handoffs on the PR. Cross-link instead of duplicating long mutable handoffs across both objects.

Handoffs should not depend on chat history.

## Recovery

A returning human or agent should be able to reconstruct state by:

1. reading `AGENTS.md` and `CONTINUUM.md`;
2. inspecting open Continuum issues;
3. inspecting a milestone when an issue is assigned to one;
4. inspecting issue dependency relationships;
5. inspecting linked PRs;
6. interpreting each Draft PR as incomplete implementation that may or may not have an active run-scoped lease, and each Ready PR as write-stopped with no active lease and available for review or handoff.

Branch listings are secondary diagnostics, not the canonical project overview.

## Discovery and installation

A repository participates in Continuum when it contains a root `CONTINUUM.md`.

`AGENTS.md` should contain a small pointer directing agents to read it. Installers must preserve unrelated `AGENTS.md` content and should own only a clearly delimited managed section.

If a repository has multiple long-lived accepted integration bases from which Continuum work may begin, each base should carry compatible Continuum discovery files or project policy must provide an equally reliable discovery path. A fresh agent starting from any accepted base should not silently miss the protocol.

The planned installer is:

```sh
le add continuum
```

It is not implemented yet. The installer should be idempotent.

## GitHub metadata

The minimal recommended metadata is:
- label: `continuum`;
- Continuum issues;
- implementation PRs linked to active issues.

Descriptive GitHub milestones are optional when grouping is useful.

Agent-specific labels such as `agent:t3`, `agent:chatgpt`, or `agent:codex` are optional. Mutable state should not be duplicated in labels when GitHub already provides it directly.

## Connector and CLI interoperability

Agents should prefer a connected GitHub tool when it supports the requested operation.

When it does not, the agent should provide a precise `gh` command for the human to run. This is part of the normal workflow, not an exceptional failure mode.

Examples of likely CLI-only operations include:
- creating or editing labels when the connector only applies labels;
- creating or editing GitHub milestones;
- GitHub Projects operations;
- native issue dependency and sub-issue operations when not exposed through the connector;
- other authenticated GitHub API actions reachable through `gh api`.

## Versioning

Continuum uses semantic versioning for the protocol itself.

During the draft phase:
- `0.x` versions may change protocol semantics;
- minor releases represent meaningful protocol revisions;
- patch releases represent compatible clarifications or fixes where practical.

After `1.0.0`:
- patch = behavior-preserving clarification or fix;
- minor = backward-compatible capability;
- major = protocol change that may cause an older compliant agent to behave incorrectly.

Installed `CONTINUUM.md` files should declare the protocol version they target.

## Protocol acceptance scenarios

The draft protocol should remain coherent under at least these scenarios:

1. A fresh agent with no chat history reconstructs the current state, constraints, and permitted next actions from repository and GitHub state and tracked policy.
2. Two capable agents observing the same authoritative state infer the same workflow state, constraints, and set of permitted next actions.
3. The human switches harnesses for the same workflow stage without changing project policy.
4. A writer can acquire work from an open issue and legally create the branch, first commit, and draft PR.
5. An abandoned pre-PR acquisition claim can be durably released or reassigned without leaving ambiguous ownership.
6. A Draft PR may rest with no active writer; before modifying it, a run verifies the current HEAD and acquires the single-writer lease.
7. A normal writing run releases its lease before yielding or ending, even when the PR remains Draft and implementation is incomplete.
8. The same writer or another writer may later acquire an unleased Draft PR at its current checkpoint without passing through Ready.
9. Two independent Draft PRs may be worked concurrently by different writers when each holds only its own branch lease.
10. A Ready PR has no active write lease and is unambiguously write-stopped and available for review or handoff.
11. Review-requested fixes do not begin until the PR returns to Draft and a writer acquires its run-scoped lease.
12. A writer blocked on required approval before commit or push may yield with a durably recorded suspended lease; no other writer may acquire the branch during that pause.
13. After approval, the suspended writer can resume, create the durable checkpoint, and release normally; if the human abandons the run instead, lease recovery explicitly accepts that unpushed work may be discarded.
14. An evidently stale lease left by an abnormally terminated run can be durably recovered without treating the writer as the permanent owner.
15. An issue blocked by native dependency relationships is not treated as ready merely because an agent is available.
16. A merged PR causes the issue acceptance criteria and downstream dependencies to be reconsidered.
17. A private or stale handoff that conflicts with current GitHub state does not override the shared state.
18. A project-specific relational constraint, such as independent review, can be discovered by a fresh agent without encoding permanent agent identities.
19. A fresh agent starting from any accepted long-lived integration base can discover that the repository uses Continuum.

## Open questions for 0.1.0

- Exact machine-readable representation for run-scoped lease acquisition, ownership, and release.
- Whether Continuum should standardize optional agent labels.
- Whether GitHub Projects should have a recommended optional profile.
- Exact native dependency and sub-issue conventions across current `gh` versions.
- Whether stronger atomic lease mechanics, transfer tooling, approval-pause tooling, or stale-lease detection are needed in practice.
- How `le continuum check` and `le continuum update` should detect and migrate protocol versions.
