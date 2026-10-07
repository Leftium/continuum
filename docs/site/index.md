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
to its exact commit before using the protocol. PRs on 0.6.1 pin it as
`Continuum: Leftium/continuum@<40-character-commit>`. Read the [canonical
protocol](https://github.com/Leftium/continuum/blob/v0.6.1/protocol/CONTINUUM.md)
and [matching client instructions](https://github.com/Leftium/continuum/blob/v0.6.1/docs/client.md)
from that exact commit.

The 0.6.2 source introduces standalone sentences such as `This PR was claimed`
and `This PR's claim <claim-comment-id> was released at <full-head-sha>`, plus
explanatory pins such as `This PR follows the [Continuum protocol at <short-commit>](https://github.com/Leftium/continuum/blob/<40-character-commit>/protocol/CONTINUUM.md).`
The link target retains the full immutable SHA; its visible text is presentation. Use these for new PRs only after
stable 0.6.2 is published; existing pins retain their original record grammar.
The [bootstrap guide](bootstrap.md) explains that release boundary and the
recommended PR-body sections.

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
