#!/usr/bin/env bash
set -euo pipefail

root=CONTINUUM.md
template=templates/CONTINUUM.md
spec=specs/001-continuum.md
agents=AGENTS.md

root_version=$(sed -n 's/^continuum: //p' "$root" | head -n1)
template_version=$(sed -n 's/^continuum: //p' "$template" | head -n1)
spec_version=$(sed -n 's/^# Continuum protocol \([0-9][0-9.]*\)-draft$/\1/p' "$spec" | head -n1)

test -n "$root_version"
test "$root_version" = "$template_version"
test "$root_version" = "$spec_version"

grep -Fq '{{issues_url}}' "$template"
grep -Fq '{{pull_requests_url}}' "$template"
grep -Fq '{{milestones_url}}' "$template"

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
