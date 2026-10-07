---
continuum: 0.6.0
artifact: protocol/CONTINUUM.md
---

# Continuum 0.6

A pull request is the work unit. Its ordinary Markdown description explains
the change. One line pins the immutable protocol source:

`Continuum: Leftium/continuum@<40-character-commit>`

The client trusts `Leftium/continuum` and fetches its canonical
`protocol/CONTINUUM.md`. The fetched file must declare the supported version.
Do not add another contract, digest, plan mirror, or target-repository file.
Project policy and human adoption still govern work.

## Lease records

The entire GitHub comment body is the record. Records contain no Markdown
fence or duplicate representation. These are the only records:

- `claim`
- `release <claim-comment-id> <full-head-sha>`
- `recover | <owner confirmation, stopped writers, and unshared-work disposition>`

GitHub's immutable ID for a `claim` comment is its lease identity. A release
must name that exact ID and the full 40-character lowercase SHA of the pushed
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
3. While the PR is open, Draft, and has no active lease, post `claim`.
4. Implement, verify, commit, and push under that lease.
5. Reread the PR head and post `release <claim-comment-id> <full-head-sha>`
   only when it matches the clean local HEAD.
6. Mark the PR Ready. GitHub reviews, checks, and a human-authorized merge
   finish the work.

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
history the reader did not fetch. New work starts with a new `claim`; later
releases still match only their named claim comment IDs.

## Client and compatibility

The reference client uses Python 3.9+, Git, and authenticated `gh`; it does not
install files in a target repository. Parse GitHub comments outside model
context and report only the active lease or conflict state.

Continuum 0.6 is incompatible with earlier versions. Existing PRs remain
governed by their exact pinned protocol. New PRs use 0.6 only after its stable
release is available. On `main`, the stable release workflow runs only when
`protocol/CONTINUUM.md` changes. It validates a version increase and exact
release target before publishing. Merging a reviewed version bump authorizes
that automatic stable publication; a human authorizes merge. Publication does
not authorize deployment or work outside the adopted PR scope.
