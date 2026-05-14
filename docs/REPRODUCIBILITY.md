# Reproducibility Guide

## Environment

Python 3.10+ is recommended. The core package uses only the Python standard library. Optional API and Elasticsearch dependencies can be installed from `requirements.txt`.

## Step 1: Build and validate data

```bash
make build
make validate
```

## Step 2: Confirm the evaluation subset

```bash
make sample
wc -l data/eval/eval_200_per_level_seed13.jsonl
```

## Step 3: Run smoke test without APIs

```bash
make smoke
```

## Step 4: Run model generations

Use `scripts/02_run_zero_shot_openai_compatible.sh` and `scripts/03_run_race_esq_openai_compatible.sh` after setting `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `MODEL_NAME`.

## Step 5: Evaluate

Exact-match evaluation works without Elasticsearch. Execution-based PR and latency require a VAERS-compatible Elasticsearch index.

## Notes on reproducing paper numbers

The repository includes `results/paper_reported/table4_metrics.csv` for reference. Rerunning exact model experiments may produce small differences due to API model versions, random sampling, provider behavior, and Elasticsearch/index settings.
