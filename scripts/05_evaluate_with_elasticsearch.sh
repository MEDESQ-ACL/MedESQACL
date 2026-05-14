#!/usr/bin/env bash
set -euo pipefail
: "${ELASTICSEARCH_URL:?Set ELASTICSEARCH_URL, e.g. http://localhost:9200}"
: "${ELASTICSEARCH_INDEX:?Set ELASTICSEARCH_INDEX, e.g. vaers}"
PRED=${1:-experiments/predictions/race_esq_gpt5.jsonl}
OUT=${2:-experiments/evaluation/race_esq_gpt5_execution.json}
PYTHONPATH=src python -m medesq.evaluate --predictions "$PRED" --out "$OUT" --elasticsearch-url "$ELASTICSEARCH_URL" --index "$ELASTICSEARCH_INDEX"
