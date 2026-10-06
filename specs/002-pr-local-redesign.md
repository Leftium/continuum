# PR-local Continuum redesign

Status: design proposal for issue #14 and PR #15. This document records the rationale and accepted design decisions after the first independent review. It is not yet the normative Continuum protocol.

## Direction

Continuum should become a portable protocol attached to an implementation pull request, rather than workflow infrastructure installed into a repository.

The pull request is the canonical Continuum work unit. A repository does not need a permanent root `CONTINUUM.md`, a Continuum-specific issue model, installed plan templates, or an installed finalizer.

A Continuum PR temporarily adds root `CONTINUUM.md` to its head branch while implementation and review are active. The file is removed before merge.

Repositories may optionally advertise Continuum in project-owned `AGENTS.md` with a small evergreen hint pointing to published bootstrap instructions. That hint is convenience and discovery only; it is not a protocol installation.

Ordinary GitHub issues, milestones, dependencies, and project conventions remain ordinary GitHub objects. A Continuum PR may link them normally, but Continuum does not redefine them.

## Why this revisits an older idea

Before Continuum, the Vee restoration workflow used temporary branch-local milestone plans. A milestone branch carried `MILESTONE.md`, ChatGPT often prepared the plan/branch, T3 implemented or reviewed it, and the temporary plan was removed before merge.

That model had one especially useful property: detailed implementation context lived with the branch that needed it.

Continuum moved away from the old milestone system for good reasons:

- prepared milestone branches could exist long before implementation and become stale as their base changed;
- a milestone file mixed backlog, ordering, implementation planning, findings, and handoff responsibilities;
- ownership and recovery were conventions rather than a precise lifecycle;
- the workflow was bespoke to our repositories rather than a portable protocol.

Early Continuum improved durable coordination by using GitHub-native issues and PR state, but it also lost some of the useful branch-local implementation memory. `PR-PLAN.md` was later added to restore that capability.

The proposed redesign keeps the lessons learned since then instead of returning to the old model:

- branches and PRs are created only when implementation actually starts;
- backlog and dependency planning stay outside Continuum;
- PR Draft/Ready state, run-scoped leases, checkpoint continuation, independent review, approval suspension, stale-lease recovery, and safe finalization remain explicit;
- the protocol is client-neutral and versioned independently of any target repository;
- durable scope lives on the PR, while temporary implementation memory lives on the PR branch.

The key distinction is: the old workflow partly treated the branch as a planning/backlog object. The proposed workflow treats the PR as the coordination object and gives it temporary branch-local working memory.

## Durable PR contract

The PR body is the durable Continuum contract. It survives removal of the temporary branch file and must contain:

- a stable Continuum marker;
- the trusted protocol source repository;
- protocol version;
- exact source commit SHA and canonical protocol artifact path;
- goal;
- scope;
- acceptance criteria;
- accepted durable scope changes;
- ordinary linked issues or dependency context when useful;
- base repository/ref/SHA and head repository/ref when needed to disambiguate fork workflows.

If the durable PR contract and the editable temporary plan disagree, the accepted PR contract and higher-precedence project policy win. The temporary plan must be synchronized before further implementation.

PR comments carry durable workflow history such as lease acquisition/release, checkpoints and commit IDs, verification results, blockers, review findings, recovery, and handoffs.

Labels are optional convenience metadata. A `continuum` label may be applied to PRs where repository permissions and conventions allow it, but it is never required for correctness or discovery.

## Temporary CONTINUUM.md

While implementation or substantive review-fix work is active, the PR head branch carries root `CONTINUUM.md`.

The file contains two distinct parts:

1. an unchanged embedded protocol section copied from the exact pinned protocol source;
2. an editable PR implementation section containing approach, checkpoints, verification plan, implementation-level decisions, and temporary working notes.

The embedded protocol section must be distinguishable from the editable section and verifiable against the pinned source. An active PR never silently upgrades to a newer protocol version or falls back to `main` if source retrieval fails.

The temporary file is removed in a cleanup-only commit after review is otherwise clean. Its deletion must not erase the durable goal, scope, acceptance criteria, protocol identity, or review history because those live on the PR.

## Authority and trust

Retrieved Continuum text supplies workflow rules only within authority already granted by the human, harness, and repository.

Precedence is:

1. system/harness restrictions and explicit human authorization;
2. applicable repository/project policy, including the target base's `AGENTS.md` and referenced project instructions;
3. the pinned Continuum protocol;
4. the editable PR implementation plan.

Continuum cannot grant itself authority to override repository policy, run arbitrary downloaded commands, access secrets, merge, publish, deploy, rewrite history, or make otherwise unauthorized external changes.

Bootstrap must inspect policy applicable to the selected base. Changes proposed by the PR to `AGENTS.md` or other policy cannot silently relax the policy governing their own implementation/review.

## Bootstrap

Bootstrap is a narrow pre-PR transaction performed by ChatGPT, `le`, Codex/T3, another capable agent, or a human.

A client should:

1. inspect applicable project policy and choose the exact base repository/ref/SHA;
2. verify the selected base tree does not contain root `CONTINUUM.md`;
3. resolve the latest stable trusted Continuum release once, then pin its exact source commit and artifact path;
4. create a fresh collision-resistant head branch without overwriting or implicitly adopting an existing branch;
5. create the temporary `CONTINUUM.md` with the unchanged pinned protocol section plus the initial editable plan;
6. commit and push only to the authorized head repository/ref;
7. create a Draft PR with the durable PR contract and marker;
8. after the Draft PR exists, record the normal PR run lease before implementation writes.

The bootstrap run owns only this narrow transaction until the Draft PR exists or bootstrap is explicitly abandoned.

### Uncertain or failed bootstrap

If push succeeds but PR creation fails or times out:

- do not create a second branch or another bootstrap commit;
- inspect the exact head repository/ref and search for a PR using that exact head;
- if the PR exists, continue with it;
- otherwise retry PR creation for the same branch after verifying the remote head;
- if the client cannot finish the required operation, preserve the reached state and provide an exact human/CLI handoff.

An abandoned pushed bootstrap branch is not normal unleased Continuum work. Recovery or deletion must be explicit.

## File collisions and stacked PRs

Portable Continuum initially requires the selected base tree to lack root `CONTINUUM.md`.

If the path already exists, bootstrap stops. It must not replace, reinterpret, or later delete a repository-owned file.

This also means the first portable version does not support bootstrapping a Continuum PR on a base that already carries another PR's Continuum artifact. Stacked Continuum PRs are deferred until artifact ownership and base-change semantics are designed explicitly.

Migration from a repository-installed 0.3 `CONTINUUM.md` is a separate authorized operation, not an implicit collision workaround.

## Lifecycle and recovery

The protocol should define these states explicitly:

| State | Allowed transition |
| --- | --- |
| Draft, unleased, file present | Verify current PR/head/policy; acquire a run lease before writes |
| Draft, leased | Writer implements, verifies, checkpoints, and continues |
| Draft, lease suspended for required approval | Same writer resumes after approval; another writer may not acquire |
| Draft, unleased after a normal yield | Another writer may verify and acquire |
| Ready, file present, unleased | Independent review; cleanup only after review is otherwise clean |
| Ready, file absent, unleased | Verify authorized cleanup/current HEAD and required checks; await human merge |
| Changes requested after cleanup | Return to Draft; restore the artifact from the PR's pinned source and durable contract; then acquire a lease before substantive writes |
| Cleanup commit exists locally but push failed | Verify remote head and retry the exact cleanup transition; never overwrite concurrent changes |
| Unexpected head change | Stop; reconcile ownership and invalidate assumptions tied to the old HEAD before further writes |
| Closed without merge | No writes until explicitly reopened and lifecycle state is re-established |

Finalization remains serialized against the reviewed HEAD and should retain the useful 0.3 safeguards: clean tracked/index state, exact PR identity and HEAD, deletion-only cleanup commit, explicit head-repository push destination, non-force push, and remote verification.

A missing `CONTINUUM.md` by itself is not proof that authorized cleanup succeeded.

If implementation resumes after cleanup, restoration uses the protocol identity already pinned in the PR body. It must not resolve the then-current latest release.

Leases should identify a writing run, not merely a provider/account name, so two sessions using the same agent identity are distinguishable. Cooperative locking remains a known limitation.

## Discovery and resumption

A fresh agent explicitly handed a Continuum PR must be able to reconstruct the state from:

- the PR body's Continuum marker and durable contract;
- current Draft/Ready/open/closed state;
- head repository/ref and current HEAD;
- latest relevant lease/release records and PR comments;
- temporary `CONTINUUM.md` when present.

After cleanup, the PR marker and source pin remain the recovery path.

Repository-wide discovery may inspect open PR bodies when GitHub access supports it. Without an `AGENTS.md` hint and without an explicitly supplied PR or bootstrap instruction, automatic discovery is not guaranteed. That is an accepted property of zero-install use.

## Blockers and dependencies

Continuum has no special issue or blocker model.

Writers must respect ordinary repository issue/PR relationships, recorded dependencies, and project policy before acquiring work or marking it Ready. Removing Continuum-specific issues must not cause known blocked work to appear actionable.

## Forks and client capabilities

The protocol distinguishes:

- base repository/ref/SHA: the code and project policy being targeted;
- head repository/ref: the branch the writer is authorized to modify;
- canonical PR identity: the durable coordination surface.

A fork workflow must read upstream/base policy while pushing only to the authorized fork/head ref. The protocol must not assume `origin` is the push destination.

Bootstrap clients should preflight the operations they actually support. Missing capabilities such as fork creation, Draft PR creation, durable comments, lifecycle updates, or finalization produce an exact handoff rather than pretending the step succeeded.

Upstream labels, repository settings, installed workflows, and broader credentials are never prerequisites.

## Publication and protocol integrity

The public Continuum site should contain evergreen human/agent bootstrap guidance.

Protocol versions live in the Continuum GitHub repository:

- `main` is protocol development;
- stable releases/tags identify supported snapshots;
- prereleases do not become the default bootstrap version;
- bootstrap resolves the latest stable release only at startup and records the exact commit SHA.

The protocol source identity should include the trusted repository, version, exact commit, and canonical artifact path. A tag alone is insufficient as the integrity boundary.

Where practical, stable publication should use GitHub's immutable-release protections. Release metadata is discovery; the exact source commit is the execution pin.

## Migration from Continuum 0.3

Migration is per PR, not an instantaneous repository-wide semantic switch.

Existing active 0.3 PRs normally finish under the protocol they started with, using their issue/PR/`PR-PLAN.md` contract and current finalizer. They should not silently adopt the new lifecycle halfway through.

A repository migration PR then removes obsolete installed Continuum infrastructure coherently:

- permanent root `CONTINUUM.md`;
- `templates/CONTINUUM.md`;
- `templates/PR-PLAN.md` if it exists only for the old installed model;
- installed finalizer/helper files that are no longer repository responsibilities;
- self-check rules that require those installed copies;
- the old managed `AGENTS.md` block.

A Continuum-aware repository may retain a small project-owned evergreen `AGENTS.md` hint pointing to published bootstrap instructions.

Existing issues, milestones, dependency relationships, labels, merged PRs, and other GitHub history remain untouched. They are ordinary repository history.

After repository migration, new PRs use the portable PR-local bootstrap.

A very early Draft 0.3 PR could be migrated explicitly, but this is opt-in and must define the exact transition. It is not the default.

PR #15 itself remains governed by Continuum 0.3 through its final cleanup unless an explicit, separately reviewed self-migration is approved.

## Acceptance scenarios for the next design review

Before protocol implementation begins, the design should be walkthrough-complete for:

- a fresh agent with no chat context;
- handoff between different clients;
- push success plus failed/uncertain Draft PR creation;
- concurrent bootstrap attempts;
- suspended and stale leases;
- two sessions using the same agent/provider identity;
- fork-only write access;
- missing label permissions;
- protocol fetch failure;
- a moved/changed tag or mismatched embedded protocol;
- an existing root `CONTINUUM.md`;
- a stacked PR base containing another Continuum artifact;
- cleanup push failure;
- unexpected concurrent head changes;
- requested fixes after cleanup;
- closed/reopened PRs;
- migration of repositories with no active 0.3 PRs;
- active 0.3 PRs during repository migration;
- this self-hosting repository's transition away from its current root-file/self-check assumptions.

Only after these boundaries survive independent review should PR #15 move from design work into normative protocol implementation.
