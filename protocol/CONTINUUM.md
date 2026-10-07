---
continuum: 0.6.2
artifact: protocol/CONTINUUM.md
---

# Continuum 0.6

A pull request is the work unit. Its ordinary Markdown description explains
the change. One sentence links to the immutable protocol source:

`This PR follows the [Continuum protocol at <short-commit>](https://github.com/Leftium/continuum/blob/<40-character-commit>/protocol/CONTINUUM.md).`

Use a short commit prefix for the visible text. The client treats that text
as presentation and validates provenance only from the link target: the trusted
repository, full immutable lowercase SHA, and exact canonical file path.

The client trusts `Leftium/continuum` and fetches its canonical
`protocol/CONTINUUM.md`. The fetched file must declare the supported version.
Do not add another contract, digest, plan mirror, or target-repository file.
Project policy and human adoption still govern work.

When bootstrapping a PR, the reference client may apply the target repository's
existing `continuum` label on a best-effort basis. It never creates that label,
and a missing label, lookup failure, permission failure, or application failure
does not block bootstrap. Applying it must preserve other labels. The label is
discovery metadata only; it grants no workflow authority and does not affect
protocol pins, leases, Draft/Ready state, review, or merge.

## PR descriptions

Prefer Summary, Changes, Verification, and optional Follow-ups when they help
readers scan the result. Small PRs may omit sections. Link the issue or spec for
scope and acceptance criteria; describe what changed, how it was verified, and
useful remaining boundaries. This is a writing convention, not protocol state
or another contract. See the [client guide](../docs/client.md#pr-description)
for an example.

## Lease records

The entire GitHub comment body is the record. Records contain no Markdown
fence or duplicate representation. These are the only records:

- `This PR was claimed`
- `This PR's claim <claim-comment-id> was released at <full-head-sha>`
- `This PR was recovered | <owner confirmation, stopped writers, and unshared-work disposition>`

GitHub's immutable ID for a `This PR was claimed` comment is its lease
identity. A release must name that exact ID and the full 40-character lowercase SHA of the pushed
head. GitHub may visually shorten the SHA; the comment body retains all 40
characters. Everything that does not exactly match a valid record is an
ordinary comment.

## Normal work

1. Read the PR, its pinned protocol, and coordination comments. A closed PR or
   uncertain/conflicting state stops writes.
2. Establish a workspace at the exact shared PR head, then read project policy
   from the selected base/head. Unrelated checkout-local pointers are not
   authority. If the current worktree has no staged, unstaged, or untracked
   changes and the branch is not checked out elsewhere, fetch and switch to it.
   Otherwise preserve local work and reuse a safe target worktree or create a
   detached worktree at the exact PR HEAD. Push only to the authorized PR head
   ref.
3. While the PR is open, Draft, and has no active lease, post `This PR was claimed`.
4. Implement, verify, commit, and push under that lease.
5. Reread the PR head and post `This PR's claim <claim-comment-id> was released at <full-head-sha>`
   only when it matches the clean local HEAD.
6. Mark the PR Ready. GitHub reviews, checks, and a human-authorized merge
   finish the work.

Creating or planning a Draft PR does not claim a lease; zero coordination
comments is valid. The writer claims immediately before making product-
repository changes. Do not infer ownership transfer from PR creation, planning,
handoff, branch ownership, or worktree ownership. If a different writer will
continue, the current writer releases first and the next writer makes a fresh
claim before writing. There is no leading release: every release names an
existing active claim comment ID.

Claims are exclusive. A claim while another is active or competing live claims
block product writes. A release clears only its matching sole active claim. A
stale, wrong, or unmatched release never clears another claim. Malformed
protocol state and untrusted records stop writes until owner recovery or human
reconciliation. Stop for an actual coordination or authority conflict, dirty
work that cannot be preserved safely, inability to establish the target
workspace, or uncertainty about the authorized push destination.

## Recovery

Only a repository OWNER may recover an abandoned or conflicting lease. The
owner must confirm every writer has stopped and inventory unshared work with its
disposition. An accepted recovery resets all earlier lease history, including
history the reader did not fetch. New work starts with a new claim comment;
later releases still match only their named claim comment IDs.

## Client and compatibility

The reference client uses Python 3.9+, Git, and authenticated `gh`; it does not
install files in a target repository. Parse GitHub comments outside model
context and report only the active lease or conflict state.

Continuum 0.6 is incompatible with earlier minor versions. The sentence records
and linked pins begin with 0.6.2. PRs pinned to 0.6.0 or 0.6.1 keep their original
`claim`, `release <claim-comment-id> <full-head-sha>`, and `recover | <confirmation>`
grammar and plain full-SHA pins. The reference client selects the record grammar
from the fetched protocol version; it never mixes grammars within a PR. Plain
full-SHA pins remain accepted in 0.6.2. Existing PRs retain their exact pin.
New PRs use 0.6.2 only after its stable release is available. On `main`, the
stable release workflow runs only when
`protocol/CONTINUUM.md` changes. It validates a version increase and exact
release target before publishing. Merging a reviewed version bump authorizes
that automatic stable publication; a human authorizes merge. Publication does
not authorize deployment or work outside the adopted PR scope.
