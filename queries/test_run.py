"""Small in-memory checks of the corrected and pending evidence paths."""

from contextlib import redirect_stdout
from datetime import datetime, timedelta
import io
import json
import unittest
from unittest.mock import Mock, patch

from rdflib import BNode, Graph, Literal, Namespace, RDF, URIRef, XSD

import run


class EvidenceTests(unittest.TestCase):
    def evidence(self, corrected):
        graph = Graph()
        obo = Namespace("http://purl.obolibrary.org/obo/")
        codes = [1, 2, 3, 4, 7, 10, 26, 26]
        for index, code in enumerate(codes):
            observation = run.BASE[str(index)]
            graph.add((observation, RDF.type, run.SCHEMA.Observation))
            graph.add((observation, run.SCHEMA.measuredValue, Literal(index + 1, datatype=XSD.int)))
            # One absent slot (02:00) and one duplicate slot (07:00).
            hour = [0, 1, 3, 4, 5, 6, 7, 7][index]
            timestamp = (datetime(2015, 1, 4) + timedelta(hours=hour)).isoformat()
            if not corrected:
                timestamp += "Z"
            graph.add((observation, run.BASE.timestamp, Literal(timestamp, datatype=XSD.dateTime)))
            if corrected:
                graph.add((observation, run.BASE.weather_code, Literal(code, datatype=XSD.int)))
            for name in ["is_weekend", "is_holiday", "temperature", "temperature_sensation", "humidity", "wind_speed"]:
                node = BNode()
                graph.add((observation, run.BASE[name], node))
                graph.add((node, RDF.type, run.SCHEMA.PropertyValue))
                flag = name.startswith("is_")
                value = Literal(index % 2 == 0) if flag else Literal(float(index))
                graph.add((node, run.SCHEMA.value, value))
                if not flag:
                    unit = "P1" if name == "humidity" else "KMH" if name == "wind_speed" else "CEL"
                    graph.add((node, run.SCHEMA.unitCode, Literal(unit)))
            relation = BNode()
            graph.add((observation, obo.RO_0002092, relation))
            graph.add((relation, RDF.type, URIRef("http://www.wikidata.org/entity/Q24384")))
            graph.add((relation, run.SCHEMA.value, URIRef(f"https://www.wikidata.org/entity/Q{1311 + index % 4}")))
        metadata = Graph().parse(run.ROOT / "data/london-bike-metadata.ttl", format="turtle")
        output = io.StringIO()
        with patch.object(run, "Graph", side_effect=[Mock(parse=Mock(return_value=graph)), Mock(parse=Mock(return_value=metadata))]):
            with patch("sys.argv", ["run.py"]), redirect_stdout(output):
                run.main()
        return json.loads(output.getvalue())

    def test_corrected_graph(self):
        result = self.evidence(corrected=True)
        self.assertTrue(result["context"]["corrected_data_ready"])
        self.assertEqual(result["CQ1"]["rows"][0]["hires"], 1)
        self.assertEqual(sum(row["hours"] for row in result["CQ2"]), 8)
        self.assertEqual(sum(row["hours"] for row in result["CQ3"]), 8)
        self.assertEqual(sum(row["hours"] for row in result["CQ4"]["rows"]), 32)
        self.assertEqual(len(result["CQ5"]), 4)
        self.assertEqual(len(result["CQ6"]), 7)
        self.assertEqual(result["CQ7"]["missing"], ["2015-01-04T02:00:00"])
        self.assertEqual(result["CQ7"]["duplicate_slots"], {"2015-01-04T07:00:00": 2})
        csv = next(row for row in result["CQ9"]["rows"] if row["mediaType"] == "text/csv")
        self.assertTrue(csv["checksum_matches_local"])

    def test_uncorrected_graph_is_pending(self):
        result = self.evidence(corrected=False)
        self.assertFalse(result["context"]["corrected_data_ready"])
        for cq in ["CQ1", "CQ6", "CQ7"]:
            self.assertIn("pending", result[cq]["status"])


if __name__ == "__main__":
    unittest.main()
