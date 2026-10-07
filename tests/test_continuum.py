"""Offline conformance tests; no live GitHub writes."""

from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO
import json
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import continuum_core as c
import continuum as client

CLAIM = "6028454738"
OTHER = "6028454739"
OWNER = {"author": "leftium", "author_association": "OWNER"}
MEMBER = {"author": "writer", "author_association": "MEMBER"}
SHA = "a" * 40


def record(text, comment_id=None, **meta):
    return {**meta, "id": comment_id, "body": text}


class LeaseRecordTests(unittest.TestCase):
    def test_records_are_exact_whole_comment_text(self):
        self.assertEqual(c.render("claim"), "claim")
        self.assertEqual(c.render("release", CLAIM, sha=SHA), f"release {CLAIM} {SHA}")
        self.assertEqual(c.render_recovery("All writers stopped; work inventoried"),
                         "recover | All writers stopped; work inventoried")

    def test_unrelated_or_nonmatching_comments_do_not_change_state(self):
        comments = [record("ordinary discussion", **MEMBER),
                    record("claim with extra text", CLAIM, **MEMBER),
                    record("```continuum\\nclaim\\n```", OTHER, **MEMBER)]
        self.assertEqual(c.reconstruct(comments).active, {})

    def test_claim_release_uses_comment_id_and_keeps_full_sha(self):
        comments = [record("claim", CLAIM, **MEMBER),
                    record(f"release {CLAIM} {SHA}", OTHER, **MEMBER)]
        state = c.reconstruct(comments)
        self.assertFalse(state.conflict)
        self.assertEqual(state.active, {})
        self.assertEqual(c.parse_comment(f"release {CLAIM} {SHA}", "writer", "MEMBER"),
                         {"action": "release", "claim_id": CLAIM, "sha": SHA})

    def test_stale_release_does_not_clear_newer_claim(self):
        comments = [record("claim", CLAIM, **MEMBER),
                    record(f"release {CLAIM} {SHA}", OTHER, **MEMBER),
                    record("claim", OTHER, **MEMBER),
                    record(f"release {CLAIM} {SHA}", "6028454740", **MEMBER)]
        state = c.reconstruct(comments)
        self.assertTrue(state.conflict)
        self.assertEqual(set(state.active), {OTHER})

    def test_stale_release_after_recovery_does_not_clear_new_claim(self):
        comments = [record("claim", CLAIM, **MEMBER),
                    record("recover | All writers stopped; old work inventoried", OTHER, **OWNER),
                    record("claim", OTHER, **MEMBER),
                    record(f"release {CLAIM} {SHA}", "6028454740", **MEMBER)]
        state = c.reconstruct(comments)
        self.assertTrue(state.conflict)
        self.assertEqual(set(state.active), {OTHER})

    def test_competing_live_claims_block_release(self):
        comments = [record("claim", CLAIM, **MEMBER), record("claim", OTHER, **OWNER),
                    record(f"release {CLAIM} {SHA}", "6028454740", **MEMBER)]
        state = c.reconstruct(comments)
        self.assertTrue(state.conflict)
        self.assertEqual(set(state.active), {CLAIM, OTHER})

    def test_owner_recovery_clears_all_active_claims_and_conflict(self):
        comments = [record("claim", CLAIM, **MEMBER), record("claim", OTHER, **OWNER),
                    record("recover | Both writers stopped; unshared work inventoried", "6028454740", **OWNER)]
        state = c.reconstruct(comments)
        self.assertFalse(state.conflict)
        self.assertEqual(state.active, {})

    def test_client_stops_pagination_at_latest_recovery_and_preserves_comment_ids(self):
        recovery = {"id": 8, "body": "recover | All writers stopped; work inventoried",
                    "user": {"login": "leftium"}, "author_association": "OWNER"}
        claim = {"id": 9, "body": "claim", "user": {"login": "writer"},
                 "author_association": "MEMBER"}
        with patch.object(client, "command", return_value=json.dumps([claim, recovery])) as command:
            comments = client.read_comments("owner/project", 42, "author")
        self.assertEqual([item["id"] for item in comments], [8, 9])
        self.assertEqual(comments[0]["body"], recovery["body"])
        command.assert_called_once()

    def test_only_repository_owner_can_recover(self):
        with self.assertRaises(c.Invalid):
            c.parse_comment("recover | All writers stopped; work inventoried", "writer", "MEMBER")

    def test_untrusted_valid_claim_fails_closed(self):
        with self.assertRaises(c.Invalid):
            c.parse_comment("claim", "stranger", "NONE", "pr-author", CLAIM)

    def test_invalid_ids_and_shas_are_ordinary_comments(self):
        for text in ("release 0 " + SHA, "release " + CLAIM + " " + "A" * 40,
                     "claim ", "claim\\nextra", "recover | "):
            with self.subTest(text=text):
                self.assertIsNone(c.parse_comment(text, "writer", "MEMBER", "writer", CLAIM))

    def test_command_line_uses_claim_id(self):
        with patch.object(sys, "argv", ["continuum.py", "release", "--pr", "url", "--claim", CLAIM]):
            # Parsing succeeds and dispatch is reached; live state access is mocked.
            with patch.object(client, "release", side_effect=RuntimeError("dispatched")):
                with self.assertRaises(RuntimeError):
                    client.main()

    def test_claim_prints_created_github_comment_id(self):
        args = type("Args", (), {"pr": "https://github.com/owner/project/pull/42"})()
        pr = {"state": "open", "draft": True}
        output = StringIO()
        with patch.object(client, "state_for", return_value=("owner/project", 42, pr, c.State())), \
                patch.object(client, "post", return_value={"id": int(CLAIM)}) as post, \
                patch.object(client, "assert_posted") as verify, redirect_stdout(output):
            client.claim(args)
        self.assertEqual(output.getvalue(), CLAIM + "\n")
        post.assert_called_once_with("owner/project", 42, "claim")
        verify.assert_called_once_with(args, claim_id=CLAIM)


if __name__ == "__main__":
    unittest.main()
