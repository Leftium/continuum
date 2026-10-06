"""Offline conformance and temporary-Git integration tests. No live GitHub writes."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import continuum_core as c
import continuum as client

FIXTURES = Path(__file__).parent / "fixtures"
RUN = "11111111-1111-4111-8111-111111111111"
REVIEW_RUN = "22222222-2222-4222-8222-222222222222"
CLEAN_RUN = "33333333-3333-4333-8333-333333333333"


def contract():
    return c.loads((FIXTURES / "contract.json").read_text())


def event(state, action, kind="write", run=RUN, value=None, details=None):
    value = value or c.readiness_tuple(contract(), "a" * 40, "b" * 40)
    return {"schema": "continuum-event/0.4", "id": c.new_id(), "prev": sorted(state.frontier), "actor": "agent", "run": run,
            "action": action, "kind": kind, "subject": state.active["id"] if state.active and action not in ("claim", "recover", "review", "revalidate") else None,
            "tuple": value, "details": details or {"acceptance": "checked policy and tests"}}


def append(events, action, **kwargs):
    item = event(c.replay(events), action, **kwargs)
    events.append(item)
    return c.replay(events)


def ready_history(value=None):
    events = []
    for action in ("claim", "verify", "ready", "release"):
        append(events, action, kind="evidence" if action in ("verify", "ready") else "write", value=value)
    append(events, "review", kind="evidence", run=REVIEW_RUN, value=value,
           details={"acceptance": "independent clean review", "independent_review": True})
    return events


class ContractTests(unittest.TestCase):
    def test_fixed_normalization_vector(self):
        expected = (FIXTURES / "normalized.json").read_bytes()
        value = contract()
        self.assertEqual(c.canonical({k: v for k, v in value.items() if k != "digest"}), expected)
        self.assertEqual(value["digest"], c.sha256(expected))
        self.assertEqual(c.validate_contract(value), value)
        self.assertIn(b"\\u00e9", expected)
        self.assertIn(b"\\ud83d\\ude80", expected)

    def test_whitespace_and_key_order_do_not_change_digest(self):
        value = contract()
        body = c.CONTRACT_START + "\n```json\n" + json.dumps(dict(reversed(list(value.items()))), indent=4) + "\n```\n" + c.CONTRACT_END
        self.assertEqual(c.read_contract(body), value)

    def test_changed_plan_invalidates_digest_and_revision_is_hashed(self):
        value = contract()
        value["plan"].append("Human edited this without metadata")
        with self.assertRaises(c.Invalid):
            c.validate_contract(value)
        self.assertNotEqual(c.seal(value, 2)["digest"], c.seal(value, 3)["digest"])

    def test_wire_rejects_ambiguous_json(self):
        for text in ('{"a":1,"a":2}', '{"a":1.0}', '{"a":-1}', '{"a":NaN}', '{"a":9007199254740992}', '{"\u00e9":1}', '"\\ud800"'):
            with self.subTest(text=text), self.assertRaises(c.Invalid):
                c.loads(text)

    def test_raw_snapshot_is_not_normalized(self):
        body = c.render(contract())
        raw = c.section(body)[2]
        altered = raw.replace('"goal":', '"goal" :')
        self.assertEqual(c.read_contract(raw), c.read_contract(altered))
        self.assertNotEqual(c.sha256(raw.encode()), c.sha256(altered.encode()))

    def test_plan_and_events_can_discuss_literal_delimiters(self):
        value = c.seal({**contract(), "plan": [c.CONTRACT_START, c.CONTRACT_END]})
        self.assertEqual(c.read_contract(c.render(value)), value)
        item = event(c.State(), "claim", details={"acceptance": "Check " + c.EVENT_START})
        self.assertEqual(c.section(c.event_text(item), c.EVENT_START, c.EVENT_END)[3], item)

    def test_control_and_supplementary_unicode_normalization(self):
        value = {"a": "\b\t\n\f\r\x00\x7f/\\\"\U0001f680"}
        self.assertEqual(c.canonical(value), b'{"a":"\\b\\t\\n\\f\\r\\u0000\\u007f/\\\\\\"\\ud83d\\ude80"}')
        self.assertNotEqual(c.canonical({"a": "\u00e9"}), c.canonical({"a": "e\u0301"}))

    def test_exact_repair_preserves_human_content_and_unrelated_body(self):
        body = (FIXTURES / "invalid-body.md").read_text()
        raw = c.section(body)[2]
        with self.assertRaises(c.Invalid):
            c.read_contract(body)
        repaired, value = c.repair_contract(body, c.sha256(raw.encode()), 7)
        self.assertEqual(value["revision"], 8)
        self.assertIn("Human accepted added verification", value["verification"])
        self.assertTrue(repaired.startswith("Unrelated introduction.\n\n"))
        self.assertTrue(repaired.endswith("\n\nUnrelated footer.\n"))
        self.assertEqual(c.read_contract(repaired), value)
        with self.assertRaises(c.Invalid):
            c.repair_contract(body.replace("introduction", "introduction").replace("Human accepted", "Other edit"), c.sha256(raw.encode()), 7)

    def test_body_update_preserves_outside_bytes_and_checks_predecessor(self):
        value = contract()
        body = "Intro\n" + c.render(value) + "\nFooter"
        replacement = c.seal({**value, "plan": ["Updated plan"]}, 2)
        updated = c.replace_contract(body, replacement, (1, value["digest"]))
        self.assertTrue(updated.startswith("Intro\n"))
        self.assertTrue(updated.endswith("\nFooter"))
        with self.assertRaises(c.Invalid):
            c.replace_contract(updated, replacement, (1, value["digest"]))
        replacement["bootstrap"]["agents_created"] = False
        with self.assertRaises(c.Invalid):
            c.replace_contract(body, c.seal(replacement, 2), (1, value["digest"]))

    def test_duplicated_malformed_or_unknown_sections_fail(self):
        body = c.render(contract())
        for altered in (body + body, body.replace("contract:0.4", "contract:0.5"), body.replace("```json", "```"), body.replace("\n", "\r\n")):
            with self.subTest(altered=altered[:50]), self.assertRaises(c.Invalid):
                c.read_contract(altered)


class ReleaseArtifactTests(unittest.TestCase):
    def test_pinned_artifact_uses_exact_commit_and_canonical_path(self):
        source = contract()["source"]
        text = "---\ncontinuum: 0.4.0\nartifact: protocol/CONTINUUM.md\n---\n"
        with patch.object(client, "gh", return_value=text) as gh:
            self.assertEqual(client.fetch_protocol(source), text)
        gh.assert_called_once_with("api", "repos/Leftium/continuum/contents/protocol/CONTINUUM.md?ref=" + source["commit"],
                                   "-H", "Accept: application/vnd.github.raw+json")

    def test_mutable_or_malformed_source_pin_stops_before_fetch(self):
        for pin in ("main", "v0.4.0", "e" * 39, "g" * 40):
            source = {**contract()["source"], "commit": pin}
            with self.subTest(pin=pin), patch.object(client, "gh") as gh:
                with self.assertRaises(c.Invalid):
                    client.fetch_protocol(source)
                gh.assert_not_called()

    def test_mismatched_artifact_metadata_is_rejected(self):
        for text in ("---\ncontinuum: 0.3.0\nartifact: protocol/CONTINUUM.md\n---\n",
                     "---\ncontinuum: 0.4.0\nartifact: CONTINUUM.md\n---\n"):
            with self.subTest(text=text), patch.object(client, "gh", return_value=text):
                with self.assertRaises(c.Invalid):
                    client.fetch_protocol(contract()["source"])


class PointerTests(unittest.TestCase):
    def setUp(self):
        self.contract = contract()

    def test_existing_instruction_bytes_round_trip(self):
        self.contract["bootstrap"]["agents_created"] = False
        self.contract = c.seal(self.contract)
        for original in (b"# Policy", b"# Policy\r\n\xff\n", b"Permanent Continuum hint\n\n"):
            data = c.append_pointer(original, c.pointer_data(self.contract))
            result, _ = c.remove_pointer(data, self.contract, True, True)
            self.assertEqual(result, original)

    def test_initial_creation_does_not_override_base_ownership(self):
        data = c.append_pointer(None, c.pointer_data(self.contract))
        self.assertIsNone(c.remove_pointer(data, self.contract, False, True)[0])
        self.assertEqual(c.remove_pointer(data, self.contract, True, True)[0], b"")
        permanent = b"# Added permanent instructions\n"
        self.assertEqual(c.remove_pointer(permanent + data, self.contract, True, True)[0], permanent)
        self.assertEqual(c.remove_pointer(data + b" \n", self.contract, False, True)[0], b" \n")

    def test_uncertain_malformed_foreign_and_duplicate_stop(self):
        data = c.append_pointer(None, c.pointer_data(self.contract))
        for altered in (data + data, data.replace(b"Discovery only", b"Authority"), data[1:], data.replace(self.contract["bootstrap"]["id"].encode(), c.new_id().encode())):
            with self.subTest(altered=altered[:80]), self.assertRaises(c.Invalid):
                c.remove_pointer(altered, self.contract, False, True)
        with self.assertRaises(c.Invalid):
            c.remove_pointer(data, self.contract, False, False)
        with self.assertRaises(c.Invalid):
            c.append_pointer(data, c.pointer_data(self.contract))

    def test_stale_pointer_has_no_authority(self):
        meta = c.pointer_data(self.contract)
        c.pointer_context(meta, meta["head"]["repository"], meta["head"]["ref"], self.contract)
        c.pointer_context(meta, meta["head"]["repository"], meta["head"]["ref"], bootstrap_run=meta["run"])
        for repo, ref, run in ((meta["target"]["repository"], meta["target"]["ref"], meta["run"]), (meta["head"]["repository"], "unrelated", meta["run"]), (meta["head"]["repository"], meta["head"]["ref"], None)):
            with self.assertRaises(c.Invalid):
                c.pointer_context(meta, repo, ref, bootstrap_run=run)


class StateTests(unittest.TestCase):
    def test_suspension_retains_owner_and_blocks_writes(self):
        events = []
        append(events, "claim")
        state = append(events, "suspend", details={"reason": "approval"})
        self.assertIsNotNone(state.active)
        with self.assertRaises(c.Invalid):
            c.replay(events + [event(state, "checkpoint")])
        with self.assertRaises(c.Invalid):
            c.replay(events + [event(state, "claim", run=REVIEW_RUN)])
        append(events, "resume", details={"acceptance": "human approved"})
        self.assertIsNone(append(events, "release").active)

    def test_two_claims_are_conflict_not_last_writer_wins(self):
        initial = c.State()
        first, second = event(initial, "claim"), event(initial, "claim", run=REVIEW_RUN)
        state = c.replay([first, second])
        self.assertTrue(state.conflict)
        self.assertEqual(state.frontier, {first["id"], second["id"]})
        recovery = event(state, "recover", kind="recovery", run=CLEAN_RUN, details={"human_confirmation": "Both runs stopped; unshared work inventoried"})
        recovered = c.replay([first, second, recovery])
        self.assertFalse(recovered.conflict)
        self.assertIsNone(recovered.active)
        recovery["prev"] = [first["id"]]
        with self.assertRaises(c.Invalid):
            c.replay([first, second, recovery])

    def test_repair_is_exclusive_and_cannot_implement(self):
        events = []
        append(events, "claim")
        repaired = c.readiness_tuple(c.seal(contract(), 2), "a" * 40, "b" * 40)
        details = {"raw_digest": "sha256:" + "c" * 64, "last_revision": 1, "acceptance": "accepted raw snapshot", "snapshot": repaired}
        state = append(events, "repair_enter", details=details)
        for action in ("checkpoint", "release", "verify"):
            with self.subTest(action=action), self.assertRaises(c.Invalid):
                c.replay(events + [event(state, action, kind="evidence" if action == "verify" else "write")])
        state = append(events, "repair_complete", value=repaired, details=details)
        self.assertEqual(state.mode, "active")
        self.assertIsNotNone(state.active)

    def test_suspended_writer_repair_resumes_only_repair_mode(self):
        events = []
        append(events, "claim")
        repaired = c.readiness_tuple(c.seal(contract(), 2), "a" * 40, "b" * 40)
        details = {"raw_digest": "sha256:" + "c" * 64, "last_revision": 1, "acceptance": "accepted snapshot", "snapshot": repaired}
        append(events, "repair_enter", details=details)
        append(events, "suspend", details={"reason": "body-edit approval"})
        resumed = event(c.replay(events), "resume", details={"acceptance": "approval granted"})
        resumed["tuple"] = None
        state = c.replay(events + [resumed])
        self.assertEqual(state.mode, "repair")
        self.assertIsNotNone(state.active["tuple"])
        with self.assertRaises(c.Invalid):
            c.replay(events + [resumed, event(state, "checkpoint")])

    def test_same_writer_run_cannot_claim_independent_review(self):
        events = ready_history()[:-1]
        with self.assertRaises(c.Invalid):
            append(events, "review", kind="evidence", details={"acceptance": "self-review", "independent_review": True})

    def test_cleanup_excludes_write_and_requires_current_review(self):
        events = ready_history()
        value = events[-1]["tuple"]
        state = c.replay(events)
        c.cleanup_gate(state, value, True, False)
        for changed in ({**value, "head_sha": "d" * 40}, {**value, "base_sha": "e" * 40}, {**value, "revision": 2}, {**value, "target": {**value["target"], "ref": "other"}}):
            with self.assertRaises(c.Invalid):
                c.cleanup_gate(state, changed, True, False)
        state = append(events, "claim", kind="cleanup", run=CLEAN_RUN)
        with self.assertRaises(c.Invalid):
            c.replay(events + [event(state, "claim")])
        self.assertIsNone(append(events, "cleanup_cancel", kind="cleanup", run=CLEAN_RUN, details={"reason": "PR returned to Draft"}).active)

    def test_review_requires_released_lease(self):
        events = []
        append(events, "claim")
        append(events, "verify", kind="evidence")
        state = append(events, "ready", kind="evidence")
        with self.assertRaises(c.Invalid):
            c.replay(events + [event(state, "review", kind="evidence", run=REVIEW_RUN, details={"independent_review": True, "acceptance": "review"})])

    def test_missing_predecessor_or_duplicate_event_fails(self):
        first = event(c.State(), "claim")
        with self.assertRaises(c.Invalid):
            c.replay([first, first])
        first["prev"] = [c.new_id()]
        with self.assertRaises(c.Invalid):
            c.replay([first])

    def test_harmless_base_revalidation_cannot_cover_material_changes(self):
        events = ready_history()
        state = c.replay(events)
        current = {**events[-1]["tuple"], "base_sha": "c" * 40}
        accepted = {"acceptance": "new base checked, no material effect", "independent_review": True}
        self.assertEqual(c.replay(events + [event(state, "revalidate", kind="evidence", run=REVIEW_RUN, value=current, details=accepted)]).evidence["review"], current)
        with self.assertRaises(c.Invalid):
            c.replay(events + [event(state, "revalidate", kind="evidence", value={**current, "head_sha": "d" * 40}, details=accepted)])


class GitIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.previous = Path.cwd()
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.bare = self.root / "head.git"
        subprocess.run(["git", "init", "--bare", str(self.bare)], check=True, capture_output=True)
        os.chdir(self.repo)
        self.g("init", "-b", "main")
        self.g("config", "user.name", "Test")
        self.g("config", "user.email", "test@example.com")
        self.g("config", "core.autocrlf", "false")
        (self.repo / "product.txt").write_text("base\n")
        self.g("add", "product.txt")
        self.g("commit", "-m", "test base")
        self.base = self.g("rev-parse", "HEAD")
        self.value = contract()
        self.value["target"]["sha"] = self.base
        self.value["head"]["ref"] = "continuum/test"
        self.value["bootstrap"]["agents_created"] = True
        self.g("switch", "-c", "continuum/test")
        data = c.append_pointer(None, c.pointer_data(self.value))
        (self.repo / "AGENTS.md").write_bytes(data)
        self.g("add", "AGENTS.md")
        self.g("commit", "-m", "chore: bootstrap pointer")
        self.boot = self.g("rev-parse", "HEAD")
        self.value["bootstrap"]["commit"] = self.boot
        self.value["bootstrap"]["pointer_digest"] = c.sha256(c.read_pointer(data)[2])
        self.value = c.seal(self.value)
        self.g("remote", "add", "fork", str(self.bare))
        self.g("push", "fork", "HEAD:refs/heads/continuum/test")
        self.events = ready_history(c.readiness_tuple(self.value, self.boot, self.base))
        self.draft = False
        self.open = True
        self.url = "https://github.com/upstream/project/pull/1"
        self.args = SimpleNamespace(pr=self.url, run=CLEAN_RUN, remote="fork", trusted_source=client.TRUSTED_SOURCE)
        self.patches = [patch.object(client, "snapshot", self.snapshot), patch.object(client, "post_event", self.post),
                        patch.object(client, "actor", return_value="agent"), patch.object(client, "push_url", return_value=str(self.bare)),
                        patch.object(client, "remote_agents", side_effect=lambda *_: self.base_agents),
                        patch.object(client, "assert_checks"), patch.object(client, "read_pr", side_effect=lambda *_: self.pr())]
        self.base_agents = None
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        os.chdir(self.previous)
        self.temporary.cleanup()

    def g(self, *args):
        return subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL, text=True).strip()

    def pr(self):
        sha = self.g("ls-remote", "--heads", str(self.bare), "refs/heads/" + self.value["head"]["ref"]).split()[0]
        return {"state": "open" if self.open else "closed", "draft": self.draft, "user": {"login": "agent"}, "body": self.body if hasattr(self, "body") else c.render(self.value), "checked_base_sha": self.base,
                "head": {"sha": sha, "ref": self.value["head"]["ref"], "repo": {"full_name": self.value["head"]["repository"]}},
                "base": {"ref": "main", "repo": {"full_name": self.value["target"]["repository"]}}}

    def snapshot(self, *_args, **_kwargs):
        value = c.section(self.pr()["body"])[3]
        if not _kwargs.get("allow_invalid", False):
            client.validate_current(value, c.replay(self.events), self.events)
        return self.pr(), value, list(self.events), c.replay(self.events)

    def post(self, _url, item, _events):
        self.events.append(item)
        return list(self.events), c.replay(self.events)

    def test_cleanup_removes_only_pointer_and_records_receipt(self):
        client.cleanup(self.args)
        self.assertFalse((self.repo / "AGENTS.md").exists())
        self.assertEqual(self.g("diff", "--name-only", self.boot, "HEAD"), "AGENTS.md")
        self.assertEqual(self.g("ls-remote", str(self.bare), "refs/heads/continuum/test").split()[0], self.g("rev-parse", "HEAD"))
        state = c.replay(self.events)
        self.assertIsNone(state.active)
        self.assertEqual(state.receipts[-1]["removal_commit"], self.g("rev-parse", "HEAD"))
        self.assertFalse(state.receipts[-1]["no_op"])

    def test_current_base_owned_empty_path_is_preserved(self):
        self.base_agents = b""
        client.cleanup(self.args)
        self.assertEqual((self.repo / "AGENTS.md").read_bytes(), b"")

    def test_added_permanent_content_survives(self):
        path = self.repo / "AGENTS.md"
        permanent = b"# Preserve me\r\n"
        path.write_bytes(permanent + path.read_bytes())
        self.g("add", "AGENTS.md")
        self.g("commit", "-m", "docs: permanent policy")
        self.g("push", "fork", "HEAD:refs/heads/continuum/test")
        self.events = ready_history(c.readiness_tuple(self.value, self.g("rev-parse", "HEAD"), self.base))
        client.cleanup(self.args)
        self.assertEqual(path.read_bytes(), permanent)

    def test_failed_push_retains_claim_and_retries_exact_commit(self):
        with patch.object(client, "push", side_effect=c.Invalid("offline")):
            with self.assertRaises(c.Invalid):
                client.cleanup(self.args)
        cleanup_sha = self.g("rev-parse", "HEAD")
        self.assertEqual(c.replay(self.events).active["kind"], "cleanup")
        client.cleanup(self.args)
        self.assertEqual(self.g("rev-parse", "HEAD"), cleanup_sha)
        self.assertIsNone(c.replay(self.events).active)

    def test_ambiguous_push_success_recovers_without_second_commit(self):
        actual_push = client.push
        def uncertain(*args):
            actual_push(*args)
            raise c.Invalid("response lost")
        with patch.object(client, "push", side_effect=uncertain):
            with self.assertRaises(c.Invalid):
                client.cleanup(self.args)
        cleanup_sha = self.g("rev-parse", "HEAD")
        with patch.object(client, "push", side_effect=AssertionError("must not push twice")):
            client.cleanup(self.args)
        self.assertEqual(self.g("rev-parse", "HEAD"), cleanup_sha)

    def new_ready_cycle(self):
        self.draft = True
        current = c.readiness_tuple(self.value, self.g("rev-parse", "HEAD"), self.base)
        append(self.events, "claim", value=current)
        (self.repo / "product.txt").write_text("review fix\n")
        self.g("add", "product.txt")
        self.g("commit", "-m", "fix: review feedback")
        self.g("push", "fork", "HEAD:refs/heads/continuum/test")
        self.value = c.seal({**self.value, "plan": ["Reviewed implementation complete"]}, 2)
        current = c.readiness_tuple(self.value, self.g("rev-parse", "HEAD"), self.base)
        append(self.events, "checkpoint", value=current)
        append(self.events, "verify", kind="evidence", value=current)
        append(self.events, "ready", kind="evidence", value=current)
        append(self.events, "release", value=current)
        self.draft = False
        append(self.events, "review", kind="evidence", run=REVIEW_RUN, value=current, details={"acceptance": "new independent review", "independent_review": True})

    def test_later_ready_cycle_uses_no_op_without_restoring_pointer(self):
        client.cleanup(self.args)
        self.new_ready_cycle()
        head = self.g("rev-parse", "HEAD")
        client.cleanup(self.args)
        self.assertEqual(self.g("rev-parse", "HEAD"), head)
        self.assertFalse((self.repo / "AGENTS.md").exists())
        receipt = c.replay(self.events).receipts[-1]
        self.assertTrue(receipt["no_op"])
        self.assertEqual(receipt["readiness"]["revision"], 2)
        self.assertNotEqual(receipt["readiness"]["head_sha"], receipt["removal_commit"])

    def test_unexplained_absence_is_not_cleanup(self):
        self.g("rm", "AGENTS.md")
        self.g("commit", "-m", "unexplained removal")
        self.g("push", "fork", "HEAD:refs/heads/continuum/test")
        self.events = ready_history(c.readiness_tuple(self.value, self.g("rev-parse", "HEAD"), self.base))
        with self.assertRaises(c.Invalid):
            client.cleanup(self.args)
        self.assertEqual(c.replay(self.events).active["kind"], "cleanup")

    def test_pointer_restore_remove_history_prevents_false_no_op(self):
        client.cleanup(self.args)
        (self.repo / "AGENTS.md").write_bytes(c.render_pointer(c.pointer_data(self.value)))
        self.g("add", "AGENTS.md")
        self.g("commit", "-m", "restore pointer without cleanup receipt")
        self.g("rm", "AGENTS.md")
        self.g("commit", "-m", "unexplained second removal")
        self.g("push", "fork", "HEAD:refs/heads/continuum/test")
        self.new_ready_cycle()
        with self.assertRaises(c.Invalid):
            client.cleanup(self.args)

    def test_draft_closed_retarget_and_dirty_stop_without_removal(self):
        for attribute in ("draft", "open"):
            setattr(self, attribute, attribute == "draft")
            with self.assertRaises(c.Invalid):
                client.cleanup(self.args)
            setattr(self, attribute, attribute == "open")
        (self.repo / "unrelated").write_text("user work")
        with self.assertRaises(c.Invalid):
            client.cleanup(self.args)
        self.assertTrue((self.repo / "AGENTS.md").exists())

    def test_origin_provenance_rejects_forged_creation(self):
        self.value["bootstrap"]["agents_created"] = False
        self.value = c.seal(self.value)
        with self.assertRaises(c.Invalid):
            client.origin_provenance(self.value)

    def damage_contract(self):
        self.body = "Introduction\n" + c.render(self.value).replace("Run focused checks", "Human accepted verification change") + "\nFooter\n"
        self.value = c.section(self.body)[3]
        return SimpleNamespace(pr=self.url, run=RUN, trusted_source=client.TRUSTED_SOURCE,
                               accepted_raw=c.sha256(c.section(self.body)[2].encode()), last_revision=1,
                               acceptance="Human accepted this exact content and all scope/pin decisions",
                               output=str(self.root / "repair.md"), apply=True, complete=False)

    def replace_body(self, _url, expected, replacement):
        self.assertEqual(self.pr()["body"], expected)
        self.body = replacement
        self.value = c.read_contract(replacement)

    def test_unleased_repair_validates_then_releases_claim(self):
        args = self.damage_contract()
        with patch.object(client, "write_body", self.replace_body):
            client.repair(args)
        state = c.replay(self.events)
        self.assertIsNone(state.active)
        self.assertEqual(state.evidence, {})
        self.assertEqual(c.read_contract(self.body)["revision"], 2)
        self.assertTrue(self.body.startswith("Introduction\n"))
        self.assertTrue(self.body.endswith("\nFooter\n"))

    def test_writer_repair_retains_implementation_lease(self):
        self.draft = True
        self.events = []
        append(self.events, "claim", value=c.readiness_tuple(self.value, self.boot, self.base))
        args = self.damage_contract()
        with patch.object(client, "write_body", self.replace_body):
            client.repair(args)
        state = c.replay(self.events)
        self.assertEqual(state.active["kind"], "write")
        self.assertEqual(state.mode, "active")
        self.assertEqual(state.active["tuple"]["revision"], 2)

    def test_complete_human_repair_handoff_requires_exact_replacement(self):
        args = self.damage_contract()
        args.apply = False
        client.repair(args)
        self.assertEqual(c.replay(self.events).mode, "repair")
        replacement = Path(args.output).read_bytes().decode()
        self.replace_body(self.url, self.body, replacement)
        args.complete = True
        client.repair(args)
        self.assertIsNone(c.replay(self.events).active)

    def test_changed_snapshot_during_repair_preserves_claim(self):
        args = self.damage_contract()
        def competing_edit(url, item, events):
            result = self.post(url, item, events)
            if item["action"] == "claim":
                self.body = self.body.replace("Human accepted", "Unexpected human edit")
            return result
        with patch.object(client, "post_event", competing_edit), patch.object(client, "write_body", side_effect=AssertionError("must not overwrite changed body")):
            with self.assertRaises(c.Invalid):
                client.repair(args)
        self.assertEqual(c.replay(self.events).active["kind"], "repair")
        self.assertIn("Unexpected human edit", self.body)

    def test_suspended_invalid_digest_repair_can_resume(self):
        args = self.damage_contract()
        args.apply = False
        client.repair(args)
        append(self.events, "suspend", kind="repair", details={"reason": "body edit approval"})
        details = self.root / "resume.json"
        details.write_text(json.dumps({"acceptance": "human approval granted"}))
        client.record(SimpleNamespace(pr=self.url, run=RUN, action="resume", details=str(details), trusted_source=client.TRUSTED_SOURCE))
        self.assertEqual(c.replay(self.events).mode, "repair")
        args.apply = True
        with patch.object(client, "write_body", self.replace_body):
            client.repair(args)
        self.assertIsNone(c.replay(self.events).active)

    def test_repair_handoff_cannot_overwrite_product_file(self):
        args = self.damage_contract()
        args.output = str(self.repo / "product.txt")
        with self.assertRaises(c.Invalid):
            client.repair(args)
        self.assertEqual((self.repo / "product.txt").read_text(), "base\n")
        self.assertIsNone(c.replay(self.events).active)

    def test_valid_digest_cannot_hide_revision_rollback(self):
        accepted = c.seal(self.value, 2)
        self.events = ready_history(c.readiness_tuple(accepted, self.boot, self.base))
        with self.assertRaises(c.Invalid):
            self.snapshot()
        args = SimpleNamespace(pr=self.url, run=RUN, trusted_source=client.TRUSTED_SOURCE,
                               accepted_raw=c.sha256(c.section(c.render(self.value))[2].encode()), last_revision=2,
                               acceptance="Human accepted exact restored content against revision 2", output=str(self.root / "repair.md"), apply=True, complete=False)
        with patch.object(client, "write_body", self.replace_body):
            client.repair(args)
        self.assertEqual(self.value["revision"], 3)

    def test_human_recomputed_digest_still_needs_a_new_revision(self):
        self.value = c.seal({**self.value, "plan": ["Human updated plan without advancing revision"]})
        with self.assertRaises(c.Invalid):
            self.snapshot()

    def bootstrap_journal(self):
        self.draft, self.events = True, []
        journal = {"run": RUN, "actor": "agent", "remote": "fork", "title": "Test bootstrap", "accepted_policy": "human decision",
                   "contract": self.value, "commit": self.boot}
        args = SimpleNamespace(remote="fork", journal=str(self.root / "bootstrap.json"), trusted_source=client.TRUSTED_SOURCE,
                               resume=True, run=RUN, recovery_authority=None)
        client.journal_write(args.journal, journal, initial=True)
        return args, journal

    def test_bootstrap_existing_pr_is_verified_without_duplicate_creation(self):
        args, journal = self.bootstrap_journal()
        response = {**self.pr(), "html_url": self.url}
        with patch.object(client, "fetch_protocol"), patch.object(client, "api", return_value=[[response]]) as call, \
             patch.object(client, "bootstrap_labels") as labels:
            client.finish_bootstrap(args, journal)
        self.assertEqual(call.call_count, 1)
        labels.assert_called_once_with(args, journal)
        self.assertEqual(self.g("rev-parse", "HEAD"), self.boot)
        self.assertEqual(json.loads(Path(args.journal).read_text())["pr"], self.url)

    def test_uncertain_bootstrap_creation_retries_same_commit_only(self):
        args, journal = self.bootstrap_journal()
        response = {**self.pr(), "html_url": self.url}
        lookups = 0
        def responses(path, *_args):
            nonlocal lookups
            if "/pulls?" in path:
                lookups += 1
                return [[]] if lookups == 1 else [[response]]
            return {"object": {"sha": self.base}}
        original_run = subprocess.run
        mutations = []
        def uncertain(argv, **kwargs):
            if argv[0] == "gh":
                mutations.append(json.loads(kwargs["input"]))
                return subprocess.CompletedProcess(argv, 1, stdout="", stderr="response lost")
            return original_run(argv, **kwargs)
        with patch.object(client, "fetch_protocol"), patch.object(client, "api", side_effect=responses), \
             patch.object(client.subprocess, "run", side_effect=uncertain), patch.object(client, "bootstrap_labels") as labels:
            with self.assertRaises(c.Invalid):
                client.finish_bootstrap(args, journal)
            client.finish_bootstrap(args, journal)
        self.assertEqual(len(mutations), 1)
        labels.assert_called_once_with(args, journal)
        self.assertTrue(mutations[0]["draft"])
        self.assertEqual(mutations[0]["head_repo"], "fork")
        self.assertEqual(mutations[0]["head"], "writer:continuum/test")
        self.assertEqual(self.g("rev-parse", "HEAD"), self.boot)

    def test_terminated_bootstrap_requires_explicit_human_recovery(self):
        args, _ = self.bootstrap_journal()
        args.run = REVIEW_RUN
        with self.assertRaises(c.Invalid):
            client.bootstrap(args)
        self.assertEqual(self.g("rev-parse", "HEAD"), self.boot)

    def test_complete_bootstrap_pins_once_and_pushes_only_fork(self):
        self.complete_stable_bootstrap("v0.4.0")

    def test_complete_bootstrap_accepts_unprefixed_stable_tag(self):
        self.complete_stable_bootstrap("0.4.0")

    def complete_stable_bootstrap(self, tag):
        base_transport = self.root / "base.git"
        subprocess.run(["git", "init", "--bare", str(base_transport)], check=True, capture_output=True)
        self.g("push", str(base_transport), "main:refs/heads/main")
        plan_path = self.root / "plan.json"
        plan_path.write_text(json.dumps({k: self.value[k] for k in ("goal", "scope", "acceptance", "plan", "verification", "changes", "context")}))
        args = SimpleNamespace(resume=False, start_now=True, accepted_policy="adopted base policy", repo="upstream/project", head_repo="writer/fork",
                               base="main", branch="continuum/new", plan=str(plan_path), title="Start implementation", run=RUN, remote="fork",
                               source_commit=None, development_source=False, trusted_source=client.TRUSTED_SOURCE,
                               journal=str(self.root / "new-bootstrap.json"), recovery_authority=None)
        calls, mutations = [], []
        def responses(path, *_args):
            calls.append(path)
            if path == "repos/upstream/project":
                return {"full_name": "upstream/project", "permissions": {"push": False}}
            if "/labels?" in path:
                return [[{"name": "continuum"}]]
            if path == "repos/upstream/project/pulls/1":
                return {"state": "open", "labels": []}
            if path == "repos/upstream/project/issues/1/labels":
                return [{"name": "continuum"}]
            if path == "repos/writer/fork":
                return {"full_name": "writer/fork", "permissions": {"push": True}}
            if "/git/ref/" in path:
                return {"object": {"sha": self.base}}
            if path.endswith("/releases/latest"):
                return {"draft": False, "prerelease": False, "tag_name": tag}
            if "/commits/" in path:
                return {"sha": "e" * 40}
            if "/pulls?" in path:
                return [[]]
            raise AssertionError("unexpected remote API " + path)
        original_git, original_run = client.git, subprocess.run
        def local_fetch(*argv):
            if argv[0] == "fetch":
                argv = (*argv[:2], str(base_transport), *argv[3:])
            return original_git(*argv)
        def create(argv, **kwargs):
            if argv[0] == "gh":
                payload = json.loads(kwargs["input"])
                mutations.append(payload)
                self.body, self.value = payload["body"], c.read_contract(payload["body"])
                return subprocess.CompletedProcess(argv, 0, stdout=json.dumps({"html_url": self.url}), stderr="")
            return original_run(argv, **kwargs)
        self.draft, self.events = True, []
        with patch.object(client, "api", side_effect=responses), patch.object(client, "fetch_protocol") as pin, \
             patch.object(client, "parent_guard"), patch.object(client, "git", side_effect=local_fetch), \
             patch.object(client.subprocess, "run", side_effect=create):
            client.bootstrap(args)
        self.assertEqual(calls.count("repos/Leftium/continuum/releases/latest"), 1)
        self.assertEqual(calls.count("repos/Leftium/continuum/commits/" + tag), 1)
        self.assertEqual(self.value["source"]["commit"], "e" * 40)
        self.assertEqual(json.loads(Path(args.journal).read_text())["contract"]["source"], self.value["source"])
        self.assertTrue(all(call.args[0]["commit"] == "e" * 40 for call in pin.call_args_list))
        self.assertEqual(len(mutations), 1)
        self.assertTrue(mutations[0]["draft"])
        self.assertEqual(mutations[0]["head"], "writer:continuum/new")
        self.assertEqual(self.g("diff", "--name-only", self.base, "HEAD"), "AGENTS.md")
        self.assertFalse((self.repo / "CONTINUUM.md").exists())
        self.assertFalse((self.repo / "PR-PLAN.md").exists())
        self.assertEqual(self.g("ls-remote", str(base_transport), "refs/heads/main").split()[0], self.base)
        self.assertTrue(client.origin_provenance(self.value))

    def test_bootstrap_rejects_unpublished_or_unsupported_stable_source(self):
        args = SimpleNamespace(resume=False, start_now=True, accepted_policy="adopted", repo="upstream/project", head_repo="writer/fork",
                               base="main", branch="continuum/fresh", plan="/outside/plan.json", title="Start", run=RUN, remote="fork",
                               source_commit=None, development_source=False, trusted_source=client.TRUSTED_SOURCE)
        cases = [
            c.Invalid("no published release"),
            {"draft": True, "prerelease": False, "tag_name": "v0.4.0"},
            {"draft": False, "prerelease": True, "tag_name": "v0.4.0"},
            {"draft": False, "prerelease": False, "tag_name": "v0.3.0"},
            {"draft": False, "prerelease": False, "tag_name": "v0.4.1"},
            {"draft": False, "prerelease": False, "tag_name": "main"},
        ]
        for release in cases:
            calls = []
            def responses(path):
                calls.append(path)
                if path.endswith("/releases/latest"):
                    if isinstance(release, Exception):
                        raise release
                    return release
                if "/git/ref/" in path:
                    return {"object": {"sha": self.base}}
                if path in ("repos/upstream/project", "repos/writer/fork"):
                    return {"full_name": path[6:], "permissions": {"push": True}}
                raise AssertionError("unexpected source fallback or mutation: " + path)
            with self.subTest(release=release), patch.object(client, "api", side_effect=responses), \
                 patch.object(client, "parent_guard"), patch.object(client, "fetch_protocol") as fetch, \
                 patch.object(client, "journal_write") as journal, patch.object(client, "push") as push:
                with self.assertRaises(c.Invalid):
                    client.bootstrap(args)
                fetch.assert_not_called()
                journal.assert_not_called()
                push.assert_not_called()
            self.assertEqual(calls.count("repos/Leftium/continuum/releases/latest"), 1)
            self.assertEqual(self.g("rev-parse", "HEAD"), self.boot)
            self.assertEqual(self.g("status", "--porcelain"), "")

    def test_bootstrap_does_not_activate_installed_legacy_base(self):
        args = SimpleNamespace(resume=False, start_now=True, accepted_policy="adopted", repo="upstream/project", head_repo="writer/fork",
                               base="main", branch="continuum/fresh", plan="/outside/plan.json", title="Start", run=RUN, remote="fork")
        def responses(path):
            return {"object": {"sha": self.base}} if "/git/ref/" in path else {"full_name": path[6:], "permissions": {"push": True}}
        with patch.object(client, "remote_sha", return_value=None), patch.object(client, "api", side_effect=responses), \
             patch.object(client, "parent_guard"), patch.object(client, "remote_agents", return_value=b"<!-- leftium:continuum:start -->"):
            with self.assertRaisesRegex(c.Invalid, "still installed 0.3"):
                client.bootstrap(args)
        self.assertEqual(self.g("branch", "--show-current"), "continuum/test")

    def test_cleanup_preserves_staged_user_work(self):
        (self.repo / "product.txt").write_text("staged user change\n")
        self.g("add", "product.txt")
        before = self.g("diff", "--staged")
        with self.assertRaises(c.Invalid):
            client.cleanup(self.args)
        self.assertEqual(self.g("diff", "--staged"), before)
        self.assertTrue((self.repo / "AGENTS.md").exists())

    def test_ignored_local_agents_cannot_hide_stale_state_from_no_op(self):
        client.cleanup(self.args)
        self.new_ready_cycle()
        (self.repo / ".git/info/exclude").write_text("AGENTS.md\n")
        local = b"Private untracked instructions\n" + c.render_pointer(c.pointer_data(self.value))
        (self.repo / "AGENTS.md").write_bytes(local)
        self.assertEqual(self.g("status", "--porcelain"), "")
        with self.assertRaises(c.Invalid):
            client.cleanup(self.args)
        self.assertEqual((self.repo / "AGENTS.md").read_bytes(), local)
        self.assertIsNone(c.replay(self.events).active)

    def test_target_identity_change_stops_every_phase(self):
        pr = self.pr()
        pr["base"]["ref"] = "other"
        with self.assertRaises(c.Invalid):
            client.live_tuple(pr, self.value)
        pr = self.pr()
        pr["head"]["repo"]["full_name"] = "another/fork"
        with self.assertRaises(c.Invalid):
            client.live_tuple(pr, self.value)

    def test_failed_cleanup_then_remote_advancement_never_overwrites(self):
        with patch.object(client, "push", side_effect=c.Invalid("offline")):
            with self.assertRaises(c.Invalid):
                client.cleanup(self.args)
        local = self.g("rev-parse", "HEAD")
        actual_pr = self.pr
        def advanced():
            pr = actual_pr()
            pr["head"]["sha"] = "f" * 40
            return pr
        with patch.object(self, "pr", advanced), patch.object(client, "push", side_effect=AssertionError("must not overwrite")):
            with self.assertRaises(c.Invalid):
                client.cleanup(self.args)
        self.assertEqual(self.g("rev-parse", "HEAD"), local)
        self.assertEqual(c.replay(self.events).active["kind"], "cleanup")


class AdapterTests(unittest.TestCase):
    def test_deferred_planning_never_starts_a_branch(self):
        args = SimpleNamespace(resume=False, start_now=False)
        with patch.object(client, "git") as call:
            with self.assertRaises(c.Invalid):
                client.bootstrap(args)
            call.assert_not_called()
    def test_source_trust_and_no_mutable_fallback(self):
        source = contract()["source"]
        with patch.object(client, "gh", return_value="---\ncontinuum: 0.4.0\nartifact: protocol/CONTINUUM.md\n---\n") as mock:
            client.fetch_protocol(source)
            self.assertIn(source["commit"], mock.call_args.args[1])
            foreign = {**source, "repository": "stranger/protocol"}
            with self.assertRaises(c.Invalid):
                client.fetch_protocol(foreign)
            self.assertEqual(mock.call_count, 1)
        with patch.object(client, "gh", return_value="0.3 or error response") as mock:
            with self.assertRaises(c.Invalid):
                client.fetch_protocol(source)
            self.assertEqual(mock.call_count, 1)

    def test_remote_identity_supports_forks_but_not_redirects(self):
        for url in ("https://github.com/writer/fork.git", "git@github.com:writer/fork.git", "ssh://git@github.com/writer/fork.git"):
            self.assertEqual(client.remote_repository(url), "writer/fork")
        for url in ("https://evil.example/writer/fork.git", "https://token@github.com/writer/fork.git", "/tmp/fork"):
            with self.assertRaises(c.Invalid):
                client.remote_repository(url)

    def test_parent_guard_checks_cleaned_closed_upstream_parent(self):
        result = {"data": {"repository": {"ref": {"associatedPullRequests": {"pageInfo": {"hasNextPage": False}, "nodes": [
            {"url": "https://github.com/upstream/project/pull/2", "body": c.render(contract()), "merged": False,
             "headRefName": "parent", "headRepository": {"nameWithOwner": "writer/fork"}}
        ]}}}}}
        with patch.object(client, "api", return_value=result):
            with self.assertRaises(c.Invalid):
                client.parent_guard("writer/fork", "parent")
            result["data"]["repository"]["ref"]["associatedPullRequests"]["nodes"][0]["merged"] = True
            client.parent_guard("writer/fork", "parent")
        with patch.object(client, "api", return_value={"errors": ["forbidden"]}):
            with self.assertRaises(c.Invalid):
                client.parent_guard("writer/fork", "parent")


if __name__ == "__main__":
    unittest.main()
