# Local Competency Question Evidence

Run from the repository root (no endpoint, server, or network required):

```sh
/tmp/opencode/fair-report-venv/bin/python queries/run.py
/tmp/opencode/fair-report-venv/bin/python queries/run.py --hour 2015-07-01T08:00:00
```

Requires Python 3 and RDFLib (tested with 7.6.0 in the supplied environment).
Full-graph parsing took about 31 seconds; unaffected queries took about 29
seconds together. Small corrected/pending-path checks can be run with:

```sh
/tmp/opencode/fair-report-venv/bin/python queries/test_run.py
```

JSON is written to stdout, progress to stderr. Paths default to this repository,
independent of the working directory. Optional `--data`, `--metadata`, and `--csv`
accept alternative local files. All queries can also run directly in a local
SPARQL 1.1 engine against the indicated graph.

| Report question | Query | Evidence |
| --- | --- | --- |
| CQ1: given hour | `hour.rq` | Observation, timestamp and hire count; edit the example literal or use `--hour` |
| CQ2: weekend | `calendar.rq` | Hours, total and mean hourly hires by weekend flag |
| CQ3: bank holiday | `calendar.rq` | Hours, total and mean hourly hires by holiday flag |
| CQ4: measurements | `measurements.rq` | Mean hourly hires by measurement bin, with units and sample sizes |
| CQ5: season | `seasons.rq` | Hours, total and mean hourly hires for four season entities |
| CQ6: original weather | `weather.rq` | Hours, total and mean hourly hires for each preserved original code |
| CQ7: absent hours | `timestamps.rq` + runner | Inclusive hourly grid, missing timestamps and duplicate-slot counts |
| CQ8: attribution/rights | `metadata.rq` | Creator, sources, rights, any explicit licence and provenance |
| CQ9: access/integrity | `distributions.rq` + runner | Both distributions, recorded access/download links and checksums; local CSV SHA-256 comparison |

Observation queries use `data/london_bikes.ttl`; metadata queries use
`data/london-bike-metadata.ttl`. Schema.org uses `http://schema.org/`, and the
local base is `http://localhost:3333/`. No URI is dereferenced. Season wrappers
have HTTP Wikidata types and HTTPS season values; weather entity wrappers are
not used to reconstruct original codes because their mapping is lossy.

## Interpretation

- Timestamps must be `YYYY-MM-DDTHH:MM:SS`, timezone unspecified. The runner
  requires hour-aligned values and refuses CQ1/CQ7 while timestamps retain `Z`
  or any other timezone. It never removes an offset or assumes UTC.
- CQ7 compares the observed minimum and maximum inclusively, not a timezone-
  aware calendar or an extrapolated coverage period. The JSON includes every
  missing slot, not just a count. No daylight-saving explanation is assumed.
- CQ6 requires exactly one `base:weather_code` with datatype `xsd:int` per
  observation and all seven source codes: 1, 2, 3, 4, 7, 10 and 26. Missing or
  partial correction is reported as pending rather than silently undercounted.
- CQ4 bins are half-open `[lower, upper)`: 5 Celsius for both temperatures,
  10 percentage points for humidity and 5 km/h for wind. These are descriptive,
  unadjusted associations, not evidence of causal effects. Means are over
  available observations only, not imputed missing hours.
- CQ8 reports `dcterms:rights` uncertainty, not a verified licence covering the
  combined dataset. Blank-node identifiers in JSON are run-local identifiers.
- CQ9 preserves distributions with no public URL. The RDF distribution is local;
  public RDF access remains pending until a deployment URL is actually recorded.
  A Kaggle access page is not a direct download URL. The CSV checksum check reads
  local bytes and does not establish remote availability or permission to reuse.

## Results Policy

No expected aggregates or frozen results are bundled while the main RDF is
being corrected. The runner always computes evidence from the current files;
`context.corrected_data_ready` indicates timestamp and weather-code readiness,
not full SHACL conformance or CSV-to-RDF fidelity. Unaffected calendar,
measurement and season aggregates can be inspected before those corrections.
Only archive stdout as `queries/results.json` after the final graph and metadata
are ready and `corrected_data_ready` is true. Public RDF publication and complete
reuse permissions can still remain pending in that evidence.
