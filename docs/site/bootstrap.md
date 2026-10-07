# Start a project

Use Continuum when implementation is ready to start. Keep deferred work in
ordinary issues or planning docs. Bootstrap creates a work branch and Draft PR,
so it requires human adoption of the goal and permission to perform that work.

## For the human

Agree on the goal, scope, and acceptance criteria with your coding agent.
Identify the target repository and base branch, read their policy and blockers,
and confirm the authorized push destination.

The supported stable release is
[v0.5.0](https://github.com/Leftium/continuum/releases/tag/v0.5.0) at
`c833afbd8218c74427526eddfdafcd13c779d3e8`. Use the reference client from a
trusted checkout of that release. Review code before executing it.

You can give your agent this starting instruction:

```text
Use Continuum for the agreed work. Trust Leftium/continuum as the protocol
source and use stable 0.5.0. Read protocol/CONTINUUM.md at exact source commit
c833afbd8218c74427526eddfdafcd13c779d3e8, plus the selected base's policy and
blockers. Bootstrap a Draft PR only when implementation starts. Claim its
write lease before product changes. Preserve existing work and stop if authority
or coordination state is unclear. Merge requires separate human authority.
```

## For the coding agent

Read the [pinned protocol](https://github.com/Leftium/continuum/blob/c833afbd8218c74427526eddfdafcd13c779d3e8/protocol/CONTINUUM.md)
and [pinned client instructions](https://github.com/Leftium/continuum/blob/c833afbd8218c74427526eddfdafcd13c779d3e8/docs/client.md)
before writing.

1. Read the PR, pinned protocol, selected-base policy, blockers, current lease, and push destination.
2. While the PR is Draft and no lease is active, post one claim with a fresh UUIDv4 run identity.
3. Implement, verify, commit, and push under that lease. Commits need no coordination events.
4. Reread the pushed head, then post one release with the same run identity and exact full head SHA.
5. Mark the PR Ready for native GitHub review and checks. A human authorizes merge.

Each coordination comment contains one visible record:

```text
claim <run-uuid>
```

```text
release <run-uuid> <full-head-sha>
```

For additional setup and client details, see the
[reference client guide](https://github.com/Leftium/continuum/blob/c833afbd8218c74427526eddfdafcd13c779d3e8/docs/client.md).
