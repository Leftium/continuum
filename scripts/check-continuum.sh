#!/usr/bin/env bash
set -euo pipefail

# Validate the canonical 0.4 source contract and offline reference client.
python3 scripts/check-protocol.py
python3 -m unittest discover -s tests
