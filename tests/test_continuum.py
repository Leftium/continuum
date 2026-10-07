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
        self.assertEqual(c.render("claim"), "This PR was claimed")
        self.assertEqual(c.render("release", CLAIM, sha=SHA), f"This PR's claim {CLAIM} was released at {SHA}")
        self.assertEqual(c.render_recovery("All writers stopped; work inventoried"),
                         "This PR was recovered | All writers stopped; work inventoried")

    def test_unrelated_or_nonmatching_comments_do_not_change_state(self):
        comments = [record("ordinary discussion", **MEMBER),
                    record("claim with extra text", CLAIM, **MEMBER),
                    record("```continuum\\nclaim\\n```", OTHER, **MEMBER)]
        self.assertEqual(c.reconstruct(comments).active, {})

    def test_bootstrap_and_planning_can_have_zero_coordination_comments(self):
        state = c.reconstruct([])
        self.assertFalse(state.conflict)
        self.assertEqual(state.active, {})

    def test_leading_release_conflicts_and_writer_handoff_needs_fresh_claim(self):
        leading = c.reconstruct([record(f"This PR's claim {CLAIM} was released at {SHA}", OTHER, **MEMBER)])
        self.assertTrue(leading.conflict)
        self.assertEqual(leading.active, {})

        handed_off = c.reconstruct([
            record("This PR was claimed", CLAIM, **MEMBER),
            record(f"This PR's claim {CLAIM} was released at {SHA}", OTHER, **MEMBER),
            record("This PR was claimed", OTHER, **OWNER),
        ])
        self.assertFalse(handed_off.conflict)
        self.assertEqual(set(handed_off.active), {OTHER})

    def test_claim_release_uses_comment_id_and_keeps_full_sha(self):
        comments = [record("This PR was claimed", CLAIM, **MEMBER),
                    record(f"This PR's claim {CLAIM} was released at {SHA}", OTHER, **MEMBER)]
        state = c.reconstruct(comments)
        self.assertFalse(state.conflict)
        self.assertEqual(state.active, {})
        self.assertEqual(c.parse_comment(f"This PR's claim {CLAIM} was released at {SHA}", "writer", "MEMBER"),
                         {"action": "release", "claim_id": CLAIM, "sha": SHA})

    def test_stale_release_does_not_clear_newer_claim(self):
        comments = [record("This PR was claimed", CLAIM, **MEMBER),
                    record(f"This PR's claim {CLAIM} was released at {SHA}", OTHER, **MEMBER),
                    record("This PR was claimed", OTHER, **MEMBER),
                    record(f"This PR's claim {CLAIM} was released at {SHA}", "6028454740", **MEMBER)]
        state = c.reconstruct(comments)
        self.assertTrue(state.conflict)
        self.assertEqual(set(state.active), {OTHER})

    def test_stale_release_after_recovery_does_not_clear_new_claim(self):
        comments = [record("This PR was claimed", CLAIM, **MEMBER),
                    record("This PR was recovered | All writers stopped; old work inventoried", OTHER, **OWNER),
                    record("This PR was claimed", OTHER, **MEMBER),
                    record(f"This PR's claim {CLAIM} was released at {SHA}", "6028454740", **MEMBER)]
        state = c.reconstruct(comments)
        self.assertTrue(state.conflict)
        self.assertEqual(set(state.active), {OTHER})

    def test_competing_live_claims_block_release(self):
        comments = [record("This PR was claimed", CLAIM, **MEMBER), record("This PR was claimed", OTHER, **OWNER),
                    record(f"This PR's claim {CLAIM} was released at {SHA}", "6028454740", **MEMBER)]
        state = c.reconstruct(comments)
        self.assertTrue(state.conflict)
        self.assertEqual(set(state.active), {CLAIM, OTHER})

    def test_owner_recovery_clears_all_active_claims_and_conflict(self):
        comments = [record("This PR was claimed", CLAIM, **MEMBER), record("This PR was claimed", OTHER, **OWNER),
                    record("This PR was recovered | Both writers stopped; unshared work inventoried", "6028454740", **OWNER)]
        state = c.reconstruct(comments)
        self.assertFalse(state.conflict)
        self.assertEqual(state.active, {})

    def test_client_keeps_comments_after_latest_recovery_in_api_order(self):
        for version in ("0.6.0", "0.6.1", "0.6.2"):
            with self.subTest(version=version):
                recovery = {"id": 8, "body": c.render_recovery("All writers stopped; work inventoried", version=version),
                            "user": {"login": "leftium"}, "author_association": "OWNER"}
                claim = {"id": 9, "body": c.render("claim", version=version), "user": {"login": "writer"},
                         "author_association": "MEMBER"}
                before = {"id": 7, "body": c.render("claim", version=version), "user": {"login": "writer"},
                          "author_association": "MEMBER"}
                with patch.object(client, "command", side_effect=[json.dumps([before, recovery, claim]), "[]"]) as command:
                    comments = client.read_comments("owner/project", 42, version=version)
                self.assertEqual([item["id"] for item in comments], [8, 9])
                self.assertEqual(comments[0]["body"], recovery["body"])
                self.assertEqual(command.call_count, 2)

    def test_only_repository_owner_can_recover(self):
        with self.assertRaises(c.Invalid):
            c.parse_comment("This PR was recovered | All writers stopped; work inventoried", "writer", "MEMBER")

    def test_untrusted_valid_claim_fails_closed(self):
        with self.assertRaises(c.Invalid):
            c.parse_comment("This PR was claimed", "stranger", "NONE", "pr-author", CLAIM)

    def test_invalid_ids_and_shas_are_ordinary_comments(self):
        for text in ("This PR's claim 0 was released at " + SHA, "This PR's claim " + CLAIM + " was released at " + "A" * 40,
                     "This PR was claimed ", "This PR was claimed\\nextra", "This PR was recovered | "):
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
        post.assert_called_once_with("owner/project", 42, "This PR was claimed")
        verify.assert_called_once_with(args, claim_id=CLAIM)

    def test_release_uses_matching_clean_head_without_branch_name_check(self):
        for version in ("0.6.0", "0.6.1", "0.6.2"):
            with self.subTest(version=version):
                args = type("Args", (), {"pr": "https://github.com/owner/project/pull/42", "claim": CLAIM})()
                active = c.State(active={CLAIM: {"action": "claim", "claim_id": CLAIM}}, version=version)
                settled = c.State()
                pr = {"state": "open", "draft": True, "head": {"sha": SHA}}
                output = StringIO()
                with patch.object(client, "state_for", side_effect=[("owner/project", 42, pr, active),
                                                                       ("owner/project", 42, pr, settled)]), \
                        patch.object(client, "command", side_effect=[SHA + "\n", ""]) as command, \
                        patch.object(client, "post") as post, \
                        patch.object(client, "assert_posted") as verify, redirect_stdout(output):
                    client.release(args)
                self.assertEqual(output.getvalue(), SHA + "\n")
                self.assertEqual([call.args for call in command.call_args_list], [
                    ("git", "rev-parse", "HEAD"), ("git", "status", "--porcelain")])
                post.assert_called_once_with("owner/project", 42, c.render("release", CLAIM, SHA, version=version))
                verify.assert_called_once_with(args, claim_id=CLAIM, released=True, released_sha=SHA)

    def test_old_and_new_record_grammars_are_isolated_by_pin(self):
        for version in ("0.6.0", "0.6.1", "0.6.2"):
            with self.subTest(version=version):
                claim = c.render("claim", version=version)
                release = c.render("release", CLAIM, SHA, version=version)
                recovery = c.render_recovery("All writers stopped; work inventoried", version=version)
                state = c.reconstruct([record(claim, CLAIM, **MEMBER),
                                       record(release, OTHER, **MEMBER)], version=version)
                self.assertFalse(state.conflict)
                self.assertEqual(state.active, {})
                self.assertEqual(state.version, version)
                self.assertEqual(c.parse_comment(recovery, "leftium", "OWNER", version=version)["action"], "recover")
                other = "0.6.1" if version == "0.6.2" else "0.6.2"
                for text in (claim, release, recovery):
                    self.assertIsNone(c.parse_comment(text, "leftium", "OWNER", comment_id=CLAIM, version=other))

    def test_legacy_claim_emits_legacy_record(self):
        args = type("Args", (), {"pr": "https://github.com/owner/project/pull/42"})()
        pr = {"state": "open", "draft": True}
        with patch.object(client, "state_for", return_value=("owner/project", 42, pr, c.State(version="0.6.1"))), \
                patch.object(client, "post", return_value={"id": int(CLAIM)}) as post, \
                patch.object(client, "assert_posted"), redirect_stdout(StringIO()):
            client.claim(args)
        post.assert_called_once_with("owner/project", 42, "claim")

    def test_recovery_emission_uses_pinned_version(self):
        args = type("Args", (), {"pr": "https://github.com/owner/project/pull/42",
                                  "confirmation": "All writers stopped; work inventoried"})()
        pr = {"state": "open"}
        for version in ("0.6.0", "0.6.1", "0.6.2"):
            active = c.State(active={CLAIM: {}}, version=version)
            with self.subTest(version=version), \
                    patch.object(client, "state_for", side_effect=[("owner/project", 42, pr, active),
                                                                   ("owner/project", 42, pr, c.State(version=version))]), \
                    patch.object(client, "command", return_value="leftium\n"), \
                    patch.object(client, "api", return_value={"role_name": "admin"}), \
                    patch.object(client, "post") as post:
                client.recover(args)
            post.assert_called_once_with("owner/project", 42, c.render_recovery(args.confirmation, version=version))

    def test_record_wrappers_and_partial_sentences_are_ordinary_comments(self):
        for text in ("claim", "claimed", "This PR was claimed\n", " This PR was claimed",
                     "```\nThis PR was claimed\n```", "This PR was claimed\nThanks!",
                     f"released {CLAIM} at {SHA}", f"This PR's claim {CLAIM} was released at {SHA[:8]}",
                     "This PR was recovered | stopped | inventoried"):
            with self.subTest(text=text):
                self.assertIsNone(c.parse_comment(text, "writer", "MEMBER", comment_id=CLAIM))

    def test_state_for_uses_pinned_grammar_for_recovery_and_replay(self):
        url = "https://github.com/owner/project/pull/42"
        pr = {"user": {"login": "writer"}}
        for version in ("0.6.1", "0.6.2"):
            with self.subTest(version=version), \
                    patch.object(client, "resolve_protocol", return_value=(SHA, version)), \
                    patch.object(client, "read_comments", return_value=[record(c.render("claim", version=version), CLAIM, **MEMBER)]) as read:
                state = client.state_for(url, pr)[3]
                read.assert_called_once_with("owner/project", 42, version=version)
                self.assertEqual(set(state.active), {CLAIM})
                self.assertEqual(state.version, version)


class BootstrapLabelTests(unittest.TestCase):
    def test_existing_label_is_added_with_additive_labels_endpoint(self):
        with patch.object(client, "api", return_value={"name": "continuum"}) as api, \
                patch.object(client, "command", return_value="[]") as command:
            self.assertTrue(client.apply_continuum_label("owner/project", 42))
        api.assert_called_once_with("repos/owner/project/labels/continuum")
        command.assert_called_once_with(
            "gh", "api", "repos/owner/project/issues/42/labels",
            "--method", "POST", "-f", "labels[]=continuum")

    def test_missing_or_unreadable_label_does_not_block_bootstrap(self):
        with patch.object(client, "api", side_effect=c.Invalid("not found")) as api, \
                patch.object(client, "command") as command:
            self.assertFalse(client.apply_continuum_label("owner/project", 42))
        api.assert_called_once_with("repos/owner/project/labels/continuum")
        command.assert_not_called()

    def test_label_application_failure_does_not_block_bootstrap(self):
        with patch.object(client, "api", return_value={"name": "continuum"}), \
                patch.object(client, "command", side_effect=c.Invalid("forbidden")):
            self.assertFalse(client.apply_continuum_label("owner/project", 42))

    def test_label_command_accepts_pr_url_and_swallows_lookup_failure(self):
        args = type("Args", (), {"pr": "https://github.com/owner/project/pull/42"})()
        with patch.object(client, "apply_continuum_label", return_value=False) as apply:
            client.label(args)
        apply.assert_called_once_with("owner/project", 42)


class ProtocolPinTests(unittest.TestCase):
    def test_client_accepts_an_earlier_patch_pin_in_the_same_minor_line(self):
        args = {"body": "Continuum: Leftium/continuum@" + "a" * 40}
        protocol = "---\ncontinuum: 0.6.0\nartifact: protocol/CONTINUUM.md\n---\n"
        with patch.object(client, "command", return_value=protocol):
            self.assertEqual(client.pinned_protocol(args), "a" * 40)

    def test_client_rejects_other_minor_lines_and_future_patches(self):
        args = {"body": "Continuum: Leftium/continuum@" + "a" * 40}
        for version in ("0.5.9", "0.6.3"):
            protocol = f"---\ncontinuum: {version}\nartifact: protocol/CONTINUUM.md\n---\n"
            with self.subTest(version=version), patch.object(client, "command", return_value=protocol):
                with self.assertRaises(c.Invalid):
                    client.pinned_protocol(args)

    def test_linked_pin_fetches_full_sha_from_canonical_target(self):
        protocol = "---\ncontinuum: 0.6.2\nartifact: protocol/CONTINUUM.md\n---\n"
        body = f"Continuum: [Leftium/continuum@{SHA[:8]}](https://github.com/Leftium/continuum/blob/{SHA}/protocol/CONTINUUM.md)"
        with patch.object(client, "command", return_value=protocol) as command:
            self.assertEqual(client.resolve_protocol({"body": body}), (SHA, "0.6.2"))
        command.assert_called_once_with("gh", "api", f"repos/Leftium/continuum/contents/protocol/CONTINUUM.md?ref={SHA}",
                                        "-H", "Accept: application/vnd.github.raw+json")

    def test_invalid_link_targets_displays_and_duplicate_pins_fail_before_fetch(self):
        valid = f"Continuum: [Leftium/continuum@{SHA[:8]}](https://github.com/Leftium/continuum/blob/{SHA}/protocol/CONTINUUM.md)"
        invalid = [valid.replace("https://", "http://"), valid.replace("github.com", "github.com.evil.test"),
                   valid.replace("Leftium/continuum/blob", "stranger/continuum/blob"),
                   valid.replace("protocol/CONTINUUM.md", "docs/client.md"),
                   valid.replace(f"blob/{SHA}", "blob/main"), valid.replace(f"blob/{SHA}", f"blob/{SHA[:8]}"),
                   valid.replace(f"@{SHA[:8]}", "@bbbbbbbb"), valid + " trailing text",
                   valid + "\n" + valid, valid + "\nContinuum: Leftium/continuum@" + SHA,
                   valid + "\nContinuum: malformed", ""]
        for body in invalid:
            with self.subTest(body=body), patch.object(client, "command") as command:
                with self.assertRaises(c.Invalid):
                    client.pinned_protocol({"body": body})
                command.assert_not_called()

    def test_linked_pin_cannot_reinterpret_an_old_protocol(self):
        body = f"Continuum: [Leftium/continuum@{SHA[:8]}](https://github.com/Leftium/continuum/blob/{SHA}/protocol/CONTINUUM.md)"
        protocol = "---\ncontinuum: 0.6.1\nartifact: protocol/CONTINUUM.md\n---\n"
        with patch.object(client, "command", return_value=protocol):
            with self.assertRaises(c.Invalid):
                client.pinned_protocol({"body": body})


if __name__ == "__main__":
    unittest.main()
