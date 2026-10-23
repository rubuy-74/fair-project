"""Run local competency-question evidence without an endpoint or network calls."""

import argparse
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
from time import perf_counter

import rdflib
from rdflib import Graph, Literal, Namespace, RDF, XSD


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = Namespace("http://localhost:3333/")
SCHEMA = Namespace("http://schema.org/")


def query(graph, filename, **bindings):
    started = perf_counter()
    print(f"Running {filename}...", file=sys.stderr, flush=True)
    result = graph.query((HERE / filename).read_text(), initBindings=bindings)
    rows = []
    for row in result:
        values = {}
        for key, term in row.asdict().items():
            value = term.toPython() if isinstance(term, Literal) else str(term)
            if isinstance(value, Decimal):
                value = float(value)
            elif isinstance(value, bytes):
                value = value.hex()
            elif not isinstance(value, (str, int, float, bool)):
                value = str(value)
            values[str(key)] = value
        rows.append(values)
    print(f"{filename}: {len(rows)} rows in {perf_counter() - started:.1f}s", file=sys.stderr)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data/london_bikes.ttl")
    parser.add_argument("--metadata", type=Path, default=ROOT / "data/london-bike-metadata.ttl")
    parser.add_argument("--csv", type=Path, default=ROOT / "data/london_merged-original.csv")
    parser.add_argument("--hour", default="2015-01-04T00:00:00")
    args = parser.parse_args()
    pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:00:00"
    if not re.fullmatch(pattern, args.hour):
        parser.error("--hour must be YYYY-MM-DDTHH:00:00, without a timezone")
    datetime.fromisoformat(args.hour)

    print("Parsing local RDF and metadata...", file=sys.stderr)
    graph = Graph().parse(args.data, format="turtle")
    metadata = Graph().parse(args.metadata, format="turtle")
    observations = set(graph.subjects(RDF.type, SCHEMA.Observation))
    invalid_times = 0
    invalid_codes = 0
    codes = set()
    for observation in observations:
        times = list(graph.objects(observation, BASE.timestamp))
        if len(times) != 1 or times[0].datatype != XSD.dateTime or not re.fullmatch(pattern, str(times[0])):
            invalid_times += 1
        weather = list(graph.objects(observation, BASE.weather_code))
        if len(weather) != 1 or weather[0].datatype != XSD.int:
            invalid_codes += 1
        else:
            codes.add(int(weather[0]))
    time_ready = bool(observations) and invalid_times == 0
    weather_ready = bool(observations) and invalid_codes == 0 and codes == {1, 2, 3, 4, 7, 10, 26}
    results: dict[str, object] = {
        "context": {
            "rdflib": rdflib.__version__,
            "data": str(args.data), "metadata": str(args.metadata),
            "observations": len(observations),
            "timezone": "unspecified; no UTC or daylight-saving interpretation",
            "invalid_or_missing_timestamps": invalid_times,
            "invalid_or_missing_weather_codes": invalid_codes,
            "corrected_data_ready": time_ready and weather_ready,
        }
    }
    results["CQ1"] = (
        {"hour": args.hour, "rows": query(graph, "hour.rq", requestedHour=Literal(args.hour, datatype=XSD.dateTime))}
        if time_ready else {"status": "pending corrected timezone-unspecified timestamps"}
    )
    calendar = query(graph, "calendar.rq")
    results["CQ2"] = [row for row in calendar if row["flag"] == str(BASE.is_weekend)]
    results["CQ3"] = [row for row in calendar if row["flag"] == str(BASE.is_holiday)]
    results["CQ4"] = {
        "interpretation": "Descriptive association only, not causality; bins are [lower, upper). No confounder adjustment.",
        "rows": query(graph, "measurements.rq"),
    }
    results["CQ5"] = query(graph, "seasons.rq")
    results["CQ6"] = (
        query(graph, "weather.rq") if weather_ready
        else {"status": "pending complete xsd:int original weather codes 1, 2, 3, 4, 7, 10, 26; no reverse mapping"}
    )
    if time_ready:
        timestamps = query(graph, "timestamps.rq")
        counts = Counter(datetime.fromisoformat(row["timestamp"]) for row in timestamps)
        start, end = min(counts), max(counts)
        slots = int((end - start).total_seconds() // 3600) + 1
        missing = [
            (start + timedelta(hours=offset)).isoformat()
            for offset in range(slots) if start + timedelta(hours=offset) not in counts
        ]
        results["CQ7"] = {
            "interval": "inclusive observed minimum to maximum; naive hourly grid",
            "start": start.isoformat(), "end": end.isoformat(), "expected_slots": slots,
            "observed_unique_slots": len(counts), "missing_count": len(missing),
            "duplicate_slots": {time.isoformat(): count for time, count in sorted(counts.items()) if count > 1},
            "missing": missing,
        }
    else:
        results["CQ7"] = {"status": "pending corrected timezone-unspecified timestamps; no silent stripping of Z"}
    results["CQ8"] = {
        "interpretation": "Rights uncertainty is not permission to redistribute; no blanket reuse licence asserted.",
        "rows": query(metadata, "metadata.rq"),
    }
    distributions = query(metadata, "distributions.rq")
    csv_hash = hashlib.sha256(args.csv.read_bytes()).hexdigest()
    for row in distributions:
        if row.get("mediaType") == "text/csv":
            row["local_sha256"] = csv_hash
            row["checksum_matches_local"] = (
                row.get("algorithm") == "http://spdx.org/rdf/terms#checksumAlgorithm_sha256"
                and str(row.get("checksum", "")).lower() == csv_hash
            )
        if row.get("mediaType") == "text/turtle":
            row["public_access_status"] = (
                "URL recorded, not tested" if row.get("downloadURL") or row.get("accessURL")
                else "pending: local RDF only; no public URL asserted"
            )
    results["CQ9"] = {
        "interpretation": "URLs are metadata evidence, not tested retrieval. Kaggle accessURL is not a direct CSV download. CSV checksum verifies local bytes only.",
        "rows": distributions,
    }
    print(json.dumps(results, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
