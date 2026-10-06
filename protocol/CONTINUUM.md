---
continuum: 0.5.0
artifact: protocol/CONTINUUM.md
---

# Continuum 0.5

A pull request is the work unit. Its ordinary Markdown description explains the
change. A single line pins the protocol used to interpret its coordination
comments:

```text
Continuum: 0.5.0; protocol source: Leftium/continuum@<40-character-commit>:protocol/CONTINUUM.md
```

Use an immutable source commit, not a moving branch or tag. The pin is the only
Continuum contract in the PR body. Do not add a JSON contract, digest, plan
mirror, or target-repository `AGENTS.md` pointer. Project policy and human
adoption still govern work.

## Normal work

The normal lifecycle has two Continuum records: `claim` and `release`. GitHub
PR Draft/Ready state, reviews, and checks remain native GitHub data. The normal
path is:

1. Read the PR, its pinned protocol, accepted-base policy, and current
   coordination records. A closed PR or an uncertain/conflicting state stops
   writes.
2. While the PR is Draft and no lease is active, post one `claim` record with a
   fresh UUIDv4 run identity.
3. Implement, verify, commit, and push under that lease. Git commits are
   savepoints; they do not need Continuum events.
4. Post one `release` with the same run identity and the exact full 40-character
   shared HEAD SHA. Release only after the pushed head has been reread and
   matches that SHA.
5. Mark the PR Ready. GitHub review, checks, and a human-authorized merge finish
   the work.

Each coordination comment contains exactly one visible, machine-readable
`continuum` fence. The record itself is the human summary; do not repeat its
fields in hidden JSON or a second summary.

```continuum
claim <run-uuid>
```

```continuum
release <run-uuid> <full-head-sha>
```

The authenticated GitHub comment author and ordering come from the same comment
records and are not repeated. Repository, PR, head ref, current head SHA, and
Draft/Ready state come from the PR data already read for the operation. The run
identity is stored because it is needed to match a release to its claim; the
full release SHA is stored to anchor handoff and review without reconstructing
historical branch movement.

An unrelated comment without a `continuum` fence has no protocol meaning. A
malformed, duplicated, unknown, or untrusted `continuum` record is ambiguous and
stops writes. Claims are exclusive: a claim while any claim remains active, or
any competing live claims, blocks all product writes. A release clears only its
matching sole active claim. A wrong-run release, missing claim, or conflicting
history never clears ownership.

### Bootstrap

Read the selected base's policy and blockers, then create a fresh work branch
from that base and open a Draft PR with an ordinary description and the single
protocol pin. Bootstrap writes no temporary file into the target repository.
If GitHub requires the head to differ before it permits a Draft PR, an empty
commit is sufficient. Acquire the lease before product implementation writes.
Do not create a pointer, setup contract, or cleanup task.

## Abandoned lease recovery

Recovery is exceptional. Only a repository OWNER may recover. The owner must
confirm that all writers have stopped, inventory unshared work, and record its
disposition. An OWNER recovery is an unconditional reset of all preceding lease
history, including history the reader did not fetch. It cannot make malformed
or untrusted records safe; those still require human reconciliation.

```continuum
recover | <owner confirmation, stopped writers, and unshared-work disposition>
```

An accepted OWNER record clears all earlier leases without a redundant run list.
Start a fresh claim after recovery; never reuse a run identity.

## State reconstruction and cost

Parse GitHub comments outside the coding model's context. Fetch the newest
comment page first and request older pages only as needed to resolve claims
since the latest valid recovery boundary; report only the compact active lease,
conflict, or clear state. Do not emit or replay a large event log into model
context. Keep one visible source of each fact. Store a value when deriving it
would require a meaningfully more expensive or ambiguous remote read; otherwise
use data already returned by the same GitHub read.

The ordinary path has two protocol comments and zero target-repository protocol
mutations. Bootstrap needs no temporary file; if GitHub requires a differing
head before opening a Draft PR, an empty commit is acceptable. Recovery adds one
exceptional comment. Checkpoints, verify/ready/review/suspend/repair/cleanup
events, event IDs/frontiers, evidence tuples, contract revisions/digests, and
duplicate target/head metadata are not part of this protocol.

## Compatibility and authority

Continuum 0.5 is incompatible with 0.4. Existing 0.4 PRs remain governed by the
exact Continuum 0.4.1 source commit pinned in each PR; do not rewrite their
contracts or histories. New work uses 0.5 only after its stable release is
available. Merging a reviewed protocol version bump to `main` authorizes the
release workflow to validate and publish that version at the merge SHA. The
workflow does nothing when the version is unchanged and refuses mismatched
existing tags/releases. A human authorizes merge; publication does not authorize
deployment or changes outside the adopted PR scope.

## Coordination-surface measurement

For a reproducible normal-path example, the 0.4.1 client rendered claim,
verify, ready, and release as 4 comments / 3,314 UTF-8 bytes. The example used
the same PR tuple in each record, 40-character identifiers and SHAs, a short
adoption reference, and a short verification reference. The 0.5 records for
the same UUID and exact release SHA are 2 comments / 161 bytes. That is 95%
fewer comment bytes. Evidence prose makes 0.4.1 sizes variable; the counts
include each complete rendered event comment, including its hidden JSON
disclosure. GitHub renders 0.5's claim, release, and recovery fences directly
as visible code blocks with no hidden payload.

The 0.4.1 bootstrap and cleanup each mutate the target repository to add or
remove the temporary pointer (2 protocol-only commits). The 0.5 normal path
makes 0 target-repository protocol mutations. A GitHub-required empty bootstrap
commit is the sole exception and changes no files.
