#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
finalizer="$root/scripts/continuum-finalize-pr.sh"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

fail() {
  echo "finalizer regression test failed: $*" >&2
  exit 1
}

setup_case() {
  local name=$1
  CASE_ROOT="$tmp/$name"
  FAKE_WORK="$CASE_ROOT/work"
  FAKE_STATE="$CASE_ROOT/state"
  FAKE_BIN="$CASE_ROOT/bin"
  mkdir -p "$FAKE_WORK" "$FAKE_STATE" "$FAKE_BIN"
  printf 'initial\n' > "$FAKE_STATE/head"
  printf 'initial\n' > "$FAKE_STATE/remote"
  : > "$FAKE_STATE/gh-polls"
  printf '# temporary plan\n' > "$FAKE_WORK/PR-PLAN.md"

  cat > "$FAKE_BIN/git" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

cmd=${1:-}
shift || true

case "$cmd" in
  rev-parse)
    case "${1:-}" in
      --is-inside-work-tree) printf 'true\n' ;;
      --show-toplevel) printf '%s\n' "$FAKE_WORK" ;;
      HEAD) cat "$FAKE_STATE/head" ;;
      *) exit 2 ;;
    esac
    ;;
  symbolic-ref)
    printf '%s\n' "${FAKE_BRANCH:-feature}"
    ;;
  status)
    [[ -f "$FAKE_STATE/dirty" ]] && printf ' M tracked.txt\n'
    ;;
  ls-files)
    [[ -f "$FAKE_WORK/PR-PLAN.md" ]]
    ;;
  remote)
    if [[ "${1:-}" == "get-url" ]]; then
      shift
      [[ "${1:-}" == "--push" ]] && shift
      [[ "${1:-}" == "--all" ]] && shift
      [[ "${1:-}" == "origin" ]] || exit 2
      printf '%s\n' "${FAKE_REMOTE_URL:-https://github.com/Leftium/continuum.git}"
      if [[ -f "$FAKE_STATE/multiple-push-urls" ]]; then
        printf 'https://github.com/other/repository.git\n'
      fi
    else
      printf 'origin\n'
    fi
    ;;
  rm)
    rm -f "$FAKE_WORK/PR-PLAN.md"
    printf 'PR-PLAN.md\n' > "$FAKE_STATE/staged"
    ;;
  diff)
    [[ "${1:-}" == "--cached" && "${2:-}" == "--name-only" ]] || exit 2
    [[ -f "$FAKE_STATE/staged" ]] && cat "$FAKE_STATE/staged"
    ;;
  restore)
    exit 0
    ;;
  commit)
    printf 'cleanup\n' > "$FAKE_STATE/head"
    rm -f "$FAKE_STATE/staged"
    ;;
  push)
    printf '%s\n' "$*" > "$FAKE_STATE/push-args"
    if [[ -f "$FAKE_STATE/push-fail" ]]; then
      exit 1
    fi
    cp "$FAKE_STATE/head" "$FAKE_STATE/remote"
    ;;
  ls-remote)
    printf '%s\n' "$*" > "$FAKE_STATE/ls-remote-args"
    [[ -f "$FAKE_STATE/verify-fail" ]] && exit 1
    if [[ "${1:-}" == "origin" ]]; then
      # Fetching through the remote name reads the other repository.
      printf 'initial\trefs/heads/feature\n'
      exit 0
    fi
    [[ "${1:-}" == "${FAKE_REMOTE_URL:-https://github.com/Leftium/continuum.git}" ]] || exit 2
    printf '%s\trefs/heads/%s\n' "$(cat "$FAKE_STATE/remote")" "${FAKE_HEAD_REF:-feature}"
    ;;
  *)
    echo "unexpected fake git command: $cmd $*" >&2
    exit 2
    ;;
esac
EOF
  chmod +x "$FAKE_BIN/git"

  cat > "$FAKE_BIN/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

[[ "${1:-}" == "pr" && "${2:-}" == "view" ]] || exit 2

if [[ "$*" == *"state,isDraft,headRefName,headRefOid,headRepository"* ]]; then
  printf 'OPEN\tfalse\t%s\tinitial\t%s\n' "${FAKE_HEAD_REF:-feature}" "${FAKE_HEAD_REPO:-Leftium/continuum}"
  exit 0
fi

if [[ "$*" == *"headRefOid"* ]]; then
  [[ -f "$FAKE_STATE/metadata-fail" ]] && exit 1
  count=0
  [[ -s "$FAKE_STATE/gh-polls" ]] && count=$(cat "$FAKE_STATE/gh-polls")
  count=$((count + 1))
  printf '%s\n' "$count" > "$FAKE_STATE/gh-polls"
  if (( count <= ${FAKE_STALE_POLLS:-0} )); then
    printf 'initial\n'
  else
    cat "$FAKE_STATE/head"
  fi
  exit 0
fi

exit 2
EOF
  chmod +x "$FAKE_BIN/gh"
}

run_finalizer() {
  PATH="$FAKE_BIN:$PATH" \
  FAKE_WORK="$FAKE_WORK" \
  FAKE_STATE="$FAKE_STATE" \
  FAKE_HEAD_REF="${FAKE_HEAD_REF:-feature}" \
  FAKE_HEAD_REPO="${FAKE_HEAD_REPO:-Leftium/continuum}" \
  FAKE_STALE_POLLS="${FAKE_STALE_POLLS:-0}" \
  CONTINUUM_FINALIZER_POLL_ATTEMPTS=5 \
  CONTINUUM_FINALIZER_POLL_SECONDS=0 \
    bash "$finalizer"
}

setup_case success
FAKE_REMOTE_URL=https://github.com/leftium/continuum.git
export FAKE_REMOTE_URL
FAKE_STALE_POLLS=2
export FAKE_STALE_POLLS
run_finalizer > "$CASE_ROOT/stdout" 2> "$CASE_ROOT/stderr" || fail "explicit-push success case returned nonzero"
grep -Fq "Continuum PR plan removed and pushed" "$CASE_ROOT/stdout" || fail "success message missing"
grep -Fxq 'origin HEAD:refs/heads/feature' "$FAKE_STATE/push-args" || fail "finalizer did not use explicit branch refspec"
grep -Fxq "$FAKE_REMOTE_URL refs/heads/feature" "$FAKE_STATE/ls-remote-args" || fail "verification did not query the push URL"
[[ "$(cat "$FAKE_STATE/remote")" == "cleanup" ]] || fail "remote ref was not updated"
[[ "$(cat "$FAKE_STATE/gh-polls")" == "3" ]] || fail "bounded stale-head polling did not converge as expected"
unset FAKE_REMOTE_URL
unset FAKE_STALE_POLLS

setup_case multiple-push-urls
touch "$FAKE_STATE/multiple-push-urls"
if run_finalizer > "$CASE_ROOT/stdout" 2> "$CASE_ROOT/stderr"; then
  fail "multiple push destinations unexpectedly succeeded"
fi
grep -Fq "single push URL" "$CASE_ROOT/stderr" || fail "ambiguous-destination diagnostic missing"
[[ -f "$FAKE_WORK/PR-PLAN.md" && ! -f "$FAKE_STATE/push-args" ]] || fail "ambiguous destination changed the plan or pushed"

setup_case stale-metadata
FAKE_STALE_POLLS=10
export FAKE_STALE_POLLS
if run_finalizer > "$CASE_ROOT/stdout" 2> "$CASE_ROOT/stderr"; then
  fail "stale metadata unexpectedly converged"
fi
grep -Fq "after 5 checks; the push succeeded" "$CASE_ROOT/stderr" || fail "propagation diagnostic missing"
[[ "$(cat "$FAKE_STATE/gh-polls")" == "5" ]] || fail "metadata polling was not bounded"
unset FAKE_STALE_POLLS

setup_case verification-failure
touch "$FAKE_STATE/verify-fail"
if run_finalizer > "$CASE_ROOT/stdout" 2> "$CASE_ROOT/stderr"; then
  fail "remote verification failure unexpectedly succeeded"
fi
grep -Fq "push succeeded, but remote branch verification failed" "$CASE_ROOT/stderr" || fail "verification failure diagnostic missing"

setup_case metadata-failure
touch "$FAKE_STATE/metadata-fail"
if run_finalizer > "$CASE_ROOT/stdout" 2> "$CASE_ROOT/stderr"; then
  fail "metadata read failure unexpectedly succeeded"
fi
grep -Fq "metadata could not be read; the push succeeded" "$CASE_ROOT/stderr" || fail "metadata read diagnostic missing"

setup_case push-failure
touch "$FAKE_STATE/push-fail"
if run_finalizer > "$CASE_ROOT/stdout" 2> "$CASE_ROOT/stderr"; then
  fail "push failure unexpectedly succeeded"
fi
grep -Fq "failed to push cleanup commit" "$CASE_ROOT/stderr" || fail "push failure diagnostic missing"

setup_case branch-mismatch
FAKE_HEAD_REF=other
export FAKE_HEAD_REF
if run_finalizer > "$CASE_ROOT/stdout" 2> "$CASE_ROOT/stderr"; then
  fail "branch mismatch unexpectedly succeeded"
fi
grep -Fq "does not match PR head" "$CASE_ROOT/stderr" || fail "branch mismatch diagnostic missing"
unset FAKE_HEAD_REF

setup_case dirty
touch "$FAKE_STATE/dirty"
if run_finalizer > "$CASE_ROOT/stdout" 2> "$CASE_ROOT/stderr"; then
  fail "dirty worktree unexpectedly succeeded"
fi
grep -Fq "tracked worktree changes are present" "$CASE_ROOT/stderr" || fail "dirty-worktree diagnostic missing"

echo "Continuum finalizer regression tests passed"
