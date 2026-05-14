# Dataset Card: MedESQ

## Summary

MedESQ is a natural-language-to-Elasticsearch-query dataset for healthcare knowledge screening. The data are organized around a Lucene/Elasticsearch complexity taxonomy with easy, medium, and hard tiers.

## Source

The dataset package was built from the submitted spreadsheet and is derived from public VAERS-style adverse event report fields. The repository contains metadata-free CSV/JSONL files rather than the original XLSX workbook.

## Format

Each JSONL example contains:

- `id`: stable example identifier.
- `template_id`: shared identifier for paraphrased variants of the same query template.
- `difficulty`: `easy`, `medium`, or `hard`.
- `question_source`: source question column in the spreadsheet.
- `combination`: operator composition label.
- `question`: natural-language query.
- `query`: gold Elasticsearch query body string.
- `es_query`: parsed query object, present for JSON-valid rows.
- `operators`, `observed_fields`, `computed_complexity`: audit metadata.

## Counts

- All expanded pairs: 6888.
- Clean JSON-valid pairs: 6796.
- Evaluation subset: 600 examples, 200 per difficulty level.

## Known caveat

The spreadsheet-derived counts differ from the counts stated in the manuscript. The package does not silently alter the source; malformed/non-JSON rows are kept in `medesq_all.jsonl` and excluded from default clean experiments.

## Ethical considerations

The data are based on de-identified public adverse event reports. They should be used for NLP and database-query research, not for clinical diagnosis or causal vaccine-safety conclusions.
