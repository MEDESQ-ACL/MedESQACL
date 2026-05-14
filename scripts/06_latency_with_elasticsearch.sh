#!/usr/bin/env bash
set -euo pipefail
: "${ELASTICSEARCH_URL:?Set ELASTICSEARCH_URL, e.g. http://localhost:9200}"
: "${ELASTICSEARCH_INDEX:?Set ELASTICSEARCH_INDEX, e.g. vaers}"
DATA=${1:-data/eval/eval_200_per_level_seed13.jsonl}
OUT=${2:-experiments/latency/eval_200_latency.jsonl}
PYTHONPATH=src python -m medesq.latency --data "$DATA" --out "$OUT" --elasticsearch-url "$ELASTICSEARCH_URL" --index "$ELASTICSEARCH_INDEX" --runs 20
