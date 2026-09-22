# Continuum protocol 0.1.0-draft

## Status

Draft specification for a GitHub-native workflow that coordinates humans and coding agents across long-running software projects.

## Goals

Continuum should:
- make current project state reconstructable from repository + GitHub state after long absences;
- support multiple agents without requiring shared hidden context;
- make handoffs durable and explicit;
- use GitHub-native objects instead of parallel project-management files where practical;
- work with partial GitHub API access by falling back to exact `gh` CLI commands for humans;
- keep the protocol light enough to add to ordinary repositories.

## Non-goals

Continuum does not attempt to:
- replace GitHub Issues, Pull Requests, Milestones, or Projects;
- provide a fully atomic distributed lock in the initial version;
- require every repository to use GitHub Projects;
- encode mutable live project state in `CONTINUUM.md`;
- require a specific coding agent or model.

## Object model

### GitHub milestone

A GitHub milestone represents a larger outcome or phase. It groups related Continuum issues.

Milestones should use descriptive names rather than ordinal identifiers whenever practical. Due dates should represent real target dates, not synthetic ordering.

### GitHub issue

A GitHub issue is the canonical Continuum unit of work.

An issue may represent implementation, investigation, modernization, comparison, documentation, or another bounded outcome. The generic GitHub term "issue" is intentionally preferred over a parallel Continuum term such as "step" or "work item".

Issues should be ordered by native dependency/blocking relationships where available rather than by embedded sequence numbers. Human-facing ordering inside a milestone may be manually adjusted without becoming protocol-critical state.

### Agent run

A run is one agent taking responsibility for advancing an issue. Runs are conceptual; Continuum 0.1.0 does not require a dedicated GitHub object for them.

A run must leave a durable handoff in the issue or linked PR when responsibility changes.

### Pull request

A PR represents implementation work for an issue.

Implementation branches and PRs should be created only when work starts. Future planned work should remain issues rather than pre-created branches.

### Lease

Continuum 0.1.0 uses PR Draft/Ready state as a cooperative write lease signal:

- Draft = active implementation; one writer owns the lease.
- Ready = writing has stopped; review or handoff may proceed.

The lease owner must be identified durably in the issue or PR handoff. Non-owners may inspect and review but must not write.

This convention is intentionally soft in 0.1.0. A future version may add an atomic ref-backed or API-backed lease while retaining Draft/Ready as the human-visible state.

## State model

Typical lifecycle:

```text
milestone
  -> issue open / ready
      -> issue active
          -> draft PR / lease held
          -> ready PR / lease released
          -> merged PR
      -> issue closed
```

Blocked work remains an open issue with native dependency/blocking relationships where possible.

## Handoffs

A durable handoff should include only information needed by the next agent:
- current goal;
- completed work and verified results;
- durable decisions and rationale;
- relevant constraints;
- exact next action;
- unresolved questions or blockers;
- linked issue/PR/commit identifiers where useful.

Handoffs should not depend on chat history.

## Recovery

A returning human or agent should be able to reconstruct state by:

1. reading `AGENTS.md` and `CONTINUUM.md`;
2. opening the relevant GitHub milestone;
3. inspecting open Continuum issues and their dependency relationships;
4. inspecting linked PRs;
5. interpreting Draft as active implementation and Ready as review/handoff.

Branch listings are secondary diagnostics, not the canonical project overview.

## Discovery and installation

A repository participates in Continuum when it contains a root `CONTINUUM.md`.

`AGENTS.md` should contain a small pointer directing agents to read it. Installers must preserve unrelated `AGENTS.md` content and should own only a clearly delimited managed section.

The intended installer is:

```sh
le add continuum
```

The installer should be idempotent.

## GitHub metadata

The minimal recommended metadata is:
- label: `continuum`;
- one or more descriptive GitHub milestones when grouping is useful;
- Continuum issues assigned to those milestones;
- implementation PRs linked to active issues.

Agent-specific labels such as `agent:t3`, `agent:chatgpt`, or `agent:codex` are optional. Mutable state should not be duplicated in labels when GitHub already provides it directly.

## Connector and CLI interoperability

Agents should prefer a connected GitHub tool when it supports the requested operation.

When it does not, the agent should provide a precise `gh` command for the human to run. This is part of the normal workflow, not an exceptional failure mode.

Examples of likely CLI-only operations include:
- creating/editing labels when the connector only applies labels;
- creating/editing GitHub milestones;
- GitHub Projects operations;
- native issue dependency/sub-issue operations when not exposed through the connector;
- other authenticated GitHub API actions reachable through `gh api`.

## Versioning

Continuum uses semantic versioning for the protocol itself.

During the draft phase:
- `0.x` versions may change protocol semantics;
- minor releases represent meaningful protocol revisions;
- patch releases represent compatible clarifications/fixes where practical.

After `1.0.0`:
- patch = behavior-preserving clarification/fix;
- minor = backward-compatible capability;
- major = protocol change that may cause an older compliant agent to behave incorrectly.

Installed `CONTINUUM.md` files should declare the protocol version they target.

## Open questions for 0.1.0

- Exact owner representation for the cooperative write lease.
- Whether Continuum should standardize optional agent labels.
- Whether GitHub Projects should have a recommended optional profile.
- Exact native dependency/sub-issue conventions across current `gh` versions.
- Whether stronger atomic lease mechanics are needed in practice.
- How `le continuum check` and `le continuum update` should detect and migrate protocol versions.
