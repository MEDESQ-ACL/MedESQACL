\
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text or "")]


def read_jsonl(path: str | Path):
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


class PatternRetriever:
    """Small dependency-free lexical retriever for RACE-ESQ prompts.

    It indexes questions and combinations from a MedESQ split and returns operator
    patterns with overlapping medical/schema terms. This is not a replacement for
    dense retrieval; it is a transparent default for anonymous reproducibility.
    """

    def __init__(self, examples: list[dict]):
        self.examples = examples
        self.doc_tokens = []
        self.df = Counter()
        for ex in examples:
            tokens = set(tokenize(" ".join([ex.get("question", ""), ex.get("combination", ""), " ".join(ex.get("observed_fields", []))])))
            self.doc_tokens.append(tokens)
            self.df.update(tokens)
        self.n = max(len(examples), 1)

    @classmethod
    def from_jsonl(cls, path: str | Path):
        return cls(list(read_jsonl(path)))

    def score(self, query: str, idx: int) -> float:
        q_tokens = tokenize(query)
        if not q_tokens:
            return 0.0
        doc = self.doc_tokens[idx]
        score = 0.0
        qtf = Counter(q_tokens)
        for token, tf in qtf.items():
            if token in doc:
                idf = math.log((self.n + 1) / (self.df[token] + 1)) + 1.0
                score += tf * idf
        return score

    def retrieve(self, query: str, top_k: int = 5, difficulty: str | None = None) -> list[dict]:
        scored = []
        for i, ex in enumerate(self.examples):
            if difficulty and ex.get("difficulty") != difficulty:
                continue
            s = self.score(query, i)
            if s > 0:
                scored.append((s, i))
        scored.sort(reverse=True)
        out = []
        seen_templates = set()
        for score, idx in scored:
            ex = self.examples[idx]
            if ex["template_id"] in seen_templates:
                continue
            seen_templates.add(ex["template_id"])
            out.append({
                "score": round(score, 4),
                "template_id": ex["template_id"],
                "difficulty": ex["difficulty"],
                "combination": ex["combination"],
                "operators": ex.get("operators", []),
                "observed_fields": ex.get("observed_fields", []),
                "question": ex["question"],
                "query": ex["query"],
            })
            if len(out) >= top_k:
                break
        return out
