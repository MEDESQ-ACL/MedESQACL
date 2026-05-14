# Limitations and Risks

- The clean default dataset excludes malformed JSON rows from the uploaded spreadsheet instead of silently repairing them.
- Execution-based pass rate requires a compatible Elasticsearch index; without it, exact canonical match is only a proxy.
- API-based model results can drift when hosted model versions change.
- VAERS-style adverse event data are appropriate for signal screening research, not causal medical conclusions.
- Some query fields appear in the spreadsheet but not in the narrower paper prompt schema; both schema lists are included for transparency.
