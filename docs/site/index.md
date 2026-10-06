# Continuum

Continuum coordinates coding agents and humans through GitHub pull requests.
Each PR keeps its current contract and plan in the body. Comments record who
owns the work, what passed verification, and what needs review or recovery.

That gives the next run a place to pick up: read the PR, check the shared head
and ownership, then acquire a lease before writing. A temporary `AGENTS.md`
pointer helps agents find the PR and is removed after clean independent review.
The plan stays in the PR body.

[Start a project](bootstrap.md) for the human and coding-agent bootstrap steps.
The optional reference client uses Python 3.9+, Git and authenticated `gh`, with
no Python package dependencies. Other clients can follow the same wire format.

## Supported protocol

The supported stable version is
[v0.4.0](https://github.com/Leftium/continuum/releases/tag/v0.4.0), resolved to
commit `76fed3f2fb03df0d7121fc8e026644431de16203`.
Read the [canonical protocol at that exact commit](https://github.com/Leftium/continuum/blob/76fed3f2fb03df0d7121fc8e026644431de16203/protocol/CONTINUUM.md)
and the [matching reference client instructions](https://github.com/Leftium/continuum/blob/76fed3f2fb03df0d7121fc8e026644431de16203/docs/client.md).

This site is evergreen guidance. GitHub releases and the version-pinned source
remain authoritative for protocol rules and integrity. Bootstrap resolves a
supported stable release once and retains the exact commit in the PR contract;
an active PR keeps its pin even if a newer release appears.

## How work moves

1. A human adopts the work and the selected base's policy and blockers are checked.
2. Bootstrap creates a dedicated branch and Draft PR with a sealed contract.
3. A fresh run acquires ownership, implements, verifies, and pushes checkpoints.
4. The writer records Ready evidence and releases ownership for independent review.
5. After clean review, an exclusive cleanup run removes the temporary pointer.
6. A separately authorized merge follows checks on the final shared head.

Issues retain ordinary GitHub semantics. Labels help discovery; contracts and
ownership comments govern coordination. Continuum does not merge automatically.
