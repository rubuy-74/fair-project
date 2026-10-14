from pathlib import Path

from pyshacl import validate
from rdflib import Dataset, Graph, Literal, URIRef


ROOT = Path(__file__).resolve().parents[2]
DATA_SHAPES = ROOT / "metadata/shacl/london-bike-data-shapes.ttl"
METADATA_SHAPES = ROOT / "metadata/shacl/london-bike-metadata-shapes.ttl"


def load_graph(*paths: Path) -> Graph:
    graph = Dataset()
    for path in paths:
        graph.parse(path, format="trig" if path.suffix == ".trig" else "turtle")
    return graph


def assert_validation(name: str, data: Graph, expected: bool, *shape_paths: Path) -> None:
    shapes = load_graph(*(shape_paths or (DATA_SHAPES,)))
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
    metadata = load_graph(
        ROOT / "metadata/dataset-metadata/london-bike-metadata.ttl",
        ROOT / "metadata/vocab/london-bike-vocabulary.ttl",
    )
    assert_validation("dataset metadata", metadata, True, METADATA_SHAPES)

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
