\
from __future__ import annotations

import json
from collections import Counter
from typing import Any

QUERY_OPERATORS = {
    "ids", "term", "terms", "range", "prefix", "wildcard", "regexp", "match",
    "match_phrase", "multi_match", "query_string", "bool", "constant_score",
    "exists", "aggs", "aggregations", "sort", "script", "nested",
}
FIELD_OPS = {"term", "terms", "range", "prefix", "wildcard", "regexp", "match", "match_phrase"}
AGG_TERMS_OPTION_KEYS = {"field", "size", "order", "missing", "min_doc_count", "shard_size", "show_term_doc_count_error"}
EASY_OPS = {"ids", "term", "terms", "bool", "constant_score", "exists"}
MEDIUM_OPS = {"range", "prefix", "wildcard", "regexp"}
HARD_OPS = {"match", "match_phrase", "multi_match", "query_string", "aggs", "aggregations", "sort"}


def walk_query(obj: Any, ops: Counter | None = None, fields: Counter | None = None, parent: str | None = None):
    """Extract ES operators and field names from a JSON-like query object."""
    if ops is None:
        ops = Counter()
    if fields is None:
        fields = Counter()
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in QUERY_OPERATORS:
                ops[key] += 1
            if parent in FIELD_OPS and isinstance(key, str):
                # `terms` is both an ES query operator and an aggregation operator.
                # In aggregations, keys such as `field` and `size` are parameters,
                # not schema fields. The actual field is captured by the `field`
                # value branch below.
                if not (parent == "terms" and key in AGG_TERMS_OPTION_KEYS):
                    fields[key] += 1
            if key == "field" and isinstance(value, str):
                fields[value] += 1
            walk_query(value, ops, fields, key)
    elif isinstance(obj, list):
        for item in obj:
            walk_query(item, ops, fields, parent)
    return ops, fields


def complexity_from_ops(operators: list[str] | set[str] | Counter) -> str:
    """Map ES operators to the paper's easy/medium/hard taxonomy."""
    op_set = set(operators)
    if op_set & HARD_OPS:
        return "hard"
    if op_set & MEDIUM_OPS:
        return "medium"
    if op_set & EASY_OPS:
        return "easy"
    return "unknown"


def parse_query(query_text: str):
    q = (query_text or "").strip()
    if not q:
        return {"status": "empty", "obj": None, "error": "empty query"}
    if q.lstrip().upper().startswith("GET "):
        return {"status": "rest_endpoint", "obj": None, "error": "REST endpoint without JSON body"}
    try:
        return {"status": "json_valid", "obj": json.loads(q), "error": ""}
    except Exception as exc:  # noqa: BLE001 - keep exact parser message for audits.
        return {"status": "json_invalid", "obj": None, "error": str(exc)}


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_query_text(query_text: str) -> str:
    parsed = parse_query(query_text)
    if parsed["obj"] is None:
        return ""
    return canonical_json(parsed["obj"])
