import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import rdflib
from rdflib import Dataset, Literal, Namespace, RDF, URIRef, XSD

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "metadata"))
from validate_fidelity import validate_fidelity


BASE = Namespace("http://localhost:3333/")
SCHEMA = Namespace("http://schema.org/")
OBO = Namespace("http://purl.obolibrary.org/obo/")
CSV = ("timestamp,cnt,t1,t2,hum,wind_speed,weather_code,is_holiday,is_weekend,season\n"
       "2015-01-04 04:00:00,47,4.0,2.0,93.0,6.0,3.0,0.0,1.0,3.0\n"
       "2015-01-04 05:00:00,48,4.0,2.0,93.0,6.0,1.0,0.0,1.0,3.0\n")


class FidelityTests(unittest.TestCase):
    def setUp(self):
        rdflib.NORMALIZE_LITERALS = False
        template = (ROOT / "metadata/examples/example-observation.ttl").read_text()
        self.data = Dataset(default_union=True)
        for index, weather in enumerate(("Q1055865", "Q13424349")):
            text = template.replace("http://localhost:3333/4", f"http://localhost:3333/{index}")
            text = text.replace("http://localhost:3333/weather/3", f"https://www.wikidata.org/entity/{weather}")
            text = text.replace("http://localhost:3333/season/3", "https://www.wikidata.org/entity/Q1311")
            if index:
                text = text.replace("04:00:00", "05:00:00").replace('"47"', '"48"')
                text = text.replace('base:weather_code "3"', 'base:weather_code "1"')
            self.data.graph(BASE[f"graph/{index}"]).parse(data=text, format="turtle")

    def errors(self, source=CSV):
        return validate_fidelity(self.data, io.StringIO(source))

    def replace(self, subject, predicate, value):
        for graph in self.data.graphs():
            graph.remove((subject, predicate, None))
        if value is not None:
            self.data.default_context.add((subject, predicate, value))

    def test_all_rows_and_named_graphs_pass(self):
        self.assertEqual(self.errors(), [])

    def test_exact_typed_values_and_links(self):
        variants = (
            (BASE["0"], BASE.timestamp, Literal("2015-01-04T04:00:00Z", datatype=XSD.dateTime)),
            (BASE["0"], BASE.timestamp, Literal("2015-01-04T04:00", datatype=XSD.dateTime)),
            (BASE["1"], SCHEMA.measuredValue, Literal(47, datatype=XSD.int)),
            (BASE["0"], SCHEMA.measuredValue, Literal(47, datatype=XSD.integer)),
            (BASE["0"], BASE.weather_code, Literal(4, datatype=XSD.int)),
            (BASE["0"], BASE.weather, URIRef("https://www.wikidata.org/entity/Q13424349")),
            (BASE["0"], BASE.temperature, BASE["1/temperature"]),
            (BASE["0/temperature"], SCHEMA.value, Literal("4.00001", datatype=XSD.double)),
            (BASE["0/temperature"], SCHEMA.value, Literal("4", datatype=XSD.decimal)),
            (BASE["0/temperature"], SCHEMA.propertyID, BASE.wrong),
            (BASE["0/temperature"], SCHEMA.unitCode, Literal("K")),
            (BASE["0/temperature"], SCHEMA.name, Literal("Air temperature")),
            (BASE["0/is_holiday"], SCHEMA.value, Literal(True)),
            (BASE["0/is_weekend"], SCHEMA.value, Literal("true")),
            (BASE["0/humidity"], RDF.type, None),
            (BASE["0/wind_speed"], SCHEMA.value, None),
        )
        for subject, predicate, value in variants:
            with self.subTest(subject=subject, predicate=predicate):
                self.setUp()
                self.replace(subject, predicate, value)
                self.assertTrue(self.errors())

    def test_missing_extra_and_orphan_nodes(self):
        for subject, predicate, value in (
            (BASE["0"], RDF.type, None),
            (BASE.extra, RDF.type, SCHEMA.Observation),
            (BASE.orphan, RDF.type, SCHEMA.PropertyValue),
            (BASE.orphan, RDF.type, URIRef("http://www.wikidata.org/entity/Q24384")),
            (BASE.orphan, SCHEMA.value, Literal(1)),
        ):
            with self.subTest(subject=subject, predicate=predicate):
                self.setUp()
                self.replace(subject, predicate, value)
                self.assertTrue(self.errors())

    def test_category_relation_matches_source(self):
        for kind in ("Q24384", "Q11663"):
            with self.subTest(kind=kind):
                self.setUp()
                relation = next(self.data.subjects(RDF.type, URIRef(f"http://www.wikidata.org/entity/{kind}")))
                self.replace(relation, SCHEMA.value, BASE.wrong)
                self.assertTrue(self.errors())

    def test_existing_weather_category_mappings(self):
        for code, identifier in ((1, "Q13424349"), (2, "Q13424349"), (3, "Q1055865"),
                                 (4, "Q1055865"), (7, "Q133224208"),
                                 (10, "Q2857578"), (26, "Q75078783")):
            with self.subTest(code=code):
                self.setUp()
                category = URIRef(f"https://www.wikidata.org/entity/{identifier}")
                for index in range(2):
                    self.replace(BASE[str(index)], BASE.weather_code, Literal(code, datatype=XSD.int))
                    self.replace(BASE[str(index)], BASE.weather, category)
                for relation in list(self.data.subjects(
                        RDF.type, URIRef("http://www.wikidata.org/entity/Q11663"))):
                    self.replace(relation, SCHEMA.value, category)
                # Category descriptions are optional; remove unused fixture categories.
                for graph in self.data.graphs():
                    for old in ("Q1055865", "Q13424349"):
                        graph.remove((URIRef(f"https://www.wikidata.org/entity/{old}"), None, None))
                source = CSV.replace(",3.0,0.0,1.0,3.0", f",{code}.0,0.0,1.0,3.0")
                source = source.replace(",1.0,0.0,1.0,3.0", f",{code}.0,0.0,1.0,3.0")
                self.assertEqual(self.errors(source), [])

    def test_all_season_associations(self):
        for code, identifier in ((0, "Q1312"), (1, "Q1313"), (2, "Q1314"), (3, "Q1311")):
            with self.subTest(code=code):
                self.setUp()
                for relation in list(self.data.subjects(
                        RDF.type, URIRef("http://www.wikidata.org/entity/Q24384"))):
                    self.replace(relation, SCHEMA.value,
                                 URIRef(f"https://www.wikidata.org/entity/{identifier}"))
                for graph in self.data.graphs():
                    graph.remove((URIRef("https://www.wikidata.org/entity/Q1311"), None, None))
                self.assertEqual(self.errors(CSV.replace(",1.0,3.0\n", f",1.0,{code}.0\n")), [])

    def test_source_code_without_existing_mapping_is_not_invented(self):
        with self.assertRaisesRegex(ValueError, "no existing weather IRI mapping"):
            self.errors(CSV.replace(",3.0,0.0,1.0,3.0", ",94.0,0.0,1.0,3.0"))

    def test_duplicate_or_shared_relations_fail(self):
        relations = set(self.data.objects(BASE["0"], OBO.RO_0002092))
        for graph in self.data.graphs():
            graph.remove((BASE["1"], OBO.RO_0002092, None))
        for relation in relations:
            self.data.default_context.add((BASE["1"], OBO.RO_0002092, relation))
        self.assertTrue(self.errors())

    def test_reordered_rows_fail(self):
        lines = CSV.splitlines()
        self.assertTrue(self.errors("\n".join((lines[0], lines[2], lines[1]))))

    def test_csv_missing_rows_fail(self):
        self.assertTrue(self.errors("\n".join(CSV.splitlines()[:2])))

    def test_empty_csv_and_invalid_header(self):
        self.assertTrue(self.errors(CSV.splitlines()[0] + "\n"))
        with self.assertRaises(ValueError):
            self.errors("timestamp,cnt\n")

    def test_cli_pass_and_failure_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.csv"
            export = Path(directory) / "export.trig"
            source.write_text(CSV)
            self.data.serialize(export, format="trig")
            command = [sys.executable, str(ROOT / "metadata/validate_fidelity.py"),
                       str(export), "--csv", str(source)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            source.write_text(CSV.replace(",48,", ",49,"))
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            source.unlink()
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
