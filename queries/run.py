"""Run the three local queries without an endpoint or network calls."""

import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys
from time import perf_counter

from rdflib import Graph, Literal


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def query(graph, filename):
    started = perf_counter()
    print(f"Running {filename}...", file=sys.stderr, flush=True)
    result = graph.query((HERE / filename).read_text())
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
    args = parser.parse_args()

    print("Parsing local RDF and metadata...", file=sys.stderr)
    graph = Graph().parse(args.data, format="turtle")
    metadata = Graph().parse(args.metadata, format="turtle")
    results = {
        "calendar.rq": query(graph, "calendar.rq"),
        "measurements.rq": query(graph, "measurements.rq"),
        "metadata.rq": query(metadata, "metadata.rq"),
    }
    print(json.dumps(results, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
