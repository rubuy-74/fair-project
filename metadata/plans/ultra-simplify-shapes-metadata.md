# Ultra-simplify the shapes and metadata

## Confirmed decisions

1. **Flat entries** (your model): one node per data row, each of the 9 columns = one direct property with its own constraint block. Kills the 150-line `sh:xone` and the 9-nodes-per-row example. Tradeoff (accepted): non-canonical SOSA — the published spec restricts an `sosa:Observation` to **exactly 1** `sosa:observedProperty` (verified in the W3C Rec). We keep `a sosa:Observation` typing, `sosa:resultTime`, and the 9 properties as `sosa:ObservableProperty` instances, but values attach directly (`lbd:AirTemperature 3.0`) instead of via `sosa:observedProperty`/`sosa:hasSimpleResult`. Noted in README.
2. **DCAT record**: structured (agent + licence nodes, identifier, keywords, checksum) but compacted to one-line property blocks; comma-grouped lists (`dcterms:source <a>, <b>, <c>`; all 5 keywords on one line).

## Before → after

| File | Now (lines) | After (lines) |
|---|---|---|
| `shacl/london-bike-shapes.ttl` | 474 | ~100 |
| `metadata/london-bike-metadata.ttl` | 102 | ~55 |
| `examples/example-observation.ttl` | 53 | ~14 |
| `vocab/london-bike-vocabulary.ttl` | 54 | 54 (unchanged, you OK'd it) |
| **Total** | **683** | **~225** |

## New shapes file (~100 lines)

Six small shapes, one-line property blocks:

1. **`lbd:DatasetShape`** (`sh:targetClass dcat:Dataset`, closed): title, description, identifier, creator (`sh:class dcterms:Agent`), licence (`sh:class dcterms:LicenseDocument`), temporal (`sh:class dcterms:PeriodOfTime`), landingPage, source, keyword, distribution — one line each.
2. **`lbd:DistributionShape`** (closed): label, accessURL, `dcat:mediaType` hasValue "text/csv", byteSize ≥ 1, checksum (`sh:class spdx:Checksum`), tableSchema (`sh:class csvw:Schema`).
3. **`lbd:PeriodOfTimeShape`**: startDate/endDate xsd:dateTime.
4. **`lbd:ChecksumShape`**: algorithm = SHA-256, value = 64-hex pattern.
5. **`lbd:ColumnShape`** (`sh:targetClass csvw:Column`, closed): `csvw:name` ∈ 10 headers; `csvw:datatype` (string form) ∈ {"datetime", "integer", "decimal", "boolean", "string"}; `csvw:propertyUrl` ≤ 1 matching `^https://w3id.org/london-bike-sharing/`.
6. **`lbd:EntryShape`** (`sh:targetClass sosa:Observation`) — the star, exactly your model: 10 one-line blocks, one per column:
   - `sosa:resultTime`: xsd:dateTime within 2015-01-04 → 2017-01-03
   - `lbd:HourlyBikeShareCount`: xsd:integer ≥ 0, exactly 1
   - `lbd:AirTemperature` / `lbd:ApparentAirTemperature`: xsd:decimal, exactly 1
   - `lbd:RelativeHumidity`: xsd:decimal 0…100, exactly 1
   - `lbd:WindSpeed`: xsd:decimal ≥ 0, exactly 1
   - `lbd:WeatherCondition`: xsd:integer `sh:in (1 2 3 4 7 10 26 94)`, exactly 1
   - `lbd:IsHoliday` / `lbd:IsWeekend`: xsd:boolean, exactly 1
   - `lbd:Season`: xsd:integer `sh:in (0 1 2 3)`, exactly 1
   - Codes stay documented in the vocabulary comments (already there); the long in-shape descriptions go.
7. **`lbd:SchemaShape`**: `csvw:column` ≥ 10 (one line).

**Deleted**: the 150-line `sh:xone`, the 10 per-column pinning shapes, the 4 unit-pinning shapes, `DatatypeShape`, `AgentShape`, `LicenseDocumentShape` (class checks move inline into `DatasetShape`).

**What this gives up** (accepted for ultra-simplicity, noted in README):
- No guarantee that each variable is bound by exactly one CSVW column (generic column constraints only)
- A property could claim any of the 3 QUDT units and pass (generic `sh:in` still restricts to the 3)
- `sosa:Observation` typing is pragmatic, not canonical (exactly-1 rule above)

## New metadata file (~55 lines)

- Dataset record: same content, compacted (sources and keywords as comma lists, one line each)
- Agent (2 lines) + licence (3 lines) nodes kept
- Distribution (closed) + checksum, one line per property
- Table schema: 10 **blank-node** columns, **one line each**, `csvw:datatype` in string form (verified earlier: CSVW range allows string):
  `csvw:column [ a csvw:Column ; csvw:name "t1" ; csvw:datatype "decimal" ; csvw:propertyUrl "https://w3id.org/london-bike-sharing/AirTemperature" ] ,`

## New example file (~14 lines)

One flat entry — the first data row:

```turtle
lbd:row-2015-01-04T000000 a sosa:Observation ;
    sosa:resultTime "2015-01-04T00:00:00"^^xsd:dateTime ;
    lbd:HourlyBikeShareCount 182 ;
    lbd:AirTemperature 3.0 ;
    lbd:ApparentAirTemperature 2.5 ;
    lbd:RelativeHumidity 93.0 ;
    lbd:WindSpeed 6.0 ;
    lbd:WeatherCondition 3 ;
    lbd:IsHoliday false ;
    lbd:IsWeekend true ;
    lbd:Season 3 .
```

## README updates

Row-level schema section rewritten for flat entries (incl. the SOSA-canonicality note), file table with new line counts, code lists reference the vocabulary comments, validation section unchanged in substance.

## Steps

1. Rewrite `shacl/london-bike-shapes.ttl` (~100 lines)
2. Rewrite `metadata/london-bike-metadata.ttl` (~55 lines)
3. Rewrite `examples/example-observation.ttl` (~14 lines)
4. Validate: `pyshacl` shapes × (metadata + vocab) → conform; × (+ example) → conform
5. Negative test: an entry with weather code 99, humidity 150 and a missing required column → must be rejected
6. Update `README.md`
