#!/usr/bin/env bash
set -euo pipefail
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY or change --api-key-env.}"
PYTHONPATH=src python -m medesq.generate   --data data/eval/eval_200_per_level_seed13.jsonl   --retrieval-pool data/splits/train.jsonl   --out experiments/predictions/race_esq_gpt5.jsonl   --method race   --provider openai_compatible   --base-url "${OPENAI_BASE_URL:-https://api.openai.com/v1}"   --model "${MODEL_NAME:-gpt-5}"   --temperature 0.2   --max-tokens 600
