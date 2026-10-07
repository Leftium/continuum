"""Offline conformance tests; no live GitHub writes."""

from pathlib import Path
import json
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import continuum_core as c
import continuum as client

RUN = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"
OWNER = {"author": "leftium", "author_association": "OWNER"}
MEMBER = {"author": "writer", "author_association": "MEMBER"}


def record(text, **meta):
    return {**meta, "body": text}


class LeaseRecordTests(unittest.TestCase):
    def test_claim_and_release_have_one_visible_compact_record(self):
        claim = c.render("claim", RUN)
        release = c.render("release", RUN, sha="a" * 40)
        self.assertEqual(claim, f"```continuum\nclaim {RUN}\n```")
        self.assertEqual(release, f"```continuum\nrelease {RUN} {'a' * 40}\n```")
        self.assertEqual(len(claim), 59)
        self.assertEqual(len(release), 102)
        recovery = c.render_recovery("Owner confirms all runs stopped; unshared work was inventoried")
        self.assertIn("recover |", recovery)

    def test_unrelated_comments_do_not_change_lease_state(self):
        self.assertEqual(c.reconstruct([record("ordinary discussion")]).active, {})

    def test_claim_release_clears_only_matching_run_and_keeps_exact_sha(self):
        comments = [record(c.render("claim", RUN), **MEMBER),
                    record(c.render("release", RUN, sha="a" * 40), **MEMBER)]
        state = c.reconstruct(comments)
        self.assertFalse(state.conflict)
        self.assertEqual(state.active, {})

    def test_wrong_run_release_does_not_clear_claim(self):
        comments = [record(c.render("claim", RUN), **MEMBER),
                    record(c.render("release", OTHER, sha="a" * 40), **MEMBER)]
        state = c.reconstruct(comments)
        self.assertTrue(state.conflict)
        self.assertEqual(set(state.active), {RUN})

    def test_competing_live_claims_block_even_after_one_release(self):
        comments = [record(c.render("claim", RUN), **MEMBER),
                    record(c.render("claim", OTHER), **OWNER),
                    record(c.render("release", RUN, sha="a" * 40), **MEMBER)]
        state = c.reconstruct(comments)
        self.assertTrue(state.conflict)
        self.assertEqual(set(state.active), {RUN, OTHER})

    def test_owner_recovery_is_unconditional_reset(self):
        comments = [record(c.render("claim", RUN), **MEMBER),
                    record(c.render("claim", OTHER), **OWNER),
                    record(c.render_recovery("Both runs stopped; unshared work inventoried"), **OWNER)]
        state = c.reconstruct(comments)
        self.assertFalse(state.conflict)
        self.assertEqual(state.active, {})
        incomplete = comments[:-1] + [record(c.render_recovery("Only one run stopped; owner resets all leases"), **OWNER)]
        self.assertEqual(c.reconstruct(incomplete).active, {})

    def test_recovery_boundary_resets_history_before_compact_reconstruction(self):
        recovery = record(c.render_recovery("All runs stopped; work inventoried"), **OWNER)
        later_claim = record(c.render("claim", OTHER), **MEMBER)
        state = c.reconstruct([recovery, later_claim], recovery_boundary=True)
        self.assertFalse(state.conflict)
        self.assertEqual(set(state.active), {OTHER})

    def test_client_stops_pagination_at_latest_recovery(self):
        recovery = {"body": c.render_recovery("All runs stopped; work inventoried"),
                    "user": {"login": "leftium"}, "author_association": "OWNER"}
        claim = {"body": c.render("claim", OTHER), "user": {"login": "writer"},
                 "author_association": "MEMBER"}
        with patch.object(client, "command", return_value=json.dumps([claim, recovery])) as command:
            comments, boundary = client.read_comments("owner/project", 42, "author")
        self.assertTrue(boundary)
        self.assertEqual([item["body"] for item in comments], [recovery["body"], claim["body"]])
        command.assert_called_once()

    def test_only_repository_owner_can_recover(self):
        text = c.render_recovery("All runs stopped; work inventoried")
        with self.assertRaises(c.Invalid):
            c.parse_comment(text, "writer", "MEMBER")

    def test_malformed_duplicate_or_unknown_records_fail_closed(self):
        for text in ("```continuum\nclaim nope\n```",
                     c.render("claim", RUN) + "\n" + c.render("claim", OTHER),
                     "```continuum\nverify " + RUN + "\n```",
                     "```continuum\nrelease " + RUN + " " + "A" * 40 + "\n```",
                     "Lease claimed:\n" + c.render("claim", RUN)):
            with self.subTest(text=text), self.assertRaises(c.Invalid):
                c.parse_comment(text, "writer", "MEMBER", "writer")

    def test_untrusted_claim_fails_closed(self):
        with self.assertRaises(c.Invalid):
            c.parse_comment(c.render("claim", RUN), "stranger", "NONE", "pr-author")

    def test_run_ids_cannot_be_reused(self):
        comments = [record(c.render("claim", RUN), **MEMBER),
                    record(c.render("release", RUN, sha="a" * 40), **MEMBER),
                    record(c.render("claim", RUN), **MEMBER)]
        with self.assertRaises(c.Invalid):
            c.reconstruct(comments)

    def test_recovery_needs_single_line_confirmation_and_fresh_identity(self):
        for text in ("", "two\nlines", "carriage\rreturn", "contains | delimiter", "```continuum"):
            with self.subTest(text=text), self.assertRaises(c.Invalid):
                c.render_recovery(text)
        with self.assertRaises(c.Invalid):
            c.render("claim", "not-a-uuid")


if __name__ == "__main__":
    unittest.main()
