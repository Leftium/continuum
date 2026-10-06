"""Offline conformance and temporary-Git integration tests. No live GitHub writes."""

import copy
import hashlib
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
        sha = self.g("ls-remote", "--heads", str(self.bare), "refs/heads/continuum/test").split()[0]
        return {"state": "open" if self.open else "closed", "draft": self.draft, "body": c.render(self.value), "checked_base_sha": self.base,
                "head": {"sha": sha, "ref": "continuum/test", "repo": {"full_name": self.value["head"]["repository"]}},
                "base": {"ref": "main", "repo": {"full_name": self.value["target"]["repository"]}}}

    def snapshot(self, *_args, **_kwargs):
        return self.pr(), self.value, list(self.events), c.replay(self.events)

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


class AdapterTests(unittest.TestCase):
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
