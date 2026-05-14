\
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from .complexity import parse_query
from .llm_clients import MockGoldClient, OpenAICompatibleClient
from .prompts import build_race_prompt, build_zero_shot_prompt
from .retrieval import PatternRetriever, read_jsonl


def extract_json_object(text: str):
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, flags=re.S)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return None
    return None


def main():
    parser = argparse.ArgumentParser(description="Generate ES queries with zero-shot or RACE-ESQ prompting.")
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--method", choices=["zero_shot", "race"], default="race")
    parser.add_argument("--provider", choices=["openai_compatible", "mock_gold"], default="openai_compatible")
    parser.add_argument("--model", default="gpt-5")
    parser.add_argument("--base-url", default="https://api.openai.com/v1")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=600)
    parser.add_argument("--retrieval-pool", type=Path, default=Path("data/splits/train.jsonl"))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--max-examples", type=int, default=None)
    args = parser.parse_args()

    examples = list(read_jsonl(args.data))
    if args.max_examples is not None:
        examples = examples[: args.max_examples]

    retriever = None
    if args.method == "race":
        pool = args.retrieval_pool if args.retrieval_pool.exists() else args.data
        retriever = PatternRetriever.from_jsonl(pool)

    if args.provider == "openai_compatible":
        client = OpenAICompatibleClient(api_key_env=args.api_key_env, base_url=args.base_url)
    else:
        client = MockGoldClient()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for ex in examples:
            retrieved = retriever.retrieve(ex["question"], top_k=args.top_k) if retriever else []
            messages = build_race_prompt(ex["question"], retrieved) if args.method == "race" else build_zero_shot_prompt(ex["question"])
            if args.provider == "mock_gold":
                parsed = parse_query(ex.get("query", ""))
                client.gold_query = parsed["obj"] if parsed["obj"] is not None else {}
            raw = client.complete(messages, model=args.model, temperature=args.temperature, max_tokens=args.max_tokens)
            obj = extract_json_object(raw)
            pred_query = obj.get("es_query") if isinstance(obj, dict) else None
            row = {
                "id": ex["id"],
                "difficulty": ex["difficulty"],
                "question": ex["question"],
                "gold_query": ex["query"],
                "method": args.method,
                "model": args.model,
                "retrieved_templates": [r.get("template_id") for r in retrieved],
                "prediction_text": raw,
                "prediction_json": obj,
                "predicted_query": pred_query,
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
