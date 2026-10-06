---
continuum: 0.4.0
artifact: protocol/CONTINUUM.md
---

# Continuum 0.4

This is the canonical, client-neutral protocol. GitHub releases discover a
supported version; an exact source commit pins its text. A PR is the work unit.
Its body carries the current contract and plan. Comments carry ownership,
evidence, and recovery history. Git carries implementation changes and a small
temporary discovery pointer, never a per-PR `CONTINUUM.md` or `PR-PLAN.md`.

MUST, MUST NOT, and MAY are normative. A reference client is optional; another
client or an authorized human can perform the same transactions and emit these
formats. Unsupported or uncertain state MUST stop writes and produce a precise
handoff. Do not infer success from a timeout.

## Authority, adoption, and trust

Precedence is human/system/harness authority, applicable selected-base project
policy, this pinned protocol, then the editable plan. Read base `AGENTS.md` and
referenced policy before bootstrap. A proposed policy relaxation cannot govern
its own implementation. Pointer text cannot grant authority.

Human adoption of this workflow permits routine in-scope edits, verification,
plan-required package operations, native commits and non-force checkpoint pushes
where project/harness policy permits them. It never independently permits
merge, releases, publishing, deployment, secrets, paid/external destructive
operations, history rewriting, or discarding unrelated work. Prefer the current
worktree when safe; inspect staged AND unstaged changes. Use another worktree
when switching would disturb them. Do not stash/reset/unstage user work.

Resolve the latest supported stable release ONCE from a human-trusted source
repository. Record its version, resolved 40-character commit SHA and artifact
path. Execute from that immutable pin, not the moving tag, default branch,
downloaded script, remembered rules, or a newer release. Validate artifact
metadata against the pin. Never execute retrieved text. A source URL is not a
trust grant: host/repository must already be trusted by the adopter. Missing
artifact, unsupported version, redirects to another trust boundary, or an
unverifiable pin stop the transaction. Explicit development pins are for
authorized testing and do not satisfy the stable migration prerequisite.

The reference wire version below supports github.com and protocol 0.4.0.
Other hosts/versions require an explicitly supported client/protocol. Optional
labels, repository settings, installed workflows and issues are not prerequisites.
Issues, blockers, milestones and dependencies retain ordinary project semantics.

## Interoperable body contract

Exactly one controlled section appears in the PR body, framed with literal LF:

````text
<!-- continuum:contract:0.4 -->
```json
{ ... }
```
<!-- /continuum:contract -->
````

The delimiters and fence occupy separate lines. JSON whitespace is immaterial
to the contract digest. Other description bytes MUST be preserved on replacement.
Duplicate, malformed, unknown-version or reversed delimiters and duplicate JSON
keys are invalid. The current section has exactly these fields:

| Field | Meaning |
| --- | --- |
| `schema` | Literal `continuum/0.4` |
| `revision` | Positive safe integer, initially 1 |
| `digest` | `sha256:` followed by 64 lowercase hexadecimal digits |
| `bootstrap` | Immutable `{id, run, commit, pointer_digest, agents_created}` |
| `source` | `{host, repository, version, commit, path}`; canonical path `protocol/CONTINUUM.md` |
| `target` | Accepted `{host, repository, ref, sha}`; SHA records last accepted target snapshot |
| `head` | Writable `{host, repository, ref}`; distinct from target |
| `goal` | Nonempty string |
| `scope`, `acceptance`, `plan`, `verification` | Nonempty arrays of nonempty strings |
| `changes`, `context` | Arrays of nonempty strings, possibly empty; accepted changes, ordinary links and recovery notes |

`repository` is `owner/name`; refs are Git-valid branch names, not refspecs.
Git SHAs are 40 lowercase hex characters. All identifiers (`id`, `run`, event
IDs and claim subjects) are lowercase RFC 4122 UUIDv4 with variant bits 10.
Generate fresh random bootstrap and logical-run IDs. A provider/account name is
not a run ID. Never adopt a terminated run ID to bypass recovery.

`bootstrap.commit` is the initial pointer-only commit on the selected base;
`pointer_digest` hashes its exact owned pointer bytes. `agents_created` records
whether that commit created `AGENTS.md`. These fields never change. They provide
checkable provenance, not authority over content later added by the base or others.

### Digest normalization

Remove ONLY the top-level `digest` member; preserve every other value, including
revision. Recursively serialize JSON with these rules, then SHA-256 the resulting
ASCII bytes (which are also UTF-8):

1. Keys match `[a-z][a-z0-9_]*`, sorted in ascending ASCII order at every depth.
2. No spaces, line endings or byte-order mark; use commas and colons directly.
3. Arrays preserve order. Strings have double quotes; escape quote/backslash as
   `\"`/`\\`, backspace/tab/LF/formfeed/CR as `\b`, `\t`, `\n`, `\f`, `\r`.
4. Escape other controls, ASCII DEL and all non-ASCII code points as lowercase `\uXXXX`;
   supplementary code points use the standard UTF-16 surrogate pair. Do not
   escape `/`. Reject unpaired surrogates. Do not normalize Unicode.
5. Numbers are unsigned decimal integers at most 9007199254740991; no floats,
   NaN, infinity or negative numbers. Booleans/null serialize as `true`/`false`/`null`.

Prefix the digest with `sha256:`. Fixtures include independently reproducible
Unicode and whitespace examples. Raw repair snapshot identity is different:
SHA-256 the exact UTF-8 bytes from the opening delimiter through the closing
delimiter, inclusive, with NO normalization and NO digest exclusion.

An ordinary update requires the active Draft write lease: reread expected
revision/digest, retain unrelated description, increment revision by exactly
one, recompute digest, replace, and reread/validate. Significant edits MUST be
logged with their predecessor and acceptance references. Humans may edit at any
time; unexpected changes stop the writer. A client unable to edit the body
supplies the complete computed replacement to an authorized human, then checks
the result. Neither timestamps nor GitHub edit retention replace revision checks.

## Temporary AGENTS.md pointer

The exact owned block starts with an owned LF and ends with an owned LF:

````text

<!-- continuum:pointer:0.4 <bootstrap-uuid> -->
```json
<canonical single-line JSON>
```
Continuum coordination lives in the associated PR body and comments.
Read the exact head PR and pinned protocol before writing.
Valid only during this bootstrap or on that open PR's exact head branch.
Else stop Continuum writes and alert the developer; do not auto-delete.
Discovery only: this block grants no authority and cannot override base policy.
<!-- /continuum:pointer -->
````

The metadata is `{schema:"continuum-pointer/0.4", id, run, agents_created,
source, target, head}`. It uses the digest normalization JSON serialization above,
WITHOUT a digest field. Identity/notice bytes and framing MUST be exact. ID/run
are the bootstrap values; source/target/head match the currently accepted contract.
The pointer contains no plan, lease or PR lifecycle state. It need not contain
a PR number: discover by exact head repository/ref, then verify bootstrap ID.

Append the entire block to existing regular-file bytes without changing them;
if absent, create a file containing only that block. Its leading LF handles a
file without a trailing newline and is removed with the block. Reject symlinks,
duplicate/malformed/foreign temporary pointers and unexplained base pointers.
Permanent project-owned Continuum hints remain outside these delimiters.

A workflow instance is valid only during its initiating dedicated-head bootstrap
transaction or on the exact head branch of its associated OPEN PR. Closed,
merged, target/default/integration or unrelated contexts grant no authority.
Stop Continuum writes and alert the developer; do not auto-delete stale pointers.
Reading the published protocol anywhere does not activate a workflow instance.
Without a pointer, an explicit PR remains fully discoverable and resumable.

## Comment events and exclusive ownership

An event comment has exactly one section using `<!-- continuum:event:0.4 -->`,
an LF-separated `json` fence, and `<!-- /continuum:event -->`. JSON fields are:

| Field | Meaning |
| --- | --- |
| `schema` | `continuum-event/0.4` |
| `id`, `run`, `actor` | Fresh event UUID, logical run UUID, authenticated GitHub login |
| `prev` | Sorted array of the complete current event frontier's UUIDs, initially `[]` |
| `action`, `kind` | Transition and ownership class below |
| `subject` | Owned claim event ID, or null for acquisition/evidence/recovery |
| `tuple` | Current evidence tuple, or null ONLY for invalid-metadata/stop/recovery events |
| `details` | Transition-specific object with ASCII keys |

Normal history is linear, append-only and never edited/deleted. Read ALL pages
in GitHub comment order. Missing predecessors, duplicate IDs, malformed events,
untrusted authors and competing frontiers stop progress. Trust events only from
the PR author or authenticated repository OWNER/MEMBER/COLLABORATOR; `actor`
must equal the actual comment author. A deployment with different delegated
writers needs explicit project-authorized trust handling, not self-asserted roles.

An evidence tuple is exactly `{revision, digest, head_sha, target, base_sha, head}`.
`target` is host/repository/ref WITHOUT SHA; `base_sha` is the checked current
tip of that target ref, fetched independently. `head` includes repository/ref,
so forks cannot redirect writes through a bare branch name. Evidence MUST bind
to this tuple. A changed contract, head, target or materially changed base
invalidates affected evidence. Labels and PR timestamps have no authority.

| Action / kind | Preconditions and effect |
| --- | --- |
| `claim` / `write` | Open Draft, valid contract, expected shared HEAD, no claims, policy/blockers accepted. Owns branch AND controlled body. `details.acceptance` references adoption/policy/blocker checks. |
| `checkpoint` / `write` | Active owner; coherent verified commit pushed or valid body update. Update expected tuple; retain lease and continue. Log changes/reconciliation in details. |
| `suspend` / held kind | Owner records `details.reason`; retains claim, no unrelated writes. Allowed when metadata/target/head becomes invalid or PR closes. |
| `resume` / held kind | Same run, explicit `details.acceptance` of approval/reconciliation; recheck open context, tuple and policy. Repair claims return to repair mode. |
| `verify`, `ready` / `evidence` | Active implementation owner. `details.acceptance` references actual checks/knowledge promotion; Ready requires current verification tuple. |
| `release` / `write` or `repair` | Active owner, coherent shared state, no pending repair/suspension. End ownership; incomplete work remains Draft. |
| `review` / `evidence` | Unleased Ready with current Ready evidence; independent logical run, `details.independent_review:true` and `acceptance` linking the clean review/checks. |
| `revalidate` / `evidence` | Unleased Ready; only base SHA changed. Independent `acceptance` and `independent_review:true` attest current policy/diff/blocker/check review. Refresh verify/ready/review tuples; material effects require Draft. |
| `claim` / `cleanup` | Open Ready, current verify/ready/independent-review evidence, no other claim. Exclusively owns bounded removal/retry, never implementation or body editing. |
| `cleanup_cancel` / `cleanup` | Owner records reason and stops, allowing later reconciliation. |
| `cleanup_complete` / `cleanup` | Verified authorized removal/no-op receipt below; atomically in the cooperative event model ends claim. |
| `claim` / `repair`, `repair_enter` / `write` | Exact accepted raw snapshot, trusted predecessor, current head/target; exclusive repair claim or existing writer retains lease in repair mode. |
| `repair_complete` / held kind | Replacement metadata validates; logs accepted raw snapshot/predecessor and invalidates previous evidence. Repair claim then releases; implementation lease remains held. |
| `recover` / `recovery` | Explicit `details.human_confirmation` that ALL conflicting/stale/suspended owners stopped, plus recovery decision/lost-work note. `prev` covers the entire frontier, even competing claims. Clear ownership/evidence, never assume unshared work was saved. |

All owner transitions identify the same authenticated actor, run and claim ID.
No competing claim is allowed while a write/repair/cleanup claim is active OR
suspended. A normal transfer is release then a fresh acquisition. On abnormal
termination, a human MUST confirm the writer stopped before recovery. Closing
does not silently dispose of ownership; record stop/abandonment/recovery. No
branch/body writes while closed. Reopening never revives an old lease.

GitHub offers no atomic PR-body compare-and-swap or multi-resource transaction.
These are cooperative guarantees, not a distributed lock against adversaries.
Before each write, reread contract, frontier/owner, head, target and applicable
policy; after body/event writes reread exact result. Conflicting acquisitions or
unexpected values MUST stop all cooperating writers, retain evidence and require
recovery. Clients MUST NOT promise that a check eliminates races with humans or
noncooperating writers. Repository/harness restrictions still apply.

## Bootstrap transaction and recovery

Do not create branches/PRs for deferred implementation, future milestones or
backlog planning. Ordinary issues/docs carry that planning. Generate IDs only
when implementation starts and preflight Git, Draft PR creation, comments, body
edit and lifecycle capabilities. Read accepted-base policy/blockers. Distinguish
base/upstream from authorized head/fork, and verify the exact push URL/ref.

Reject stacking: the selected base repository/ref MUST NOT be the head of ANY
unmerged Continuum PR, including closed-unmerged or cleaned Ready parents.
Detect via canonical PR markers and repository/ref identity, not pointer presence.
If parent status cannot be established, stop/handoff. An unexplained temporary
pointer on the base also blocks bootstrap; a permanent hint does not.

Record intent/IDs/pin/target/head in a durable initiating-run journal outside
the target worktree BEFORE branch mutation. Create a fresh collision-resistant
branch on the checked base, append the pointer, commit ONLY that bootstrap change,
push ONLY the authorized head, record bootstrap SHA, then create the Draft PR
with initial sealed contract. Verify target/head/open/Draft/marker/bootstrap ID,
revision/digest and transport-visible remote HEAD. Bootstrap ownership ends there:
acquire a normal PR lease before implementation or further controlled-body writes.

If creation fails/times out after push, preserve the journal/branch. Search the
exact head repository/ref, including closed PRs, and verify the same remote
bootstrap SHA. One matching PR must satisfy the complete intended tuple and
ownership; multiple/mismatched/retargeted results stop. If none exists, only the
still-active initiating run or explicitly authorized human recovery may retry
creation for that SAME branch/commit. Never make a second bootstrap commit or
branch. Earlier interrupted stages require explicit reconstruction/handoff.
An orphan branch is exceptional recovery state, never prepared backlog.

## Contract repair

Invalid revision/digest blocks ordinary acquisition, implementation, review,
Ready and cleanup. Identify trusted PR/pin/head/target, trusted last-valid revision
(zero only when a human establishes no valid predecessor), and EXACT raw section.
Obtain required human/project acceptance of that snapshot, including otherwise
unauthorized scope/acceptance/source/target changes. Repair does not grant it.

Unleased repair claims must first exclude all other claims. The details include
`raw_digest`, `last_revision`, `acceptance` and `snapshot` (the intended repaired
evidence tuple). An existing writer uses `repair_enter` with these details and
keeps its lease. Only metadata recovery is permitted until validation succeeds.
Reread the identical snapshot and live head/target/frontier; preserve edited
content and unrelated description, set revision to trusted predecessor plus one,
compute digest, replace, reread/validate, record completion/invalidation. Other
schema damage or changed raw bytes needs new acceptance/recovery, not guessing.

Without body permission, provide the COMPLETE computed replacement and retain
repair ownership. An authorized human applies it; verify that exact contract and
head/target, then complete/release. Do not hand a human an unexplained digest to
patch manually. Interrupted repair requires normal explicit stale-owner recovery.

## Readiness, changes, and cleanup

Checkpoint verification/commits/non-force pushes are savepoints, not default
yields. Continue the adopted plan. Before normal yield, make shared state coherent,
record a handoff and release. Suspend ownership only for actual required approval
or reconciliation; a suspended owner performs no unrelated branch writes.

Before Ready, promote durable knowledge to reviewed code/tests/docs, complete
verification, check current target tip/policy/blockers/merge diff and tuple,
record Ready evidence, release, THEN mark Ready. Independent review follows.
Review fixes require Draft and a fresh write lease. After cleanup, the plan
remains in the body; restore the SAME owned pointer only AFTER acquiring that
lease if discovery is wanted. Absence never cancels an existing claim.

Unexpected target/head changes stop EVERY phase. Writers suspend; Ready loses
assumptions and returns to Draft before substantive continuation; cleanup stops
and cancels or undergoes human recovery before implementation acquisition. Require
human/project target acceptance, reread target policy/blockers/merge diff, update
the contract/revision under ownership, preserve base instructions when reconciling
the pointer, and invalidate affected evidence. Never overwrite an unexpected
remote head or force-push. Same-ref base advancement may be harmless but must be
checked again before Ready, cleanup and merge; material effects require Draft.

Acquire the exclusive cleanup claim only after clean independent review/checks,
current contract/tuple, policy/knowledge promotion and exact pointer ownership
are verified. Reread these immediately before removal/push. Remove only the
exact owned block. Preserve EVERY other byte. Delete the entire `AGENTS.md` only
if bootstrap verifiably created it, no bytes remain except provably bootstrap-owned
whitespace, AND the CURRENT accepted base does not own that path. The reference
client owns no whitespace outside its block, so it deletes only an empty remainder.
Uncertain/duplicate/malformed/foreign pointers or uncertain provenance stop.

Create a removal-only commit, verify its actual contents, non-force push to the
verified head repository/ref, and record `cleanup_complete` with exact details:
`{bootstrap_id, pointer_digest, removal_commit, readiness, prior_receipt, no_op}`.
The first receipt uses reviewed pre-removal `readiness`, the actual removal SHA,
`prior_receipt:null`, `no_op:false`; event tuple uses the resulting cleanup HEAD
with otherwise identical contract/target/base. Recheck repository checks on that
HEAD when required. This narrow removal exception preserves product review;
it never permits merge or waives checks.

If push fails, retain the cleanup claim. Retry only the exact verified cleanup
commit when remote still equals reviewed HEAD and all other readiness values
remain unchanged. For ambiguous success, verify remote equals that exact cleanup
commit and record recovered completion. Advancement, retarget, body change or
Draft stops cleanup; cancel/recover before a normal writer starts. A stale claim
requires explicit human confirmation before recovery.

If the pointer is already absent, a later Ready cycle MAY do verified no-op
cleanup: prove an authorized receipt for the same bootstrap/pointer identity,
current absence, removal ancestry and no unexplained restore/removal in subsequent
history (or explicit durable human rebase reconciliation mapping the removal).
Independently validate current verify/Ready/review evidence and current base SHA;
do not reuse the old readiness tuple. Claim cleanup, then record a new receipt
with current readiness, `no_op:true`, and `prior_receipt` identifying the earlier
receipt; keep the original removal SHA/pointer digest. No branch commit is needed.
Unexplained absence, foreign stale blocks, or uncertain history requires recovery.
The reference client requires demonstrable Git ancestry; rewritten history needs
a human/client reconciliation rather than a bypass flag.

Before merge, verify clean shared head, valid contract, no claims, authorized
cleanup provenance, no temporary pointer, current target policy/diff/blockers,
review/check validity (including cleanup HEAD checks), and human/project merge
authority. Continuum does not merge automatically.

## Version 0.3 migration boundary

Existing 0.3 PRs finish as 0.3: issue/PR/`PR-PLAN.md`, installed root protocol,
leases and plan-only finalization. Adding this artifact/client does not migrate
the reference repository or silently activate 0.4 on a legacy PR.

Before draining, a project owner records a durable admission gate in project-owned
policy visible to 0.3 agents. Ban new ordinary 0.3 claims/bootstrap, reopening for
implementation and implicit orphan adoption. Existing open work may finish or
be explicitly abandoned. Pre-gate bootstraps become inventoried PRs or are human
abandoned. Inventory ALL other Draft/Ready unmerged 0.3 PRs, active/suspended
leases, known acquisition/bootstrap claims and closed-unmerged work intended to
resume. Exactly ONE designated final migration PR/claim, with recorded identity
and migration-only scope BEFORE bootstrap, is the sole admission/drain exception.

Migration is blocked while any inventory work is active or resumable. Keep the
gate through final merge and recheck the drain. The final migration PR removes
installed 0.3 root/template/helper/check machinery and ONLY its managed AGENTS
block, preserving project-owned content. It still runs under 0.3 through merge,
using its pinned-base finalizer or documented plan-only manual fallback if the
local helper is removed. A supported stable 0.4 release/artifact MUST exist before
merge. PR #15 is not implicitly designated by implementing this version.

After migration, new work uses 0.4. Old closed-unmerged 0.3 work normally starts a
fresh 0.4 PR on migrated base with only relevant code/context. Explicit human
in-place conversion must pin stable 0.4, reconcile/rebase without restoring 0.3
infrastructure, remove obsolete temporary artifacts, create a NEW bootstrap ID
and valid 0.4 contract/pointer, log conversion and leave Draft/unleased for a
fresh lease. Reopening alone is never conversion. Ordinary GitHub history,
issues/milestones/dependencies/labels remain untouched.
