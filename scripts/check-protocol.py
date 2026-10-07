#!/usr/bin/env python3
"""Validate the canonical 0.6 source without installing it into a target."""

from pathlib import Path
import sys

import continuum_core as c

root = Path(__file__).resolve().parents[1]
protocol = (root / "protocol/CONTINUUM.md").read_text(encoding="utf-8")
c.require(sys.version_info >= (3, 9), "Python 3.9+ required")
c.require(protocol.startswith(f"---\ncontinuum: {c.VERSION}\nartifact: protocol/CONTINUUM.md\n---\n"), "canonical source/version metadata mismatch")
for marker in ("This PR was claimed", "This PR's claim <claim-comment-id> was released at <full-head-sha>", "This PR was recovered | <owner confirmation"):
    c.require(marker in protocol, "normative document missing lease syntax " + marker)
c.require('Continuum: [Leftium/continuum@<short-commit>](https://github.com/Leftium/continuum/blob/<40-character-commit>/protocol/CONTINUUM.md)' in protocol,
          "canonical source is missing the linked immutable PR pin")
c.require("<!-- continuum:contract:" not in protocol and "<!-- continuum:pointer:" not in protocol,
          "0.6 must not reintroduce a JSON contract or target-repository pointer")
print("Canonical Continuum source validated: " + c.VERSION)
