# PR-native Continuum redesign

Status: design proposal for issue #14 and PR #15. This document records the current design after two independent reviews. It is not yet the normative Continuum protocol.

## Direction

Continuum should become a portable protocol whose canonical coordination state lives on a GitHub pull request, rather than workflow infrastructure installed into a repository or a temporary protocol/plan file committed to each implementation branch.

The pull request is the Continuum work unit.

A repository does not need:
- a permanent root `CONTINUUM.md`;
- a temporary per-PR `CONTINUUM.md`;
- a Continuum-specific issue model;
- installed plan templates;
- an installed finalizer.

Ordinary GitHub issues, milestones, dependencies, projects, and labels remain ordinary repository mechanisms. A Continuum PR may link or respect them normally, but Continuum does not redefine them.

The target repository may optionally carry a small permanent, project-owned hint in `AGENTS.md` that points agents to evergreen Continuum bootstrap guidance. That hint is not a protocol installation.

During bootstrap and while a Continuum PR is active, the implementation branch may carry a small temporary Continuum pointer block in `AGENTS.md`. The block is discovery/recovery metadata only. It does not contain the protocol, implementation plan, or authority to override project policy.

A Continuum workflow instance is valid only in one of two contexts:

1. the narrow bootstrap transaction on its dedicated head branch before the Draft PR exists; or
2. the exact head branch of its associated open Continuum PR.

Continuum is never activated merely because a temporary pointer appears on a target/default/integration branch or an unrelated branch. If an agent finds the temporary block outside its valid bootstrap/PR context, the block grants no authority: stop Continuum writes and inform the developer that stale state, incorrect ancestry, or missed cleanup may exist. Do not auto-delete the block without normal ownership/recovery checks. The published Continuum protocol may be read anywhere; a workflow instance is valid only in the contexts above.

## Why this revisits an older idea without returning to it

Before Continuum, the Vee restoration workflow used temporary branch-local milestone plans. A milestone branch carried `MILESTONE.md`, ChatGPT often prepared the plan/branch, T3 implemented or reviewed it, and the temporary plan was removed before merge.

That model had one especially useful property: detailed implementation context stayed close to the work.

Continuum moved away from the old milestone system for good reasons:
- prepared milestone branches could exist long before implementation and become stale as their base changed;
- a milestone file mixed backlog, ordering, implementation planning, findings, and handoff responsibilities;
- ownership and recovery were conventions rather than a precise lifecycle;
- the workflow was bespoke to our repositories rather than a portable protocol.

Early Continuum improved durable coordination by using GitHub-native issues and PR state, but it also lost some useful implementation memory. `PR-PLAN.md` was later added to restore that capability.

The proposed redesign keeps the later lessons:
- branches and PRs are created only when implementation actually starts;
- future planning/backlog/dependency management remains outside Continuum;
- Draft/Ready state, run-scoped leases, checkpoint continuation, approval suspension, stale-owner recovery, safe workspaces, and independent review remain explicit;
- the protocol is client-neutral and versioned independently of any target repository;
- the PR carries the durable contract and current implementation plan;
- PR comments carry operational history;
- Git carries only product/source changes plus a temporary bootstrap/discovery pointer when needed.

The key distinction is: the old workflow partly treated a prepared branch as a planning/backlog object. The proposed workflow treats the PR as the coordination object.

### Negative historical constraint

If a human asks an agent to prepare a plan for a future milestone while implementation is explicitly deferred, the client must not create a Continuum branch or Draft PR. Planning remains in ordinary issues, project docs, discussions, or another repository-native planning surface until implementation is actually starting.

Recovery of an interrupted bootstrap is exceptional state recovery, not an available queue of prepared future branches.

## Canonical state

### PR body: current canonical contract and plan

A Continuum PR body owns the current canonical state needed to understand and resume the work:

- stable Continuum marker;
- bootstrap ID;
- protocol source repository;
- protocol version;
- exact source commit SHA;
- canonical protocol artifact path;
- base repository/ref and accepted target/base identity;
- head repository/ref;
- goal;
- scope;
- acceptance criteria;
- current implementation plan;
- current verification plan;
- accepted durable scope/plan changes;
- ordinary linked issues/dependencies when useful;
- recovery notes when a non-normal transition requires them.

The PR body is the current truth. GitHub's edit history is useful supporting history, but Continuum should not depend on body-edit retention as its only audit or recovery mechanism.

The Continuum-controlled body section carries a `contract-revision` and `contract-digest`. The digest covers the controlled section under a defined normalization while excluding the digest field itself. A cooperating client that changes the controlled section must:

1. re-read the current body;
2. verify the expected revision and digest;
3. preserve all unrelated PR-description content;
4. apply the authorized change;
5. increment the revision and recompute the digest;
6. write the replacement; and
7. re-read and verify the resulting revision/digest.

During Draft implementation, the active run-scoped write lease owns cooperative mutation of both the head branch and the Continuum-controlled PR-body section. Reviewers and other agents comment instead of rewriting that section. The lease does not create GitHub permissions: a client that cannot edit the PR body must hand the exact contract edit to an authorized human/PR author, then re-read and reconcile the resulting revision before continuing.

Humans remain authoritative and may edit the PR body at any time. A human edit that changes the controlled section, or causes its recorded digest to stop matching, is an external contract change. The active writer must stop, reconcile the new content, and obtain any required human/project decision before further implementation. Scope or acceptance changes require human/project authority unless that authority was explicitly delegated.

Workflow-significant changes to scope, acceptance criteria, target identity, or a reviewed implementation plan must also leave a durable PR comment explaining the change. Routine clarifications and formatting edits outside the controlled section need not create separate comments.

Checkpoint, verification, Ready, review, and cleanup evidence bind to an accepted state tuple:

```text
contract revision + contract digest
+ PR HEAD
+ target repository/ref + checked target/base SHA
```

A material controlled-section change creates a new contract revision and invalidates evidence whose assumptions it changes. A Ready PR with a material contract change returns to Draft before implementation resumes. Independent review and cleanup must state or be reconstructable against the accepted tuple they evaluated.

If the PR body conflicts with a previous plan revision, the latest valid accepted controlled-section revision wins, subject to higher-precedence project policy. If the body conflicts with live GitHub state, live PR state, branch HEAD, target fields, and the latest valid ownership record govern mutable workflow state; the disagreement is a reconciliation condition rather than permission to overwrite either side.

### PR comments: event and handoff history

PR comments own durable workflow events where chronology matters, including:
- lease acquisition, suspension, release, recovery, or transfer;
- checkpoints and relevant commit IDs;
- verification results worth preserving;
- significant contract/plan changes and rationale;
- blockers and handoffs;
- review findings and fix handoffs;
- bootstrap recovery or abandonment;
- cleanup results and exceptional recovery.

A checkpoint comment is required only when it carries durable evidence or context; checkpoints remain savepoints, not default yield points.

### Git: product history

Git should contain implementation, tests, durable product/project documentation, and other repository knowledge that belongs in the project itself.

Coordination metadata should not be committed merely to obtain Git versioning. Durable implementation knowledge discovered during a PR must be promoted into appropriate code, tests, specs, or documentation before the PR becomes Ready when that knowledge is needed after the PR closes.

## Protocol publication and pinning

The public Continuum site should contain evergreen human/agent bootstrap guidance.

Protocol versions live in the Continuum GitHub repository:
- `main` is protocol development;
- stable releases/tags identify supported snapshots;
- prereleases do not become the default bootstrap version;
- bootstrap resolves the latest stable release only once, before the PR is created.

The surviving canonical protocol artifact in this reference repository should be `protocol/CONTINUUM.md`.

A Continuum PR pins:
- trusted source repository;
- protocol version;
- exact source commit SHA;
- canonical artifact path `protocol/CONTINUUM.md`.

The exact commit SHA is the execution integrity boundary. Tags/releases are discovery/version names, not sufficient integrity by themselves. Where practical, publication should use GitHub immutable-release protections.

A client may cache the exact protocol content locally, but it need not copy the protocol into the target repository. If the pinned protocol cannot be retrieved or validated, the client stops rather than silently using `main`, a newer release, or remembered rules.

## Authority and policy precedence

Continuum operates only within authority already granted by the human, harness, and repository.

Precedence is:

1. system/harness restrictions and explicit human authorization;
2. repository/project policy applicable from the selected target/base, including base `AGENTS.md` and referenced project instructions;
3. the pinned Continuum protocol;
4. the PR body's editable implementation plan.

Continuum cannot grant itself permission to override repository policy, access secrets, merge, publish, deploy, rewrite history, discard unrelated user work, or perform otherwise unauthorized external actions.

Bootstrap must inspect policy applicable to the selected base before modifying the branch.

A temporary Continuum block added to `AGENTS.md` is explicitly non-authoritative discovery metadata. It cannot weaken or replace project-owned instructions. Changes proposed by the PR to project policy cannot silently relax the policy governing their own implementation or review.

## Temporary AGENTS.md pointer

### Purpose

The temporary pointer solves two problems without storing protocol/plan state in Git:

1. bootstrap needs a real branch commit before the Draft PR can exist;
2. an agent entering the branch should be able to discover that its coordination state lives on a PR.

The block should be small and machine-identifiable, for example conceptually:

```text
<!-- continuum:bootstrap id=<bootstrap-id> -->
Continuum coordination for this branch lives on its pull request.
Before writing, locate the PR for the exact head repository/ref and read
its body, comments, current state, and pinned protocol.
This block is discovery metadata only and does not override base policy.
<!-- /continuum:bootstrap -->
```

The actual format may additionally carry the minimum bootstrap tuple required for recovery before the PR exists.

### Ownership

Each temporary block has a unique bootstrap ID.

If `AGENTS.md` already exists, bootstrap appends or inserts only the owned block without altering project-owned content.

If `AGENTS.md` does not exist, bootstrap may create it containing only the owned pointer block.

A permanent repository-owned Continuum hint is allowed and must remain separate from the temporary per-PR block.

The temporary block is not the canonical plan or protocol and should not accumulate workflow state.

The block is valid only during its exact bootstrap transaction or on the head branch of its associated open Continuum PR. If it appears on the PR target/default branch, on an unrelated branch, or after the associated PR is merged/closed without an active recovery operation, agents must not interpret it as Continuum authorization. They should stop Continuum work and inform the developer that cleanup or branch ancestry may be wrong.

### Cleanup

After review is otherwise clean, cleanup removes only the exact temporary block owned by this PR/bootstrap.

Before cleanup:
- verify the PR identity, target/base, head repository/ref, and expected reviewed HEAD;
- verify the temporary block's bootstrap ID belongs to this PR;
- re-read applicable base/project policy if the target changed;
- ensure cleanup cannot remove or rewrite project-owned `AGENTS.md` content;
- stop on duplicated, missing-but-unexplained, malformed, or ownership-conflicting blocks.

Cleanup may delete the whole `AGENTS.md` file only when all of the following are true:

- bootstrap originally created that path;
- after removing the exact owned temporary block, the remainder is empty apart from bootstrap-owned whitespace; and
- the current accepted target/base does not own `AGENTS.md`.

Every other byte is preserved, including permanent repository-owned Continuum hints, foreign Continuum blocks, comments, and unrelated agent instructions. Initial creation provenance never overrides later base ownership. If path ownership or provenance is uncertain, cleanup stops instead of deleting the file.

Cleanup uses a cleanup-only commit and non-force push. It does not authorize merge or waive repository checks.

If project-owned `AGENTS.md` changes due to a rebase or retarget, reconcile by preserving the live base content plus the owned pointer. Never resolve conflicts by replacing base policy with the temporary pointer.

## Bootstrap

Bootstrap is a narrow transaction performed by ChatGPT, `le`, Codex/T3, another capable agent, or a human.

Before branch creation, generate a collision-resistant bootstrap ID and run ID and establish the intended tuple:

- host;
- bootstrap ID;
- initiating run ID;
- selected base repository/ref/SHA;
- authorized head repository/ref;
- pinned protocol repository/version/SHA/path.

A client should then:

1. inspect the selected base and applicable project policy;
2. verify implementation is actually starting, not merely being planned for later;
3. preflight required client capabilities;
4. create a fresh collision-resistant head branch without overwriting or implicitly adopting an existing branch;
5. add the temporary `AGENTS.md` pointer containing the bootstrap identity and recovery tuple;
6. commit and push that bootstrap state to the authorized head repository/ref;
7. record the resulting bootstrap commit SHA in the bootstrap handoff/recovery data available to the initiating run;
8. create a Draft PR whose body contains the canonical Continuum marker, the same bootstrap identity/tuple, goal/scope/acceptance/current plan, bootstrap commit SHA, and initial valid contract revision/digest;
9. verify the created PR's base repository/ref, head repository/ref, open/Draft state, marker, bootstrap ID, contract revision/digest, and current remote HEAD;
10. before any further branch or Continuum-controlled PR-body writes, acquire the normal PR run-scoped lease.

No issue claim is required.

The bootstrap run owns only the narrow bootstrap transaction. That ownership does not authorize implementation writes after the Draft PR exists.

### Failed or uncertain PR creation

If the bootstrap commit was pushed but Draft PR creation fails or times out:

- do not create a second branch or second bootstrap commit;
- inspect the exact head repository/ref;
- read the pointer block and verify the bootstrap ID and intended tuple;
- verify the remote HEAD still equals the expected bootstrap commit;
- search for a PR using that exact head repository/ref;
- if exactly one PR exists, verify its target/base, state, marker/bootstrap ID when present, and ownership before continuing;
- if no PR exists and the original run is still active, retry creation for the same branch/tuple;
- if the original run terminated, a human must explicitly authorize recovery or abandonment before another run continues;
- if the client lacks the required capability, preserve state and provide an exact human/CLI handoff rather than pretending bootstrap completed.

If the PR was retargeted during an uncertain result, do not simply continue. Revalidate applicable policy and require explicit acceptance of the new target before resuming.

An orphan bootstrap branch is not backlog and is not implicitly available for another agent to adopt.

## Target and head reconciliation

The live PR target and head can change independently of the branch commit a writer last inspected. Unexpected target/head changes are stop conditions in every lifecycle phase.

### Target repository/ref change

If the base repository or base ref changes unexpectedly:

- an active writer stops branch/body writes and records the lease as suspended for target reconciliation;
- a Ready PR is no longer assumed review-valid and returns to Draft before substantive continuation;
- an active cleanup claim stops and must be cancelled or recovered before any implementation lease can start;
- applicable target policy, blockers/dependencies, merge diff, and project assumptions are re-read;
- a human/project authority explicitly accepts the new target or restores the previous one;
- the canonical PR contract is synchronized to the accepted target under a new contract revision/digest;
- evidence tied to the prior target is invalidated to the extent its assumptions changed.

If the temporary pointer was already cleaned up and the accepted retarget requires substantive work, return to Draft, acquire a normal write lease, and only then restore the pointer if branch-local discovery is needed.

### Advancement of the same base ref

Ordinary movement of the same accepted base ref does not automatically require a new contract revision or full re-review. Before Ready, cleanup, and merge, however, the client must check the current target/base SHA and re-evaluate material policy, dependency, and merge-diff effects. Material effects trigger the same reconciliation path as a target change.

### Unexpected head change

If remote PR HEAD differs from the expected checkpoint during a writing run or cleanup claim, stop. Do not overwrite or force-push. Reconstruct the source of the advancement, reconcile ownership and contract/evidence assumptions, and use human stale-owner/recovery rules when cooperative ownership is ambiguous.

## Write lease lifecycle

A write lease grants one recorded run exclusive cooperative permission to modify one Draft PR's head branch **and the Continuum-controlled section of that PR body**.

Lease identity must distinguish runs, not merely provider/account names.

### Acquisition

To begin a writing run:

1. verify the PR is open and Draft;
2. verify target/base identity and current head repository/ref;
3. verify current branch HEAD is the expected checkpoint;
4. verify the canonical contract revision/digest;
5. verify no active/suspended write lease and no active cleanup claim exists;
6. check recorded blockers/dependencies and applicable project policy;
7. durably record the run ID/writer, expected HEAD, accepted target, and contract revision/digest and acquire the lease;
8. only then modify the branch or Continuum-controlled PR-body section.

Acquisition is cooperative rather than atomic. If any expected value changes before the first write, the run stops and re-acquires/reconciles instead of proceeding on stale assumptions.

### Checkpoints and normal release

During an active run:
1. reach a coherent state;
2. run appropriate verification;
3. commit and non-force-push the checkpoint;
4. when durable evidence is recorded, bind it to the relevant contract revision/digest, HEAD, and target identity;
5. continue through the accepted plan without releasing merely because a checkpoint was reached.

Before a normal run ends or yields:
1. make shared state coherent, committed, and pushed;
2. record a handoff when context is needed;
3. durably release the lease.

If implementation is incomplete, the PR remains Draft and unleased.

A transfer is release plus acquisition, even if tooling later performs it atomically.

### Becoming Ready

A PR must not become Ready while an active or suspended write lease exists.

To become Ready:
1. complete the accepted implementation/plan;
2. promote durable repository knowledge that must survive the PR into code/tests/docs/specs and include it in review;
3. complete required verification;
4. ensure all branch work is committed and pushed;
5. revalidate the current contract revision/digest, HEAD, target repo/ref, and checked target/base SHA;
6. durably record the Ready/review tuple;
7. release the lease;
8. mark the PR Ready.

Any material contract/target/head change after that tuple is recorded invalidates affected Ready/review assumptions and requires reconciliation before merge.

### Approval suspension

If required human approval blocks an operation needed to form a durable checkpoint:
1. durably record the suspended lease and blocked operation;
2. retain the lease;
3. make no unrelated branch writes while suspended;
4. after approval, the same run resumes, performs the approved operation, checkpoints, and continues or releases normally.

Approval itself does not transfer ownership.

If the human decides not to resume a suspended run, the human may explicitly abandon it and recover the lease. Record abandonment and acknowledge that uncommitted/unpushed work may be lost.

### Stale/abnormal owner recovery

If a run terminates abnormally while holding a lease, another run may not simply acquire it.

A human must establish that the recorded writer is no longer actively writing, then durably record stale-owner recovery and the resulting ownership state.

Recovery never assumes unpushed work exists in shared state.

### Review changes while the pointer is present

When review requires substantive fixes:
1. return the PR to Draft;
2. verify current HEAD/target;
3. acquire a lease;
4. apply and verify fixes;
5. release;
6. return to Ready only when complete.

### Review changes after pointer cleanup

If review requests substantive changes after the temporary `AGENTS.md` pointer was cleaned up:
1. return the PR to Draft;
2. verify current PR/head/target and canonical PR body;
3. acquire the run lease **before any branch write**;
4. restore the owned temporary pointer block using the same bootstrap ID/tuple if branch-local discovery is desired by the protocol;
5. verify the pointer and current PR state;
6. continue implementation.

If the run crashes after acquiring the lease but before restoring the pointer, the held lease remains authoritative. Recovery follows suspended/stale-owner rules; another run must not write merely because the pointer is absent.

The implementation plan itself needs no restoration because the current plan remains in the PR body.

### Closure and reopening

Closing a PR does not silently dispose of a held lease.

If a PR is closed while a lease is active or suspended, record whether the run was stopped, abandoned, or explicitly completed. No further writes occur while closed.

Reopening does not automatically reactivate a previous lease. Re-establish Draft/Ready state and acquire a fresh run lease before new writes.

## Discovery and resumption

A fresh agent explicitly handed a Continuum PR reconstructs state from:
- PR body marker and canonical contract/plan;
- protocol pin;
- current open/Draft/Ready state;
- base/head repository/ref and current HEAD;
- latest relevant lease/release/recovery comments;
- review state and required checks;
- temporary `AGENTS.md` pointer when present.

A fresh agent entering an active branch can use the temporary pointer to locate the exact head repository/ref and then the associated PR. The pointer does not replace reading the PR.

After pointer cleanup, the PR remains self-describing. No implementation plan is lost because the plan was never deleted.

Repository-wide discovery may inspect open PR bodies when GitHub access supports it. Without a repository hint, explicit PR/branch context, or a temporary pointer, automatic discovery is not guaranteed; this is an accepted property of zero-install usage.

## Blockers and dependencies

Continuum has no special issue or blocker model.

Writers must respect ordinary repository issue/PR relationships, recorded blockers, milestones/projects where relevant, and project policy before acquisition and before Ready.

Work that has not started may remain ordinary issues or other planning artifacts indefinitely without becoming a Continuum branch/PR.

## Forks and client capabilities

The protocol distinguishes:
- base repository/ref/SHA: target code and policy;
- head repository/ref: writable implementation branch;
- canonical PR identity: coordination surface.

A fork workflow reads upstream/base policy while pushing only to the authorized head/fork ref. The protocol must not assume `origin` is the push destination.

Clients preflight the operations they actually support. Missing capabilities such as fork creation, Draft PR creation, durable comments, lifecycle changes, or cleanup produce an exact human/CLI handoff and preserve reached state.

Upstream labels, settings changes, installed workflows, and broader credentials are never prerequisites.

## Stacking

The absence of a temporary root protocol/plan file removes the main file-collision problem, but stacked Continuum PRs still complicate target identity, review inheritance, and merge ordering.

The first portable version does not support stacked Continuum PRs.

Bootstrap must reject a selected base when either condition holds:

- the selected base repository/ref is the head repository/ref of an unmerged Continuum PR, whether that parent is Draft, Ready, cleaned up, open, or closed-unmerged; or
- the selected base contains an unexplained temporary Continuum pointer block that is not ordinary permanent repository policy.

Parent detection uses canonical PR marker/state, not pointer presence, so cleaning the parent's temporary block does not make it a supported integration base. If the client cannot determine whether the selected base belongs to an unmerged Continuum parent, it stops or hands off rather than assuming stacking is safe.

A permanent repository-owned Continuum hint is not a parent pointer and does not itself block bootstrap.

Stacking can be added later with explicit parent/child identities, retarget behavior, review inheritance, and merge-order semantics.

## Migration from Continuum 0.3

Migration uses a strict version boundary and an explicit admission gate.

### Migration admission gate

Before draining 0.3 work, the project owner establishes a durable migration gate in project-owned repository policy visible to 0.3 agents, such as an `AGENTS.md` section outside the managed 0.3 block.

While the gate is active:

- no new 0.3 acquisition claim/bootstrap may start;
- no closed 0.3 PR may be reopened for implementation;
- no orphan/in-flight pre-PR 0.3 branch is implicitly adoptable;
- already-open 0.3 PRs may continue only to finish or be explicitly abandoned;
- a bootstrap that began before the gate must either be completed into a known 0.3 PR included in the drain inventory or explicitly abandoned by a human.

The drain inventory includes Draft/Ready unmerged 0.3 PRs, active or suspended leases, known pre-PR claims/bootstraps, and closed-unmerged 0.3 work that the project intends to resume.

The gate remains active through the final migration merge, and the final migration rechecks the drain before merging.

### Active 0.3 PR rule

Repository migration to 0.4 is blocked while any drain-inventory 0.3 work remains active or resumable under 0.3.

Existing 0.3 PRs finish under the semantics they started with, including issue/PR/`PR-PLAN.md`, lease rules, and 0.3 cleanup. They do not silently adopt 0.4.

This avoids needing 0.3 installed machinery to coexist with a migrated base or allowing old PRs to reintroduce deleted infrastructure.

### Final migration PR

Once the 0.3 drain is empty, one final migration PR may remove the installed 0.3 machinery:
- root installed `CONTINUUM.md`;
- `templates/CONTINUUM.md`;
- `templates/PR-PLAN.md` if obsolete;
- installed finalizer/helper copies that are no longer repository responsibilities;
- old self-check rules requiring installed protocol copies;
- the old managed Continuum `AGENTS.md` block.

It must preserve all project-owned `AGENTS.md` content outside the old managed block.

The Continuum reference repository moves its canonical protocol source to `protocol/CONTINUUM.md` and updates self-checks to validate the published source/release contract rather than downstream installation equality.

The migration PR itself remains governed by 0.3 until it merges. If it removes its local copy of the 0.3 finalizer before final cleanup, it uses the exact 0.3 cleanup procedure pinned by its base commit, including the documented manual fallback for deleting only `PR-PLAN.md`. It does not infer 0.4 semantics for itself.

Before final migration merge, a supported stable 0.4 release/artifact must exist at the canonical source so the repository does not land in a state that advertises a nonexistent or older protocol.

PR #15 remains governed by 0.3 unless an explicit later decision makes it the final migration PR under these conditions.

### Reopening old 0.3 work after migration

After migration, an old closed/unmerged 0.3 PR cannot automatically resume under 0.3.

The default path is to create a fresh 0.4 PR from the migrated integration base and carry forward only the still-relevant implementation commits/context.

An in-place conversion is allowed only with explicit human authorization and must:

1. verify a supported stable 0.4 protocol exists and pin it;
2. reconcile/rebase the branch against the migrated target without reintroducing removed 0.3 infrastructure;
3. remove obsolete temporary 0.3 coordination artifacts from the proposed merge result;
4. create a fresh 0.4 bootstrap ID and temporary pointer as needed;
5. replace/add the canonical 0.4 PR-body controlled section with a valid initial revision/digest, current goal/scope/acceptance/plan, and accepted target/head identity;
6. record the conversion durably;
7. leave the PR Draft and unleased; and
8. require a fresh 0.4 write lease before any implementation write.

Reopening alone never reactivates an old 0.3 lease or protocol.

After migration merges, new Continuum PRs use the PR-native protocol.

Existing issues, milestones, labels, merged PRs, dependencies, and GitHub history are left untouched.

## Cleanup and final merge gate

Cleanup has its own narrow cooperative claim, mutually exclusive with an implementation write lease.

### Cleanup claim

A cleanup run may claim cleanup only when:

- the PR is open and Ready;
- implementation and required verification are complete;
- review is otherwise clean;
- no active/suspended write lease or cleanup claim exists;
- durable implementation knowledge has been promoted and reviewed;
- current target/base and applicable policy have been revalidated; and
- the temporary pointer is expected to belong to this PR/bootstrap.

The cleanup claim comment records:

- cleanup run ID;
- expected reviewed HEAD;
- accepted contract revision/digest;
- target repository/ref and checked target/base SHA;
- head repository/ref;
- bootstrap ID.

Implementation lease acquisition must reject an active cleanup claim. Returning the PR to Draft while cleanup is claimed is a stop/reconciliation event; cleanup does not race resumed implementation.

### Cleanup execution

After claiming cleanup, the run re-fetches and verifies the claimed tuple and pointer ownership. It removes only the exact owned temporary block.

Whole-file `AGENTS.md` deletion is allowed only under the stricter ownership rule above: bootstrap created the path, the post-removal remainder is empty/whitespace-only, and the current accepted base does not own the file.

The run must preserve clean tracked/index state, stage only the authorized pointer/file removal, create a cleanup-only commit, push non-force to the explicit PR head repository/ref, and verify the remote result.

If any claimed value changed before the cleanup write, stop and reconcile rather than committing against stale state.

### Cleanup recovery

- **Local cleanup commit, push failed:** keep the cleanup claim. Verify the PR is still Ready, the claimed contract/target is current, and remote HEAD still equals the claimed reviewed HEAD. Then retry only the exact authorized cleanup commit. If remote HEAD advanced, stop and reconcile.
- **Push may have succeeded but recording/verification failed:** inspect the exact remote head and cleanup commit identity. If the authorized cleanup commit is the remote result and the expected pointer removal is verified, record recovered completion. If remote state is ambiguous or advanced unexpectedly, stop for reconciliation; do not infer success from pointer absence alone.
- **Pointer already absent when cleanup begins:** look for a matching prior cleanup-completion record/commit for the same bootstrap ID and accepted tuple. Without one, stop and ask for human recovery instead of treating absence as success.
- **Concurrent remote advancement:** cleanup does not force-push or replay over it. Reconcile ownership, lifecycle state, target, contract revision, and review evidence first.
- **Cleanup run terminates:** a human may recover an evidently stale cleanup claim after establishing the run stopped, just as with a stale write lease. Record recovery before another cleanup claim or write lease begins.

On verified success, record the cleanup commit/outcome and release/complete the cleanup claim.

After cleanup, ordinary repository checks/approvals may run on the cleanup HEAD. Human merge remains outside Continuum's automatic authority unless separately authorized by project policy.

## Walkthrough acceptance scenarios

Before normative 0.4 implementation begins, the design should be executable on paper for:

- fresh agent with no chat context but an explicit PR;
- fresh agent entering an active branch through the pointer;
- handoff between different clients;
- future milestone planning with implementation deferred: no branch, pointer, or Draft PR is created;
- push success plus failed/uncertain Draft PR creation;
- abandoned bootstrap and explicit human recovery;
- concurrent bootstrap attempts;
- PR retargeted during bootstrap uncertainty;
- suspended and stale leases;
- two sessions using the same provider/account identity;
- normal yield/release and transfer;
- transition to Ready;
- closure/reopening with a held or suspended lease;
- review fixes before cleanup;
- review fixes after pointer cleanup;
- run crash after lease acquisition but before pointer restoration;
- fork-only write access;
- missing label permissions;
- protocol fetch failure or mismatched source SHA;
- existing permanent `AGENTS.md`;
- bootstrap-created `AGENTS.md`;
- concurrent project-owned edits to `AGENTS.md`;
- bootstrap-created `AGENTS.md` later becoming base-owned;
- permanent Continuum-only repository hints surviving cleanup;
- stale temporary pointer discovered on target/default/unrelated branch;
- concurrent or human PR-body edits during a write lease;
- material plan/contract revision after Ready/review;
- retargeting during an active lease, while Ready, and after pointer cleanup;
- rebase/target advancement changing policy or merge assumptions;
- cleaned-up but unmerged Continuum parent selected as a base;
- unexplained foreign temporary pointer on the selected base;
- cleanup push failure, uncertain success, stale cleanup claim, and concurrent advancement;
- unexpected concurrent head changes;
- migration gate blocking new/in-flight 0.3 starts;
- reopening closed 0.3 work after migration and explicit 0.4 conversion;
- final 0.3-to-0.4 migration of the Continuum reference repository.

Only after these boundaries survive independent review should PR #15 move from design work into normative protocol implementation.
