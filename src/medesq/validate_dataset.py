\
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .complexity import parse_query, walk_query, complexity_from_ops


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def validate(path: Path):
    counts = Counter()
    levels = Counter()
    operators = Counter()
    fields = Counter()
    mismatches = Counter()
    errors = []
    for ex in read_jsonl(path):
        levels[ex.get("difficulty", "unknown")] += 1
        parsed = parse_query(ex.get("query", ""))
        counts[parsed["status"]] += 1
        if parsed["obj"] is None:
            errors.append({"id": ex.get("id"), "status": parsed["status"], "error": parsed["error"]})
            continue
        ops, fs = walk_query(parsed["obj"])
        operators.update(ops)
        fields.update(fs)
        computed = complexity_from_ops(ops)
        if computed != ex.get("difficulty"):
            mismatches[(ex.get("difficulty"), computed)] += 1
    return {
        "file": str(path),
        "examples": sum(levels.values()),
        "difficulty_counts": dict(levels),
        "parse_status_counts": dict(counts),
        "operator_counts": dict(operators.most_common()),
        "field_counts": dict(fields.most_common()),
        "computed_vs_assigned_mismatches": {str(k): v for k, v in mismatches.items()},
        "non_json_or_invalid_examples": errors[:100],
        "non_json_or_invalid_examples_truncated": len(errors) > 100,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    report = validate(args.data)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
