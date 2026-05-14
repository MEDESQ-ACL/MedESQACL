\
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--n-per-level", type=int, default=200)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    examples = list(read_jsonl(args.data))
    sample = []
    for level in ["easy", "medium", "hard"]:
        pool = [ex for ex in examples if ex.get("difficulty") == level]
        sample.extend(rng.sample(pool, min(args.n_per_level, len(pool))))
    sample.sort(key=lambda ex: (ex.get("difficulty", ""), ex.get("id", "")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for ex in sample:
            handle.write(json.dumps(ex, ensure_ascii=False) + "\n")
    print(f"wrote {len(sample)} examples to {args.out}")


if __name__ == "__main__":
    main()
