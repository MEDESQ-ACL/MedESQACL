\
from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from .complexity import canonical_json, complexity_from_ops, parse_query, walk_query
from .xlsx_reader import read_xlsx_sheets

QUESTION_COLUMNS = {
    "easy": ["Narrative Question"],
    "medium": ["Question", "Repgrase", "Unnamed: 12", "Narrative Question"],
    "hard": ["Question", "Rephrase", "Narrative Question"],
}


def slugify(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", str(text).strip().lower()).strip("_") or "col"


def norm(x) -> str:
    return "" if x is None else str(x).strip()


def write_jsonl(path: Path, rows: Iterable[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_csv(path: Path, rows: Iterable[dict], fieldnames: list[str] | None = None):
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out = {}
            for key in fieldnames:
                value = row.get(key, "")
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False, sort_keys=True)
                out[key] = value
            writer.writerow(out)


def read_source_csv(source_dir: Path) -> list[dict]:
    templates = []
    for level in ["easy", "medium", "hard"]:
        path = source_dir / f"{level}_templates.csv"
        with path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                row["difficulty"] = level
                row["source_row"] = int(row["source_row"])
                templates.append(row)
    return templates


def read_source_xlsx(xlsx_path: Path) -> tuple[list[dict], list[dict]]:
    sheets = read_xlsx_sheets(xlsx_path)
    templates = []
    for title, level in [("Easy", "easy"), ("Medium", "medium"), ("Hard", "hard")]:
        rows = sheets[title]
        header = [norm(v) for v in rows[0]]
        h_index = {h: i for i, h in enumerate(header) if h}
        for source_row, row in enumerate(rows[1:], start=2):
            combination = norm(row[h_index.get("Combination", 0)] if h_index.get("Combination", 0) < len(row) else "")
            query = norm(row[h_index.get("Query", 1)] if h_index.get("Query", 1) < len(row) else "")
            if not combination and not query:
                continue
            t = {
                "template_id": f"{level}_r{source_row:04d}",
                "difficulty": level,
                "source_row": source_row,
                "combination": combination,
                "query": query,
            }
            for qcol in QUESTION_COLUMNS[level]:
                idx = h_index.get(qcol)
                t[slugify(qcol)] = norm(row[idx] if idx is not None and idx < len(row) else "")
            templates.append(t)
    combinations = []
    if "Combinations" in sheets:
        for source_row, row in enumerate(sheets["Combinations"][1:], start=2):
            if not any(norm(v) for v in row):
                continue
            combinations.append({
                "source_row": source_row,
                "level": norm(row[0] if len(row) > 0 else ""),
                "combination": norm(row[1] if len(row) > 1 else ""),
                "count": norm(row[4] if len(row) > 4 else ""),
                "summary_level": norm(row[5] if len(row) > 5 else ""),
                "summary_count": norm(row[6] if len(row) > 6 else ""),
            })
    return templates, combinations


def expand_templates(templates: list[dict]) -> list[dict]:
    examples = []
    for t in templates:
        parse = parse_query(t["query"])
        ops = Counter()
        fields = Counter()
        canon = ""
        if parse["obj"] is not None:
            ops, fields = walk_query(parse["obj"])
            canon = canonical_json(parse["obj"])
        for qcol in QUESTION_COLUMNS[t["difficulty"]]:
            key = slugify(qcol)
            question = norm(t.get(key, ""))
            if not question:
                continue
            ex = {
                "id": f"medesq_{t['difficulty']}_r{int(t['source_row']):04d}_{key}",
                "template_id": t["template_id"],
                "difficulty": t["difficulty"],
                "source_row": int(t["source_row"]),
                "question_source": qcol,
                "combination": t["combination"],
                "question": question,
                "query": t["query"],
                "query_parse_status": parse["status"],
                "query_json_valid": parse["status"] == "json_valid",
                "query_parse_error": parse["error"],
                "operators": sorted(ops),
                "operator_counts": dict(sorted(ops.items())),
                "observed_fields": sorted(fields),
                "computed_complexity": complexity_from_ops(ops),
                "canonical_query": canon,
            }
            if parse["obj"] is not None:
                ex["es_query"] = parse["obj"]
            examples.append(ex)
    return examples


def split_by_template(examples: list[dict], seed: int = 13):
    rng = random.Random(seed)
    tids_by_level = defaultdict(list)
    for ex in examples:
        if ex["query_json_valid"]:
            tids_by_level[ex["difficulty"]].append(ex["template_id"])
    assignments = {}
    for level, tids in tids_by_level.items():
        tids = sorted(set(tids))
        rng.shuffle(tids)
        n = len(tids)
        n_train = int(round(n * 0.8))
        n_dev = int(round(n * 0.1))
        for tid in tids[:n_train]:
            assignments[tid] = "train"
        for tid in tids[n_train:n_train + n_dev]:
            assignments[tid] = "dev"
        for tid in tids[n_train + n_dev:]:
            assignments[tid] = "test"
    splits = {"train": [], "dev": [], "test": []}
    for ex in examples:
        if ex["query_json_valid"]:
            split = assignments[ex["template_id"]]
            splits[split].append(ex)
    return splits


def sample_eval(examples: list[dict], seed: int = 13, n_per_level: int = 200):
    rng = random.Random(seed)
    result = []
    for level in ["easy", "medium", "hard"]:
        pool = [ex for ex in examples if ex["difficulty"] == level and ex["query_json_valid"]]
        result.extend(rng.sample(pool, min(n_per_level, len(pool))))
    return sorted(result, key=lambda row: (row["difficulty"], row["id"]))


def validation_report(templates: list[dict], examples: list[dict]):
    all_status = Counter(ex["query_parse_status"] for ex in examples)
    clean = [ex for ex in examples if ex["query_json_valid"]]
    op_counts = Counter()
    field_counts = Counter()
    combo_counts = Counter()
    computed_mismatch = Counter()
    for ex in clean:
        op_counts.update(ex["operators"])
        field_counts.update(ex["observed_fields"])
        combo_counts[(ex["difficulty"], ex["combination"])] += 1
        if ex["computed_complexity"] != ex["difficulty"]:
            computed_mismatch[(ex["difficulty"], ex["computed_complexity"])] += 1
    return {
        "dataset_name": "MedESQ",
        "source": "Spreadsheet-derived anonymous package",
        "template_rows_by_difficulty": dict(Counter(t["difficulty"] for t in templates)),
        "expanded_examples_by_difficulty_all": dict(Counter(ex["difficulty"] for ex in examples)),
        "expanded_examples_by_difficulty_clean_json": dict(Counter(ex["difficulty"] for ex in clean)),
        "expanded_examples_total_all": len(examples),
        "expanded_examples_total_clean_json": len(clean),
        "query_parse_status_counts": dict(all_status),
        "operator_counts": dict(op_counts.most_common()),
        "observed_field_counts": dict(field_counts.most_common()),
        "computed_vs_assigned_complexity_mismatch_counts": {str(k): v for k, v in computed_mismatch.items()},
        "notes": [
            "Clean examples require a JSON-valid Elasticsearch query body.",
            "One REST endpoint row and malformed JSON rows are retained in medesq_all.jsonl but excluded from medesq_clean.jsonl and default splits.",
            "Question variants in Medium and Hard are expanded into separate NL-ESQ pairs while sharing the same template_id.",
            "The manuscript reports 1,887 easy, 1,737 medium, and 2,779 hard examples; the uploaded spreadsheet-derived clean JSON subset contains the counts shown here. This package preserves the discrepancy for auditability.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Build MedESQ JSONL/CSV files from source templates.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source-dir", type=Path, help="Directory containing exported *_templates.csv source files.")
    group.add_argument("--xlsx", type=Path, help="Original source workbook, if available.")
    parser.add_argument("--out-dir", type=Path, default=Path("data"))
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()

    if args.xlsx:
        templates, combinations = read_source_xlsx(args.xlsx)
        if combinations:
            write_csv(args.out_dir / "metadata" / "combinations.csv", combinations)
    else:
        templates = read_source_csv(args.source_dir)

    examples = expand_templates(templates)
    clean = [ex for ex in examples if ex["query_json_valid"]]
    report = validation_report(templates, examples)

    write_jsonl(args.out_dir / "medesq_all.jsonl", examples)
    write_jsonl(args.out_dir / "medesq_clean.jsonl", clean)
    write_csv(args.out_dir / "medesq_clean.csv", clean)
    write_jsonl(args.out_dir / "medesq_templates.jsonl", templates)
    write_jsonl(args.out_dir / "eval" / "eval_200_per_level_seed13.jsonl", sample_eval(examples, seed=args.seed, n_per_level=200))

    splits = split_by_template(examples, seed=args.seed)
    for split, rows in splits.items():
        write_jsonl(args.out_dir / "splits" / f"{split}.jsonl", rows)

    (args.out_dir / "metadata").mkdir(parents=True, exist_ok=True)
    (args.out_dir / "metadata" / "validation_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
