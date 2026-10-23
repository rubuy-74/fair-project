import argparse
from pathlib import Path

from pyshacl import validate
from rdflib import Dataset, Graph, Literal, Namespace, URIRef


ROOT = Path(__file__).resolve().parents[2]
DATA_SHAPES = ROOT / "metadata/shacl/london-bike-data-shapes.ttl"
METADATA_SHAPES = ROOT / "metadata/shacl/london-bike-metadata-shapes.ttl"
METADATA = ROOT / "data/london-bike-metadata.ttl"
VOCABULARY = ROOT / "metadata/vocab/london-bike-vocabulary.ttl"
LBD = Namespace("https://w3id.org/london-bike-sharing/")
SH = Namespace("http://www.w3.org/ns/shacl#")
DCAT = Namespace("http://www.w3.org/ns/dcat#")


def load_graph(*paths: Path) -> Graph:
    graph = Dataset()
    for path in paths:
        graph.parse(path, format="trig" if path.suffix == ".trig" else "turtle")
    return graph


def assert_validation(
    name: str, data: Graph, expected: bool, *shape_paths: Path, publication: bool = False
) -> None:
    shapes = load_graph(*(shape_paths or (DATA_SHAPES,)))
    if publication:
        shapes.add((LBD.PublishedDistributionShape, SH.targetClass, DCAT.Distribution))
    conforms, _, report = validate(
        data_graph=data,
        shacl_graph=shapes,
        inference="none",
        abort_on_first=False,
        meta_shacl=True,
    )
    if conforms != expected:
        raise AssertionError(f"{name} expected conforms={expected}\n{report}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate local metadata and RDF fixtures")
    parser.add_argument(
        "--publication", action="store_true",
        help="also require public URL syntax and final size/checksum on each distribution",
    )
    args = parser.parse_args()
    metadata = load_graph(METADATA, VOCABULARY)
    assert_validation("dataset metadata", metadata, True, METADATA_SHAPES, publication=args.publication)
    print("Dataset metadata validated without inspecting CSV columns or cells.")

    example_path = ROOT / "metadata/examples/example-observation.ttl"
    assert_validation(
        "RDF Transform example",
        load_graph(example_path),
        True,
        DATA_SHAPES,
    )

    transform_sample = ROOT / "metadata/examples/example-rdf-transform-sample.trig"
    assert_validation("RDF Transform TriG sample", load_graph(transform_sample), False, DATA_SHAPES)

    invalid_path = ROOT / "metadata/examples/invalid-property-value.ttl"
    assert_validation("invalid property value", load_graph(invalid_path), False, DATA_SHAPES)

    unexpected = load_graph(example_path)
    unexpected.add(
        (
            URIRef("http://localhost:3333/4/temperature"),
            URIRef("http://schema.org/unexpected"),
            Literal("not in the mapping"),
        )
    )
    assert_validation("unexpected observation property", unexpected, False, DATA_SHAPES)

    print("All RDF and SHACL validations passed.")


if __name__ == "__main__":
    main()
