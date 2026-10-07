# Using the reference client

Continuum 0.6.1 uses Python 3.9+, Git, and authenticated `gh`. The client does
not install files in a target repository. Existing PRs remain on the exact
protocol version pinned in each PR.

## Pin and inspect

New 0.6 PRs use an ordinary Markdown description and one immutable protocol
pin:

`Continuum: Leftium/continuum@<40-character-commit>`

The client trusts `Leftium/continuum` and fetches
`protocol/CONTINUUM.md` at that exact commit. Read accepted-base policy and
project blockers before work. The client reconstructs lease state from GitHub
comments and prints the active claim comment IDs.

## Bootstrap

Create a fresh branch from the selected base, then read its policy and
blockers. Open a Draft PR with an ordinary description and one immutable
protocol pin. Do not add a temporary target-repository file. If GitHub requires
a different head commit before it allows a Draft PR, an empty commit is enough:

```sh
git switch -c feature-name origin/main
git commit --allow-empty -m 'chore: start Continuum PR'
git push -u origin feature-name
pr_url=$(gh pr create --draft --base main --head feature-name \
  --title 'Implement the adopted change' \
  --body $'Describe the work here.\n\nContinuum: Leftium/continuum@<40-character-commit>')
python3 scripts/continuum.py label --pr "$pr_url"
```

Replace the placeholder with the exact source commit. The label command adds
the existing `continuum` label when available. It never creates the label, and
lookup or application errors do not affect PR creation. The label is discovery
metadata only. PR creation and planning leave coordination comments empty; do
not claim until the implementation writer is about to make product-repository
changes. Inspect the current worktree and establish the PR's exact target
workspace before that claim.

```sh
python3 scripts/continuum.py status --pr https://github.com/owner/project/pull/42
```

## Claim, work, and release

Before claiming, inspect staged, unstaged, and untracked files. Read policy from
the PR's selected base and head after moving to its target workspace; branch-local
pointers or instructions from an unrelated checkout are not authority. If the
worktree is clean and the PR branch is not checked out elsewhere, fetch and
check out the exact PR head. If switching would disturb local work or the branch
is already checked out elsewhere, preserve that state and reuse a safe target
worktree or create a detached worktree at the exact PR HEAD. A different
starting branch alone is not a reason to stop.

For a detached worktree, push explicitly to the authorized PR head ref, for
example:

```sh
git push origin HEAD:refs/heads/feature-name
```

Stop only for an actual coordination or authority conflict, dirty work that
cannot be preserved safely, inability to establish the target workspace, or
uncertainty about the authorized push destination. Then claim while the PR is
open and Draft, with no active lease:

```sh
python3 scripts/continuum.py claim --pr https://github.com/owner/project/pull/42
```

The command prints the created GitHub comment ID. That ID is the lease
identity. Implement, test, commit, and push using the repository's ordinary
workflow.

Planning, branch ownership, and worktree ownership do not transfer a lease. If
another writer takes over after a claim, the current writer releases its claim
and the next writer makes a fresh claim before product-repository writes.

After the shared PR head matches the clean local HEAD, release with the claim
comment ID:

```sh
python3 scripts/continuum.py release --pr https://github.com/owner/project/pull/42 --claim <claim-comment-id>
```

The client requires a clean worktree and local HEAD equal to the PR's reread
shared HEAD after push. It does not require a particular local branch name. The
release contains the full 40-character HEAD SHA and is reread before success
is reported. Then use GitHub's native Ready transition, review, checks, and
human-authorized merge.

## Conflicts and abandoned leases

Overlapping claims, untrusted records, or uncertain state stop writes. A stale
release cannot clear a newer claim because releases name the immutable claim
comment ID. A repository OWNER may recover only after confirming all writers
stopped and recording the unshared-work inventory and disposition:

```sh
python3 scripts/continuum.py recover --pr https://github.com/owner/project/pull/42 \
  --confirmation 'All writers stopped; unshared work inventoried and disposition recorded'
```

Recovery clears earlier claims. New work uses a new claim comment. The client
never treats an older release as a release of that new claim.

`bash scripts/check-continuum.sh` validates the canonical source and offline
conformance tests. The suite uses local data and does not write to GitHub.
