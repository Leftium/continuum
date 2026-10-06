#!/usr/bin/env python3
"""Publish a stable release only for a validated protocol version bump on main."""

import os
from pathlib import Path
import re
import subprocess
import sys


def version(text):
    match = re.match(r"---\ncontinuum: ([0-9]+\.[0-9]+\.[0-9]+)\n", text)
    if not match:
        raise SystemExit("invalid protocol front matter version")
    return tuple(map(int, match.group(1).split(".")))


def run(*args, check=True):
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode:
        raise SystemExit(result.stderr.strip() or "command failed: " + " ".join(args))
    return result


def main():
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise SystemExit("release publishing is main-only")
    sha = os.environ["GITHUB_SHA"]
    current = Path("protocol/CONTINUUM.md").read_text()
    old = run("git", "show", os.environ["GITHUB_EVENT_BEFORE"] + ":protocol/CONTINUUM.md", check=False)
    if old.returncode:
        print("No prior protocol file; no release")
        return
    previous, proposed = version(old.stdout), version(current)
    if proposed == previous:
        print("Protocol version unchanged; no release")
        return
    if proposed <= previous:
        raise SystemExit("protocol version must increase")
    tag = "v" + ".".join(map(str, proposed))
    core = Path("scripts/continuum_core.py").read_text()
    if f'VERSION = "{".".join(map(str, proposed))}"' not in core:
        raise SystemExit("protocol and client version declarations disagree")
    run("bash", "scripts/check-continuum.sh")
    existing_tag = run("git", "ls-remote", "--tags", "origin", "refs/tags/" + tag,
                       "refs/tags/" + tag + "^{}", check=False).stdout.splitlines()
    if existing_tag:
        rows = [line.split()[0] for line in existing_tag]
        if sha not in rows:
            raise SystemExit("existing immutable tag points elsewhere")
    release = run("gh", "release", "view", tag, "--json", "tagName,isDraft,isPrerelease,targetCommitish", check=False)
    if release.returncode == 0:
        import json
        data = json.loads(release.stdout)
        if data["isDraft"] or data["isPrerelease"] or data["tagName"] != tag:
            raise SystemExit("existing release is draft, prerelease, or mismatched")
        resolved = run("gh", "api", "repos/Leftium/continuum/git/ref/tags/" + tag, "--jq", ".object.sha").stdout.strip()
        if resolved != sha:
            raise SystemExit("existing release tag does not point to this merge SHA")
        print("Expected stable release already exists")
        return
    if not existing_tag:
        run("git", "tag", "-a", tag, sha, "-m", tag)
        run("git", "push", "origin", "refs/tags/" + tag)
    run("gh", "release", "create", tag, "--target", sha, "--title", tag, "--generate-notes")


if __name__ == "__main__":
    main()
