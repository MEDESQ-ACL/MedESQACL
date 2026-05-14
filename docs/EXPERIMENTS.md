# Experiment Protocol

## Baselines

The manuscript compares GPT4, GPT4o, GPT5, Grok4, GLM4.5, Qwen3, and RACE-ESQ. This package supports any OpenAI-compatible chat-completions endpoint through `medesq.generate`.

## RACE-ESQ

RACE-ESQ uses a two-stage prompt:

1. schema grounding and operator-pattern retrieval;
2. cost-aware Elasticsearch query composition.

The default retrieval pool is `data/splits/train.jsonl`, and the default evaluation set is `data/eval/eval_200_per_level_seed13.jsonl`.

## Metrics

- ECR: executable code ratio.
- PR: pass rate by exact canonical match or execution-result comparison.
- Latency: median/mean Elasticsearch execution time over repeated runs.

## Recommended ablations

- Zero-shot vs RACE-ESQ.
- RACE-ESQ without retrieved examples.
- RACE-ESQ without cost-aware golden rules.
- Different retrieval top-k values.
- Execution latency by difficulty tier.
