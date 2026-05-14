#!/usr/bin/env bash
set -euo pipefail
PRED=${1:-experiments/predictions/race_esq_gpt5.jsonl}
OUT=${2:-experiments/evaluation/race_esq_gpt5_exact.json}
PYTHONPATH=src python -m medesq.evaluate --predictions "$PRED" --out "$OUT"
