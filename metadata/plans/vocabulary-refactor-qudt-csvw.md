# Vocabulary refactor: QUDT units + CSVW columns, zero custom glue terms

## Revision changes (from the discussion)

1. **Units → QUDT (verified)**: delete `lbd:Unit`, `lbd:DegreeCelsius`, `lbd:KilometrePerHour`, `lbd:Percent`, `lbd:symbol`, `lbd:ucumCode`. QUDT already ships all three units with symbols and UCUM codes — including the correct `km.h-1` UCUM code for km/h (our hand-rolled `"km/h"` was non-standard):
   - `unit:DEG_C` (°C, Cel) · `unit:KiloM-PER-HR` (km/h, km.h-1) · `unit:PERCENT` (%, %)
   - Linking property: `lbd:unit` → **`qudt:hasUnit`** (schema-level link; `qudt:unit` is for measured values)
2. **`lbd:sourceColumn` → CSVW (verified)**: columns become `csvw:Column` nodes (see design below); `lbd:sourceColumn` deleted.
3. **`lbd:variable` → deleted**: only lived in the metadata file; derivable via dataset → distribution → tableSchema → column → propertyUrl → property.
4. Result: **no custom classes or properties remain** — the only `lbd:` terms are the 9 `ObservableProperty` instances (inherently dataset-specific) plus record node IRIs (dataset, distribution, agent, licence).

## Verified CSVW terms used (from https://www.w3.org/ns/csvw)

| Term | Verified semantics |
|---|---|
| `csvw:Table` / `csvw:tableSchema` | table → schema description (domain: Table/TableGroup) |
| `csvw:Schema` / `csvw:column` | schema → column descriptions (range csvw:Column) |
| `csvw:Column` / `csvw:name` | canonical column name (range xsd:string) |
| `csvw:datatype` / `csvw:Datatype` / `csvw:base` | datatype object with base term: `"datetime"`, `"integer"`, `"decimal"`, `"boolean"`, `"string"` (all map to xsd:* in the term definitions) |
| `csvw:propertyUrl` | column → property binding. **Caveat: range is `csvw:uriTemplate` (⊑ xsd:string)** — the binding is the property URI as a *string*, not an IRI edge. Standard CSVW, but SPARQL traversals need string matching |

## New design

### Column binding table (replaces sourceColumn)

| Column (`csvw:name`) | `csvw:base` | `csvw:propertyUrl` (string) |
|---|---|---|
| `timestamp` | `datetime` | — (maps to `sosa:resultTime`, not a variable) |
| `cnt` | `integer` | `.../HourlyBikeShareCount` |
| `t1` | `decimal` | `.../AirTemperature` (unit `unit:DEG_C`) |
| `t2` | `decimal` | `.../ApparentAirTemperature` (unit `unit:DEG_C`) |
| `hum` | `decimal` | `.../RelativeHumidity` (unit `unit:PERCENT`) |
| `wind_speed` | `decimal` | `.../WindSpeed` (unit `unit:KiloM-PER-HR`) |
| `weather_code` | `integer` | `.../WeatherCondition` |
| `is_holiday` | `boolean` | `.../IsHoliday` |
| `is_weekend` | `boolean` | `.../IsWeekend` |
| `season` | `integer` | `.../Season` |

### File changes

**1. `vocab/london-bike-vocabulary.ttl`** — shrinks to the 9 `sosa:ObservableProperty` instances (label, comment, `qudt:hasUnit` where applicable). All term declarations and units deleted. Prefixes: `lbd:`, `sosa:`, `qudt:`, `unit:`, `rdfs:`.

**2. `metadata/london-bike-metadata.ttl`**:
- Dataset: drop the 9 `lbd:variable` links (everything else unchanged)
- Distribution: dual-typed `a dcat:Distribution, csvw:Table`, gains `csvw:tableSchema` → `lbd:londonMergedCsvSchema a csvw:Schema` with 10 named column nodes (`lbd:columnTimestamp` … `lbd:columnSeason`), each: `csvw:name`, `csvw:datatype [ a csvw:Datatype ; csvw:base "…" ]`, and `csvw:propertyUrl "https://w3id.org/london-bike-sharing/…"` (9 of 10; not the timestamp column)

**3. `shacl/london-bike-shapes.ttl`**:
- `DatasetShape`: remove the `lbd:variable` property shape
- `DistributionShape`: add `csvw:tableSchema` (exactly 1, `sh:class csvw:Schema`)
- New `SchemaShape` (`sh:targetClass csvw:Schema`): `csvw:column` exactly 10, each `sh:class csvw:Column`
- New `ColumnShape` (`sh:targetClass csvw:Column`, closed): `csvw:name` exactly 1 with `sh:in` (the 10 real headers), `csvw:datatype` exactly 1 `sh:class csvw:Datatype`, `csvw:propertyUrl` maxCount 1
- New `DatatypeShape` (`sh:targetClass csvw:Datatype`): `csvw:base` exactly 1, `sh:in ("datetime" "integer" "decimal" "boolean" "string")`
- New per-column pinning shapes (same `sh:targetNode` pattern as the unit shapes): 10 shapes pinning each column node's `csvw:name`, `csvw:base`, and `csvw:propertyUrl` — guarantees each variable bound exactly once, no SPARQL needed
- `ObservablePropertyShape`: drop `lbd:sourceColumn`; `lbd:unit` → `qudt:hasUnit` (maxCount 1, `sh:in (unit:DEG_C unit:KiloM-PER-HR unit:PERCENT)`)
- The 4 unit-pinning `sh:targetNode` shapes: `qudt:hasUnit` `sh:hasValue unit:DEG_C` / `unit:PERCENT` / `unit:KiloM-PER-HR` respectively
- Delete `UnitShape` (`sh:targetClass lbd:Unit`)
- `ObservationShape`: unchanged

**4. `examples/example-observation.ttl`** — unchanged (no glue terms referenced).

**5. `README.md`** — updated: files table, mapping table (columns now via `csvw:name`/`csvw:base`/`csvw:propertyUrl`/QUDT units), design notes (propertyUrl-as-string caveat, why timestamp column has no propertyUrl), FAIR coverage (I2 now: DCAT, SOSA/SSN, QUDT, CSVW, SHACL, DCTERMS).

### Execution steps

1. Rewrite `vocab/london-bike-vocabulary.ttl` (9 properties + QUDT links)
2. Rewrite `metadata/london-bike-metadata.ttl` (drop variables; add CSVW schema + columns)
3. Update `shacl/london-bike-shapes.ttl` (shape changes above)
4. Re-validate: `pyshacl` shapes × (vocab + metadata) → zero violations; re-run example + negative test (unchanged files must still pass)
5. Update `README.md`

## What the model looks like after (term census)

| Vocabulary | Terms used |
|---|---|
| DCAT/DCTERMS/SPDX | dataset record + distribution |
| SOSA/SSN | `sosa:ObservableProperty` (×9), `sosa:Observation` schema |
| QUDT | `qudt:hasUnit`, `unit:DEG_C`, `unit:KiloM-PER-HR`, `unit:PERCENT` |
| CSVW | Table/Schema/Column/Datatype/name/base/datatype/tableSchema/propertyUrl |
| `lbd:` (custom) | **only instance IRIs** — 9 observable properties + record nodes; zero custom classes/properties |
