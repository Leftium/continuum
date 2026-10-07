# Continuum

Continuum is a GitHub-native workflow for coordinating coding agents and humans
across long-running software projects.

The 0.6 design uses GitHub comment IDs as write-lease identities. A normal PR
uses two coordination comments in 0.6.2: `This PR was claimed` before product
writes, then `This PR's claim <claim-comment-id> was released at <full-head-sha>`.
The claim comment ID identifies the lease; the full SHA identifies the shared
repository state at release. GitHub
Draft/Ready state, reviews, checks, and a human-authorized merge handle the
rest. The protocol has no JSON PR-body contract, target-repository pointer, or
cleanup lifecycle.

Read the canonical [0.6 protocol](protocol/CONTINUUM.md) and [reference client
instructions](docs/client.md). The client uses Python 3.9+, Git, and
authenticated `gh`. It does not install files in a target repository.

Continuum 0.6 is incompatible with earlier versions. Existing PRs keep their
exact pinned interpreter and history. New work uses the published stable 0.6
release. The sentence records and explanatory linked protocol pins begin with 0.6.2;
use them for new PRs only after that stable release is published. The client
continues to parse and emit the original records for 0.6.0/0.6.1 pins.

Prefer Summary, Changes, Verification, and optional Follow-ups when they make
the PR body easier to skim. Link the issue or spec for scope and acceptance
criteria. See the [description example](docs/client.md#pr-description).

The public documentation site at
[leftium.github.io/continuum](https://leftium.github.io/continuum/) documents the
stable 0.6 workflow. See [site maintenance](docs/site/maintaining.md) for local
builds and Pages setup.

## Starting work

Inspect the current worktree first. Switch to the exact PR head if it is clean,
or preserve local work in a separate worktree. Read policy from the selected
base/head after moving. Planning and Draft PR creation leave coordination
comments empty; the implementation writer claims immediately before product
writes. Implement and verify under that lease, release with the exact shared
HEAD SHA, and mark the PR Ready for native GitHub review and checks. A writer
handoff requires release followed by a fresh claim. Merge requires human
authority.

Use `python3 scripts/continuum.py status --pr <full-pr-url>` to inspect current
lease state. See the [client guide](docs/client.md) for claim, release, and
owner-only abandoned-lease recovery.

## Repository layout

- `protocol/CONTINUUM.md` - canonical 0.6 protocol and whole-comment records.
- `scripts/continuum.py`, `scripts/continuum_core.py` - reference client and
  offline state parser.
- `tests/` - lease, conflict, recovery, and wire-format conformance tests.
- `AGENTS.md` - project-owned policy and historical migration boundary.
- `docs/` - client instructions, site maintenance, and historical release records.
- `specs/` - design history; these documents do not override the protocol.
- `scripts/check-continuum.sh` - canonical source validation and offline tests.

## Verification

Run `bash scripts/check-continuum.sh` for canonical source validation and the
full offline suite, or `python3 -m unittest discover -s tests` for tests alone.
Tests do not write to GitHub. Pull request checks do not publish releases, deploy, or merge. A main-branch protocol version bump runs the stable release workflow, which validates and publishes that version at the merge commit.

For the documentation build, install `requirements-docs.txt` in an isolated
environment and run `python -m mkdocs build --strict`, as described in
[site maintenance](docs/site/maintaining.md#build-and-preview-locally).
