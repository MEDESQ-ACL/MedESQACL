\
from __future__ import annotations

import json

PAPER_SCHEMA_FIELDS = [
    "RECVDATE", "STATE", "AGE_YRS", "VAERS_ID", "SEX", "SYMPTOM_TEXT", "DIED",
    "ER_VISIT", "L_THREAT", "HOSPITAL", "HOSPDAYS", "DISABLE", "VAX_DATE",
    "LAB_DATA", "OTHER_MEDS", "CUR_ILL", "HISTORY", "PRIOR_VAX", "TODAYS_DATE",
    "OFC_VISIT", "VAX_TYPE", "VAX_MANU", "VAX_LOT", "VAX_DOSE_SERIES", "VAX_NAME",
    "ALLERGIES",
]

GOLDEN_RULES = [
    "Use only fields that appear in the schema unless the prompt explicitly supplies an observed extended VAERS field.",
    "Normalize symptom expressions before generating the final query.",
    "Prefer exact filters (term, terms, range, prefix) for structured fields.",
    "Use match, match_phrase, multi_match, or query_string only for free-text fields such as SYMPTOM_TEXT, LAB_DATA, HISTORY, CUR_ILL, OTHER_MEDS, and ALLERGIES.",
    "When multiple valid plans exist, prefer the lower-cost operator pattern.",
    "If the question is underspecified, return a safe minimal query rather than hallucinating extra constraints.",
    "Output a JSON object with standard_terms, retrieved_patterns, and es_query. Do not include prose outside JSON.",
]

OPERATOR_COST_ORDER = [
    "ids", "term", "terms", "bool/filter", "range", "prefix", "wildcard", "regexp",
    "match", "match_phrase", "multi_match", "query_string", "sort", "aggs",
]


def schema_block(extra_fields: list[str] | None = None) -> str:
    fields = list(PAPER_SCHEMA_FIELDS)
    for field in extra_fields or []:
        if field not in fields:
            fields.append(field)
    return ", ".join(fields)


def build_zero_shot_prompt(question: str, extra_fields: list[str] | None = None) -> list[dict]:
    system = f"""You are an expert Elasticsearch engineer. Convert each natural-language question into a correct, minimal, schema-compliant Elasticsearch query.

Elasticsearch database fields: {schema_block(extra_fields)}

Golden rules:
- """ + "\n- ".join(GOLDEN_RULES)
    user = f"""Question: {question}

Return JSON only with this structure:
{{"standard_terms": [], "retrieved_patterns": [], "es_query": {{...}}}}"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_race_prompt(question: str, retrieved_patterns: list[dict], extra_fields: list[str] | None = None) -> list[dict]:
    examples = []
    for item in retrieved_patterns:
        examples.append({
            "difficulty": item.get("difficulty"),
            "combination": item.get("combination"),
            "operators": item.get("operators", []),
            "observed_fields": item.get("observed_fields", []),
            "example_question": item.get("question"),
            "example_query": item.get("query"),
        })
    system = f"""You are an expert Elasticsearch engineer implementing RACE-ESQ: a retrieval-augmented, complexity-aware text-to-Elasticsearch-query pipeline.

Elasticsearch database fields: {schema_block(extra_fields)}

Operator cost preference, lowest to highest: {", ".join(OPERATOR_COST_ORDER)}

Golden rules:
- """ + "\n- ".join(GOLDEN_RULES)
    user = f"""Stage 1 - schema grounding and pattern retrieval:
Use the retrieved operator patterns below to identify valid fields, normalized values, and the lowest-cost plan that preserves the question semantics.

Retrieved patterns:
{json.dumps(examples, ensure_ascii=False, indent=2)}

Stage 2 - cost-aware query composition:
Question: {question}

Return JSON only with this structure:
{{"standard_terms": [], "retrieved_patterns": [], "es_query": {{...}}}}"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
