# Continuum

Continuum is a GitHub-native workflow for coordinating coding agents and humans
across long-running software projects.

The 0.5 design centers on one run-scoped write lease. A normal PR uses two
visible coordination comments: claim before product writes, then release with
the exact full shared HEAD SHA. GitHub Draft/Ready state, reviews, checks, and a
human-authorized merge handle the rest. The new protocol has no JSON PR-body
contract, target-repository pointer, or cleanup lifecycle.

Read the canonical [0.5 protocol](protocol/CONTINUUM.md) and [reference client
instructions](docs/client.md). The client uses Python 3.9+, Git, and
authenticated `gh`. It does not install files in a target repository.

Continuum 0.5 is an incompatible development version. Do not use it as a stable
workflow or publish it from this PR. Existing 0.4 PRs keep their exact pinned
0.4.1 interpreter and history. New work uses 0.5 only after a separate stable
release makes it available.

The public documentation site at
[leftium.github.io/continuum](https://leftium.github.io/continuum/) retains the
published 0.4 guidance until its documentation work is updated separately. See
[site maintenance](docs/site/maintaining.md) for local builds and Pages setup.

## Starting work

Read accepted-base policy and project blockers. Claim the Draft PR before
product writes, implement and verify under that lease, then release with the
exact shared HEAD SHA. Mark the PR Ready for native GitHub review and checks.
Merge requires human authority.

Use `python3 scripts/continuum.py status --pr <full-pr-url>` to inspect current
lease state. See the [client guide](docs/client.md) for claim, release, and
owner-only abandoned-lease recovery.

## Repository layout

- `protocol/CONTINUUM.md` - canonical 0.5 protocol and visible comment records.
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
Tests do not write to GitHub. Checks do not publish releases, deploy, or merge.

For the documentation build, install `requirements-docs.txt` in an isolated
environment and run `python -m mkdocs build --strict`, as described in
[site maintenance](docs/site/maintaining.md#build-and-preview-locally).
