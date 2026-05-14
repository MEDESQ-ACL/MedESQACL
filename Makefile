PYTHON ?= python
PYTHONPATH := src

.PHONY: build validate sample smoke table4 clean

build:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m medesq.build_dataset --source-dir data/source --out-dir data --seed 13

validate:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m medesq.validate_dataset --data data/medesq_clean.jsonl --out data/metadata/validation_from_make.json

sample:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m medesq.sample_eval --data data/medesq_clean.jsonl --out data/eval/eval_200_per_level_seed13.jsonl --seed 13 --n-per-level 200

smoke:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m medesq.generate --data data/eval/eval_200_per_level_seed13.jsonl --out experiments/smoke/mock_gold_predictions.jsonl --provider mock_gold --method race --max-examples 12
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m medesq.evaluate --predictions experiments/smoke/mock_gold_predictions.jsonl --out experiments/smoke/mock_gold_eval.json

table4:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m medesq.tables --metrics results/paper_reported/table4_metrics.csv --out results/paper_reported/table4_metrics.md

clean:
	rm -rf experiments/smoke/*.jsonl experiments/smoke/*.json data/metadata/validation_from_make.json
