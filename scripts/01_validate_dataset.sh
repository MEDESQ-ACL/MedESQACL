#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=src python -m medesq.validate_dataset --data data/medesq_clean.jsonl --out data/metadata/validation_from_script.json
