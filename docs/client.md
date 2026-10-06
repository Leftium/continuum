# Using the reference client

The accepted architecture is in `specs/002-pr-local-redesign.md`; the normative
wire format and lifecycle are in `protocol/CONTINUUM.md`. Use an explicitly
trusted local checkout of the same version, Python 3.9+, Git and authenticated
`gh`. There are no Python package dependencies. Do not pipe downloaded code into
a shell. Other clients can implement the same formats without installation in
the target repository.

This client supports github.com and 0.4.0. Commands do not merge or publish.
Comment/body operations have rereads, not atomic locks. Check ownership and live
state before your own product writes. Acceptance references must name actual
human/project decisions and substantive checks; the client cannot invent them.

## Bootstrap

Inspect the selected base's policy, referenced instructions and ordinary blockers.
Confirm implementation starts now. Keep the current workspace when safe; use a
clean worktree when unrelated staged/unstaged/untracked changes prevent switching.
This client's bootstrap requires a clean workspace and never stashes/resets work.

Prepare a JSON plan outside the target worktree with these seven fields:

```json
{
  "goal": "Deliver the adopted change",
  "scope": ["Agreed boundaries"],
  "acceptance": ["Observable completion criteria"],
  "plan": ["Implement", "Verify", "Independent review"],
  "verification": ["Relevant project checks"],
  "changes": [],
  "context": ["Ordinary issue or decision links when relevant"]
}
```

From the target checkout, invoke the trusted client's absolute path:

```sh
python3 /trusted/continuum/scripts/continuum.py bootstrap \
  --repo upstream/project --base main --head-repo writer/fork --remote fork \
  --plan /outside/plan.json --journal /outside/bootstrap.json \
  --title 'Implement the adopted change' --start-now \
  --accepted-policy 'Human adoption and base-policy/blocker decision reference'
```

Configure `fork` to the authorized writable repository. The client checks its
effective push URL. Same-repository work uses that repository for both identities.
Generated branch/run/bootstrap IDs avoid collisions. The private recovery journal
must be outside the worktree; it records intent/pin and the bootstrap SHA before
PR creation. It is not a prepared-work queue.

Default stable discovery queries the trusted source repository's latest stable
release. It accepts only `v0.4.0` or `0.4.0`, resolves the tag through GitHub's
commit endpoint to a full 40-character commit SHA, and reads
`protocol/CONTINUUM.md` at that SHA. The artifact metadata must match 0.4.0.
The resulting contract and recovery journal retain that exact pin; resume does
not rediscover a newer release. Missing, draft, prerelease or unsupported releases
stop bootstrap without falling back to `main` or 0.3.
Authorized testing can use `--development-source --source-commit <40-character-sha>`;
this does not satisfy stable publication or migration prerequisites.

Bootstrap applies an existing `continuum` label best-effort. When the label is
missing and repository permissions allow creation, an interactive terminal offers
create/skip, then a separate backfill choice after creation. Both prompts default
to skip. Labels have no authority over contracts, leases, or readiness, and label
failures never block bootstrap.

For automation, pass `--label create` or `--label skip` and
`--label-backfill sync` or `--label-backfill skip`. Without these flags, a
noninteractive invocation skips creation/backfill and reports the available
options. Creating the label applies it to the current PR; backfill only adds it
to other open PRs with a parseable canonical 0.4 body section. Choices are saved
in the recovery journal before label mutations so resume does not infer consent.
Explicit flags on resume can replace a saved choice before the next label action.

To backfill later, first create the repository label through an explicitly
authorized operation, then run:

```sh
python3 /trusted/continuum/scripts/continuum.py label sync --repo upstream/project
```

Sync never creates labels, removes labels, or guesses 0.3 PRs from titles or
branches. It rereads each candidate, skips closed/already-labeled PRs, reports
each confirmed addition, and reports partial failures. A missing label or lookup
failure leaves the repository unchanged. Repeating sync is safe.

For uncertain PR creation, resume the SAME branch and recorded commit:

```sh
python3 /trusted/continuum/scripts/continuum.py bootstrap --resume \
  --journal /outside/bootstrap.json --remote fork --run <initiating-run-uuid>
```

If that run terminated, use a new UUID and
`--recovery-authority 'Human decision confirming the old run stopped'`.
Never reuse a terminated run ID to bypass recovery. Interruption before a recorded
commit, target changes, unexpected ancestry or missing capabilities requires a
human/client handoff using preserved journal and Git state, never a second branch
or second bootstrap commit.

## Ownership and readiness

Use the full PR URL. `status --pr <pr-url>` retrieves the exact protocol pin and
reconstructs all comment pages without mutation. Write a details JSON file outside
the worktree, for example:

```json
{"acceptance":"Human adoption; selected-base policy and blockers checked"}
```

Acquire with a fresh run UUID BEFORE branch or controlled-body writes:

```sh
python3 /trusted/continuum/scripts/continuum.py event --pr <pr-url> \
  --run <run-uuid> --action claim --details /outside/details.json
```

Perform adopted implementation/checks/native commits and qualified non-force
pushes. Record `event --action checkpoint` with details referencing checks/changes
and any explicit reconciliation. It requires the current local/shared HEAD and
clean workspace. Continue under the same lease; this is not a default yield.
Do not checkpoint unexplained external advancement as your own work.

For a body edit, prepare the complete contract JSON, then use
`edit --pr ... --run ... --input ...`. It increments/seals metadata, preserves
unrelated description and records a checkpoint. Material goal/scope/acceptance,
pin or target changes require `--accept-change 'Human/project decision reference'`.
This records actual authority, not a way to invent it.

Record `event --action verify` with actual verification and knowledge-promotion
references. `ready --pr ... --run ... --details ...` records Ready evidence,
releases, then marks Ready. Failed/pending checks, conflicts, unknown mergeability
and requested changes stop it. If the last lifecycle operation fails after
release, an authorized human/client may mark Ready only after confirming the
same tuple. No lease silently revives.

An independent run uses `event --action review` with:

```json
{"acceptance":"Link to clean independent review and required checks","independent_review":true}
```

The client checks known GitHub signals; these references must also establish
project-specific review/blocker/verification requirements. Review fixes use
`gh pr ready <pr-url> --undo`, then a fresh write claim. After authorized cleanup,
`pointer-sync --pr ... --run ...` may restore the SAME bootstrap identity AFTER
acquisition; commit/push and checkpoint it. Leaving the pointer absent is supported.
The plan always remains in the body.

## Suspension and reconciliation

`event --action suspend` with `{"reason":"Blocked operation or changed tuple"}`
retains ownership. No unrelated writes while suspended. Resume the SAME run
with `--action resume` and `{"acceptance":"Approval or explicit reconciliation"}`.
Repair ownership still requires repair completion before implementation.
For invalid metadata, resume compares the repair's accepted raw snapshot and
head/target binding without requiring the damaged digest to validate first.
If suspension preceded entering repair mode, include `raw_digest` for the exact
accepted section in resume details, then run bounded repair before implementation.

Target/head changes stop EVERY phase. Use `--action cleanup_cancel` with a reason
before implementation acquisition, or recover a terminated cleanup owner. Return
Ready to Draft, obtain human target acceptance, reread policy/blockers/diff,
resume/acquire ownership, update the body and `pointer-sync` if present, preserving
permanent instructions. Never force-push or overwrite unexpected remote HEAD.
Harmless same-ref base movement alone may use unleased `--action revalidate` with
independent acceptance; all other tuple values must remain identical.

For abnormal termination/conflicting claims, a human confirms ALL owners stopped
and inventories unshared work. `--action recover` with
`{"human_confirmation":"Decision reference, stopped owners and lost-work assessment"}`
clears claims/evidence. Acquire afresh; unpushed work is not assumed saved.
Closed PRs permit stop/recovery comments, never product/body writes. Reopening
does not restore ownership. Malformed/untrusted history needs an explicit human
handoff; this client will not silently ignore it.

## Digest repair

Offline commands grant no authority:

```sh
python3 /trusted/continuum/scripts/continuum.py contract validate --body /outside/body.md
python3 /trusted/continuum/scripts/continuum.py contract snapshot --body /outside/body.md
python3 /trusted/continuum/scripts/continuum.py contract seal \
  --input /outside/contract.json --revision 1 --output /outside/section.md
```

Fetch the complete live body without newline conversion. Agree on the exact raw
snapshot and trusted predecessor revision. Accept all edited content, including
changes needing separate human/project authority, then:

```sh
python3 /trusted/continuum/scripts/continuum.py repair --pr <pr-url> \
  --run <run-uuid> --accepted-raw sha256:<raw-snapshot-digest> \
  --last-revision <trusted-predecessor> --acceptance 'Human snapshot decision' \
  --output /outside/replacement.md --apply
```

An unleased PR gets an exclusive repair claim; a held writer enters repair mode.
No implementation/cleanup until metadata validates. Omit `--apply` to prepare a
COMPLETE replacement for an authorized human; retain ownership. After that human
applies it, rerun the same arguments with `--complete` instead of `--apply`.
The exact replacement contract and live tuple must match. Never ask a human to
guess a digest. Changed snapshots/interrupted claims require reconciliation.
Offline `contract repair` with the same snapshot arguments prepares text only.
Revision rollback or a recomputed digest at an already-recorded revision also
requires repair/reconciliation; a syntactically valid hash cannot bypass history.

## Cleanup and verification

After current independent review is clean:

```sh
python3 /trusted/continuum/scripts/continuum.py cleanup --pr <pr-url> \
  --run <fresh-cleanup-run-uuid> --remote fork
```

The client claims cleanup, verifies bootstrap/current-base ownership, removes
only the owned block, commits/pushes the exact head and records provenance.
The reference client owns no whitespace outside its block. It deletes the entire
`AGENTS.md` only when the remainder is empty, bootstrap created the file, and the
current accepted base does not own the path.
Failed/ambiguous push retains the claim; rerun the SAME run to verify/retry the
same commit. Changed state requires cancellation or human stale-owner recovery.
Check required checks on cleanup HEAD before any separately authorized merge.

A later Ready cycle with independently refreshed evidence and proven historical
removal gets a no-op receipt without a commit. Restore-then-remove without a
receipt is rejected. The client requires demonstrable Git ancestry: the recorded
removal must remain an ancestor, and subsequent `AGENTS.md` history must prove
absence. Rewritten-history mapping is an explicit
human/capable-client handoff, not a validation bypass flag.

`bash scripts/check-continuum.sh` validates the canonical 0.4 source and runs
the offline reference-client tests.
Tests use fixtures/local temporary Git repositories, never live GitHub mutations.
New work uses stable 0.4 after the migration PR merges; see
[migration.md](migration.md) for that boundary and its historical 0.3 procedure.
