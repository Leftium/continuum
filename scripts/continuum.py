#!/usr/bin/env python3
"""Small GitHub reference client for Continuum 0.6 lease records."""

import argparse
import json
import re
import subprocess
from urllib.parse import quote

import continuum_core as c

TRUSTED_REPOSITORY = "Leftium/continuum"
PIN = re.compile(r"^Continuum: Leftium/continuum@([0-9a-f]{40})$", re.MULTILINE)


def command(*args):
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    c.require(result.returncode == 0, "command failed: " + " ".join(args[:3]) + "\n" + result.stderr.strip())
    return result.stdout


def api(path, *args):
    return json.loads(command("gh", "api", path, *args))


def identity(url):
    match = re.fullmatch(r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/pull/([1-9][0-9]*)", url)
    c.require(match is not None, "use the full GitHub PR URL")
    return match.group(1), int(match.group(2))


def read_pr(url):
    repository, number = identity(url)
    pr = api(f"repos/{repository}/pulls/{number}")
    c.require(pr.get("head", {}).get("repo") and pr.get("base", {}).get("repo"), "PR head or base repository is unavailable")
    return pr


def pinned_protocol(pr):
    pins = PIN.findall(pr.get("body") or "")
    c.require(len(pins) == 1, "PR must contain one immutable Continuum 0.6 protocol pin")
    source = pins[0]
    content = command("gh", "api", f"repos/{TRUSTED_REPOSITORY}/contents/protocol/CONTINUUM.md?ref={source}",
                      "-H", "Accept: application/vnd.github.raw+json")
    match = re.match(r"---\ncontinuum: ([0-9]+)\.([0-9]+)\.([0-9]+)\nartifact: protocol/CONTINUUM\.md\n---\n", content)
    current = tuple(map(int, c.VERSION.split(".")))
    c.require(match is not None and tuple(map(int, match.groups()))[:2] == current[:2] and
              tuple(map(int, match.groups())) <= current,
              "pinned source is not a supported canonical protocol version")
    return source


def read_comments(repository, number):
    """Read comments in API order, retaining only records after latest recovery."""
    records = []
    page = 1
    while True:
        items = json.loads(command("gh", "api", f"repos/{repository}/issues/{number}/comments"
                                   f"?per_page=100&page={page}"))
        if not items:
            return records
        for item in items:
            comment = {"id": item.get("id"), "body": item.get("body") or "",
                       "author": (item.get("user") or {}).get("login", ""),
                       "author_association": item.get("author_association", "")}
            if (re.fullmatch(r"recover \| ([^\r\n|]+)", comment["body"]) and
                    comment["body"].split("|", 1)[1].strip() and
                    comment["author_association"] == "OWNER"):
                records = [comment]
            else:
                records.append(comment)
        page += 1


def state_for(url, pr=None):
    repository, number = identity(url)
    pr = pr or read_pr(url)
    pinned_protocol(pr)
    comments = read_comments(repository, number)
    state = c.reconstruct(comments, pr["user"]["login"])
    return repository, number, pr, state


def status(args):
    _, _, pr, state = state_for(args.pr)
    c.require(not state.conflict, "conflicting live claims; owner recovery required")
    print(json.dumps({"open": pr["state"] == "open", "draft": pr["draft"],
                      "head_sha": pr["head"]["sha"], "active_claims": sorted(state.active)}, separators=(",", ":")))


def post(repository, number, body):
    result = command("gh", "api", f"repos/{repository}/issues/{number}/comments",
                     "--method", "POST", "-f", "body=" + body)
    return json.loads(result)


def apply_continuum_label(repository, number):
    """Apply the existing discovery label when available; never block bootstrap."""
    try:
        api(f"repos/{repository}/labels/continuum")
    except (c.Invalid, json.JSONDecodeError, OSError):
        return False
    try:
        command("gh", "api", f"repos/{repository}/issues/{number}/labels",
                "--method", "POST", "-f", "labels[]=continuum")
    except (c.Invalid, json.JSONDecodeError, OSError):
        return False
    return True


def label(args):
    repository, number = identity(args.pr)
    apply_continuum_label(repository, number)


def assert_posted(args, claim_id=None, released=False, released_sha=None):
    _, _, pr, state = state_for(args.pr)
    c.require(not state.conflict, "a competing record appeared; stop all writes")
    if released:
        c.require(not state.active and pr["head"]["sha"] == released_sha,
                  "release did not settle at the current PR head; stop and reconcile")
    else:
        c.require(set(state.active) == {str(claim_id)}, "claim did not become the sole active lease; stop all writes")


def claim(args):
    repository, number, pr, state = state_for(args.pr)
    c.require(pr["state"] == "open" and pr["draft"], "claim requires an open Draft PR")
    c.require(not state.conflict and not state.active, "another or conflicting lease is active")
    comment = post(repository, number, c.render("claim"))
    c.require(isinstance(comment, dict) and comment.get("id") is not None,
              "GitHub claim response did not include its comment ID")
    claim_id = str(comment["id"])
    assert_posted(args, claim_id=claim_id)
    print(claim_id)


def release(args):
    repository, number, pr, state = state_for(args.pr)
    c.require(pr["state"] == "open" and pr["draft"] and not state.conflict and
              set(state.active) == {args.claim},
              "release requires this claim's sole active lease on an open Draft PR")
    sha = command("git", "rev-parse", "HEAD").strip()
    c.require(sha == pr["head"]["sha"], "local HEAD differs from shared PR HEAD; push and reread before release")
    c.require(not command("git", "status", "--porcelain"), "release requires a clean worktree")
    post(repository, number, c.render("release", claim_id=args.claim, sha=sha))
    assert_posted(args, claim_id=args.claim, released=True, released_sha=sha)
    print(sha)


def recover(args):
    repository, number, pr, state = state_for(args.pr)
    c.require(pr["state"] == "open", "recovery cannot resume a closed PR")
    c.require(state.active or state.conflict, "recovery is only for an active or conflicting lease history")
    user = command("gh", "api", "user", "--jq", ".login").strip()
    permission = api(f"repos/{repository}/collaborators/{quote(user, safe='')}/permission")
    c.require(permission.get("role_name") == "admin", "recovery requires repository-owner permission")
    post(repository, number, c.render_recovery(args.confirmation))
    _, _, _, updated = state_for(args.pr)
    c.require(not updated.conflict and not updated.active, "recovery did not clear exactly the accepted leases")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, function in (("status", status), ("claim", claim), ("release", release)):
        item = sub.add_parser(name)
        item.add_argument("--pr", required=True)
        if name == "release":
            item.add_argument("--claim", required=True)
        item.set_defaults(function=function)
    item = sub.add_parser("label", help="best-effort apply an existing continuum label")
    item.add_argument("--pr", required=True)
    item.set_defaults(function=label)
    item = sub.add_parser("recover")
    item.add_argument("--pr", required=True)
    item.add_argument("--confirmation", required=True)
    item.set_defaults(function=recover)
    args = parser.parse_args()
    args.function(args)


if __name__ == "__main__":
    main()
