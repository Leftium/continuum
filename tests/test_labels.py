"""Optional label behavior with an in-memory GitHub adapter; no network writes."""

import contextlib
import copy
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import continuum as client
import continuum_core as c


class LabelTests(unittest.TestCase):
    def setUp(self):
        value = c.loads((Path(__file__).parent / "fixtures/contract.json").read_text())
        self.body = c.render(value)
        self.labels = []
        self.permissions = {"push": True}
        self.prs = {1: self.pr(1)}
        self.calls, self.saved = [], []
        self.fail = None
        self.args = SimpleNamespace(label=None, label_backfill=None, journal="/outside/bootstrap.json")
        self.journal = {"pr": "https://github.com/upstream/project/pull/1"}
        self.out, self.err = io.StringIO(), io.StringIO()
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(contextlib.redirect_stdout(self.out))
        self.stack.enter_context(contextlib.redirect_stderr(self.err))
        self.stack.enter_context(patch.object(client, "api", side_effect=self.api))
        self.stack.enter_context(patch.object(client, "journal_write", side_effect=lambda _path, data: self.saved.append(copy.deepcopy(data))))
        self.terminal = self.stack.enter_context(patch.object(client.sys.stdin, "isatty", return_value=False))

    def pr(self, number, body=None, state="open", labels=None):
        return {"number": number, "body": self.body if body is None else body, "state": state,
                "merged_at": None, "labels": list(labels or [{"name": "unrelated"}])}

    def api(self, path, *args):
        self.calls.append((path, args))
        if self.fail and self.fail(path, args):
            raise c.Invalid("permission denied or response lost")
        if path.endswith("/labels?per_page=100"):
            self.assertEqual(args, ("--paginate", "--slurp"))
            return [[], copy.deepcopy(self.labels)]  # Existing label may be on a later page.
        if path == "repos/upstream/project":
            return {"permissions": self.permissions}
        if path == "repos/upstream/project/labels":
            self.assertEqual(self.saved[-1]["label"], "create")
            self.labels.append({"name": "continuum"})
            return self.labels[-1]
        if path.endswith("/pulls?state=open&per_page=100"):
            self.assertEqual(args, ("--paginate", "--slurp"))
            return [[], copy.deepcopy(list(self.prs.values()))]
        if "/pulls/" in path:
            return copy.deepcopy(self.prs[int(path.rsplit("/", 1)[1])])
        if "/issues/" in path and path.endswith("/labels"):
            self.assertEqual(args, ("--method", "POST", "-f", "labels[]=continuum"))
            number = int(path.split("/")[-2])
            self.prs[number]["labels"].append({"name": "continuum"})
            return copy.deepcopy(self.prs[number]["labels"])
        raise AssertionError("unexpected API " + path)

    def additions(self):
        return [path for path, _ in self.calls if "/issues/" in path]

    def test_existing_label_applies_without_prompt_or_creation(self):
        self.labels = [{"name": "Continuum"}]
        with patch("builtins.input", side_effect=AssertionError("unexpected prompt")):
            client.bootstrap_labels(self.args, self.journal)
        self.assertEqual(len(self.additions()), 1)
        self.assertEqual(self.prs[1]["labels"][0]["name"], "unrelated")
        self.assertFalse(self.saved)
        self.assertNotIn(("repos/upstream/project", ()), self.calls)

    def test_interactive_creation_and_separate_backfill_choice(self):
        self.terminal.return_value = True
        self.prs[2] = self.pr(2)
        with patch("builtins.input", side_effect=["yes", "y"]) as prompt:
            client.bootstrap_labels(self.args, self.journal)
        self.assertEqual(prompt.call_count, 2)
        self.assertEqual(self.journal["label"], "create")
        self.assertEqual(self.journal["label_backfill"], "sync")
        self.assertEqual(len(self.additions()), 2)
        self.assertIn("/pull/2", self.out.getvalue())

    def test_interactive_decline_does_not_mutate(self):
        self.terminal.return_value = True
        with patch("builtins.input", return_value="n") as prompt:
            client.bootstrap_labels(self.args, self.journal)
        self.assertEqual(prompt.call_count, 1)
        self.assertFalse(self.additions())
        self.assertFalse(self.labels)

    def test_noninteractive_default_and_explicit_skip_never_create(self):
        for choice in (None, "skip"):
            with self.subTest(choice=choice):
                self.args.label = choice
                client.bootstrap_labels(self.args, dict(self.journal))
        self.assertFalse(self.labels)
        self.assertFalse(self.additions())
        self.assertIn("--label create", self.err.getvalue())

    def test_explicit_create_does_not_imply_backfill(self):
        self.args.label = "create"
        self.prs[2] = self.pr(2)
        client.bootstrap_labels(self.args, self.journal)
        self.assertEqual(len(self.additions()), 1)
        self.assertEqual(self.journal["label_backfill"], "skip")
        self.assertIn("--label-backfill sync", self.err.getvalue())

    def test_missing_permission_skips_even_with_creation_option(self):
        self.permissions = {"push": False}
        self.args.label = "create"
        client.bootstrap_labels(self.args, self.journal)
        self.assertFalse(self.labels)
        self.assertFalse(self.additions())
        self.assertFalse(self.saved)

    def test_lookup_creation_and_application_failures_are_nonblocking(self):
        for fragment in ("/labels?", "/project/labels", "/issues/1/labels"):
            with self.subTest(fragment=fragment):
                self.labels = []
                self.args.label = "create"
                self.fail = lambda path, _args: fragment in path
                client.bootstrap_labels(self.args, dict(self.journal))
        self.assertIn("failed or uncertain", self.err.getvalue())

    def test_resume_reuses_saved_choices_and_is_idempotent(self):
        self.args.label, self.args.label_backfill = "create", "sync"
        self.prs[2] = self.pr(2)
        client.bootstrap_labels(self.args, self.journal)
        self.args.label = self.args.label_backfill = None
        self.terminal.return_value = True
        with patch("builtins.input", side_effect=AssertionError("consent already saved")):
            client.bootstrap_labels(self.args, self.journal)
        self.assertEqual(len(self.additions()), 2)
        self.assertEqual(len(self.labels), 1)

    def test_lost_creation_response_resumes_with_separate_backfill_consent(self):
        self.journal["label"] = "create"
        self.labels = [{"name": "continuum"}]  # The previous creation succeeded remotely.
        self.terminal.return_value = True
        with patch("builtins.input", return_value="n") as prompt:
            client.bootstrap_labels(self.args, self.journal)
        self.assertEqual(prompt.call_count, 1)
        self.assertEqual(self.journal["label_backfill"], "skip")
        self.assertEqual(len(self.additions()), 1)

    def test_sync_uses_marker_pages_preserves_labels_and_reports_exact_changes(self):
        self.labels = [{"name": "continuum"}]
        self.prs[2] = self.pr(2, body="Continuum PR with branch continuum/example")
        self.prs[3] = self.pr(3, body=self.body.replace("contract:0.4", "contract:0.3"))
        self.prs[4] = self.pr(4, state="closed")
        self.prs[5] = self.pr(5, labels=[{"name": "continuum"}, {"name": "other"}])
        self.prs[6] = self.pr(6)
        client.label_sync(SimpleNamespace(repo="upstream/project"))
        client.label_sync(SimpleNamespace(repo="upstream/project"))
        self.assertEqual(self.additions(), ["repos/upstream/project/issues/1/labels", "repos/upstream/project/issues/6/labels"])
        self.assertEqual(self.out.getvalue().count("Labeled "), 2)
        self.assertIn("2 confirmed additions", self.out.getvalue())
        self.assertIn("0 confirmed additions", self.out.getvalue())
        self.assertEqual(self.prs[6]["labels"], [{"name": "unrelated"}, {"name": "continuum"}])

    def test_sync_rereads_candidates_before_mutation(self):
        listing = copy.deepcopy(list(self.prs.values()))
        self.prs[1]["body"] = "marker removed after listing"
        original_api = self.api
        def changed(path, *args):
            return [listing] if "/pulls?" in path else original_api(path, *args)
        with patch.object(client, "api", side_effect=changed):
            client.sync_pr_labels("upstream/project")
        self.assertFalse(self.additions())

    def test_sync_reports_partial_failures_and_continues(self):
        self.labels = [{"name": "continuum"}]
        self.prs[2] = self.pr(2)
        self.fail = lambda path, _args: "/issues/1/labels" in path
        with self.assertRaises(c.Invalid):
            client.label_sync(SimpleNamespace(repo="upstream/project"))
        self.assertIn("PR #1 failed or uncertain", self.err.getvalue())
        self.assertIn("Labeled https://github.com/upstream/project/pull/2", self.out.getvalue())
        self.assertIn("1 confirmed additions; 1 failed", self.out.getvalue())

    def test_sync_missing_label_never_creates_it(self):
        with self.assertRaisesRegex(c.Invalid, "label is missing"):
            client.label_sync(SimpleNamespace(repo="upstream/project"))
        self.assertFalse(self.additions())
        self.assertFalse(self.saved)

    def test_parser_exposes_explicit_noninteractive_policies(self):
        args = client.parser().parse_args(["bootstrap", "--remote", "fork", "--journal", "/outside/journal",
                                          "--label", "create", "--label-backfill", "skip"])
        self.assertEqual((args.label, args.label_backfill), ("create", "skip"))
        args = client.parser().parse_args(["label", "sync", "--repo", "upstream/project"])
        self.assertIs(args.function, client.label_sync)


if __name__ == "__main__":
    unittest.main()
