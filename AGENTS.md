# Agent instructions



## Project-owned 0.4 migration admission gate

Project owner Leftium authorized the migration drain in
[issue #21](https://github.com/Leftium/continuum/issues/21). This policy activates
when [gate PR #23](https://github.com/Leftium/continuum/pull/23) merges into `main`.
It remains active through the final migration merge. Preserve this project-owned
section when removing the managed Continuum block; after migration it records
the historical boundary, and new implementation work uses stable Continuum 0.4.

While the gate is active, do not start ordinary 0.3 implementation, acquire new
ordinary 0.3 claims or bootstrap branches, reopen old 0.3 work for implementation,
or implicitly adopt orphan branches. Existing pre-gate work must finish under
0.3 or be explicitly abandoned by the owner. Reopening a PR or finding an old
branch does not grant permission to resume it.

The sole post-gate admission/drain exception is
[issue #22](https://github.com/Leftium/continuum/issues/22), reserved claim identity
`continuum-0.4-final-migration`. Its pre-PR acquisition comment and resulting PR
must name that identity and issue. The exception permits only removing the
retained 0.3 installation, updating its checks and migration/status documentation,
and preserving project-owned policy and the 0.4 protocol/client/tests, as scoped
in #22. It does not admit docs-site work, unrelated protocol changes, publication,
or deployment. The designated migration PR remains governed by 0.3 through merge,
including lease, independent review, and root `PR-PLAN.md` finalization. Merge
requires separate human authority.

Before acquiring that claim or bootstrapping its PR, #23 must finish implementation, review,
0.3 plan-only finalization, and merge. Reverify the drain immediately before
migration bootstrap and before migration merge. Inspect GitHub PRs and coordination
comments together with branch provenance: open PR enumeration alone is insufficient.
Inventory every other unmerged Draft/Ready PR, active or suspended writing run,
acquisition claim, known pre-PR bootstrap branch/claim, and closed-unmerged work
intended to resume. Any active/resumable ordinary 0.3 work or competing claim/lease
blocks migration until it finishes or the owner explicitly abandons it. Record
new discoveries and their disposition durably on #21/#22 or the relevant PR;
GitHub coordination records remain authoritative for current lease and review state.

The supported stable prerequisite was verified during gate preparation:
[release `v0.4.0`](https://github.com/Leftium/continuum/releases/tag/v0.4.0) is
published, neither draft nor prerelease, and is the latest stable release. Its tag
resolves to `76fed3f2fb03df0d7121fc8e026644431de16203`. Reverify that exact release
and commit before migration bootstrap and merge; a development pin is insufficient.

### Drain inventory recorded at gate preparation

The 2026-10-07 (Asia/Seoul) inspection found the following identities and
dispositions. This is the preparation record, not a substitute for the required
fresh drain checks.

| Inventory | Identity and disposition |
| --- | --- |
| Pre-gate unmerged PR | #23 / `issue/21-migration-admission-gate` is the only open PR. Finish, independently review, finalize, and merge it under 0.3 before #22 bootstrap. |
| Writing runs and acquisition claims | #23's bootstrap claim was explicitly released. Its implementation runs must acquire/release on #23; all must be released before migration bootstrap. No other active or suspended lease/acquisition claim was found in issue/PR coordination records. |
| Pre-PR bootstrap work | No other known bootstrap branch/claim was found. #23's bootstrap became its inventoried PR; #22 is reserved and has not bootstrapped. Newly discovered pre-gate work must become an inventoried 0.3 PR or be explicitly owner-abandoned. |
| Closed-unmerged resumable work | None found. Every historical PR (#2, #4, #6, #8, #11, #13, #15, #18, #20) is merged; those PRs and their historical heads are non-resumable 0.3 work. |
| Deferred ordinary work | [Issue #16](https://github.com/Leftium/continuum/issues/16), docs-site implementation, waits until migration lands and then uses 0.4. |
| Completed redesign | [Issue #14](https://github.com/Leftium/continuum/issues/14) is closed; its implementation merged in #15 and supplies no migration exception. |

Every remaining remote branch other than `main` and #23's branch was verified at
the exact head of a merged PR. These are historical artifacts, not orphan
bootstrap work or permission to resume implementation:

| Historical branch | Merged PR |
| --- | --- |
| `protocol/state-inference` | #2 |
| `protocol/field-use-refinements` | #4 |
| `protocol/pr-plan` | #6 |
| `issue/7-continuum-0.3-execution` | #8 |
| `issue/10-renamed-remotes` | #11 |
| `issue/12-managed-continuum-file` | #13 |
| `issue/14-pr-local-continuum` | #15 |

This gate PR preserves the managed 0.3 block and all retained 0.3 machinery.
It does not itself migrate the repository or authorize #22 bootstrap before
the gate merges and the ordinary-work drain is reverified empty.

## Workflow after the migration boundary

After PR #24 merges, new implementation work uses published stable Continuum
0.4.0 at `76fed3f2fb03df0d7121fc8e026644431de16203`. Read the canonical
[protocol](protocol/CONTINUUM.md) and [client instructions](docs/client.md), then
inspect live GitHub PR contracts, comments and repository policy before writing.
Bootstrap resolves the supported stable release to an exact source commit; the
PR body retains its contract and plan, and comments record run-scoped ownership.
Do not restore the removed 0.3 installation or create root `PR-PLAN.md` for new
work. The admission gate above remains active until PR #24 merges and records
historical policy afterward; issue #16 waits for that merge.

PR #24 itself remains governed by the 0.3 protocol from its accepted base
`c2a474850606171788c30be9a3e7183c19bdff02` through independent review, plan-only
finalization and merge. After clean review, verify the reviewed shared HEAD and
push destination, delete only root `PR-PLAN.md`, commit as
`chore: remove temporary PR plan`, and non-force push to the PR branch. Reverify
the drain and stable release before merge, which needs separate human authority.
