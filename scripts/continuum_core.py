"""Continuum 0.5 visible comment records and lease-state reconstruction."""

import re
import uuid
from dataclasses import dataclass, field

VERSION = "0.5.0"
FENCE = re.compile(r"```continuum\n([^\n]*)\n```", re.IGNORECASE)
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")


class Invalid(ValueError):
    """Malformed or ambiguous state; the caller must stop writes."""


def require(ok, message):
    if not ok:
        raise Invalid(message)


def new_run():
    return str(uuid.uuid4())


def render(action, run, sha=None, confirmation=None):
    require(UUID.fullmatch(run), "run identity must be a UUIDv4")
    if action == "claim":
        require(sha is None and confirmation is None, "claim takes only a run identity")
        line = f"claim {run}"
    elif action == "release":
        require(sha is not None and SHA.fullmatch(sha), "release requires the exact full HEAD SHA")
        require(confirmation is None, "release does not take confirmation text")
        line = f"release {run} {sha}"
    else:
        raise Invalid("use recover() for recovery records")
    return f"```continuum\n{line}\n```"


def render_recovery(runs, confirmation):
    runs = sorted(set(runs))
    require(runs and all(UUID.fullmatch(run) for run in runs), "recovery must name active UUIDv4 run identities")
    require(isinstance(confirmation, str) and confirmation.strip(), "recovery needs owner confirmation and work disposition")
    require(not any(ch in confirmation for ch in ("\n", "\r", "|", "`")),
            "recovery confirmation must be one line without record delimiters")
    return "```continuum\nrecover " + ", ".join(runs) + " | " + confirmation.strip() + "\n```"


def parse_comment(body, author, association, pr_author=""):
    if "```continuum" not in body.lower():
        return None
    matches = list(FENCE.finditer(body))
    require(len(matches) == 1 and body.count("```continuum") == 1,
            "malformed or duplicated Continuum record")
    require(matches[0].group(0) == body, "coordination comment must contain only its visible record")
    require(matches[0].group(1).strip() == matches[0].group(1), "record has surrounding whitespace")
    line = matches[0].group(1)
    match = re.fullmatch(r"claim ([0-9a-f-]+)", line)
    if match:
        run = match.group(1)
        require(UUID.fullmatch(run), "invalid claim run identity")
        require(author == pr_author or association in ("OWNER", "MEMBER", "COLLABORATOR"),
                "untrusted lease author")
        return {"action": "claim", "run": run}
    match = re.fullmatch(r"release ([0-9a-f-]+) ([0-9a-f]{40})", line)
    if match:
        run, sha = match.groups()
        require(UUID.fullmatch(run) and SHA.fullmatch(sha), "invalid release record")
        require(author == pr_author or association in ("OWNER", "MEMBER", "COLLABORATOR"),
                "untrusted lease author")
        return {"action": "release", "run": run, "sha": sha}
    match = re.fullmatch(r"recover ([0-9a-f-]+(?:, [0-9a-f-]+)*) \| (.+)", line)
    require(match is not None, "unknown or malformed Continuum record")
    require(association == "OWNER", "only a repository OWNER may recover a lease")
    runs = match.group(1).split(", ")
    require(all(UUID.fullmatch(run) for run in runs) and len(runs) == len(set(runs)),
            "invalid recovery run list")
    confirmation = match.group(2)
    require(confirmation.strip() == confirmation and confirmation and "\r" not in confirmation,
            "empty or malformed recovery confirmation")
    return {"action": "recover", "runs": runs, "confirmation": confirmation}


@dataclass
class State:
    active: dict = field(default_factory=dict)
    conflict: bool = False
    used_runs: set = field(default_factory=set)


def reconstruct(comments, pr_author="", recovery_boundary=False):
    """Replay trusted records in GitHub order; comments stay outside model context."""
    state = State()
    for index, comment in enumerate(comments):
        record = parse_comment(comment.get("body") or "", comment.get("author", ""),
                               comment.get("author_association", ""), pr_author)
        if record is None:
            continue
        action = record["action"]
        if action == "claim":
            run = record["run"]
            require(run not in state.used_runs, "run identity reused; human reconciliation required")
            state.used_runs.add(run)
            if state.active:
                state.conflict = True
            state.active[run] = record
        elif action == "release":
            if state.conflict or set(state.active) != {record["run"]}:
                state.conflict = True
            else:
                del state.active[record["run"]]
        else:
            if not (recovery_boundary and index == 0):
                require(set(record["runs"]) == set(state.active),
                        "recovery must name the complete active lease set")
            state.active.clear()
            state.conflict = False
    return state
