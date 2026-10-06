# Start a project

Use Continuum when implementation is ready to start. Keep deferred work in
ordinary issues or planning docs. Bootstrap creates a work branch and PR, so it
requires human adoption of the goal and permission to perform that work.

## For the human

Agree on the goal, scope, acceptance criteria and verification with your coding
agent. Identify the trusted Continuum source repository, the target repository
and base branch, and the writable head repository. Read selected-base project
instructions and resolve ordinary blockers before bootstrap.

The supported stable release is
[v0.4.0](https://github.com/Leftium/continuum/releases/tag/v0.4.0) at
`76fed3f2fb03df0d7121fc8e026644431de16203`. Use an explicitly trusted local
checkout of that version for the reference client. Review code before executing
it; do not pipe downloaded scripts into a shell.

You can give your agent this starting instruction:

```text
Use Continuum for the agreed work. Trust Leftium/continuum as the protocol
source and use supported stable 0.4.0. Read the selected base's project policy
and blockers, then read protocol/CONTINUUM.md at exact source commit
76fed3f2fb03df0d7121fc8e026644431de16203. Follow that pinned protocol and the
matching client instructions. Preserve my existing work. Bootstrap only when
implementation starts, acquire ownership before writing, and stop for unclear
authority or conflicting state. Merge and publication need separate authority.
```

## For the coding agent

Read the [pinned protocol](https://github.com/Leftium/continuum/blob/76fed3f2fb03df0d7121fc8e026644431de16203/protocol/CONTINUUM.md)
and [pinned client instructions](https://github.com/Leftium/continuum/blob/76fed3f2fb03df0d7121fc8e026644431de16203/docs/client.md)
before any writes. The summary below is an entry point; the pinned source owns
the full lifecycle and recovery rules.

1. Confirm adoption, selected-base instructions, blockers and the push destination.
   Inspect both staged and unstaged changes. Preserve unrelated work; the
   reference bootstrap requires a clean workspace.
2. Prepare the seven-field plan JSON and recovery journal outside the worktree.
   The plan contains `goal`, `scope`, `acceptance`, `plan`, `verification`,
   `changes` and `context`.
3. Run bootstrap from a trusted client checkout. Stable discovery must resolve
   the supported release to an exact commit and validate its protocol metadata.
   Missing or unsupported releases stop bootstrap.
4. Verify the created Draft PR's contract and exact head, then claim a fresh
   run-scoped write lease before implementation or controlled-body edits.
5. Verify and push coherent checkpoints. Release ownership before a normal
   handoff. Ready requires actual verification and then independent review;
   cleanup and merge have separate gates.

For same-repository work, the invocation looks like this after you substitute
the adopted repository, plan paths and actual acceptance reference:

```sh
python3 /trusted/continuum/scripts/continuum.py bootstrap \
  --repo owner/project --base main --head-repo owner/project --remote origin \
  --plan /outside/plan.json --journal /outside/bootstrap.json \
  --title 'Implement the adopted change' --start-now \
  --accepted-policy 'Actual human adoption and base-policy/blocker decision reference' \
  --label skip --label-backfill skip
```

`origin` must point to the authorized writable repository. Forks use the
appropriate head repository and remote. Label creation is optional and needs
explicit consent; skipping labels does not change coordination authority.

Bootstrap creates a temporary discovery pointer while preserving existing
`AGENTS.md` instructions. Version 0.4 needs no installed root protocol,
`PR-PLAN.md` or finalizer in the target repository.

If the head, target, contract or ownership changes unexpectedly, stop writes and
follow the pinned recovery procedure. A timeout is not proof of success, and
reopening a PR does not restore ownership. Existing 0.3 work follows the
[migration boundary in the pinned protocol](https://github.com/Leftium/continuum/blob/76fed3f2fb03df0d7121fc8e026644431de16203/protocol/CONTINUUM.md#version-03-migration-boundary).
