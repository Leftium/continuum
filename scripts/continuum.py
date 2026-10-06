#!/usr/bin/env python3
"""Dependency-free reference client. Remote writes require explicit subcommands."""

import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import quote

import continuum_core as c

TRUSTED_SOURCE = "Leftium/continuum"


def command(*args, check=True):
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode:
        raise c.Invalid("command failed (state preserved): " + " ".join(args[:3]) + "\n" + result.stderr.strip())
    return result


def git(*args):
    return command("git", *args).stdout.strip()


def gh(*args):
    return command("gh", *args).stdout


def api(path, *args):
    return json.loads(gh("api", path, *args))


def pr_identity(url):
    match = re.fullmatch(r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/pull/([1-9][0-9]*)", url)
    c.require(match is not None, "use a full github.com PR URL")
    return match[1], int(match[2])


def read_pr(url):
    repository, number = pr_identity(url)
    pr = api(f"repos/{repository}/pulls/{number}")
    c.require(pr["head"]["repo"] and pr["base"]["repo"], "deleted head/base repository")
    base_sha = api(f"repos/{pr['base']['repo']['full_name']}/git/ref/heads/{quote(pr['base']['ref'], safe='')}")["object"]["sha"]
    pr["checked_base_sha"] = base_sha
    return pr


def live_tuple(pr, contract, reconcile=False):
    head = {"host": "github.com", "repository": pr["head"]["repo"]["full_name"], "ref": pr["head"]["ref"]}
    target = {"host": "github.com", "repository": pr["base"]["repo"]["full_name"], "ref": pr["base"]["ref"]}
    if not reconcile:
        c.require(head == contract["head"] and target == {k: contract["target"][k] for k in target}, "unexpected target/head identity; suspend/cancel and obtain human reconciliation")
    return c.readiness_tuple({**contract, "head": head, "target": {**target, "sha": pr["checked_base_sha"]}}, pr["head"]["sha"], pr["checked_base_sha"])


def fetch_protocol(source, trusted=TRUSTED_SOURCE):
    c.validate_source(source)
    c.require(source["repository"].lower() == trusted.lower(), "untrusted remote protocol repository; explicit trust decision required")
    content = gh("api", f"repos/{source['repository']}/contents/{source['path']}?ref={source['commit']}", "-H", "Accept: application/vnd.github.raw+json")
    c.require(content.startswith(f"---\ncontinuum: {c.VERSION}\nartifact: protocol/CONTINUUM.md\n"), "pinned artifact is not the supported canonical protocol")
    return content  # Text only. Never execute downloaded code or replace with main.


def comments(url, pr):
    repository, number = pr_identity(url)
    pages = api(f"repos/{repository}/issues/{number}/comments?per_page=100", "--paginate", "--slurp")
    events = []
    for item in (item for page in pages for item in page):
        text = item["body"] or ""
        if "<!-- continuum:event" not in text:
            continue
        event = c.section(text, c.EVENT_START, c.EVENT_END)[3]
        c.validate_event(event)
        c.require(item["user"]["login"] == event["actor"], "event actor does not match authenticated comment author")
        c.require(item["user"]["login"] == pr["user"]["login"] or item["author_association"] in ("OWNER", "MEMBER", "COLLABORATOR"), "event from untrusted commenter; human recovery required")
        events.append(event)
    return events


def snapshot(url, trusted=TRUSTED_SOURCE, allow_invalid=False):
    pr = read_pr(url)
    contract = c.section(pr["body"] or "")[3]
    if not allow_invalid:
        c.validate_contract(contract)
    fetch_protocol(contract["source"], trusted)
    events = comments(url, pr)
    state = c.replay(events)
    if not allow_invalid:
        validate_current(contract, state, events)
    return pr, contract, events, state


def validate_current(contract, state, events):
    c.validate_contract(contract)
    c.require(contract["revision"] >= state.last_revision, "contract revision rolled back behind durable history; repair required")
    accepted = [e["tuple"] for e in events if e["tuple"] and e["tuple"]["revision"] == contract["revision"]]
    c.require(not accepted or accepted[-1]["digest"] == contract["digest"], "same revision has changed digest; reconcile/repair required")


def actor():
    return api("user")["login"]


def make_event(state, run, action, kind, value, details, owner=None):
    return {"schema": "continuum-event/0.4", "id": c.new_id(), "prev": sorted(state.frontier), "actor": actor(), "run": run,
            "action": action, "kind": kind, "subject": owner, "tuple": value, "details": details}


def post_event(url, event, events):
    # Replay locally first; verify the append and full frontier after writing.
    expected = c.replay(events + [event])
    c.require(not expected.conflict, "competing event frontier; explicit human recovery required")
    repository, number = pr_identity(url)
    api(f"repos/{repository}/issues/{number}/comments", "--method", "POST", "-f", "body=" + c.event_text(event))
    pr = read_pr(url)
    actual_events = comments(url, pr)
    actual = c.replay(actual_events)
    c.require(not actual.conflict and actual.frontier == {event["id"]}, "concurrent claim/event; stop all writes and alert developer")
    return actual_events, actual


def assert_owner(state, run, kinds=("write",), mode="active"):
    c.require(not state.conflict and state.active and state.active["run"] == run and state.active["actor"] == actor()
              and state.active["kind"] in kinds and (mode is None or state.mode == mode), "exclusive matching run claim required")


def clean_worktree():
    c.require(not git("status", "--porcelain"), "preserve staged/unstaged/untracked work; use a clean workspace")


def working_agents():
    path = Path("AGENTS.md")
    c.require(not path.is_symlink() and (not path.exists() or path.is_file()), "AGENTS.md must be a regular file")
    return path.read_bytes() if path.exists() else None


def remote_repository(url):
    patterns = (r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?",
                r"git@github\.com:([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?",
                r"ssh://git@github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?")
    for pattern in patterns:
        match = re.fullmatch(pattern, url)
        if match:
            return match[1]
    raise c.Invalid("push URL must identify the exact github.com head repository without credentials")


def push_url(remote, head):
    c.require(re.fullmatch(r"[A-Za-z0-9_.-]+", remote) and not remote.startswith("-"), "invalid remote name")
    urls = git("remote", "get-url", "--push", "--all", remote).splitlines()
    c.require(len(urls) == 1, "multiple push destinations are unsafe")
    resolved = git("ls-remote", "--get-url", urls[0])
    c.require(all(remote_repository(u).lower() == head["repository"].lower() for u in (urls[0], resolved)), "push destination differs from authorized head repository")
    c.require(command("git", "config", "--bool", "--get", f"remote.{remote}.mirror", check=False).stdout.strip() != "true", "mirror remote is unsafe")
    return resolved


def remote_sha(url, ref):
    value = git("ls-remote", "--heads", url, "refs/heads/" + ref)
    c.require(not value or len(value.splitlines()) == 1, "ambiguous remote branch")
    return value.split()[0] if value else None


def push(remote, head):
    push_url(remote, head)
    git("push", "--no-follow-tags", "--recurse-submodules=no", remote, "HEAD:refs/heads/" + head["ref"])


def branch_context(contract, expected):
    c.require(git("branch", "--show-current") == contract["head"]["ref"] and git("rev-parse", "HEAD") == expected, "local branch/HEAD differs from authorized PR head")
    clean_worktree()


def blob(commit, path="AGENTS.md"):
    entry = git("ls-tree", commit, "--", path)
    if not entry:
        return None
    c.require(entry.split()[0] in ("100644", "100755"), "AGENTS.md must be a regular tracked file")
    return subprocess.check_output(["git", "show", commit + ":" + path])


def remote_agents(repository, sha):
    tree = api(f"repos/{repository}/git/trees/{sha}")["tree"]
    matches = [entry for entry in tree if entry["path"] == "AGENTS.md"]
    if not matches:
        return None
    c.require(matches[0]["mode"] in ("100644", "100755"), "base AGENTS.md is not a regular file")
    obj = api(f"repos/{repository}/git/blobs/{matches[0]['sha']}")
    c.require(obj["encoding"] == "base64", "unsupported Git blob encoding")
    return base64.b64decode(obj["content"], validate=False)


def origin_provenance(contract):
    boot = contract["bootstrap"]
    initial = blob(boot["commit"])
    c.require(initial is not None, "bootstrap pointer commit unavailable")
    left, right, raw, meta = c.read_pointer(initial)
    c.require(c.sha256(raw) == boot["pointer_digest"] and meta["id"] == boot["id"] and meta["run"] == boot["run"]
              and meta["agents_created"] == boot["agents_created"], "bootstrap pointer provenance mismatch")
    parent = git("rev-parse", boot["commit"] + "^")
    c.require(parent == meta["target"]["sha"] and git("diff", "--name-only", parent, boot["commit"]) == "AGENTS.md", "bootstrap must be pointer-only on the accepted base")
    before = blob(parent)
    c.require((before is None) == boot["agents_created"] and initial[:left] + initial[right:] == (before or b""), "bootstrap rewrote project-owned instructions")
    return True


def assert_checks(url):
    info = json.loads(gh("pr", "view", url, "--json", "reviewDecision,statusCheckRollup,mergeable"))
    c.require(info["reviewDecision"] != "CHANGES_REQUESTED" and info["mergeable"] == "MERGEABLE", "review changes, conflict, or unknown mergeability blocks cleanup/Ready")
    for check in info["statusCheckRollup"] or []:
        if check.get("__typename") == "CheckRun":
            c.require(check.get("status") == "COMPLETED" and check.get("conclusion") in ("SUCCESS", "NEUTRAL", "SKIPPED"), "pending/failed check blocks cleanup/Ready")
        else:
            c.require(check.get("state") == "SUCCESS", "pending/failed status blocks cleanup/Ready")


def write_body(url, expected_body, new_body):
    # GitHub has no compare-and-swap for PR bodies. Check before and after.
    c.require(read_pr(url)["body"] == expected_body, "PR body changed before replacement")
    repository, number = pr_identity(url)
    api(f"repos/{repository}/pulls/{number}", "--method", "PATCH", "-f", "body=" + new_body)
    actual = read_pr(url)["body"]
    c.require(actual == new_body, "body readback changed; stop and reconcile")
    c.read_contract(actual)


def status(args):
    pr, contract, _, state = snapshot(args.pr, args.trusted_source)
    current = live_tuple(pr, contract)
    print(json.dumps({"pr": args.pr, "open": pr["state"] == "open", "draft": pr["draft"], "tuple": current,
                      "claim": state.active, "mode": state.mode, "conflict": state.conflict,
                      "frontier": sorted(state.frontier), "evidence": state.evidence, "receipts": state.receipts}, indent=2))


def record(args):
    pr, contract, events, state = snapshot(args.pr, args.trusted_source, allow_invalid=args.action in ("suspend", "resume", "recover", "cleanup_cancel"))
    details = c.loads(Path(args.details).read_text()) if args.details else {}
    action = args.action
    if action == "recover":
        c.require(details.get("human_confirmation"), "explicit human confirmation that all owners stopped is required")
        value, kind, owner = None, "recovery", None
    elif action in ("suspend", "cleanup_cancel"):
        assert_owner(state, args.run, ("write", "repair", "cleanup"), None)
        value, kind, owner = None, state.active["kind"], state.active["id"]
    else:
        c.require(pr["state"] == "open", "no writes/progression on closed PR")
        try:
            validate_current(contract, state, events)
            invalid = False
        except c.Invalid:
            invalid = True
        if action == "resume" and (invalid or state.repair):
            assert_owner(state, args.run, ("write", "repair"), "suspended")
            raw_digest = c.sha256(c.section(pr["body"])[2].encode("utf-8"))
            expected = state.repair["snapshot"] if state.repair else state.active["tuple"]
            c.require(raw_digest == (state.repair["raw_digest"] if state.repair else details.get("raw_digest")), "invalid-metadata resume requires accepted unchanged raw snapshot")
            effective = {**contract, "revision": expected["revision"], "digest": expected["digest"]}
            c.require(live_tuple(pr, effective) == expected, "repair resume head/target changed; explicit recovery required")
            value = None
        else:
            validate_current(contract, state, events)
            value = live_tuple(pr, contract, reconcile=action == "resume" and bool(details.get("acceptance")))
        kind, owner = "evidence", None
        if action == "claim":
            c.require(pr["draft"] and not state.conflict and state.active is None and details.get("acceptance"), "write acquisition requires unclaimed Draft and accepted policy/blockers")
            branch_context(contract, value["head_sha"])
            kind = "write"
        elif action in ("review", "revalidate"):
            c.require(not pr["draft"] and state.active is None, "independent review/base revalidation requires unleased Ready")
            assert_checks(args.pr)
            last_writers = [e["run"] for e in events if e["action"] == "claim" and e["kind"] == "write"]
            c.require(args.run not in last_writers, "review run must be independent of implementation")
        else:
            assert_owner(state, args.run, ("write", "repair") if action == "resume" else ("write",), mode=None if action == "resume" else "active")
            c.require(pr["draft"] or (action == "resume" and state.active["kind"] == "repair"), "implementation progression requires Draft; suspend if state changed")
            if action == "resume":
                c.require(state.mode == "suspended" and details.get("acceptance"), "resume needs explicit approval/reconciliation")
            owner = state.active["id"]
            if action not in ("checkpoint", "resume"):
                c.require(value == state.active["tuple"], "HEAD/contract/base changed; reconcile and checkpoint before progression")
            if action in ("verify", "ready", "release", "checkpoint"):
                branch_context(contract, value["head_sha"])
            if action == "checkpoint":
                c.require(details.get("acceptance"), "checkpoint needs verification/reconciliation handoff")
            if action == "ready":
                assert_checks(args.pr)
            if action not in ("verify", "ready"):
                kind = state.active["kind"]
    event = make_event(state, args.run, action, kind, value, details, owner)
    post_event(args.pr, event, events)
    if value is not None:
        latest = read_pr(args.pr)
        c.require(live_tuple(latest, c.read_contract(latest["body"]), reconcile=action == "resume") == value, "live tuple changed after event; claim retained, stop and reconcile")
    print(event["id"])


def ready(args):
    args.action = "ready"
    record(args)
    args.action = "release"
    record(args)
    pr, contract, _, state = snapshot(args.pr, args.trusted_source)
    c.require(state.active is None and state.evidence.get("ready") == live_tuple(pr, contract) and pr["state"] == "open", "Ready tuple changed after release")
    gh("pr", "ready", args.pr)


def edit(args):
    pr, contract, events, state = snapshot(args.pr, args.trusted_source)
    assert_owner(state, args.run)
    c.require(pr["state"] == "open" and pr["draft"], "body editing requires open Draft")
    replacement = c.loads(Path(args.input).read_text())
    replacement = c.seal(replacement, contract["revision"] + 1)
    material = any(replacement[k] != contract[k] for k in ("source", "target", "head", "goal", "scope", "acceptance"))
    c.require(not material or args.accept_change, "source/target/scope change requires explicit human/project authority reference")
    fetch_protocol(replacement["source"], args.trusted_source)
    current = live_tuple(pr, contract, reconcile=bool(args.accept_change))
    c.require((contract["revision"], contract["digest"]) == (state.active["tuple"]["revision"], state.active["tuple"]["digest"]), "external contract change; suspend/reconcile before ordinary editing")
    c.require(current["head_sha"] == state.active["tuple"]["head_sha"], "unexpected HEAD change during body edit")
    live_tuple(pr, replacement)
    body = c.replace_contract(pr["body"], replacement, (contract["revision"], contract["digest"]))
    before = snapshot(args.pr, args.trusted_source)
    c.require(before[3].frontier == state.frontier and before[0]["head"]["sha"] == pr["head"]["sha"]
              and before[0]["base"]["ref"] == pr["base"]["ref"] and before[0]["checked_base_sha"] == pr["checked_base_sha"], "state changed before contract edit")
    write_body(args.pr, pr["body"], body)
    value = live_tuple(read_pr(args.pr), replacement)
    event = make_event(state, args.run, "checkpoint", "write", value,
                       {"acceptance": args.accept_change or "authorized plan update", "contract_predecessor": contract["digest"]}, state.active["id"])
    post_event(args.pr, event, events)


def repair(args):
    outside_path(args.output)
    pr, candidate, events, state = snapshot(args.pr, args.trusted_source, allow_invalid=True)
    c.require(pr["state"] == "open" and not state.conflict, "repair requires open PR and uncontested ownership")
    if args.complete:
        assert_owner(state, args.run, ("write", "repair"), "repair")
        repaired = c.read_contract(pr["body"])
        c.require(repaired == c.read_contract(Path(args.output).read_bytes().decode("utf-8")), "human replacement differs from exact prepared contract")
        origin = next(e for e in reversed(events) if e["action"] in ("claim", "repair_enter") and e["details"].get("raw_digest"))
        details = origin["details"]
        c.require(details["raw_digest"] == args.accepted_raw and details["acceptance"] == args.acceptance
                  and details["last_revision"] == args.last_revision, "completion does not match accepted repair claim")
        value = live_tuple(pr, repaired)
        c.require(value == details["snapshot"], "repair HEAD/target/replacement changed")
        complete_repair(args, events, state, value, details)
        return
    raw = c.section(pr["body"])[2]
    try:
        validate_current(candidate, state, events)
    except c.Invalid:
        pass
    else:
        raise c.Invalid("metadata already validates; use --complete for an applied repair handoff")
    c.require(c.sha256(raw.encode()) == args.accepted_raw and args.acceptance, "repair needs explicit acceptance of exact raw section")
    c.require(args.last_revision >= state.last_revision, "predecessor is older than durable accepted revision")
    body, repaired = c.repair_contract(pr["body"], args.accepted_raw, args.last_revision)
    value = live_tuple(pr, repaired)
    details = {"raw_digest": args.accepted_raw, "last_revision": args.last_revision, "acceptance": args.acceptance, "snapshot": value}
    if state.active is None:
        event = make_event(state, args.run, "claim", "repair", None, details)
        events, state = post_event(args.pr, event, events)
    else:
        assert_owner(state, args.run, ("write", "repair"), None)
        if state.mode != "repair":
            c.require(state.mode == "active", "suspended run must resume before repair")
            event = make_event(state, args.run, "repair_enter", "write", None, details, state.active["id"])
            events, state = post_event(args.pr, event, events)
        else:
            origin = next(e for e in reversed(events) if e["action"] in ("claim", "repair_enter") and e["details"].get("raw_digest"))
            c.require(origin["details"] == details, "repair snapshot changed; explicit recovery/new acceptance required")
    Path(args.output).write_bytes(body.encode("utf-8"))
    if not args.apply:
        print("Exact replacement saved; repair claim retained. Authorized human must apply this complete body, then rerun with --complete to validate/release.")
        return
    latest, _, latest_events, latest_state = snapshot(args.pr, args.trusted_source, allow_invalid=True)
    c.require(latest_state.frontier == state.frontier and latest["body"] == pr["body"] and live_tuple(latest, repaired) == value, "repair snapshot/ownership changed")
    write_body(args.pr, pr["body"], body)
    complete_repair(args, events, state, value, details)


def complete_repair(args, events, state, value, details):
    event = make_event(state, args.run, "repair_complete", state.active["kind"], value, details, state.active["id"])
    events, state = post_event(args.pr, event, events)
    if state.active["kind"] == "repair":
        event = make_event(state, args.run, "release", "repair", value, {"acceptance": "metadata validated"}, state.active["id"])
        post_event(args.pr, event, events)


def pointer_sync(args):
    pr, contract, _, state = snapshot(args.pr, args.trusted_source)
    assert_owner(state, args.run)
    c.require(pr["state"] == "open" and pr["draft"], "pointer restoration needs open Draft lease")
    current = live_tuple(pr, contract)
    c.require(current == state.active["tuple"], "reconcile/checkpoint changed tuple before pointer write")
    branch_context(contract, current["head_sha"])
    origin_provenance(contract)
    path = Path("AGENTS.md")
    original = working_agents()
    c.require(original == blob(current["head_sha"]), "untracked/filtered AGENTS.md content; preserve it and hand off")
    if original is not None and b"<!-- continuum:pointer" in original:
        left, right, _, meta = c.read_pointer(original)
        c.require(meta["id"] == contract["bootstrap"]["id"] and meta["run"] == contract["bootstrap"]["run"]
                  and meta["agents_created"] == contract["bootstrap"]["agents_created"], "foreign pointer cannot be replaced")
        result = original[:left] + c.render_pointer(c.pointer_data(contract)) + original[right:]
    else:
        c.no_op_receipt(state, contract, current, original, lambda commit: is_ancestor(commit), lambda commit: absence_history(commit))
        result = c.append_pointer(original, c.pointer_data(contract))
    path.write_bytes(result)
    print("Owned pointer updated. Commit/push this change under the held write lease.")


def is_ancestor(commit):
    return command("git", "merge-base", "--is-ancestor", commit, "HEAD", check=False).returncode == 0


def absence_history(commit):
    # Inspect every relevant tree, so restore-then-remove is not mistaken for absence.
    for sha in git("rev-list", commit + "..HEAD", "--", "AGENTS.md").splitlines():
        if b"<!-- continuum:pointer" in (blob(sha) or b""):
            return False
    return b"<!-- continuum:pointer" not in (blob(commit) or b"")


def cleanup(args):
    pr, contract, events, state = snapshot(args.pr, args.trusted_source)
    current = live_tuple(pr, contract)
    destination = push_url(args.remote, contract["head"])
    clean_worktree()
    c.require(git("branch", "--show-current") == contract["head"]["ref"], "cleanup must use exact head branch")
    c.require(working_agents() == blob(git("rev-parse", "HEAD")), "untracked/filtered AGENTS.md content; preserve it and hand off")
    origin_provenance(contract)
    if state.active is None:
        c.cleanup_gate(state, current, pr["state"] == "open", pr["draft"])
        branch_context(contract, current["head_sha"])
        assert_checks(args.pr)
        claim = make_event(state, args.run, "claim", "cleanup", current, {"acceptance": "current independent review and checks"})
        events, state = post_event(args.pr, claim, events)
    assert_owner(state, args.run, ("cleanup",))
    claimed = state.active["tuple"]
    c.require(pr["state"] == "open" and not pr["draft"], "cleanup stopped: PR no longer open Ready")
    c.require({k: v for k, v in current.items() if k != "head_sha"} == {k: v for k, v in claimed.items() if k != "head_sha"}, "cleanup tuple changed; cancel/recover claim before reconciliation")
    base_owned = remote_agents(contract["target"]["repository"], current["base_sha"]) is not None
    local_head = git("rev-parse", "HEAD")
    if local_head == claimed["head_sha"]:
        c.require(current == claimed and remote_sha(destination, contract["head"]["ref"]) == local_head, "unexpected remote HEAD during cleanup")
        agents = blob(local_head)
        if agents is None or b"<!-- continuum:pointer" not in agents:
            receipt = c.no_op_receipt(state, contract, current, agents, is_ancestor, absence_history)
            finish_cleanup(args, events, state, contract, current, receipt)
            return
        remainder, pointer_digest = c.remove_pointer(agents, contract, base_owned, True)
        assert_cleanup_snapshot(args, state, contract, claimed, (claimed["head_sha"],))
        path = Path("AGENTS.md")
        c.require(not path.is_symlink() and path.read_bytes() == agents, "working AGENTS.md changed")
        if remainder is None:
            git("rm", "--", "AGENTS.md")
        else:
            path.write_bytes(remainder)
            git("add", "--", "AGENTS.md")
        c.require(git("diff", "--cached", "--name-only") == "AGENTS.md", "cleanup index contains unrelated work")
        git("commit", "-m", "chore: remove temporary Continuum pointer")
        local_head = git("rev-parse", "HEAD")
    else:
        # A failed/ambiguous push may leave the one verified cleanup commit locally.
        c.require(git("rev-list", "--parents", "-n", "1", local_head).split() == [local_head, claimed["head_sha"]]
                  and git("diff", "--name-only", claimed["head_sha"], local_head) == "AGENTS.md", "unexpected local HEAD; never overwrite advancement")
        remainder, pointer_digest = c.remove_pointer(blob(claimed["head_sha"]), contract, base_owned, True)
        c.require(blob(local_head) == remainder, "local cleanup commit contains unauthorized AGENTS.md changes")
    clean_worktree()
    c.require(git("rev-list", "--parents", "-n", "1", local_head).split() == [local_head, claimed["head_sha"]]
              and git("diff", "--name-only", claimed["head_sha"], local_head) == "AGENTS.md"
              and blob(local_head) == remainder, "cleanup commit/hooks changed more than the owned pointer")
    receipt = {"bootstrap_id": contract["bootstrap"]["id"], "pointer_digest": pointer_digest, "removal_commit": local_head,
               "readiness": claimed, "prior_receipt": None, "no_op": False}
    assert_cleanup_snapshot(args, state, contract, claimed, (claimed["head_sha"], local_head))
    remote = remote_sha(destination, contract["head"]["ref"])
    if remote == claimed["head_sha"]:
        push(args.remote, contract["head"])
    else:
        c.require(remote == local_head, "remote advanced; cleanup claim retained for recovery")
    # GitHub can lag Git transport. A bounded retry never changes the commit/ref.
    for attempt in range(5):
        latest = read_pr(args.pr)
        if latest["head"]["sha"] == local_head:
            break
        time.sleep(1)
    c.require(latest["head"]["sha"] == local_head, "GitHub still lags cleanup push; rerun same run/claim")
    finish_cleanup(args, events, state, contract, c.readiness_tuple(contract, local_head, claimed["base_sha"]), receipt)


def assert_cleanup_snapshot(args, state, contract, claimed, allowed_heads):
    pr, fresh, _, fresh_state = snapshot(args.pr, args.trusted_source)
    value = live_tuple(pr, fresh)
    c.require(pr["state"] == "open" and not pr["draft"] and fresh_state.frontier == state.frontier and fresh == contract
              and value["head_sha"] in allowed_heads and {k: v for k, v in value.items() if k != "head_sha"}
              == {k: v for k, v in claimed.items() if k != "head_sha"}, "cleanup ownership/readiness changed; retain claim and stop")


def finish_cleanup(args, events, state, contract, current, receipt):
    assert_cleanup_snapshot(args, state, contract, receipt["readiness"], (current["head_sha"],))
    event = make_event(state, args.run, "cleanup_complete", "cleanup", current, receipt, state.active["id"])
    post_event(args.pr, event, events)
    print("Cleanup complete; claim released. Merge remains a separate human/project gate.")


def parent_guard(repository, ref):
    # Ref-associated PRs include upstream PRs made from forks and closed-unmerged PRs.
    owner, name = repository.split("/")
    query = """query($owner:String!,$name:String!,$ref:String!,$cursor:String) {
      repository(owner:$owner,name:$name) { ref(qualifiedName:$ref) {
        associatedPullRequests(first:100,after:$cursor,states:[OPEN,CLOSED,MERGED]) {
          pageInfo {hasNextPage endCursor} nodes {url body merged headRefName headRepository {nameWithOwner}}
        } } } }"""
    cursor = None
    while True:
        fields = ["-f", "query=" + query, "-f", "owner=" + owner, "-f", "name=" + name, "-f", "ref=refs/heads/" + ref]
        if cursor:
            fields += ["-f", "cursor=" + cursor]
        result = api("graphql", *fields)
        c.require(not result.get("errors") and result.get("data", {}).get("repository", {}).get("ref"), "cannot establish parent/stacking status")
        connection = result["data"]["repository"]["ref"]["associatedPullRequests"]
        for pr in connection["nodes"]:
            if pr["headRepository"] and pr["headRepository"]["nameWithOwner"].lower() == repository.lower() and pr["headRefName"] == ref:
                c.require(pr["merged"] or "<!-- continuum:contract" not in (pr["body"] or ""), "unsupported unmerged Continuum parent: " + pr["url"])
        if not connection["pageInfo"]["hasNextPage"]:
            return
        cursor = connection["pageInfo"]["endCursor"]


def outside_path(path):
    path = Path(path).resolve()
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    c.require(root not in path.parents and path != root, "journal/repair handoff must be outside target worktree")
    return path


def journal_write(path, data, initial=False):
    path = outside_path(path)
    if initial:
        with path.open("x", encoding="utf-8") as output:
            os.chmod(path, 0o600)
            json.dump(data, output, indent=2)
            output.flush()
            os.fsync(output.fileno())
    else:
        temporary = path.with_name(path.name + ".tmp")
        with temporary.open("x", encoding="utf-8") as output:
            os.chmod(temporary, 0o600)
            json.dump(data, output, indent=2)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)


def bootstrap(args):
    if args.resume:
        journal = c.loads(Path(args.journal).read_text())
        c.require(args.run == journal["run"] or args.recovery_authority, "terminated bootstrap needs explicit human recovery")
        c.require(journal.get("commit"), "bootstrap interrupted before recorded commit; preserve branch and use human recovery")
        c.require(args.remote == journal["remote"], "resume must use recorded remote")
        finish_bootstrap(args, journal)
        return
    c.require(args.start_now and args.accepted_policy and args.repo and args.head_repo and args.base and args.plan and args.title, "bootstrap requires implementation-now adoption, accepted base policy, repo/head/base, title and complete plan")
    clean_worktree()
    run, bootstrap_id = args.run or c.new_id(), c.new_id()
    c.require(c.REPOSITORY.fullmatch(args.repo) and c.REPOSITORY.fullmatch(args.head_repo), "invalid base/head repository")
    base_repository = api(f"repos/{args.repo}")
    head_repository = api(f"repos/{args.head_repo}")
    args.repo, args.head_repo = base_repository["full_name"], head_repository["full_name"]
    head = {"host": "github.com", "repository": args.head_repo, "ref": args.branch or "continuum/" + bootstrap_id}
    c._identity(head)
    destination = push_url(args.remote, head)
    c.require(remote_sha(destination, head["ref"]) is None and command("git", "show-ref", "--verify", "refs/heads/" + head["ref"], check=False).returncode != 0, "head branch already exists; never adopt/overwrite")
    base_sha = api(f"repos/{args.repo}/git/ref/heads/{quote(args.base, safe='')}")["object"]["sha"]
    target = {"host": "github.com", "repository": args.repo, "ref": args.base, "sha": base_sha}
    c._identity(target, True)
    parent_guard(args.repo, args.base)
    base_agents = remote_agents(args.repo, base_sha)
    c.require(b"<!-- continuum:pointer" not in (base_agents or b""), "selected base has stale/parent pointer")
    c.require(b"<!-- leftium:continuum:start -->" not in (base_agents or b""), "selected base is still installed 0.3; follow migration gate/drain before 0.4 adoption")
    c.require(head_repository.get("permissions", {}).get("push"), "cannot push to authorized head repository")
    login = actor()
    # Creation makes this authenticated account the PR author, who can edit its
    # own body. Do not require upstream push permission or personal fork ownership.
    if args.source_commit:
        c.require(args.development_source, "explicit source commit requires --development-source; stable discovery is the default")
        source_commit = args.source_commit
    else:
        release = api(f"repos/{args.trusted_source}/releases/latest")
        c.require(not release["draft"] and not release["prerelease"] and release["tag_name"] in (c.VERSION, "v" + c.VERSION), "no supported stable 0.4 release; do not fall back to 0.3/main")
        source_commit = api(f"repos/{args.trusted_source}/commits/{quote(release['tag_name'], safe='')}")["sha"]
    source = {"host": "github.com", "repository": args.trusted_source, "version": c.VERSION, "commit": source_commit, "path": "protocol/CONTINUUM.md"}
    fetch_protocol(source, args.trusted_source)
    plan = c.loads(Path(args.plan).read_text())
    c.require(set(plan) == {"goal", "scope", "acceptance", "plan", "verification", "changes", "context"}, "plan JSON must contain the seven documented planning fields")
    contract = {**plan, "schema": "continuum/0.4", "revision": 1, "digest": "", "source": source, "target": target, "head": head,
                "bootstrap": {"id": bootstrap_id, "run": run, "commit": "0" * 40, "pointer_digest": "sha256:" + "0" * 64, "agents_created": base_agents is None}}
    pointer = c.render_pointer(c.pointer_data(contract))
    contract["bootstrap"]["pointer_digest"] = c.sha256(pointer)
    c.seal(contract)
    journal = {"run": run, "actor": login, "remote": args.remote, "title": args.title, "accepted_policy": args.accepted_policy, "contract": contract, "commit": None}
    journal_write(args.journal, journal, initial=True)
    git("fetch", "--no-tags", "https://github.com/" + args.repo + ".git", "refs/heads/" + args.base)
    c.require(git("rev-parse", "FETCH_HEAD") == base_sha, "base advanced before bootstrap; preserve journal and start only after reconciliation")
    git("switch", "--no-overwrite-ignore", "-c", head["ref"], base_sha)
    c.require(blob(base_sha) == base_agents, "base policy retrieval mismatch")
    c.require(working_agents() == base_agents, "ignored/untracked or filtered AGENTS.md; preserve it and recover bootstrap explicitly")
    Path("AGENTS.md").write_bytes(c.append_pointer(base_agents, c.pointer_data(contract)))
    git("add", "--", "AGENTS.md")
    git("commit", "-m", "chore: bootstrap Continuum PR discovery")
    journal["commit"] = git("rev-parse", "HEAD")
    contract["bootstrap"]["commit"] = journal["commit"]
    journal["contract"] = c.seal(contract)
    journal_write(args.journal, journal)
    origin_provenance(journal["contract"])
    push(args.remote, head)
    finish_bootstrap(args, journal)


def finish_bootstrap(args, journal):
    contract = c.validate_contract(journal["contract"])
    fetch_protocol(contract["source"], args.trusted_source)
    destination = push_url(args.remote, contract["head"])
    branch_context(contract, journal["commit"])
    origin_provenance(contract)
    actual = remote_sha(destination, contract["head"]["ref"])
    if actual is None:
        push(args.remote, contract["head"])
        actual = remote_sha(destination, contract["head"]["ref"])
    c.require(actual == journal["commit"], "bootstrap remote advanced; do not overwrite or create duplicate branch")
    repository = contract["target"]["repository"]
    owner = contract["head"]["repository"].split("/")[0]
    query = quote(owner + ":" + contract["head"]["ref"], safe="")
    pages = api(f"repos/{repository}/pulls?state=all&head={query}&per_page=100", "--paginate", "--slurp")
    matches = [pr for page in pages for pr in page if pr["head"]["repo"] and pr["head"]["repo"]["full_name"].lower() == contract["head"]["repository"].lower() and pr["head"]["ref"] == contract["head"]["ref"]]
    c.require(len(matches) <= 1, "multiple PRs for bootstrap head; human recovery required")
    if not matches:
        c.require(api(f"repos/{repository}/git/ref/heads/{quote(contract['target']['ref'], safe='')}")["object"]["sha"] == contract["target"]["sha"], "base changed during bootstrap; explicitly reconcile before PR creation")
        # Persist complete body before the possibly ambiguous network mutation.
        body = c.render(contract)
        journal["body"] = body
        journal_write(args.journal, journal)
        payload = {"title": journal["title"], "head": owner + ":" + contract["head"]["ref"], "head_repo": contract["head"]["repository"].split("/")[1], "base": contract["target"]["ref"], "body": body, "draft": True}
        result = subprocess.run(["gh", "api", f"repos/{repository}/pulls", "--method", "POST", "--input", "-"], input=json.dumps(payload), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        c.require(result.returncode == 0, "PR creation failed or uncertain; preserve journal and resume same branch/run (no second bootstrap commit): " + result.stderr.strip())
        url = json.loads(result.stdout)["html_url"]
    else:
        url = matches[0]["html_url"]
    pr, found, _, state = snapshot(url, args.trusted_source)
    c.require(pr["state"] == "open" and pr["draft"] and found == contract and live_tuple(pr, found)["head_sha"] == journal["commit"] and not state.active and not state.conflict, "existing PR does not match bootstrap identity/state; explicit recovery required")
    c.require(pr["checked_base_sha"] == contract["target"]["sha"], "base advanced during bootstrap; revalidate policy and use explicit recovery")
    c.require(pr["user"]["login"] == journal["actor"] or args.recovery_authority, "bootstrap PR author changed; explicit human ownership acceptance required")
    journal["pr"] = url
    if args.recovery_authority:
        journal["recovery_authority"] = args.recovery_authority
        api(f"repos/{repository}/issues/{pr_identity(url)[1]}/comments", "--method", "POST", "-f",
            "body=Bootstrap recovery accepted: " + args.recovery_authority + "\nBootstrap: " + contract["bootstrap"]["id"]
            + "\nNo implementation lease acquired.")
    journal_write(args.journal, journal)
    print(url + "\nBootstrap complete. Acquire a normal write lease before any implementation/body write.\nRun: " + journal["run"])


def offline(args):
    if args.operation == "seal":
        contract = c.seal(c.loads(Path(args.input).read_text()), args.revision)
        Path(args.output).write_bytes((c.render(contract) + "\n").encode("utf-8"))
    elif args.operation == "validate":
        body = Path(args.body).read_bytes().decode("utf-8")
        print(json.dumps(c.read_contract(body), indent=2))
    elif args.operation == "snapshot":
        body = Path(args.body).read_bytes().decode("utf-8")
        print(c.sha256(c.section(body)[2].encode("utf-8")))
    elif args.operation == "repair":
        body = Path(args.body).read_bytes().decode("utf-8")
        repaired, _ = c.repair_contract(body, args.accepted_raw, args.last_revision)
        Path(args.output).write_bytes(repaired.encode("utf-8"))


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    body = commands.add_parser("contract", help="offline body preparation/validation; grants no lease")
    body.add_argument("operation", choices=("seal", "validate", "snapshot", "repair"))
    for key in ("input", "output", "body", "accepted-raw"):
        body.add_argument("--" + key)
    body.add_argument("--revision", type=int, default=1)
    body.add_argument("--last-revision", type=int)
    body.set_defaults(function=offline)
    for name, function in (("status", status), ("event", record), ("ready", ready), ("edit", edit), ("repair", repair), ("pointer-sync", pointer_sync), ("cleanup", cleanup)):
        sub = commands.add_parser(name)
        sub.add_argument("--pr", required=True)
        sub.add_argument("--trusted-source", default=TRUSTED_SOURCE)
        if name != "status":
            sub.add_argument("--run", required=True)
        if name in ("event", "ready"):
            sub.add_argument("--details", help="JSON file with evidence/approval references")
        if name == "event":
            sub.add_argument("--action", choices=("claim", "checkpoint", "suspend", "resume", "release", "recover", "verify", "review", "revalidate", "cleanup_cancel"), required=True)
        if name == "edit":
            sub.add_argument("--input", required=True)
            sub.add_argument("--accept-change")
        if name == "repair":
            sub.add_argument("--accepted-raw", required=True)
            sub.add_argument("--acceptance", required=True)
            sub.add_argument("--last-revision", type=int, required=True)
            sub.add_argument("--output", required=True)
            sub.add_argument("--apply", action="store_true")
            sub.add_argument("--complete", action="store_true", help="validate exact replacement applied by an authorized human")
        if name == "cleanup":
            sub.add_argument("--remote", required=True)
        sub.set_defaults(function=function)
    boot = commands.add_parser("bootstrap")
    for key in ("repo", "base", "head-repo", "branch", "plan", "title", "run", "accepted-policy", "source-commit", "recovery-authority"):
        boot.add_argument("--" + key)
    boot.add_argument("--remote", required=True)
    boot.add_argument("--journal", required=True)
    boot.add_argument("--trusted-source", default=TRUSTED_SOURCE)
    for key in ("start-now", "development-source", "resume"):
        boot.add_argument("--" + key, action="store_true")
    boot.set_defaults(function=bootstrap)
    return root


def main():
    args = parser().parse_args()
    try:
        c.require(sys.version_info >= (3, 9), "Python 3.9+ required")
        args.function(args)
    except (c.Invalid, OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        print("STOP: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
