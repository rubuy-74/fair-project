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

Validation checks the observations and their attributes, not row
completeness or agreement with the original CSV. A passing report alone does
not establish that every source field was exported correctly.

## Publication Metadata

Project landing page: <https://github.com/rubuy-74/fair-project>.
The publication namespace remains
`https://w3id.org/FAIR-course-UT/2026/group20/`. Deployment is in progress.
The file routes below are planned placeholders, not verified working endpoints.

| Distribution | Planned access and download URL | Local file |
| --- | --- | --- |
| RDF | `https://w3id.org/FAIR-course-UT/2026/group20/data/london_bikes.ttl` | `data/london_bikes.ttl` |
| CSV | `https://w3id.org/FAIR-course-UT/2026/group20/data/london_merged-original.csv` | `data/london_merged-original.csv` |

The CSV also retains its Kaggle access page. Both distribution descriptions
explicitly say **deployment pending**. Metadata syntax/completeness validation
does not test URL reachability, download behavior, or redistribution rights.
The metadata and distribution resource identities have not been renamed.

Integrity metadata describes the current local files, which are not changed by
metadata preparation:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| RDF | 47187685 | `3de43362884fbca8413d470899335474eb769405a45afa2ab36527e55e8a1a09` |
| CSV | 1034821 | `db881c26314329377f81265480856f2fe4fb049fc1e79bd5f548813c99c4c446` |

The values remain valid if these exact bytes are published unchanged. If a file
changes, update its size and checksum. After deployment, download each file and
compare it with the recorded values before removing the pending wording.
Confirm or correct the planned routes, media types, and identifier redirects.
In particular, confirm that file URLs return file bytes rather than HTML pages.

Run the metadata-only regression suite, including both the local profile and
the publication syntax/completeness profile:

```sh
.venv/bin/python -B -m unittest discover -s metadata/tests -p 'test_metadata.py'
```

This avoids the historical observation fixtures in `metadata/tests/validate.py`,
which still describe the previous RDF model. The full historical test suite is
not evidence that the current export or deployment has been validated.

## Attribution and Reuse

Hristo Mavrodiev is the original dataset compiler. **Rubem Neto** and
**Pedro Oliveira** are the FAIRification contributors, recorded separately as
`dcterms:contributor`. No publisher institution, contact address, or licence
grant has been inferred.

Suggested citation, pending a release version and date:

> Neto, Rubem; Oliveira, Pedro. London bike sharing dataset: FAIRified RDF
> representation. Based on the dataset compiled by Hristo Mavrodiev.
> https://github.com/rubuy-74/fair-project

**Powered by TfL Open Data.** Combined-source rights remain unresolved as
described in [rights-notes.md](rights-notes.md). The planned URLs are not
permission to redistribute the files. Confirm applicable terms before public
redistribution; add a licence URI only when supported by that evidence.

## Model and Reproducibility

Each `schema:Observation` has a rental count in `schema:value`, the measured
property `ont:hourlyBikeRental`, an observation date, direct weather/season
category links, and six `schema:additionalProperty` attributes. Attributes have
names, quantity identifiers, typed values, and units where applicable:
`CEL` for both temperatures, `P1` for relative humidity, and `KMH` for wind speed.
Holiday and weekend attributes are booleans. Here `ont:` denotes
`https://w3id.org/FAIR-course-UT/2026/group20/ont#`; the ontology is maintained at
`data/hourlyBikeRentalOnt.ttl`.

The course SHACL profile accepts the teacher-approved minute-precision timestamp
convention, including `Z`. The recorded coverage endpoints do not imply an
uninterrupted hourly series. The latest full course-profile validation checked
17,414 observations and 104,484 attributes with zero violations using RDFLib
7.6.0 and pySHACL 0.40.1. This is structural validation, not external FAIR
certification. Re-run the export command above after any observation-file change.

A minimal SPARQL query for the current model is:

```sparql
PREFIX schema: <http://schema.org/>
SELECT ?observation ?time ?rentals
WHERE {
  ?observation a schema:Observation ;
      schema:observationDate ?time ;
      schema:value ?rentals .
}
ORDER BY ?time
LIMIT 10
```

The original input is `data/london_merged-original.csv`; its checksum above
identifies the input bytes. `data/london_bikes.json` preserves OpenRefine operation
history and RDF Transform mappings, including a recorded RDF Transform version
of 2.3.6. Its final mapping still contains the older `2025-2026` namespace,
whereas the current export uses `2026`. The history is retained unchanged and
is not yet a complete reproduction recipe for the current export. Reconcile
that difference and document the exact preprocessing, OpenRefine version, and
export procedure for the release rather than silently rewriting historical
operations.

Release version/date, a maintainer contact, identifier-maintenance commitments,
metadata-retention policy, and catalog registration remain pending. They have
not been invented or added as completed metadata fields.
