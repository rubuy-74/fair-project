# RDF Export Validation

Install the validator dependencies in a virtual environment:

```sh
python3 -m venv .venv
.venv/bin/pip install -r metadata/tests/requirements.txt
```

Validate the current export (defaults to `data/london_bikes.ttl`):

```sh
.venv/bin/python metadata/validate_export.py --report /tmp/london-bike-report.ttl
```

Validate a different export:

```sh
.venv/bin/python metadata/validate_export.py path/to/export.trig --report /tmp/report.ttl
```

The script loads only `shacl/london-bike-data-shapes.ttl`. No metadata or
vocabulary graph is needed. TriG parsing supports named graphs as well as plain
Turtle, even if a named-graph export has a `.ttl` extension. Literal lexical
forms are preserved so invalid boolean values are not silently normalized.

Exit codes: `0` for conformance, `1` for non-conformance, `2` for parsing,
validation setup errors, or an export with no applicable targets.

Run the CLI tests:

```sh
.venv/bin/python -m unittest discover -s metadata/tests -p 'test_*.py'
```

Validation checks the existing attributes and relation nodes, not row
completeness or agreement with the original CSV. A passing report alone does
not establish that every source field was exported correctly.
