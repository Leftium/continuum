# Using the reference client

Continuum 0.6 uses Python 3.9+, Git, and authenticated `gh`. The client does
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

After reading the selected base's policy and blockers, create a fresh branch
from that base and open a Draft PR with an ordinary description and one
immutable protocol pin. Do not add a temporary target-repository file. If
GitHub requires a different head commit before it allows a Draft PR, an empty
commit is enough:

```sh
git switch -c feature-name origin/main
git commit --allow-empty -m 'chore: start Continuum PR'
git push -u origin feature-name
gh pr create --draft --base main --head feature-name \
  --title 'Implement the adopted change' \
  --body $'Describe the work here.\n\nContinuum: Leftium/continuum@<40-character-commit>'
```

Replace the placeholder with the exact source commit. Claim the PR before
implementation writes, then switch to and verify its exact head branch.

```sh
python3 scripts/continuum.py status --pr https://github.com/owner/project/pull/42
```

## Claim, work, and release

Claim while the PR is open and Draft, with no active lease:

```sh
python3 scripts/continuum.py claim --pr https://github.com/owner/project/pull/42
```

The command prints the created GitHub comment ID. That ID is the lease
identity. Before product writes, use the PR's exact head branch and verify its
shared HEAD. Implement, test, commit, and push using the repository's ordinary
workflow.

After the shared PR head matches the clean local HEAD, release with the claim
comment ID:

```sh
python3 scripts/continuum.py release --pr https://github.com/owner/project/pull/42 --claim <claim-comment-id>
```

The release contains the full 40-character HEAD SHA and is reread before
success is reported. Then use GitHub's native Ready transition, review, checks,
and human-authorized merge.

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
