"""Offline tests for stable tag idempotency helpers."""

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

from types import SimpleNamespace

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/publish-release.py"
spec = importlib.util.spec_from_file_location("publish_release", SCRIPT)
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class ReleaseHelperTests(unittest.TestCase):
    def test_semver_reads_canonical_front_matter(self):
        self.assertEqual(publisher.version("---\ncontinuum: 0.5.0\nartifact: protocol\n"), (0, 5, 0))
        with self.assertRaises(SystemExit):
            publisher.version("continuum: latest")

    def test_tag_resolution_follows_annotated_ref_to_commit(self):
        replies = ["tag-object\n", "commit\tmerge-commit\n"]
        def fake_run(*args, **kwargs):
            return SimpleNamespace(returncode=0, stdout=replies.pop(0), stderr="")
        with patch.object(publisher, "run", side_effect=fake_run):
            self.assertEqual(publisher.tag_commit("v0.5.0"), "merge-commit")

    def test_tag_resolution_accepts_lightweight_commit_ref(self):
        def fake_run(*args, **kwargs):
            if any("git/ref/tags" in arg for arg in args):
                return SimpleNamespace(returncode=0, stdout="merge-commit\n", stderr="")
            return SimpleNamespace(returncode=1, stdout="", stderr="not an annotated tag")
        with patch.object(publisher, "run", side_effect=fake_run):
            self.assertEqual(publisher.tag_commit("v0.5.0"), "merge-commit")


if __name__ == "__main__":
    unittest.main()
