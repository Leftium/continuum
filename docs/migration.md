# Publishing and migrating to 0.4

Adding the canonical artifact and client does not migrate this repository. Root
`CONTINUUM.md`, templates, finalizer, `PR-PLAN.md` and managed AGENTS block retain
0.3 semantics. PR #15 itself stays 0.3 through independent review/finalization.

Publication is separately authorized. Review/check the artifact at an exact
source commit, then publish a supported stable `v0.4.0` tag/release pointing to
it. The release version and `protocol/CONTINUUM.md` metadata must agree. Avoid
moving published tags; use immutable-release protections where available.
Bootstrap resolves the stable tag to an immutable commit once. A development
pin, draft release or prerelease does not meet the migration prerequisite.
Self-checks do not create releases.

Before draining, the owner records a durable admission gate in project-owned
policy outside the old managed AGENTS block. Record owner/decision and exactly
ONE designated final migration PR/claim identity and migration-only scope BEFORE
its bootstrap. Ban new ordinary 0.3 starts, reopen-for-implementation and implicit
orphan adoption. That designated migration is the sole admission/drain exception.

Maintain a durable inventory with identity/disposition of:

- Every other Draft/Ready unmerged 0.3 PR.
- Every active/suspended writing run and acquisition claim.
- Known pre-PR bootstrap branches/claims, including ones predating the gate.
- Closed-unmerged 0.3 work intended to resume.

Existing open work finishes under 0.3 or is explicitly abandoned. Pre-gate
bootstraps become inventoried PRs or are human abandoned. Migration is blocked
while any inventory work is active/resumable. Open PR enumeration alone is not
an empty drain. Keep the gate through final merge and recheck the drain then.

The designated final migration may remove installed 0.3 root/template/helper
copies, obsolete plan template, installation-equality checks and ONLY the managed
AGENTS block. Preserve project-owned instructions and the new source/client/tests.
It remains 0.3 through merge. If its local helper is removed, use the exact
pinned-base finalizer or documented plan-only fallback: verify reviewed shared
head/destination, `git rm -- PR-PLAN.md`, make the removal-only commit and qualified
non-force push. Do not infer 0.4 semantics for the migration PR itself.

Before merge, establish supported stable 0.4 publication, clean independent
review/checks, empty drain and merge authority. None is implied by implementation
PR #15. New work uses 0.4 only after the migration boundary lands.

Old closed-unmerged work normally starts a NEW 0.4 PR on migrated base with only
relevant code/context. In-place conversion needs explicit human authorization:
pin stable 0.4, reconcile/rebase without restoring removed infrastructure, remove
obsolete temporary artifacts, create a NEW bootstrap ID and valid contract/pointer,
log conversion and leave Draft/unleased. Require a fresh 0.4 lease. Reopening
alone is not conversion. Ordinary issues/milestones/dependencies/history stay intact.
