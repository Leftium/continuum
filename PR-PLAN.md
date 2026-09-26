# PR Plan

Issue: #5

## Goal

Standardize a required temporary root `PR-PLAN.md` for Continuum implementation
PRs so detailed implementation context travels with the branch instead of through
large chat handoffs.

## Scope

- bump the draft protocol from 0.1.0 to 0.2.0;
- define `PR-PLAN.md` ownership, content, lifecycle, recovery, review, and
  pre-merge deletion rules in the protocol;
- update the installed `CONTINUUM.md` template and this repository's
  self-hosted copy;
- add a durable `templates/PR-PLAN.md` starter;
- update README and self-check coverage;
- add a standard finalizer helper so deleting the temporary plan is a mechanical, pre-authorized operation rather than an ad hoc cleanup run;
- make routine in-scope, non-destructive actions on a leased Continuum PR standing-authorized unless project or higher-precedence policy narrows that authority;
- prefer checking out the PR branch in the existing project worktree when it is safe, with separate worktrees as a fallback rather than the default;
- dogfood the new rule with this temporary root plan.

## Design

Keep responsibility explicit:

- issue: durable goal, scope, acceptance, dependencies, product decisions;
- `PR-PLAN.md`: temporary implementation contract, approach, checkpoints,
  evidence, and verification plan;
- PR comments: checkpoint SHAs/results, review findings, fix handoffs;
- GitHub state: Draft/Ready and write-lease ownership.

Every implementation PR gets the file, but its size is proportional to the work.
A trivial PR may use only Goal, Scope, and Verify.

The root plan must not land on the integration branch. Promote durable knowledge
before review is complete. Once review is otherwise clean, use the standard
finalizer to delete `PR-PLAN.md` as a narrow cleanup-only commit. That
finalization is standing-authorized and does not require reopening implementation
or acquiring a normal write lease. Normal repository checks may still run on the
new HEAD before merge.

## Verify

- `scripts/check-continuum.sh`;
- inspect root/template/spec version agreement;
- confirm the durable template is present;
- confirm protocol acceptance scenarios cover creation, recovery/handoff, review,
  and pre-merge deletion;
- verify the finalizer refuses tracked dirty work and removes only the root plan;
- confirm execution authorization and in-place worktree preference are explicit;
- confirm this PR retains its temporary root plan until review is otherwise clean.
