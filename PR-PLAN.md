# PR Plan

Issue: #10

## Goal

Allow the Continuum cleanup finalizer to accept a configured GitHub push URL that uses a repository's pre-rename slug when GitHub canonicalizes that slug to the PR head repository.

Preserve all existing destination-safety checks and continue pushing to/verifying the actual configured push URL.

## Scope

- Keep the existing fast path for literal case-insensitive repository-slug matches.
- When a parsed single GitHub push URL does not literally match the PR head repository, resolve that slug through GitHub and compare its canonical repository name to the PR head repository.
- Reject lookup failures, genuine repository mismatches, non-GitHub URLs, and ambiguous multiple push URLs.
- Do not rewrite the user's Git remote.
- Keep the finalizer and installable template byte-identical.
- Add focused fake-git/gh regression coverage for renamed-repository success and genuine mismatch rejection.
- Preserve macOS stock-Bash compatibility.

## Checkpoint A — regression coverage

- Extend the fake `gh` harness to model GitHub repository canonicalization.
- Add the HN rename case: PR head `Leftium/hn`, push URL `https://github.com/Leftium/news.git`, canonical result `Leftium/hn`.
- Add/retain a genuine mismatched-repository rejection case and the existing multiple-push rejection.
- Confirm the rename test fails against the old finalizer behavior conceptually, then continue to the implementation.

## Checkpoint B — finalizer fix

- Add canonical repository resolution only as a fallback after literal slug comparison fails.
- Accept the remote only when GitHub's canonical `full_name` matches the PR head repository case-insensitively.
- Keep `head_remote_url` set to the original configured push URL so push verification still tests the real destination.
- Synchronize `scripts/continuum-finalize-pr.sh` and `templates/continuum-finalize-pr.sh`.
- Commit and non-force-push the coherent checkpoint, then continue without yielding.

## Checkpoint C — verification

- Run/observe the Continuum self-check and finalizer regressions.
- Confirm stock-Bash syntax/static safeguards still pass.
- Inspect the complete diff for scope.
- Record the HN pilot linkage and any limitations.
- Release the lease and mark the PR Ready for independent review.

## Verify

- `scripts/test-finalizer.sh`
- `scripts/check-continuum.sh`
- GitHub Actions `Continuum`
- finalizer/template byte equality
- no unrelated protocol changes

The user controls final merge.
