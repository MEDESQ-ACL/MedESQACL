#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=src python -m medesq.generate --data data/eval/eval_200_per_level_seed13.jsonl --out experiments/smoke/mock_gold_predictions.jsonl --provider mock_gold --method race --max-examples 12
PYTHONPATH=src python -m medesq.evaluate --predictions experiments/smoke/mock_gold_predictions.jsonl --out experiments/smoke/mock_gold_eval.json
cat experiments/smoke/mock_gold_eval.json
