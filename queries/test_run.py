"""Small in-memory checks using the current exported RDF model."""

from contextlib import redirect_stdout
import io
import json
import unittest
from unittest.mock import Mock, patch

from rdflib import BNode, Graph, Literal, Namespace, RDF, URIRef, XSD

import run


SCHEMA = Namespace("http://schema.org/")
WD = Namespace("https://www.wikidata.org/entity/")


class EvidenceTests(unittest.TestCase):
    def evidence(self):
        graph = Graph()
        base = Namespace("https://w3id.org/FAIR-course-UT/2026/group20/data/")
        quantities = {
            "is_weekend": WD.Q211391,
            "is_holiday": WD.Q1445650,
            "temperature": URIRef("http://qudt.org/vocab/quantitykind/Temperature"),
            "temperature_sensation": URIRef("https://bimerr.iot.linkeddata.es/def/weather#feels_like"),
            "humidity": URIRef("https://bimerr.iot.linkeddata.es/def/weather#Humidity"),
            "wind_speed": URIRef("https://bimerr.iot.linkeddata.es/def/weather#WindSpeed"),
        }
        for index in range(8):
            observation = base[str(index)]
            graph.add((observation, RDF.type, SCHEMA.Observation))
            graph.add((observation, SCHEMA.value, Literal(index + 1, datatype=XSD.int)))
            for name, quantity in quantities.items():
                node = BNode()
                graph.add((observation, SCHEMA.additionalProperty, node))
                graph.add((node, RDF.type, SCHEMA.PropertyValue))
                graph.add((node, SCHEMA.propertyID, quantity))
                flag = name.startswith("is_")
                value = Literal(index % 2 == 0) if flag else Literal(float(index - 2))
                graph.add((node, SCHEMA.value, value))
                if not flag:
                    unit = "P1" if name == "humidity" else "KMH" if name == "wind_speed" else "CEL"
                    graph.add((node, SCHEMA.unitCode, Literal(unit)))
        metadata = Graph().parse(run.ROOT / "data/london-bike-metadata.ttl", format="turtle")
        output = io.StringIO()
        with patch.object(run, "Graph", side_effect=[Mock(parse=Mock(return_value=graph)), Mock(parse=Mock(return_value=metadata))]):
            with patch("sys.argv", ["run.py"]), redirect_stdout(output):
                run.main()
        return json.loads(output.getvalue())

    def test_calendar(self):
        result = self.evidence()
        self.assertEqual(set(result), {"calendar.rq", "measurements.rq", "metadata.rq"})
        self.assertEqual(len(result["calendar.rq"]), 4)
        for flag in [WD.Q211391, WD.Q1445650]:
            rows = [row for row in result["calendar.rq"] if row["flag"] == str(flag)]
            self.assertEqual(len(rows), 2)
            by_value = {row["value"]: row for row in rows}
            self.assertEqual(by_value[True]["hours"], 4)
            self.assertEqual(by_value[True]["totalHires"], 16)
            self.assertEqual(by_value[True]["meanHourlyHires"], 4)
            self.assertEqual(by_value[False]["hours"], 4)
            self.assertEqual(by_value[False]["totalHires"], 20)
            self.assertEqual(by_value[False]["meanHourlyHires"], 5)

    def test_measurements(self):
        result = self.evidence()
        self.assertEqual(sum(row["hours"] for row in result["measurements.rq"]), 32)
        temperature = [row for row in result["measurements.rq"] if row["measurement"] == "http://qudt.org/vocab/quantitykind/Temperature"]
        self.assertEqual([(row["lower"], row["hours"]) for row in temperature], [(-5, 2), (0, 5), (5, 1)])
        self.assertEqual([row["meanHourlyHires"] for row in temperature], [1.5, 5, 8])
        self.assertTrue(all(row["unit"] == "CEL" for row in temperature))
        self.assertEqual({row["unit"] for row in result["measurements.rq"]}, {"CEL", "P1", "KMH"})

    def test_metadata(self):
        result = self.evidence()
        rows = result["metadata.rq"]
        self.assertTrue(any(row.get("label") == "Hristo Mavrodiev" for row in rows))
        predicates = {row["predicate"] for row in rows}
        for name in ["creator", "source", "rights", "provenance"]:
            self.assertIn("http://purl.org/dc/terms/" + name, predicates)
        self.assertNotIn("http://purl.org/dc/terms/license", predicates)


if __name__ == "__main__":
    unittest.main()
