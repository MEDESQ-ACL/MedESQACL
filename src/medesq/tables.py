\
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Render paper metrics CSV as Markdown table.")
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with args.metrics.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    headers = rows[0].keys() if rows else []
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(row[h] for h in headers) + " |")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
