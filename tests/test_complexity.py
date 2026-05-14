from medesq.complexity import complexity_from_ops, parse_query, walk_query

def test_complexity_tiers():
    assert complexity_from_ops(["term", "bool"]) == "easy"
    assert complexity_from_ops(["prefix", "term"]) == "medium"
    assert complexity_from_ops(["match", "sort"]) == "hard"

def test_parse_and_extract():
    parsed = parse_query('{"query":{"term":{"STATE":{"value":"CA"}}}}')
    assert parsed["status"] == "json_valid"
    ops, fields = walk_query(parsed["obj"])
    assert "term" in ops
    assert "STATE" in fields
