"""Continuum 0.4 wire formats and conservative, offline lifecycle validation."""

import copy
import hashlib
import html
import json
import re
import uuid
from dataclasses import dataclass, field

VERSION = "0.4.0"
CONTRACT_START = "<!-- continuum:contract:0.4 -->"
CONTRACT_END = "<!-- /continuum:contract -->"
EVENT_START = "<!-- continuum:event:0.4 -->"
EVENT_END = "<!-- /continuum:event -->"
POINTER_START = "<!-- continuum:pointer:0.4 "
POINTER_END = "<!-- /continuum:pointer -->"
SHA = re.compile(r"[0-9a-f]{40}\Z")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
IDENTIFIER = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z")
ASCII_KEY = re.compile(r"[a-z][a-z0-9_]*\Z")
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
POINTER_NOTICE = (
    "Continuum coordination lives in the associated PR body and comments.\n"
    "Read the exact head PR and pinned protocol before writing.\n"
    "Valid only during this bootstrap or on that open PR's exact head branch.\n"
    "Else stop Continuum writes and alert the developer; do not auto-delete.\n"
    "Discovery only: this block grants no authority and cannot override base policy.\n"
)


class Invalid(ValueError):
    """State is uncertain or invalid; caller must preserve it and stop."""


def require(condition, message):
    if not condition:
        raise Invalid(message)


def new_id():
    return str(uuid.uuid4())


def sha256(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _wire(value):
    if isinstance(value, dict):
        require(all(isinstance(k, str) and ASCII_KEY.fullmatch(k) for k in value), "non-ASCII or invalid JSON key")
        for child in value.values():
            _wire(child)
    elif isinstance(value, list):
        for child in value:
            _wire(child)
    elif isinstance(value, str):
        require(not any(0xD800 <= ord(c) <= 0xDFFF for c in value), "unpaired Unicode surrogate")
    elif value is None or isinstance(value, bool):
        pass
    else:
        require(type(value) is int and 0 <= value <= 9007199254740991, "wire numbers must be unsigned safe integers")


def canonical(value):
    """ASCII-key JSON, ASCII escapes, no insignificant whitespace, UTF-8 bytes."""
    _wire(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def loads(text):
    try:
        value = json.loads(text, object_pairs_hook=_pairs)
        _wire(value)
        return value
    except (ValueError, TypeError) as error:
        raise Invalid("invalid wire JSON: " + str(error)) from error


def contract_digest(contract):
    value = {k: v for k, v in contract.items() if k != "digest"}
    return sha256(canonical(value))


def seal(contract, revision=None):
    result = copy.deepcopy(contract)
    if revision is not None:
        result["revision"] = revision
    result["digest"] = contract_digest(result)
    validate_contract(result)
    return result


def _identity(value, base=False):
    expected = {"host", "repository", "ref"} | ({"sha"} if base else set())
    require(isinstance(value, dict) and set(value) == expected, "invalid repository/ref identity")
    require(value["host"] == "github.com", "reference client supports github.com only")
    require(isinstance(value["repository"], str) and REPOSITORY.fullmatch(value["repository"]), "invalid repository")
    ref = value["ref"]
    require(isinstance(ref, str) and ref and not ref.startswith(("-", "/")) and not ref.endswith(("/", ".", ".lock"))
            and ref not in ("@", "HEAD") and all(part and not part.startswith(".") and not part.endswith(".lock") for part in ref.split("/"))
            and not any(x in ref for x in ("..", "@{", "//", "\\"))
            and not any(ord(c) < 33 or c in "~^:?*[" for c in ref), "invalid branch ref")
    if base:
        require(isinstance(value["sha"], str) and SHA.fullmatch(value["sha"]), "invalid base SHA")


def validate_source(source):
    require(isinstance(source, dict) and set(source) == {"host", "repository", "version", "commit", "path"}, "invalid protocol pin")
    require(source["host"] == "github.com" and REPOSITORY.fullmatch(source["repository"]), "invalid protocol repository")
    require(source["version"] == VERSION and SHA.fullmatch(source["commit"]), "unsupported version or mutable source pin")
    require(source["path"] == "protocol/CONTINUUM.md", "invalid canonical protocol path")


def validate_contract(contract, digest=True):
    required = {"schema", "revision", "digest", "bootstrap", "source", "target", "head", "goal", "scope", "acceptance", "plan", "verification", "changes", "context"}
    require(isinstance(contract, dict) and set(contract) == required, "missing or unknown contract fields")
    _wire(contract)
    require(contract["schema"] == "continuum/0.4", "unsupported contract schema")
    require(type(contract["revision"]) is int and contract["revision"] > 0, "invalid contract revision")
    validate_source(contract["source"])
    _identity(contract["target"], True)
    _identity(contract["head"])
    require(contract["target"]["repository"] != contract["head"]["repository"] or contract["target"]["ref"] != contract["head"]["ref"], "head cannot be target")
    boot = contract["bootstrap"]
    require(isinstance(boot, dict) and set(boot) == {"id", "run", "commit", "pointer_digest", "agents_created"}, "invalid bootstrap provenance")
    require(IDENTIFIER.fullmatch(boot["id"]) and IDENTIFIER.fullmatch(boot["run"]), "invalid bootstrap/run UUID")
    require(SHA.fullmatch(boot["commit"]) and DIGEST.fullmatch(boot["pointer_digest"]), "invalid bootstrap commit/pointer digest")
    require(type(boot["agents_created"]) is bool, "invalid path creation provenance")
    require(isinstance(contract["goal"], str) and contract["goal"].strip(), "goal required")
    for key in ("scope", "acceptance", "plan", "verification", "changes", "context"):
        require(isinstance(contract[key], list) and all(isinstance(s, str) and s.strip() for s in contract[key]), "invalid " + key)
        if key not in ("changes", "context"):
            require(contract[key], key + " required")
    if digest:
        require(isinstance(contract["digest"], str) and DIGEST.fullmatch(contract["digest"])
                and contract["digest"] == contract_digest(contract), "contract digest mismatch; repair required")
    return contract


def section(text, start=CONTRACT_START, end=CONTRACT_END):
    require(text.count(start) == 1 and text.count(end) == 1, "missing/duplicated controlled delimiters")
    # Unknown versions and malformed lookalikes are never silently ignored.
    family = "<!-- continuum:contract" if start == CONTRACT_START else "<!-- continuum:event"
    require(text.count(family) == 1, "unknown or malformed controlled section")
    left = text.index(start)
    right = text.index(end) + len(end)
    require(left < right - len(end), "reversed controlled delimiters")
    raw = text[left:right]
    prefix, suffix = start + "\n```json\n", "\n```\n" + end
    require(raw.startswith(prefix) and raw.endswith(suffix), "controlled section must use exact LF/fenced-JSON framing")
    return left, right, raw, loads(raw[len(prefix):-len(suffix)])


def render(contract):
    validate_contract(contract)
    return CONTRACT_START + "\n```json\n" + pretty(contract) + "\n```\n" + CONTRACT_END


def pretty(value):
    # A plan may discuss the delimiters themselves. Escape '<' in presentation
    # JSON so string values cannot impersonate framing; the digest is unchanged.
    return json.dumps(value, indent=2, ensure_ascii=True, sort_keys=True).replace("<", "\\u003c")


def read_contract(body):
    return validate_contract(section(body)[3])


def replace_contract(body, replacement, expected):
    current = read_contract(body)
    require((current["revision"], current["digest"]) == expected, "contract changed since read")
    require(replacement["revision"] == current["revision"] + 1, "revision must advance by exactly one")
    require(replacement["bootstrap"] == current["bootstrap"], "bootstrap provenance is immutable")
    left, right, _, _ = section(body)
    return body[:left] + render(replacement) + body[right:]


def repair_contract(body, accepted_raw_digest, last_valid_revision):
    """Only metadata changes. Human acceptance and exclusive claim are caller gates."""
    left, right, raw, contract = section(body)
    require(sha256(raw.encode("utf-8")) == accepted_raw_digest, "accepted raw snapshot changed")
    require(type(last_valid_revision) is int and last_valid_revision >= 0, "trusted predecessor revision required")
    # A human may damage revision/digest. All other fields still have to validate.
    candidate = copy.deepcopy(contract)
    candidate["revision"] = last_valid_revision + 1
    repaired = seal(candidate)
    return body[:left] + render(repaired) + body[right:], repaired


def pointer_data(contract):
    return {"schema": "continuum-pointer/0.4", "id": contract["bootstrap"]["id"], "run": contract["bootstrap"]["run"],
            "agents_created": contract["bootstrap"]["agents_created"], "source": contract["source"],
            "target": contract["target"], "head": contract["head"]}


def render_pointer(data):
    require(set(data) == {"schema", "id", "run", "agents_created", "source", "target", "head"}, "invalid pointer metadata")
    require(data["schema"] == "continuum-pointer/0.4" and IDENTIFIER.fullmatch(data["id"]) and IDENTIFIER.fullmatch(data["run"]), "invalid pointer identity")
    require(type(data["agents_created"]) is bool, "invalid pointer provenance")
    validate_source(data["source"])
    _identity(data["target"], True)
    _identity(data["head"])
    # The leading LF belongs to the block, even for a previously unterminated file.
    return ("\n" + POINTER_START + data["id"] + " -->\n```json\n" + canonical(data).decode("ascii")
            + "\n```\n" + POINTER_NOTICE + POINTER_END + "\n").encode("utf-8")


def read_pointer(data):
    require(data.count(b"<!-- continuum:pointer") == 1 and data.count(POINTER_END.encode()) == 1, "missing, foreign, duplicated or malformed pointer")
    left = data.find(b"\n" + POINTER_START.encode())
    require(left >= 0, "pointer framing altered")
    right = data.find(POINTER_END.encode(), left) + len(POINTER_END) + 1
    raw = data[left:right]
    match = re.fullmatch(rb'\n<!-- continuum:pointer:0\.4 ([^\n]+) -->\n```json\n([^\n]+)\n```\n.*<!-- /continuum:pointer -->\n', raw, re.S)
    require(match is not None, "malformed pointer")
    meta = loads(match[2].decode("utf-8"))
    require(meta["id"].encode() == match[1] and render_pointer(meta) == raw, "pointer bytes/notice altered")
    return left, right, raw, meta


def append_pointer(original, meta):
    original = original or b""
    require(b"<!-- continuum:pointer" not in original and POINTER_END.encode() not in original, "base contains temporary pointer; stacking/recovery required")
    return original + render_pointer(meta)


def remove_pointer(data, contract, base_owns_agents, origin_verified):
    left, right, raw, meta = read_pointer(data)
    require(meta == pointer_data(contract), "pointer is not owned by current accepted contract")
    require(origin_verified, "bootstrap creation provenance not verified")
    remainder = data[:left] + data[right:]
    delete = contract["bootstrap"]["agents_created"] and remainder == b"" and not base_owns_agents
    return None if delete else remainder, sha256(raw)


def pointer_context(meta, repository, ref, open_pr_contract=None, bootstrap_run=None):
    require((repository, ref) == (meta["head"]["repository"], meta["head"]["ref"]), "stale pointer on unrelated/target branch; alert developer")
    if open_pr_contract is not None:
        require(meta == pointer_data(open_pr_contract), "pointer/PR identity mismatch; alert developer")
    else:
        require(bootstrap_run == meta["run"], "orphan/closed pointer needs explicit human recovery; alert developer")


def readiness_tuple(contract, head_sha, base_sha):
    require(SHA.fullmatch(head_sha) and SHA.fullmatch(base_sha), "invalid live SHA")
    return {"revision": contract["revision"], "digest": contract["digest"], "head_sha": head_sha,
            "target": {k: contract["target"][k] for k in ("host", "repository", "ref")}, "base_sha": base_sha,
            "head": contract["head"]}


def validate_tuple(value):
    require(isinstance(value, dict) and set(value) == {"revision", "digest", "head_sha", "target", "base_sha", "head"}, "invalid evidence tuple")
    require(type(value["revision"]) is int and value["revision"] > 0 and DIGEST.fullmatch(value["digest"]), "invalid evidence contract identity")
    require(SHA.fullmatch(value["head_sha"]) and SHA.fullmatch(value["base_sha"]), "invalid evidence SHA")
    _identity(value["target"])
    _identity(value["head"])


def event_text(event):
    validate_event(event)
    # Escape framing lookalikes in values without changing the parsed metadata.
    metadata = canonical(event).decode("ascii").replace("<", "\\u003c")
    return (event_summary(event) + "\n\n<details>\n<summary>Continuum metadata</summary>\n\n"
            + EVENT_START + "\n```json\n" + metadata + "\n```\n" + EVENT_END
            + "\n\n</details>")


def event_summary(event):
    """Presentation only; controlled metadata remains the replay authority."""
    action, kind = event["action"], event["kind"]
    if action == "claim":
        message = {"write": "Write lease acquired", "repair": "Metadata repair lease acquired",
                   "cleanup": "Pointer cleanup lease acquired"}[kind]
    elif action == "cleanup_complete":
        message = ("Pointer cleanup confirmed (already absent)" if event["details"].get("no_op") is True
                   else "Pointer cleanup completed")
    else:
        message = {
            "checkpoint": "Checkpoint saved; write lease retained",
            "verify": "Verification recorded",
            "ready": "Ready evidence recorded",
            "review": "Independent review recorded",
            "release": "Lease released",
            "suspend": "Lease suspended; ownership retained",
            "resume": "Lease resumed",
            "repair_enter": "Metadata repair started; write lease retained",
            "repair_complete": "Metadata repair completed",
            "recover": "Human-authorized ownership recovery recorded",
            "revalidate": "Base revalidation recorded",
            "cleanup_cancel": "Pointer cleanup cancelled; lease ended",
        }[action]
    summary = f"**{message}.**"
    key = ("reason" if action in ("suspend", "cleanup_cancel") else
           "human_confirmation" if action == "recover" else "acceptance")
    detail = event["details"].get(key)
    if isinstance(detail, str) and detail.strip():
        # Keep full evidence in metadata. Display excerpts as a paragraph,
        # escaping formatting and framing; reference URLs may still autolink.
        excerpt = " ".join(detail.split())
        if len(excerpt) > 280:
            excerpt = excerpt[:277].rsplit(" ", 1)[0] + "..."
        excerpt = html.escape(excerpt, quote=False)
        excerpt = re.sub(r"([\\`*_~\[\]])", r"\\\1", excerpt)
        excerpt = re.sub(r"^([#+-])", r"\\\1", excerpt)
        excerpt = re.sub(r"^(\d{1,9})([.)])(?=\s|$)", r"\1\\\2", excerpt)
        summary += "\n\n" + excerpt
    return summary


ACTIONS = {"claim", "checkpoint", "suspend", "resume", "repair_enter", "repair_complete", "release", "recover", "verify", "ready", "review", "revalidate", "cleanup_complete", "cleanup_cancel"}


def validate_event(event):
    require(isinstance(event, dict) and set(event) == {"schema", "id", "prev", "actor", "run", "action", "kind", "subject", "tuple", "details"}, "invalid event fields")
    _wire(event)
    require(event["schema"] == "continuum-event/0.4" and IDENTIFIER.fullmatch(event["id"]) and IDENTIFIER.fullmatch(event["run"]), "invalid event/run identity")
    require(isinstance(event["actor"], str) and re.fullmatch(r"[A-Za-z0-9-]+(?:\[bot\])?", event["actor"]), "invalid actor")
    require(isinstance(event["prev"], list) and len(set(event["prev"])) == len(event["prev"]) and all(IDENTIFIER.fullmatch(i) for i in event["prev"]), "invalid event predecessor frontier")
    require(event["prev"] == sorted(event["prev"]), "event predecessor frontier must be sorted")
    require(event["action"] in ACTIONS and event["kind"] in ("write", "repair", "cleanup", "evidence", "recovery"), "unknown event")
    kinds = {"claim": ("write", "repair", "cleanup"), "checkpoint": ("write",), "suspend": ("write", "repair", "cleanup"),
             "resume": ("write", "repair", "cleanup"), "repair_enter": ("write",), "repair_complete": ("write", "repair"),
             "release": ("write", "repair"), "recover": ("recovery",), "cleanup_complete": ("cleanup",), "cleanup_cancel": ("cleanup",)}
    require(event["kind"] in kinds.get(event["action"], ("evidence",)), "action/kind mismatch")
    require(event["subject"] is None or IDENTIFIER.fullmatch(event["subject"]), "invalid claim subject")
    require(isinstance(event["details"], dict), "invalid event details")
    required_detail = ("acceptance" if event["action"] in ("claim", "verify", "ready", "review", "revalidate", "resume") else
                       "reason" if event["action"] in ("suspend", "cleanup_cancel") else
                       "human_confirmation" if event["action"] == "recover" else None)
    if required_detail:
        value = event["details"].get(required_detail)
        require(isinstance(value, str) and value.strip(), "event needs a nonempty " + required_detail + " reference")
    if event["kind"] == "repair" or event["action"] == "repair_enter":
        details = event["details"]
        if event["action"] in ("claim", "repair_enter"):
            require(DIGEST.fullmatch(details.get("raw_digest", "")) and type(details.get("last_revision")) is int
                    and details["last_revision"] >= 0 and details.get("acceptance"), "repair needs accepted exact raw snapshot and trusted predecessor")
            validate_tuple(details.get("snapshot"))
            require(details["snapshot"]["revision"] == details["last_revision"] + 1, "repair replacement must follow trusted revision")
    if event["tuple"] is not None:
        validate_tuple(event["tuple"])
    require(event["tuple"] is not None or event["kind"] in ("repair", "recovery") or event["action"] in ("repair_enter", "suspend", "resume", "release"), "event tuple required")


@dataclass
class State:
    frontier: set = field(default_factory=set)
    active: dict = None
    mode: str = "active"
    conflict: bool = False
    evidence: dict = field(default_factory=dict)
    receipts: list = field(default_factory=list)
    last_revision: int = 0
    repair: dict = None
    resume_mode: str = "active"
    writer_runs: set = field(default_factory=set)


def replay(events):
    """Append-only cooperative history. Competing claims need explicit recovery."""
    state, seen = State(), set()
    for event in events:
        validate_event(event)
        eid, prev, action = event["id"], set(event["prev"]), event["action"]
        require(eid not in seen and prev <= seen, "duplicate event ID or missing/reordered history")
        old_frontier = set(state.frontier)
        if prev != old_frontier:
            state.conflict = True
        state.frontier.difference_update(prev)
        state.frontier.add(eid)
        seen.add(eid)
        if action == "recover":
            require(prev == old_frontier, "recovery must cover entire frontier")
            require(event["kind"] == "recovery" and event["details"].get("human_confirmation"), "human stale-owner confirmation required")
            state.active, state.mode, state.conflict = None, "active", False
            state.repair = None
            state.evidence.clear()
            continue
        if state.conflict:
            continue
        if event["tuple"]:
            state.last_revision = max(state.last_revision, event["tuple"]["revision"])
        if action == "claim":
            require(state.active is None and event["kind"] in ("write", "repair", "cleanup") and event["subject"] is None, "competing claim or invalid acquisition")
            if event["kind"] == "cleanup":
                require(all(state.evidence.get(k) == event["tuple"] for k in ("verify", "ready", "review")), "cleanup claim requires current review evidence")
            state.active = event
            state.mode = "repair" if event["kind"] == "repair" else "active"
            if event["kind"] == "repair":
                state.repair = event["details"]
            if event["kind"] == "write":
                state.writer_runs.add(event["run"])
        elif action == "revalidate":
            require(event["kind"] == "evidence" and state.active is None and event["details"].get("acceptance")
                    and event["details"].get("independent_review") is True and event["run"] not in state.writer_runs, "base revalidation requires unleased independent acceptance")
            for name in ("verify", "ready", "review"):
                previous = state.evidence.get(name)
                require(previous and {k: v for k, v in previous.items() if k != "base_sha"}
                        == {k: v for k, v in event["tuple"].items() if k != "base_sha"}, "material change needs Draft reconciliation")
            state.evidence = {k: event["tuple"] for k in ("verify", "ready", "review")}
        elif action in ("verify", "ready", "review"):
            require(event["kind"] == "evidence", "evidence event kind required")
            if action == "review":
                require(state.active is None and state.evidence.get("ready") == event["tuple"] and event["details"].get("independent_review") is True
                        and event["run"] not in state.writer_runs and event["subject"] is None, "review requires independent unleased current Ready evidence")
            else:
                require(state.active and state.active["kind"] == "write" and state.mode == "active"
                        and state.active["run"] == event["run"] and state.active["actor"] == event["actor"]
                        and event["subject"] == state.active["id"], "writer owns verification/Ready evidence")
                if action == "ready":
                    require(state.evidence.get("verify") == event["tuple"], "Ready requires current verification")
            require(event["details"].get("acceptance"), "evidence must reference actual checks/review")
            state.evidence[action] = event["tuple"]
        else:
            require(state.active and event["subject"] == state.active["id"] and event["run"] == state.active["run"]
                    and event["actor"] == state.active["actor"], "event is not from claim owner")
            kind = state.active["kind"]
            require(event["kind"] == kind, "transition must retain claim kind")
            if action == "suspend":
                require(event["details"].get("reason"), "suspension reason required")
                if state.mode != "suspended":
                    state.resume_mode = state.mode
                state.mode = "suspended"
            elif action == "resume":
                require(state.mode == "suspended" and event["details"].get("acceptance"), "resume needs approval/reconciliation")
                state.mode = state.resume_mode
                if event["tuple"] is not None:
                    state.active = {**state.active, "tuple": event["tuple"]}
            elif action == "repair_enter":
                require(kind == "write" and state.mode != "suspended", "repair mode requires writer")
                state.mode = "repair"
                state.repair = event["details"]
                state.evidence.clear()
            elif action == "repair_complete":
                require(state.mode == "repair" and event["tuple"] and event["details"].get("raw_digest"), "repair completion needs valid replacement")
                require(state.repair and all(event["details"].get(k) == state.repair[k] for k in ("raw_digest", "last_revision", "acceptance", "snapshot"))
                        and event["tuple"] == state.repair["snapshot"], "repair completion differs from accepted snapshot/replacement")
                state.mode = "active"
                state.repair = None
                state.active = {**state.active, "tuple": event["tuple"]}
                state.evidence.clear()
            elif action == "checkpoint":
                require(kind == "write" and state.mode == "active", "checkpoint requires active implementation lease")
                state.active = {**state.active, "tuple": event["tuple"]}
            elif action == "cleanup_complete":
                require(kind == "cleanup" and state.mode == "active", "cleanup completion needs cleanup claim")
                receipt = event["details"]
                require(set(receipt) == {"bootstrap_id", "pointer_digest", "removal_commit", "readiness", "prior_receipt", "no_op"}, "invalid removal receipt")
                require(IDENTIFIER.fullmatch(receipt["bootstrap_id"]) and DIGEST.fullmatch(receipt["pointer_digest"])
                        and SHA.fullmatch(receipt["removal_commit"]), "invalid removal provenance")
                validate_tuple(receipt["readiness"])
                require(type(receipt["no_op"]) is bool and receipt["readiness"] == state.active["tuple"], "cleanup receipt readiness mismatch")
                if receipt["no_op"]:
                    require(any(r["event_id"] == receipt["prior_receipt"] and r["bootstrap_id"] == receipt["bootstrap_id"]
                                and r["pointer_digest"] == receipt["pointer_digest"] and r["removal_commit"] == receipt["removal_commit"] for r in state.receipts), "no-op needs prior authorized removal")
                    require(event["tuple"] == receipt["readiness"], "no-op cannot change HEAD")
                else:
                    require(receipt["prior_receipt"] is None and event["tuple"]["head_sha"] == receipt["removal_commit"], "removal receipt must identify cleanup HEAD")
                    require({k: v for k, v in event["tuple"].items() if k != "head_sha"}
                            == {k: v for k, v in receipt["readiness"].items() if k != "head_sha"}, "cleanup cannot change contract/target/base")
                state.receipts.append({**receipt, "event_id": eid})
                state.active = None
            elif action == "cleanup_cancel":
                require(kind == "cleanup" and event["details"].get("reason"), "cleanup cancellation needs reason")
                state.active = None
            elif action == "release":
                require(kind in ("write", "repair") and state.mode == "active", "resume/repair must complete before normal release")
                state.active = None
            else:
                raise Invalid("invalid transition: " + action)
    return state


def cleanup_gate(state, current, is_open, is_draft):
    require(is_open and not is_draft and not state.conflict and state.active is None, "cleanup requires open Ready, unclaimed PR")
    require(all(state.evidence.get(k) == current for k in ("verify", "ready", "review")), "cleanup requires independent current verification/Ready/review tuple")


def no_op_receipt(state, contract, current, agents, ancestor, path_unchanged):
    """Caller supplies verified Git ancestry and absence since authorized removal."""
    require(b"<!-- continuum:pointer" not in (agents or b""), "pointer/foreign stale block present")
    for receipt in reversed(state.receipts):
        if receipt["bootstrap_id"] == contract["bootstrap"]["id"] and ancestor(receipt["removal_commit"]) and path_unchanged(receipt["removal_commit"]):
            return {k: receipt[k] for k in ("bootstrap_id", "pointer_digest", "removal_commit")} | {
                "readiness": current, "prior_receipt": receipt["event_id"], "no_op": True}
    raise Invalid("unexplained pointer absence or rewritten history; explicit human recovery required")
