# Start a project

Use Continuum when implementation is ready to start. Keep deferred work in
ordinary issues or planning docs. Bootstrap creates a work branch and Draft PR,
so it requires human adoption of the goal and permission to perform that work.

## For the human

Agree on the goal, scope, and acceptance criteria with your coding agent.
Identify the target repository and base branch, read their policy and blockers,
and confirm the authorized push destination.

The supported stable release is
[v0.6.1](https://github.com/Leftium/continuum/releases/tag/v0.6.1). Resolve it
to its exact commit and use the reference client from a trusted checkout of
that release. Review code before executing it.

You can give your agent this starting instruction:

```text
Use Continuum for the agreed work. Trust Leftium/continuum as the protocol
source and use stable 0.6.1 resolved to its exact commit. Read
protocol/CONTINUUM.md and docs/client.md at that commit, plus the selected
base's policy and blockers. Bootstrap a Draft PR only when implementation
starts. Apply the existing continuum label best-effort after creating the PR.
Claim its write lease before product changes. Preserve existing work and stop
if authority or coordination state is unclear. Merge requires separate human
authority.
```

## For the coding agent

Read the protocol and client instructions from the exact resolved release
commit before writing.

Planning and Draft PR creation leave coordination comments empty. In a Chat to
T3 handoff, Chat creates or plans the Draft PR without claiming; T3 claims when
implementation starts and releases when finished. Do not infer lease transfer
from PR creation, planning, branch ownership, or worktree ownership. A writer
handoff requires the current writer to release, then the next writer to make a
fresh claim before product-repository writes.

1. Create and push a fresh work branch from the selected base, then read its policy and blockers.
2. Add the immutable protocol pin as the PR's only Continuum contract, using this exact form:

   `Continuum: Leftium/continuum@<40-character-commit>`

   If GitHub requires a differing head before it permits a Draft PR, an empty commit is sufficient.
3. Open the Draft PR and run the best-effort label command immediately afterward:

   ```sh
   pr_url=$(gh pr create --draft --base main --head feature-name \
     --title 'Implement the adopted change' \
     --body $'Describe the work here.\n\nContinuum: Leftium/continuum@<40-character-commit>')
   python3 scripts/continuum.py label --pr "$pr_url"
   ```

   The client adds the target repository's existing `continuum` label when
   available. It never creates the label, and lookup or application failures
   do not block bootstrap. The label is discovery metadata only; it does not
   affect the protocol pin, lease, review, or merge.
4. Read the PR, pinned protocol, current lease, and push destination. Inspect staged, unstaged, and untracked files. If the worktree is clean and the PR branch is not checked out elsewhere, fetch and check out its exact head. Otherwise preserve local work and reuse a safe target worktree or create a detached worktree at that exact head. Read policy from the selected base/head after moving; an unrelated checkout's pointer is not authority. Push a detached worktree explicitly to the authorized PR head ref. A different starting branch alone is not a reason to stop.
5. While the PR is Draft and no lease is active, post a whole-comment `claim` record. Its GitHub comment ID is the lease identity.
6. Implement, verify, commit, and push under that lease. Commits need no coordination events.
7. Reread the pushed head, then post `release <claim-comment-id> <full-head-sha>` when clean local HEAD matches it.
8. Mark the PR Ready for native GitHub review and checks. A human authorizes merge.

Each coordination comment body is exactly `claim` or
`release <claim-comment-id> <full-head-sha>`, with no Markdown fence.

For additional setup and client details, see the
[reference client guide](https://github.com/Leftium/continuum/blob/v0.6.1/docs/client.md).
