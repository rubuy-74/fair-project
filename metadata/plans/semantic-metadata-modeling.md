# Semantic Metadata Modeling — `london_merged.csv` (FAIR)

## Revision changes (addressing your feedback)

1. **No SKOS** — code lists are now plain SHACL enumerations (`sh:in`) with the code→meaning documentation written directly in the shape's description. No separate code-list vocabulary, one less moving part.
2. **No "present/absent" commentary** — `weather_code` 94 is simply a valid member of the code list, full stop.
3. **Value ranges** — you were right to flag it: constraining to *observed* ranges is NOT the convention; it would wrongly reject valid future data (e.g. a 35 °C day). SHACL convention is to constrain only what is **semantically guaranteed** (counts ≥ 0, percentages 0–100, code enumerations). Observed min/max move to descriptive statistics in the README.
4. **DCAT record explained** — see §5: it's a machine-readable "catalog card" for the dataset.
5. **No `ex:` placeholder namespace** — project namespace named after the dataset (prefix `lbd:`, base `https://w3id.org/london-bike-sharing/`). The Kaggle link you provided goes into the record as the dataset's landing page + source (verified: creator Hristo Mavrodiev, TfL licence, sources TfL/freemeteo/gov.uk).
6. **Units self-defined** — creating all three ourselves is trivial work (3 nodes), so we define **all unit IRIs in the project namespace** (`lbd:DegreeCelsius`, `lbd:KilometrePerHour`, `lbd:Percent`), with label/symbol/UCUM code and an optional cross-reference to the QUDT equivalent — self-contained, no external unit vocabulary dependency.
7. **`weather_code` 94** — included as a normal valid code in the enumeration.

## 1. Objective

Define a machine-readable **semantic metadata model** for the London bike-sharing dataset, expressed primarily as a **SHACL shapes graph**, following FAIR principles (F2, I1–I3, R1). The data stays as CSV; the model is a schema-level sidecar describing the dataset, its columns, their semantics and units — plus a reusable shape for future row-level RDF-ization. The model is self-contained: only W3C standards are reused (DCAT, DCTERMS, SOSA/SSN, SHACL itself); all dataset-specific terms live in the project vocabulary.

## 2. Data profile (grounding, verified)

- 17,414 hourly records, `2015-01-04T00:00` → `2017-01-03T23:00`, strictly monotonic, 130 missing hours (factual note in README)
- No missing values; 10 columns

| Column | Domain | Datatype |
|---|---|---|
| `timestamp` | 2015-01-04 → 2017-01-03, hourly cadence | xsd:dateTime |
| `cnt` | count of new bike shares | xsd:integer |
| `t1` | real temperature in C | xsd:decimal |
| `t2` | temperature in C "feels like" | xsd:decimal |
| `hum` | humidity in percentage | xsd:decimal |
| `wind_speed` | wind speed in km/h | xsd:decimal |
| `weather_code` | {1, 2, 3, 4, 7, 10, 26, 94} | coded |
| `is_holiday` | {0, 1} | xsd:boolean |
| `is_weekend` | {0, 1} | xsd:boolean |
| `season` | {0, 1, 2, 3} (spring/summer/fall/winter) | coded |

- Upstream semantics of `cnt` (from the TfL source, verified): count of **new** bike-share hires grouped by **start hour**; long-duration hires are excluded.

## 3. Vocabulary design

| Vocabulary | Role |
|---|---|
| **SHACL** | The model itself: shapes + inline code lists (`sh:in`) with code→meaning documentation in the shape descriptions |
| **DCAT + DCTERMS** | Dataset-level catalog record only (title, creator, license, temporal coverage, distribution, provenance) |
| **SOSA/SSN** | Observation schema: each variable is a `sosa:ObservableProperty`; a row (if ever RDF-ized) is a `sosa:Observation` with `sosa:resultTime` |
| **`lbd:` project vocabulary** | All dataset-specific terms: 10 observable properties + 3 units, all owned by the project — no SKOS, no QUDT dependency |

Code lists (e.g. `weather_code`) are documented as: `sh:in (1 2 3 4 7 10 26 94)` + description text "1 = Clear; 2 = scattered/few clouds; 3 = broken clouds; 4 = cloudy; 7 = rain/light rain shower; 10 = rain with thunderstorm; 26 = snowfall; 94 = freezing fog". Machine-enumerable values, human-readable meanings, one place — no extra vocabulary needed.

Units — all three self-defined in the project namespace (each: label, symbol, UCUM code, `rdfs:seeAlso` to its QUDT counterpart for interop, without depending on it):

| Unit IRI | Symbol | UCUM |
|---|---|---|
| `lbd:DegreeCelsius` | °C | `Cel` |
| `lbd:KilometrePerHour` | km/h | `km/h` |
| `lbd:Percent` | % | `%` |

## 4. Column → term mapping (constraints = semantic domains only, per convention)

| Column | ObservableProperty (`lbd:`) | Datatype | Unit | Value constraints |
|---|---|---|---|---|
| `timestamp` | — (`sosa:resultTime`) | xsd:dateTime | — | within 2015-01-04 → 2017-01-03 |
| `cnt` | `HourlyBikeShareCount` | xsd:integer | — | `sh:minInclusive 0` |
| `t1` | `AirTemperature` | xsd:decimal | `lbd:DegreeCelsius` | — (datatype + unit only) |
| `t2` | `ApparentAirTemperature` | xsd:decimal | `lbd:DegreeCelsius` | — (datatype + unit only) |
| `hum` | `RelativeHumidity` | xsd:decimal | `lbd:Percent` | 0 … 100 |
| `wind_speed` | `WindSpeed` | xsd:decimal | `lbd:KilometrePerHour` | `sh:minInclusive 0` |
| `weather_code` | `WeatherCondition` | coded | — | `sh:in {1, 2, 3, 4, 7, 10, 26, 94}` |
| `is_holiday` | `IsHoliday` | xsd:boolean | — | true/false |
| `is_weekend` | `IsWeekend` | xsd:boolean | — | true/false |
| `season` | `Season` | coded | — | `sh:in {0, 1, 2, 3}` |

Observed ranges (cnt 0–7860; t1 −1.5–34.0; t2 −6.0–34.0; hum 20.5–100.0; wind 0–56.5) are recorded as **descriptive statistics** in the README, not as validation constraints.

## 5. Deliverables

```
vocab/
  london-bike-vocabulary.ttl   lbd: 10 observable properties + 3 units
metadata/
  london-bike-metadata.ttl     DCAT catalog record (see below)
shacl/
  london-bike-shapes.ttl       SHACL shapes graph — the core deliverable
examples/
  example-observation.ttl       1–2 rows as sosa:Observation (smoke test)
README.md                       mapping table, observed stats, FAIR coverage, validation how-to
```

**What is the DCAT record?** (`metadata/london-bike-metadata.ttl`)
It is a machine-readable **catalog card** for the dataset — the same information you fill in when publishing on Zenodo/Kaggle (title, description, author, license, time span, keywords, download link), but written as RDF using the W3C **Data Catalog Vocabulary (DCAT)** so data catalogs and harvesters can ingest it automatically (this is what makes it *Findable*). It will contain:

- Title: "London bike sharing dataset" · Creator: Hristo Mavrodiev
- Description: historical bike-share counts with weather, London, hourly, 2015–2017
- Landing page: https://www.kaggle.com/datasets/hmavrodiev/london-bike-sharing-dataset
- License: TfL Open Data Licence (OGL v2.0-based), attribution "Powered by TfL Open Data"
- Provenance/sources: TfL cycling data (cycling.data.tfl.gov.uk) · freemeteo.com (weather) · gov.uk/bank-holidays
- Temporal coverage: 2015-01-04 → 2017-01-03
- Distribution: points at `london_merged.csv` (media type text/csv, byte size, checksum)

**SHACL shapes** (`shacl/london-bike-shapes.ttl`) — what it constrains:

1. **Dataset shape** (`sh:targetClass dcat:Dataset`): required title, description, identifier, license; ≥1 distribution; temporal coverage; landing page; sources; closed shape.
2. **Distribution shape** (`dcat:Distribution`): media type text/csv, byte size > 0, access URL, checksum.
3. **ObservableProperty shape** (`sosa:ObservableProperty`): required label + source column name (`sh:in` the 10 real CSV headers); unit required exactly where the mapping table says so, and must be one of the 3 `lbd:` units.
4. **Unit shape**: required label, symbol, UCUM code.
5. **Observation shape** (`sosa:Observation`): the reusable row schema — `sosa:resultTime` xsd:dateTime within coverage; per-variable result datatype + the semantic-domain constraints from §4. Ready for any future row-level RDF-ization; smoke-tested on `examples/example-observation.ttl`.

## 6. Execution steps

1. Set up tooling: `pip install pyshacl rdflib` (neither is currently installed).
2. Write `vocab/london-bike-vocabulary.ttl` (10 properties + 3 units, `lbd:` namespace).
3. Write `metadata/london-bike-metadata.ttl` (DCAT record with the content above).
4. Write `shacl/london-bike-shapes.ttl`.
5. Validate: `pyshacl` shapes × (vocabulary + metadata) → iterate to zero violations.
6. Smoke-test the Observation shape against `examples/example-observation.ttl`.
7. Write `README.md` (mapping table, descriptive stats, FAIR coverage, validation instructions).

## 7. FAIR coverage

| Principle | How the model satisfies it |
|---|---|
| F1 | Dataset IRI + identifier + checksum (persistent `lbd:` namespace) |
| F2 | Rich metadata: DCAT record + variable-level semantics + constraints |
| F3 | Metadata references the data file explicitly via `dcat:Distribution` |
| I1 | RDF + SHACL: formal, machine-readable semantics, machine-validatable |
| I2 | Reuses W3C standards (DCAT, DCTERMS, SOSA/SSN, SHACL); project terms cross-referenced to QUDT equivalents |
| I3 | Interlinks: landing page, sources (TfL, freemeteo, gov.uk), unit cross-references |
| R1 | Provenance (creator, sources), descriptive statistics |
| R1.1 | License: TfL Open Data Licence, attribution included |
| R1.3 | Community standards: DCAT, SOSA/SSN, SHACL |

## 8. Resolved in this revision (from your feedback + upstream verification)

- License: TfL Open Data Licence (OGL v2.0-based) · Creator: Hristo Mavrodiev · Landing page: the Kaggle URL you provided.
- Sources: TfL cycling data + freemeteo (weather) + gov.uk (bank holidays) — verified via the Kaggle dataset metadata.
- Code lists: inline SHACL `sh:in` enumerations, including 94 as a plain valid code.
- Units: all self-defined (`lbd:` namespace), no external unit vocabulary dependency.

## 9. Remaining open items

1. **Namespace base** for `lbd:` — proposed `https://w3id.org/london-bike-sharing/` (persistent IRIs, free one-line registration at w3id.org; can be swapped to any other base later with a one-line change). OK?
