# Using the reference client

Continuum 0.5 uses Python 3.9+, Git, and authenticated `gh`. The client does not
install files in a target repository. Existing 0.4 PRs use their exact pinned
0.4.1 protocol and client; do not run this client against their histories.

## Pin and inspect

New 0.5 PRs use an ordinary Markdown description and one immutable protocol
pin:

```text
Continuum: 0.5.0; protocol source: Leftium/continuum@<40-character-commit>:protocol/CONTINUUM.md
```

Read accepted-base policy and project blockers before work. Inspect the PR's
state and complete coordination history before claiming. The client fetches
GitHub comments and reconstructs lease state locally, then prints only the
current lease state.

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
  --body $'Describe the work here.\n\nContinuum: 0.5.0; protocol source: Leftium/continuum@<40-character-commit>:protocol/CONTINUUM.md'
```

Replace the placeholder with the exact source commit and use the repository's
authorized remote. Claim the new PR before implementation writes, then switch
to and verify its exact head branch.

```sh
python3 scripts/continuum.py status --pr https://github.com/owner/project/pull/42
```

## Claim, work, and release

Claim while the PR is open and Draft, with no active lease:

```sh
python3 scripts/continuum.py claim --pr https://github.com/owner/project/pull/42
```

The command prints the fresh run UUID. Before product writes, use the PR's exact
head branch and verify its shared HEAD. Implement, test, commit, and push using
the repository's ordinary workflow. Commits are savepoints; no checkpoint
comments are needed.

After the shared PR head matches the clean local HEAD, release with that run:

```sh
python3 scripts/continuum.py release --pr https://github.com/owner/project/pull/42 --run <run-uuid>
```

The release stores the exact full HEAD SHA and is reread before success is
reported. Then use GitHub's native Ready transition, review, checks, and
human-authorized merge. Review fixes return the PR to Draft and require a fresh
claim.

## Conflicts and abandoned leases

Any overlapping live claims, malformed protocol record, untrusted author,
wrong-run release, or uncertain state stops writes. Never resolve a conflict by
guessing which writer is active. A repository OWNER may recover only after
confirming all writers stopped and recording the unshared-work inventory
and disposition:

```sh
python3 scripts/continuum.py recover --pr https://github.com/owner/project/pull/42 \
  --confirmation 'All writers stopped; unshared work inventoried and disposition recorded'
```

An OWNER recovery unconditionally clears all earlier leases, including leases
outside the fetched history. After recovery, claim with a new UUID. Malformed
records or uncertain writer status require human reconciliation before writing.

`bash scripts/check-continuum.sh` validates the canonical source and offline
conformance tests. The suite uses local data and does not write to GitHub.
