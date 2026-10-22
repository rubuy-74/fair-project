import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import rdflib
from pyshacl import validate
from rdflib import Dataset, Graph, Literal, Namespace, RDF, URIRef, XSD


ROOT = Path(__file__).resolve().parents[2]
BASE = Namespace("http://localhost:3333/")
SCHEMA = Namespace("http://schema.org/")
OBO = Namespace("http://purl.obolibrary.org/obo/")


class ExportValidationTests(unittest.TestCase):
    def setUp(self):
        rdflib.NORMALIZE_LITERALS = False
        self.data = Graph().parse(ROOT / "metadata/examples/example-observation.ttl")
        self.shapes = Graph().parse(ROOT / "metadata/shacl/london-bike-data-shapes.ttl")

    def conforms(self):
        return validate(self.data, shacl_graph=self.shapes, inference="none", inplace=True)[0]

    def test_timestamp_requires_seconds_and_no_timezone(self):
        for timestamp in ("2015-01-04T04:00", "2015-01-04T04:00:00Z",
                          "2015-01-04T04:00:00+00:00", "2015-01-04T04:00:00.0",
                          "2015-01-04 04:00:00", "2015-02-30T04:00:00"):
            with self.subTest(timestamp=timestamp):
                self.data.set((BASE["4"], BASE.timestamp,
                               Literal(timestamp, datatype=XSD.dateTime, normalize=False)))
                self.assertFalse(self.conforms())

    def test_required_observation_fields(self):
        for predicate in (BASE.timestamp, BASE.weather_code, SCHEMA.measuredValue,
                          BASE.weather, BASE.is_holiday, BASE.is_weekend, BASE.temperature,
                          BASE.temperature_sensation, BASE.humidity, BASE.wind_speed,
                          SCHEMA.measuredProperty, OBO.BFO_0000066):
            with self.subTest(predicate=predicate):
                triples = list(self.data.triples((BASE["4"], predicate, None)))
                self.data.remove((BASE["4"], predicate, None))
                self.assertFalse(self.conforms())
                for triple in triples:
                    self.data.add(triple)

    def test_wrong_observation_values(self):
        for predicate, value in (
            (BASE.weather_code, Literal(5, datatype=XSD.int)),
            (BASE.weather_code, Literal(3, datatype=XSD.integer)),
            (SCHEMA.measuredValue, Literal(47.5, datatype=XSD.double)),
            (SCHEMA.measuredValue, Literal(-1, datatype=XSD.int)),
            (BASE.timestamp, Literal("2015-01-04T04:00:00")),
            (BASE.weather, Literal("cloudy")),
            (SCHEMA.measuredProperty, SCHEMA.BuyAction),
            (OBO.BFO_0000066, BASE.elsewhere),
            (BASE.temperature, BASE["4/humidity"]),
        ):
            with self.subTest(predicate=predicate, value=value):
                previous = self.data.value(BASE["4"], predicate)
                self.data.set((BASE["4"], predicate, value))
                self.assertFalse(self.conforms())
                self.data.set((BASE["4"], predicate, previous))

    def test_weather_codes_include_original_rare_codes(self):
        for code in (1, 2, 3, 4, 7, 10, 26, 94):
            with self.subTest(code=code):
                self.data.set((BASE["4"], BASE.weather_code, Literal(code, datatype=XSD.int)))
                self.assertTrue(self.conforms())

    def test_relation_types_must_be_distinct(self):
        weather_type = URIRef("http://www.wikidata.org/entity/Q11663")
        season_type = URIRef("http://www.wikidata.org/entity/Q24384")
        relation = self.data.value(predicate=RDF.type, object=weather_type)
        self.data.set((relation, RDF.type, season_type))
        self.assertFalse(self.conforms())

    def test_split_named_graphs_validate_as_union(self):
        data = Dataset(default_union=True)
        for index, triple in enumerate(self.data):
            data.graph(BASE[f"graph/{index % 2}"]).add(triple)
        self.data = data
        self.assertTrue(self.conforms())
        data.graph(BASE.bad).add((BASE["4"], BASE.weather_code, Literal(5, datatype=XSD.int)))
        self.assertFalse(self.conforms())

    def test_valid_turtle_export_without_vocabulary(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "metadata/validate_export.py"),
             str(ROOT / "metadata/examples/example-observation.ttl")],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Conforms: True", result.stdout)

    def test_named_graph_invalid_export_saves_report(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.ttl"
            result = subprocess.run(
                [sys.executable, str(ROOT / "metadata/validate_export.py"),
                 str(ROOT / "metadata/examples/example-rdf-transform-sample.trig"),
                 "--report", str(report)], capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("Conforms: False", result.stdout)
            self.assertTrue(report.exists())

    def test_missing_export_returns_error(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "metadata/validate_export.py"),
             str(ROOT / "missing-export.ttl")], capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)

    def test_empty_export_cannot_pass_vacuously(self):
        with tempfile.TemporaryDirectory() as directory:
            export = Path(directory) / "empty.ttl"
            export.touch()
            result = subprocess.run(
                [sys.executable, str(ROOT / "metadata/validate_export.py"), str(export)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("No data-shape targets found", result.stderr)


if __name__ == "__main__":
    unittest.main()
