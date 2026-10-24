# Three Local Queries

Run the selected queries with Python 3 and RDFLib (tested with 7.6.0):

```sh
/tmp/opencode/fair-venv/bin/python -B queries/run.py
/tmp/opencode/fair-venv/bin/python -B queries/test_run.py
```

The interpreter path is the available local virtual environment. Any Python
environment with RDFLib installed can be used instead. No endpoint, server,
remote download, or URI dereferencing is used.

JSON is written to stdout, progress to stderr. Default paths are relative to
the repository, independent of the working directory. Optional `--data` and
`--metadata` select other local files. The SPARQL files can also run directly in
a local SPARQL 1.1 engine against the indicated graph.

## What Each Query Contributes

| Query | Question | Output | Project Value |
| --- | --- | --- | --- |
| `calendar.rq` | How does rental demand differ on weekends and public holidays? | Observed hours, total hires and mean hourly hires for each boolean flag | Compares demand across calendar contexts |
| `measurements.rq` | How does demand vary with temperature, feels-like temperature, humidity and wind speed? | Measurement identifier, unit, bin bounds, observed hours and mean hourly hires | Demonstrates analysis across semantically identified, unit-bearing measurements |
| `metadata.rq` | Who created the dataset, where did it come from, and what is known about reuse rights? | Creator, source links, provenance, rights and any explicit licence | Makes attribution and reuse constraints inspectable |

JSON output contains exactly three keys: `calendar.rq`, `measurements.rq`, and
`metadata.rq`. Each key maps directly to that query's result rows. Weekend and
holiday results are together under `calendar.rq`, distinguished by `flag`.

## Local Data and Model

The calendar and measurement queries use `data/london_bikes.ttl`. The metadata
query uses `data/london-bike-metadata.ttl`. No CSV is read by the runner.

Schema.org uses `http://schema.org/`. Rental counts are in `schema:value`.
Calendar flags and measurements are linked through `schema:additionalProperty`
and identified by `schema:propertyID`, not observation-specific resource paths.
The queries do not use the old `http://localhost:3333/` properties.

## Interpretation

- Calendar flags are analysed separately, not as a joint weekend/holiday grouping.
  Mean hourly hires are more comparable than totals when groups contain different
  numbers of observed hours. Non-holiday hours can include weekends.
- Measurement bins are half-open `[lower, upper)`: 5 Celsius for both temperature
  measures, 10 percentage points for humidity and 5 km/h for wind. An observation
  contributes once to each of the four measurement analyses, so their sample
  counts should not be summed as distinct observation counts.
- All aggregates describe available observations, not imputed missing hours.
  They show associations, not causal effects; there is no adjustment for season,
  hour of day or other confounding variables.
- Metadata reports rights uncertainty, not verified permission to redistribute
  the combined dataset. An absent licence is not an open licence. Blank-node
  identifiers are run-local, and source URLs are reported without being accessed.
- Query execution and regression tests are not full SHACL conformance, FAIR
  certification, CSV-to-RDF fidelity or remote-deployment checks.
