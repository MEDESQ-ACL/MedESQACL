\
from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.request
from pathlib import Path


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def execute(base_url: str, index: str, body: dict, timeout: int = 60):
    url = base_url.rstrip("/") + f"/{index}/_search"
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as response:  # noqa: S310 - experiment endpoint.
        response.read()
    return (time.perf_counter() - t0) * 1000.0


def main():
    parser = argparse.ArgumentParser(description="Measure Elasticsearch query latency.")
    parser.add_argument("--data", type=Path, required=True, help="JSONL with es_query or query fields.")
    parser.add_argument("--elasticsearch-url", required=True)
    parser.add_argument("--index", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--runs", type=int, default=20)
    args = parser.parse_args()
    rows = []
    for ex in read_jsonl(args.data):
        body = ex.get("es_query")
        if body is None and ex.get("query"):
            try:
                body = json.loads(ex["query"])
            except Exception:
                body = None
        if body is None:
            continue
        times = []
        errors = []
        for _ in range(args.runs):
            try:
                times.append(execute(args.elasticsearch_url, args.index, body))
            except Exception as exc:  # noqa: BLE001
                errors.append(str(exc))
        rows.append({
            "id": ex.get("id"),
            "difficulty": ex.get("difficulty"),
            "n_runs": len(times),
            "median_ms": statistics.median(times) if times else None,
            "mean_ms": statistics.mean(times) if times else None,
            "p25_ms": statistics.quantiles(times, n=4)[0] if len(times) >= 4 else None,
            "p75_ms": statistics.quantiles(times, n=4)[2] if len(times) >= 4 else None,
            "errors": errors[:3],
        })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
