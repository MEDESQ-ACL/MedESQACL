import json
from pathlib import Path

def test_clean_dataset_exists_and_has_examples():
    path = Path("data/medesq_clean.jsonl")
    assert path.exists()
    first = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert "question" in first and "query" in first
