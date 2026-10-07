"""Offline tests for stable tag idempotency helpers."""

import importlib.util
import importlib
from pathlib import Path
import unittest
import sys
from unittest.mock import patch

from types import SimpleNamespace

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/publish-release.py"
spec = importlib.util.spec_from_file_location("publish_release", SCRIPT)
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)
sys.path.insert(0, str(SCRIPT.parent))
import continuum_core as c
import continuum as client


class ReleaseHelperTests(unittest.TestCase):
    def test_semver_reads_canonical_front_matter(self):
        self.assertEqual(publisher.version("---\ncontinuum: 0.6.0\nartifact: protocol\n"), (0, 6, 0))
        with self.assertRaises(SystemExit):
            publisher.version("continuum: latest")

    def test_tag_resolution_follows_annotated_ref_to_commit(self):
        replies = ["tag-object\n", "commit\tmerge-commit\n"]
        def fake_run(*args, **kwargs):
            return SimpleNamespace(returncode=0, stdout=replies.pop(0), stderr="")
        with patch.object(publisher, "run", side_effect=fake_run):
            self.assertEqual(publisher.tag_commit("v0.6.0"), "merge-commit")

    def test_tag_resolution_accepts_lightweight_commit_ref(self):
        def fake_run(*args, **kwargs):
            if any("git/ref/tags" in arg for arg in args):
                return SimpleNamespace(returncode=0, stdout="merge-commit\n", stderr="")
            return SimpleNamespace(returncode=1, stdout="", stderr="not an annotated tag")
        with patch.object(publisher, "run", side_effect=fake_run):
            self.assertEqual(publisher.tag_commit("v0.6.0"), "merge-commit")

    def test_pr_pin_regex_tracks_client_protocol_version(self):
        try:
            with patch.object(c, "VERSION", "9.8.7"):
                importlib.reload(client)
                self.assertIsNotNone(client.PIN.fullmatch(
                    "Continuum: Leftium/continuum@" + "a" * 40))
                self.assertIsNone(client.PIN.fullmatch(
                    "Continuum: 0.6.0; protocol source: Leftium/continuum@" + "a" * 40 + ":protocol/CONTINUUM.md"))
        finally:
            importlib.reload(client)


if __name__ == "__main__":
    unittest.main()
