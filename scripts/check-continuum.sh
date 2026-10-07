#!/usr/bin/env bash
set -euo pipefail

# Validate the canonical 0.5 source and offline lease client.
python3 scripts/check-protocol.py
python3 -m unittest discover -s tests
