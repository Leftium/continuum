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

A run must leave a durable handoff in the issue or linked PR when responsibility changes.

### Pull request

A PR represents implementation work for an issue.

Implementation branches and PRs should be created only when work starts. Future planned work should remain issues rather than pre-created branches.

### Write lease

A write lease grants one recorded writer exclusive permission to modify one implementation branch.

Continuum 0.1.0 uses PR Draft and Ready states as the normal cooperative lease signals:

- Draft = the PR's implementation branch has an active write lease.
- Ready = that branch's lease is released; review or handoff may proceed.

Each lease is scoped to one implementation branch and its PR, not the repository. Multiple draft implementation PRs may coexist when their work can safely proceed concurrently.

The lease owner must be identified durably in the issue or PR handoff. Prefer a simple explicit record such as `Writer: T3 / Codex`; the latest explicit writer record for a Draft PR is the cooperative lease-owner record unless project policy defines another representation. Non-owners may inspect and review the branch but must not write to it.

Issue dependencies or tracked project policy may prohibit concurrency even when separate branches exist. Continuum does not attempt to lock files or subsystems across otherwise independent PRs.

#### Lease acquisition before a PR exists

Because a draft PR normally requires a branch and commit first, an issue may carry a temporary acquisition claim:

1. verify the issue is ready to begin;
2. record the intended writer durably on the issue;
3. that claim authorizes only the bootstrap work needed to create the implementation branch, initial commit, push, and draft PR;
4. once the draft PR exists, it supersedes the acquisition claim as the lease signal.

The acquisition claim is issue-scoped. It must not be interpreted as repository-wide ownership. If acquisition is abandoned before a draft PR exists, the recorded writer or a human may release or reassign the claim. The release or reassignment must be recorded durably on the issue before another writer proceeds.

#### Draft-to-Draft writer transfer

A Draft PR may change writers without becoming Ready for review. This is useful when implementation is still active but responsibility changes because of harness switching, usage exhaustion, specialization, or another handoff.

The current writer must:

1. stop at a coherent checkpoint;
2. commit and push all intended checkpoint changes;
3. record a durable handoff and the new writer;
4. stop writing to the implementation branch.

The new recorded writer may then continue on the same Draft PR. The PR remains Draft throughout; Ready must not be used merely to signal an implementation handoff.

#### Requested changes

A Ready PR remains write-stopped during review.

When review requires fixes:

1. select and durably record the writer for that PR;
2. convert the PR back to Draft;
3. only then modify its implementation branch;
4. return it to Ready after fixes and verification.

Other PR-scoped leases are unaffected.

This convention is intentionally soft in 0.1.0. A future version may add an atomic ref-backed or API-backed lease while retaining Draft and Ready as the human-visible state.

## State model

Typical lifecycle for one issue:

```text
open ready issue
  -> acquisition claim; writer recorded
  -> branch + initial commit
  -> draft PR; branch lease held
  -> ready PR; branch lease released
      -> approved -> merged
      -> changes requested
          -> writer recorded
          -> draft PR; branch lease reacquired
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

Tracked files and PR bodies should describe durable policy, scope, rationale, and facts rather than duplicate mutable GitHub workflow state such as the current Draft/Ready status, current review stage, or current writer. When such prose becomes stale, live GitHub state and the latest durable ownership record remain authoritative.
```

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

draft implementation PR
  -> implementation is active; recorded writer owns that branch's lease

ready implementation PR
  -> that branch is write-stopped; review or handoff may begin

review requests changes
  -> record writer, convert that PR to draft, then implement fixes

merged implementation PR
  -> verify issue acceptance criteria; if they are satisfied, close the issue and reassess downstream dependencies
```

Blocked issues remain blocked regardless of agent availability. Project policy may add stages or constraints, but should do so durably so another agent can reach the same conclusion.

Project policy may also define risk-tiered verification. A bounded parser or documentation fix need not run the same verification matrix as a deployment, layout, persistence, or runtime-boundary change, provided the required checks are explicit and the branch is verified before its lease is released.

For archaeology, restoration, or migration work where correctness depends on historical behavior, project policy may require a behavior or semantics inventory before implementation begins. This is an optional readiness refinement, not a mandatory Continuum lifecycle stage.

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
6. interpreting each Draft PR as an active branch-scoped lease and each Ready PR as write-stopped and available for review or handoff.

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
6. A draft PR is unambiguously recognized as a single-writer lease for its implementation branch.
7. Two independent draft PRs may be worked concurrently by different writers.
8. A ready PR is unambiguously recognized as write-stopped and available for review or handoff.
9. A Draft PR may transfer directly from one recorded writer to another at a pushed coherent checkpoint without passing through Ready.
10. Review-requested fixes do not begin until that PR returns to Draft with a recorded writer.
11. An issue blocked by native dependency relationships is not treated as ready merely because an agent is available.
12. A merged PR causes the issue acceptance criteria and downstream dependencies to be reconsidered.
13. A private or stale handoff that conflicts with current GitHub state does not override the shared state.
14. A project-specific relational constraint, such as independent review, can be discovered by a fresh agent without encoding permanent agent identities.
15. A fresh agent starting from any accepted long-lived integration base can discover that the repository uses Continuum.

## Open questions for 0.1.0

- Exact owner representation for acquisition claims and cooperative write leases.
- Whether Continuum should standardize optional agent labels.
- Whether GitHub Projects should have a recommended optional profile.
- Exact native dependency and sub-issue conventions across current `gh` versions.
- Whether stronger atomic lease mechanics are needed in practice.
- How `le continuum check` and `le continuum update` should detect and migrate protocol versions.
