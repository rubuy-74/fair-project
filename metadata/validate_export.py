"""Validate an RDF export without loading the project metadata or vocabulary."""

import argparse
import sys
import time
from pathlib import Path

import rdflib
from pyshacl import validate
from rdflib import Dataset, Graph, Namespace, RDF


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path, nargs="?", default=root / "data/london_bikes.ttl")
    parser.add_argument("--format", choices=("turtle", "trig"), default="trig",
                        help="TriG also accepts Turtle, including exports named .ttl")
    parser.add_argument("--report", type=Path, help="Save the complete SHACL report as Turtle")
    args = parser.parse_args()

    # Preserve invalid lexical forms rather than silently converting booleans.
    rdflib.NORMALIZE_LITERALS = False
    sh = Namespace("http://www.w3.org/ns/shacl#")
    schema = Namespace("http://schema.org/")
    obo = Namespace("http://purl.obolibrary.org/obo/")
    try:
        print(f"Loading {args.export}", flush=True)
        started = time.perf_counter()
        data = Dataset(default_union=True)
        data.parse(args.export, format=args.format)
        print(f"Loaded in {time.perf_counter() - started:.1f}s", flush=True)
        observations = set(data.subjects(RDF.type, schema.Observation))
        attributes = set(data.subjects(RDF.type, schema.PropertyValue))
        relations = set(data.objects(None, obo.RO_0002092))
        print(f"Targets: {len(observations)} observations, {len(attributes)} attributes, "
              f"{len(relations)} relations", flush=True)
        if not observations and not attributes and not relations:
            print("No data-shape targets found; refusing a vacuous validation pass.", file=sys.stderr)
            return 2

        shapes = Graph().parse(root / "metadata/shacl/london-bike-data-shapes.ttl")
        started = time.perf_counter()
        conforms, report, _ = validate(
            data, shacl_graph=shapes, inference="none", meta_shacl=True, inplace=True,
        )
        print(f"Validated in {time.perf_counter() - started:.1f}s", flush=True)
        if not isinstance(report, Graph):
            raise ValueError(f"SHACL validation failed: {report}")
        if args.report:
            report.serialize(destination=args.report, format="turtle")
            print(f"Full report: {args.report}")
        results = list(report.subjects(RDF.type, sh.ValidationResult))
        print(f"Conforms: {conforms}. Validation results: {len(results)}")
        for result in results[:20]:
            focus = report.value(result, sh.focusNode)
            shape = report.value(result, sh.sourceShape)
            print(f"  {focus}: {shape}")
            for message in report.objects(result, sh.resultMessage):
                print(f"    {message}")
        if len(results) > 20:
            print(f"  {len(results) - 20} more results; use --report for the full report.")
        return 0 if conforms else 1
    except Exception as error:
        print(f"Validation error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
