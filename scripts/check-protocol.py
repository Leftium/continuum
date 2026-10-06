#!/usr/bin/env python3
"""Validate the published source contract without installing it into a target."""

from pathlib import Path
import sys

import continuum_core as c

root = Path(__file__).resolve().parents[1]
protocol = (root / "protocol/CONTINUUM.md").read_text(encoding="utf-8")
c.require(sys.version_info >= (3, 9), "Python 3.9+ required")
c.require(protocol.startswith(f"---\ncontinuum: {c.VERSION}\nartifact: protocol/CONTINUUM.md\n---\n"), "canonical source/version metadata mismatch")
for marker in (c.CONTRACT_START, c.CONTRACT_END, c.EVENT_START, c.EVENT_END, c.POINTER_END):
    c.require(marker in protocol, "normative document missing wire delimiter " + marker)
fixture = c.loads((root / "tests/fixtures/contract.json").read_text())
c.validate_contract(fixture)
c.require(c.canonical({k: v for k, v in fixture.items() if k != "digest"}) == (root / "tests/fixtures/normalized.json").read_bytes(), "wire normalization fixture mismatch")
print("Canonical Continuum source validated: " + c.VERSION)
