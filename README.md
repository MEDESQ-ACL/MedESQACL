# MedESQ Anonymous Reproducibility Package

This repository contains the anonymous dataset and experiment package for **MedESQ: Rethinking Efficient Text-to-NoSQL Querying Generation with a Complexity Taxonomy for Lucene Data Structures**.

The package is designed for anonymous review. It contains no author names, no institution-specific paths, and no personal Git metadata. The original spreadsheet was exported into metadata-free CSV/JSONL files for review.

## What is included

- `data/source/`: metadata-free CSV template rows exported from the submitted spreadsheet.
- `data/medesq_all.jsonl`: all expanded natural-language / ESQ pairs from the spreadsheet.
- `data/medesq_clean.jsonl`: JSON-valid ES query-body subset used by default experiments.
- `data/splits/`: template-grouped train/dev/test splits.
- `data/eval/eval_200_per_level_seed13.jsonl`: 200-example-per-level evaluation subset, matching the paper's evaluation scale.
- `src/medesq/`: dataset builder, taxonomy validator, RACE-ESQ prompt builder, retrieval module, generation harness, evaluation code, and latency measurement.
- `prompts/`: zero-shot and RACE-ESQ prompt text.
- `results/paper_reported/`: manuscript-reported Table 4 metrics and runtime values.
- `paper/`: anonymous manuscript draft copy.

## Dataset counts from the uploaded spreadsheet

| Split/source | Easy | Medium | Hard | Total |
| --- | ---: | ---: | ---: | ---: |
| Expanded all pairs | 582 | 1608 | 4698 | 6888 |
| Clean JSON-valid pairs | 581 | 1604 | 4611 | 6796 |

The manuscript reports a final MedESQ count of 1,887 easy, 1,737 medium, and 2,779 hard examples. The uploaded spreadsheet expands Medium and Hard rows into multiple question variants and contains a small number of non-JSON or malformed query rows. The validation report keeps this discrepancy explicit: see `data/metadata/validation_report.json`.

## Rebuild the dataset

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
make build
make validate
```

The builder can also parse the original workbook if available:

```bash
PYTHONPATH=src python -m medesq.build_dataset --xlsx /path/to/MedESQ.xlsx --out-dir data --seed 13
```

## Run the RACE-ESQ smoke test

The smoke test uses a mock client that returns the gold query, so it requires no API key and verifies that generation/evaluation plumbing works.

```bash
make smoke
```

## Run API-based experiments

Set an OpenAI-compatible endpoint and model name. The paper used zero-shot settings with temperature 0.2 and max output length 600.

```bash
export OPENAI_API_KEY=YOUR_KEY
export OPENAI_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-5
bash scripts/02_run_zero_shot_openai_compatible.sh
bash scripts/03_run_race_esq_openai_compatible.sh
bash scripts/04_evaluate_exact.sh experiments/predictions/race_esq_gpt5.jsonl experiments/evaluation/race_esq_gpt5_exact.json
```

For execution-based pass rate and latency, also provide Elasticsearch variables:

```bash
export ELASTICSEARCH_URL=http://localhost:9200
export ELASTICSEARCH_INDEX=vaers
bash scripts/05_evaluate_with_elasticsearch.sh experiments/predictions/race_esq_gpt5.jsonl experiments/evaluation/race_esq_gpt5_execution.json
bash scripts/06_latency_with_elasticsearch.sh data/eval/eval_200_per_level_seed13.jsonl experiments/latency/eval_200_latency.jsonl
```

## Metrics

- **Executable Code Ratio (ECR):** percentage of generated queries that parse as JSON and, when an ES server is supplied, execute without syntax/schema errors.
- **Pass Rate (PR):** exact canonical query match by default; with Elasticsearch enabled, PR compares normalized execution results between predicted and gold queries.
- **Latency:** repeated `_search` execution time in milliseconds.

## Anonymity note

This ZIP is ready to upload to an anonymous repository service or supplementary-material system. Before de-anonymization, avoid adding author names, ORCID IDs, personal emails, institution-specific cluster paths, or non-anonymous Git remotes.
