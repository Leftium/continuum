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

The root plan must not land on the integration branch. After review is clean,
promote durable knowledge and delete `PR-PLAN.md` in a final non-substantive
cleanup commit before merge.

## Verify

- `scripts/check-continuum.sh`;
- inspect root/template/spec version agreement;
- confirm the durable template is present;
- confirm protocol acceptance scenarios cover creation, recovery/handoff, review,
  and pre-merge deletion;
- confirm this PR retains its temporary root plan until review is otherwise clean.
