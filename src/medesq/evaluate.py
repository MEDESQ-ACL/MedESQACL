\
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .complexity import canonical_json, parse_query


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def execute_es(base_url: str, index: str, body: dict, timeout: int = 60):
    url = base_url.rstrip("/") + f"/{index}/_search"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as response:  # noqa: S310 - experiment endpoint.
        payload = json.loads(response.read().decode("utf-8"))
    return payload, (time.perf_counter() - t0) * 1000.0


def comparable_result(es_response: dict[str, Any]):
    """Normalize ES results for pass-rate comparison.

    If aggregations are present, compare aggregations. Otherwise compare hit IDs and total count.
    """
    if "aggregations" in es_response:
        return es_response["aggregations"]
    hits = es_response.get("hits", {})
    total = hits.get("total", {})
    if isinstance(total, dict):
        total_value = total.get("value")
    else:
        total_value = total
    ids = [hit.get("_id") for hit in hits.get("hits", [])]
    return {"total": total_value, "ids": ids}


def evaluate(predictions: list[dict], es_url: str | None = None, index: str | None = None):
    rows = []
    for pred in predictions:
        predicted = pred.get("predicted_query")
        pred_valid_json = isinstance(predicted, dict)
        executable = pred_valid_json
        passed = False
        error = ""
        pred_latency = None
        gold_latency = None
        if pred_valid_json:
            if es_url and index:
                try:
                    pred_resp, pred_latency = execute_es(es_url, index, predicted)
                    gold_parsed = parse_query(pred.get("gold_query", ""))
                    if gold_parsed["obj"] is None:
                        passed = False
                    else:
                        gold_resp, gold_latency = execute_es(es_url, index, gold_parsed["obj"])
                        passed = comparable_result(pred_resp) == comparable_result(gold_resp)
                    executable = True
                except Exception as exc:  # noqa: BLE001
                    executable = False
                    error = str(exc)
            else:
                gold_parsed = parse_query(pred.get("gold_query", ""))
                passed = gold_parsed["obj"] is not None and canonical_json(predicted) == canonical_json(gold_parsed["obj"])
        else:
            error = "predicted_query is not a JSON object"
        rows.append({
            "id": pred.get("id"),
            "difficulty": pred.get("difficulty", "unknown"),
            "method": pred.get("method", "unknown"),
            "model": pred.get("model", "unknown"),
            "executable": executable,
            "passed": passed,
            "error": error,
            "pred_latency_ms": pred_latency,
            "gold_latency_ms": gold_latency,
        })
    return rows


def summarize(rows: list[dict]):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["model"], row["method"], row["difficulty"])].append(row)
    summary = []
    for (model, method, difficulty), items in sorted(groups.items()):
        n = len(items)
        ecr = sum(bool(x["executable"]) for x in items) / n if n else 0.0
        pr = sum(bool(x["passed"]) for x in items) / n if n else 0.0
        summary.append({"model": model, "method": method, "difficulty": difficulty, "n": n, "ECR": ecr, "PR": pr})
    return summary


def main():
    parser = argparse.ArgumentParser(description="Evaluate generated MedESQ predictions.")
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--elasticsearch-url", default=None)
    parser.add_argument("--index", default=None)
    args = parser.parse_args()
    preds = list(read_jsonl(args.predictions))
    rows = evaluate(preds, es_url=args.elasticsearch_url, index=args.index)
    report = {"summary": summarize(rows), "items": rows}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
