# Continuum

Continuum coordinates coding agents and humans through GitHub pull requests. A
pull request is the work unit, and its description explains the change. A
claim comment's GitHub ID identifies the write lease. The owner releases it
with that ID and the exact shared head SHA when work is ready to hand off.

GitHub Draft/Ready state, reviews, checks, and a human-authorized merge handle
the rest. The normal workflow uses only a claim and a release coordination
record. Commits are savepoints; they do not need coordination events.

[Start a project](bootstrap.md) for the human and coding-agent bootstrap steps.
The optional reference client uses Python 3.9+, Git, and authenticated `gh`,
with no Python package dependencies.

## Supported protocol

The supported stable release is
[v0.6.1](https://github.com/Leftium/continuum/releases/tag/v0.6.1). Resolve it
to its exact commit before using the protocol. New PRs pin it as
`Continuum: Leftium/continuum@<40-character-commit>`. Read the [canonical
protocol](https://github.com/Leftium/continuum/blob/v0.6.1/protocol/CONTINUUM.md)
and [matching client instructions](https://github.com/Leftium/continuum/blob/v0.6.1/docs/client.md)
from that exact commit.

This site is evergreen guidance. The published release and version-pinned
source remain authoritative. An active PR keeps its protocol pin if a newer
release appears.

## How work moves

1. A human adopts the work and the selected base's policy and blockers are checked.
2. Bootstrap opens a Draft PR with an ordinary description and protocol pin.
3. A fresh claim comment identifies the lease; the writer implements, verifies, commits, and pushes.
4. The writer releases using that claim comment ID and exact shared head SHA, then marks the PR Ready.
5. Native GitHub review, checks, and a separately authorized human merge finish the work.

Issues retain ordinary GitHub semantics. Labels help discovery; the PR and its
coordination records govern the work. Continuum does not merge automatically.
