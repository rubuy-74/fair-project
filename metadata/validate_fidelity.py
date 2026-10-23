"""Compare every original CSV row with its zero-based row-index RDF observation."""

import argparse
import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import sys
import time

import rdflib
from rdflib import Dataset, Literal, Namespace, RDF, URIRef, XSD


BASE = Namespace("http://localhost:3333/")
SCHEMA = Namespace("http://schema.org/")
OBO = Namespace("http://purl.obolibrary.org/obo/")
WD = Namespace("https://www.wikidata.org/entity/")
SEASON_TYPE = URIRef("http://www.wikidata.org/entity/Q24384")
WEATHER_TYPE = URIRef("http://www.wikidata.org/entity/Q11663")
# Preserve the shipped reconciliations, including the shared weather categories.
WEATHER = {1: WD.Q13424349, 2: WD.Q13424349, 3: WD.Q1055865,
           4: WD.Q1055865, 7: WD.Q133224208, 10: WD.Q2857578,
           26: WD.Q75078783}
SEASONS = {0: WD.Q1312, 1: WD.Q1313, 2: WD.Q1314, 3: WD.Q1311}
ATTRIBUTES = (
    ("is_holiday", "is_holiday", WD.Q1445650, "Public holiday", None),
    ("is_weekend", "is_weekend", WD.Q211391, "Weekend", None),
    ("temperature", "t1", URIRef("http://qudt.org/vocab/quantitykind/Temperature"),
     "Air temperature", "CEL"),
    ("temperature_sensation", "t2", URIRef("https://bimerr.iot.linkeddata.es/def/weather#feels_like"),
     "Feels-like temperature", "CEL"),
    ("humidity", "hum", URIRef("https://bimerr.iot.linkeddata.es/def/weather#Humidity"),
     "Relative humidity", "P1"),
    ("wind_speed", "wind_speed", URIRef("https://bimerr.iot.linkeddata.es/def/weather#WindSpeed"),
     "Wind speed", "KMH"),
)
COLUMNS = {"timestamp", "cnt", "t1", "t2", "hum", "wind_speed", "weather_code",
           "is_holiday", "is_weekend", "season"}


def validate_fidelity(data, source):
    """Return fidelity errors; source is an open CSV text stream, data a union graph."""
    errors = []
    observations, attributes, relations, categories = set(), set(), set(), set()

    def exact(subject, predicate, expected):
        actual = set(data.objects(subject, predicate))
        if actual != set(expected):
            errors.append(f"{subject} {predicate}: expected {set(expected)!r}, got {actual!r}")

    def number(subject, predicate, raw, datatype):
        values = list(data.objects(subject, predicate))
        valid = False
        if len(values) == 1:
            value = values[0]
            if isinstance(value, Literal) and value.datatype == datatype and not value.ill_typed:
                if datatype == XSD.boolean:
                    valid = str(value) in ("true", "false", "1", "0") and (
                        value.toPython() == bool(Decimal(raw)))
                else:
                    try:
                        valid = Decimal(str(value)) == Decimal(raw)
                    except ArithmeticError:
                        pass
        if not valid:
            errors.append(f"{subject} {predicate}: expected {raw} as {datatype}, got {values!r}")

    reader = csv.DictReader(source)
    if set(reader.fieldnames or ()) != COLUMNS:
        raise ValueError("CSV must contain exactly the original ten source columns")
    for index, row in enumerate(reader):
        observation = BASE[str(index)]
        observations.add(observation)
        exact(observation, RDF.type, [SCHEMA.Observation])
        timestamp = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
        exact(observation, BASE.timestamp, [Literal(timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
                                                   datatype=XSD.dateTime, normalize=False)])
        number(observation, SCHEMA.measuredValue, row["cnt"], XSD.int)
        weather = Decimal(row["weather_code"])
        season = Decimal(row["season"])
        if weather not in (1, 2, 3, 4, 7, 10, 26, 94) or season not in SEASONS:
            raise ValueError(f"Row {index}: unsupported source weather/season code")
        number(observation, BASE.weather_code, row["weather_code"], XSD.int)
        # Code 94 has no shipped reconciliation (and no rows in the original CSV).
        # Refuse to invent a mapping if a different source introduces it.
        if weather not in WEATHER:
            raise ValueError(f"Row {index}: no existing weather IRI mapping for code {weather}")
        weather_iri, season_iri = WEATHER[int(weather)], SEASONS[int(season)]
        categories.update((weather_iri, season_iri))
        exact(observation, BASE.weather, [weather_iri])
        exact(observation, SCHEMA.measuredProperty, [SCHEMA.RentAction])
        exact(observation, OBO.BFO_0000066, [OBO.GAZ_00003672])
        for name, column, quantity, label, unit in ATTRIBUTES:
            attribute = BASE[f"{index}/{name}"]
            attributes.add(attribute)
            exact(observation, BASE[name], [attribute])
            exact(attribute, RDF.type, [SCHEMA.PropertyValue])
            exact(attribute, SCHEMA.propertyID, [quantity])
            exact(attribute, SCHEMA.name, [Literal(label, lang="en")])
            exact(attribute, SCHEMA.unitCode, [] if unit is None else [Literal(unit)])
            if unit is None and Decimal(row[column]) not in (0, 1):
                raise ValueError(f"Row {index}: invalid source flag {column}")
            number(attribute, SCHEMA.value, row[column], XSD.boolean if unit is None else XSD.double)
        linked = set(data.objects(observation, OBO.RO_0002092))
        if len(linked) != 2:
            errors.append(f"{observation}: expected two distinct relation nodes, got {len(linked)}")
        for kind, category in ((SEASON_TYPE, season_iri), (WEATHER_TYPE, weather_iri)):
            matches = {node for node in linked if (node, RDF.type, kind) in data}
            if len(matches) != 1:
                errors.append(f"{observation}: expected one relation of type {kind}")
            for node in matches:
                exact(node, RDF.type, [kind])
                exact(node, SCHEMA.value, [category])
        if relations.intersection(linked):
            errors.append(f"{observation}: relation nodes shared between observations")
        relations.update(linked)

    if not observations:
        errors.append("No source observations; refusing a vacuous fidelity pass")
    for kind, expected in ((SCHEMA.Observation, observations), (SCHEMA.PropertyValue, attributes)):
        actual = set(data.subjects(RDF.type, kind))
        if actual != expected:
            errors.append(f"{kind}: missing {len(expected - actual)}, unexpected {len(actual - expected)} nodes")
    typed_relations = set(data.subjects(RDF.type, SEASON_TYPE)) | set(data.subjects(RDF.type, WEATHER_TYPE))
    if typed_relations != relations:
        errors.append("Relation node inventory differs from observation links (missing or orphan nodes)")
    unexpected = set(data.subjects()) - observations - attributes - relations - categories
    if unexpected:
        errors.append(f"Unexpected/orphan subject nodes: {len(unexpected)}; example: {next(iter(unexpected))}")
    return errors


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path, nargs="?", default=root / "data/london_bikes.ttl")
    parser.add_argument("--csv", type=Path, default=root / "data/london_merged-original.csv")
    parser.add_argument("--format", choices=("turtle", "trig"), default="trig")
    args = parser.parse_args()
    rdflib.NORMALIZE_LITERALS = False
    try:
        started = time.perf_counter()
        print(f"Loading {args.export}", flush=True)
        data = Dataset(default_union=True)
        data.parse(args.export, format=args.format)
        print(f"Loaded in {time.perf_counter() - started:.1f}s", flush=True)
        started = time.perf_counter()
        with args.csv.open(newline="", encoding="utf-8-sig") as source:
            errors = validate_fidelity(data, source)
        print(f"Fidelity: {not errors}. Errors: {len(errors)}. Checked in {time.perf_counter() - started:.1f}s")
        for error in errors[:20]:
            print(f"  {error}")
        if len(errors) > 20:
            print(f"  {len(errors) - 20} more errors")
        return 1 if errors else 0
    except Exception as error:
        print(f"Fidelity error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
