#!/usr/bin/env bash
set -euo pipefail

root=CONTINUUM.md
template=templates/CONTINUUM.md
pr_plan_template=templates/PR-PLAN.md
finalizer=scripts/continuum-finalize-pr.sh
finalizer_template=templates/continuum-finalize-pr.sh
finalizer_test=scripts/test-finalizer.sh
spec=specs/001-continuum.md
agents=AGENTS.md

root_version=$(sed -n 's/^continuum: //p' "$root" | head -n1)
template_version=$(sed -n 's/^continuum: //p' "$template" | head -n1)
spec_version=$(sed -n 's/^# Continuum protocol \([0-9][0-9.]*\)-draft$/\1/p' "$spec" | head -n1)

test -n "$root_version"
test "$root_version" = "$template_version"
test "$root_version" = "$spec_version"

test -f "$pr_plan_template"
grep -Fq '# PR Plan' "$pr_plan_template"
grep -Fq '## Goal' "$pr_plan_template"
grep -Fq '## Scope' "$pr_plan_template"
grep -Fq '## Verify' "$pr_plan_template"
grep -Fq 'Checkpoints are durable savepoints' "$pr_plan_template"
grep -Fq 'delete the root' "$pr_plan_template"

test -f "$finalizer"
test -f "$finalizer_template"
cmp "$finalizer" "$finalizer_template"
bash -n "$finalizer"
grep -Fq 'git rm -- "$plan"' "$finalizer"
grep -Fq 'gh pr view --json state,isDraft,headRefName' "$finalizer"
grep -Fq 'git push "$head_remote" "HEAD:refs/heads/$head_ref"' "$finalizer"
grep -Fq 'git ls-remote "$head_remote" "refs/heads/$head_ref"' "$finalizer"
grep -Fq 'for ((attempt = 1; attempt <= poll_attempts; attempt++))' "$finalizer"
if grep -Fq ',,}' "$finalizer"; then
  echo "finalizer uses Bash 4-only lowercase expansion" >&2
  exit 1
fi
if grep -Fxq 'git push' "$finalizer"; then
  echo "finalizer still contains an unqualified plain git push" >&2
  exit 1
fi

test -f "$finalizer_test"
bash -n "$finalizer_test"
bash "$finalizer_test"

grep -Fq '{{issues_url}}' "$template"
grep -Fq '{{pull_requests_url}}' "$template"
grep -Fq '{{milestones_url}}' "$template"
grep -Fq 'PR-PLAN.md' "$template"
grep -Fq 'PR-PLAN.md' "$root"
grep -Fq 'PR-PLAN.md' "$spec"

if grep -Eq '<(issues|pull-requests|milestones)-url>' "$template"; then
  echo "legacy angle-bracket URL placeholder found" >&2
  exit 1
fi

if grep -Eq '\{\{(issues|pull_requests|milestones)_url\}\}' "$root"; then
  echo "unreplaced URL placeholder found in root CONTINUUM.md" >&2
  exit 1
fi

grep -Fq '<!-- leftium:continuum:start -->' "$agents"
grep -Fq 'Read `CONTINUUM.md` before coordinating or modifying work.' "$agents"
grep -Fq 'provide standing authorization to carry the planned implementation through all checkpoints' "$agents"
grep -Fq 'A checkpoint is a savepoint, not a default handoff.' "$agents"
grep -Fq '<!-- leftium:continuum:end -->' "$agents"

normalized=$(mktemp)
trap 'rm -f "$normalized"' EXIT
sed \
  -e 's#https://github.com/Leftium/continuum/issues#{{issues_url}}#g' \
  -e 's#https://github.com/Leftium/continuum/pulls#{{pull_requests_url}}#g' \
  -e 's#https://github.com/Leftium/continuum/milestones#{{milestones_url}}#g' \
  "$root" > "$normalized"

diff -u "$normalized" "$template"

echo "Continuum self-check passed for protocol $root_version"
