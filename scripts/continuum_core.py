"""Continuum 0.6 whole-comment records and lease-state reconstruction."""

import re
from dataclasses import dataclass, field

VERSION = "0.6.2"
COMMENT_ID = re.compile(r"[1-9][0-9]*\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")


class Invalid(ValueError):
    """Malformed or ambiguous state; the caller must stop writes."""


def require(ok, message):
    if not ok:
        raise Invalid(message)


def grammar(version=VERSION):
    require(version in ("0.6.0", "0.6.1", "0.6.2"), "unsupported record grammar")
    if version == "0.6.2":
        return "This PR was claimed", "This PR's claim", "was released at", "This PR was recovered"
    return "claim", "release", "", "recover"


def render(action, claim_id=None, sha=None, confirmation=None, version=VERSION):
    claim, release, at, _ = grammar(version)
    if action == "claim":
        require(claim_id is None and sha is None and confirmation is None,
                "claim takes no fields")
        return claim
    if action == "release":
        require(isinstance(claim_id, str) and COMMENT_ID.fullmatch(claim_id),
                "release requires the exact claim comment ID")
        require(isinstance(sha, str) and SHA.fullmatch(sha),
                "release requires the exact full HEAD SHA")
        require(confirmation is None, "release does not take confirmation text")
        return " ".join(part for part in (release, claim_id, at, sha) if part)
    raise Invalid("use render_recovery() for recovery records")


def render_recovery(confirmation, version=VERSION):
    require(isinstance(confirmation, str) and confirmation.strip(),
            "recovery needs owner confirmation and work disposition")
    confirmation = confirmation.strip()
    require("\n" not in confirmation and "\r" not in confirmation and "|" not in confirmation,
            "recovery confirmation must be one line without record delimiters")
    return grammar(version)[3] + " | " + confirmation


def parse_comment(body, author, association, pr_author="", comment_id=None, version=VERSION):
    """Return protocol records only when the whole comment matches the grammar."""
    claim, release, at, recovery = grammar(version)
    if body == claim:
        require(isinstance(comment_id, (int, str)) and COMMENT_ID.fullmatch(str(comment_id)),
                "claim comment is missing its GitHub comment ID")
        record = {"action": "claim", "claim_id": str(comment_id)}
    else:
        match = re.fullmatch(re.escape(release) + r" ([1-9][0-9]*) " +
                            (re.escape(at) + " " if at else "") + r"([0-9a-f]{40})", body)
        if match:
            record = {"action": "release", "claim_id": match.group(1), "sha": match.group(2)}
        else:
            match = re.fullmatch(re.escape(recovery) + r" \| ([^\r\n|]+)", body)
            if not match or not match.group(1).strip():
                return None
            record = {"action": "recover", "confirmation": match.group(1)}

    if record["action"] == "recover":
        require(association == "OWNER", "only a repository OWNER may recover a lease")
    else:
        require(author == pr_author or association in ("OWNER", "MEMBER", "COLLABORATOR"),
                "untrusted lease author")
    return record


@dataclass
class State:
    active: dict = field(default_factory=dict)
    conflict: bool = False
    version: str = VERSION


def reconstruct(comments, pr_author="", version=VERSION):
    """Replay trusted records in GitHub order; comments stay outside model context."""
    grammar(version)
    state = State(version=version)
    for comment in comments:
        record = parse_comment(comment.get("body") or "", comment.get("author", ""),
                               comment.get("author_association", ""), pr_author,
                               comment.get("id"), version=version)
        if record is None:
            continue
        action = record["action"]
        if action == "claim":
            claim_id = record["claim_id"]
            if claim_id in state.active or state.active:
                state.conflict = True
            state.active[claim_id] = record
        elif action == "release":
            claim_id = record["claim_id"]
            if state.conflict or set(state.active) != {claim_id}:
                state.conflict = True
            else:
                del state.active[claim_id]
        else:
            state.active.clear()
            state.conflict = False
    return state
