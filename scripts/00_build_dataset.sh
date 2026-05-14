#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=src python -m medesq.build_dataset --source-dir data/source --out-dir data --seed 13
