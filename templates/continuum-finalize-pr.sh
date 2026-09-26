#!/usr/bin/env bash
set -euo pipefail

plan=PR-PLAN.md

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "not inside a Git worktree" >&2
  exit 1
fi

branch=$(git symbolic-ref --quiet --short HEAD || true)
if [[ -z "$branch" ]]; then
  echo "detached HEAD; check out the PR branch before finalizing" >&2
  exit 1
fi

if [[ ! -e "$plan" ]]; then
  echo "$plan is already absent"
  exit 0
fi

if ! git ls-files --error-unmatch "$plan" >/dev/null 2>&1; then
  echo "$plan exists but is not tracked" >&2
  exit 1
fi

if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  echo "tracked worktree changes are present; refusing to mix them with finalization" >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI is required to verify the PR is Ready" >&2
  exit 1
fi

IFS=$'\t' read -r state is_draft head_ref < <(
  gh pr view --json state,isDraft,headRefName \
    --jq '[.state, (.isDraft | tostring), .headRefName] | @tsv'
)

if [[ "$state" != "OPEN" || "$is_draft" != "false" ]]; then
  echo "the current branch must belong to an open Ready PR" >&2
  exit 1
fi

if [[ "$head_ref" != "$branch" ]]; then
  echo "current branch '$branch' does not match PR head '$head_ref'" >&2
  exit 1
fi

git rm -- "$plan"

staged=$(git diff --cached --name-only)
if [[ "$staged" != "$plan" ]]; then
  echo "finalization staged an unexpected path; aborting before commit" >&2
  git restore --staged -- "$plan"
  git restore -- "$plan"
  exit 1
fi

git commit -m "chore: remove temporary PR plan"
git push

echo "Continuum PR plan removed and pushed from $branch"
