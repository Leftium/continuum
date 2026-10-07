#!/usr/bin/env python3
"""Validate the canonical 0.6 source without installing it into a target."""

from pathlib import Path
import sys

import continuum_core as c

root = Path(__file__).resolve().parents[1]
protocol = (root / "protocol/CONTINUUM.md").read_text(encoding="utf-8")
c.require(sys.version_info >= (3, 9), "Python 3.9+ required")
c.require(protocol.startswith(f"---\ncontinuum: {c.VERSION}\nartifact: protocol/CONTINUUM.md\n---\n"), "canonical source/version metadata mismatch")
for marker in ("claim", "release <claim-comment-id> <full-head-sha>", "recover | <owner confirmation"):
    c.require(marker in protocol, "normative document missing lease syntax " + marker)
c.require("Continuum: Leftium/continuum@<40-character-commit>" in protocol,
          "canonical source is missing the compact immutable PR pin")
c.require("<!-- continuum:contract:" not in protocol and "<!-- continuum:pointer:" not in protocol,
          "0.6 must not reintroduce a JSON contract or target-repository pointer")
print("Canonical Continuum source validated: " + c.VERSION)
