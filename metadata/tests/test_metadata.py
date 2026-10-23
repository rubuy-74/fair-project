import hashlib
import unittest

from rdflib import BNode, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

from validate import (
    DCAT, LBD, METADATA, METADATA_SHAPES, ROOT, VOCABULARY,
    assert_validation, load_graph,
)


DCTERMS = Namespace("http://purl.org/dc/terms/")
SPDX = Namespace("http://spdx.org/rdf/terms#")


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.graph = load_graph(METADATA, VOCABULARY)

    def check(self, expected=True, publication=False):
        assert_validation(
            self.id(), self.graph, expected, METADATA_SHAPES, publication=publication,
        )

    def test_local_metadata_without_table_schema(self):
        self.check()

    def test_metadata_has_no_csv_structure_dependencies(self):
        shapes = load_graph(METADATA_SHAPES)
        for graph in (self.graph, shapes):
            self.assertFalse(any(
                isinstance(term, URIRef) and str(term).startswith("http://www.w3.org/ns/csvw#")
                for triple in graph for term in triple
            ))
        self.check()

    def test_csv_checksum_and_size(self):
        content = (ROOT / "data/london_merged-original.csv").read_bytes()
        distribution = LBD.londonMergedCsvDistribution
        self.assertEqual(int(self.graph.value(distribution, DCAT.byteSize)), len(content))
        checksum = self.graph.value(distribution, SPDX.checksum)
        self.assertEqual(str(self.graph.value(checksum, SPDX.checksumValue)), hashlib.sha256(content).hexdigest())

    def test_unknown_distribution_format_fails(self):
        self.graph.set((LBD.londonBikesRdfDistribution, DCAT.mediaType, Literal("application/pdf")))
        self.check(False)

    def test_uncertain_rights_are_not_a_license(self):
        self.assertFalse(list(self.graph.objects(LBD.londonBikeSharingDataset, DCTERMS.license)))
        self.graph.remove((LBD.londonBikeSharingDataset, DCTERMS.rights, None))
        self.check(False)

    def test_local_distribution_does_not_claim_publication(self):
        distribution = LBD.londonBikesRdfDistribution
        self.assertFalse(list(self.graph.objects(distribution, DCAT.accessURL)))
        self.assertFalse(list(self.graph.objects(distribution, DCAT.downloadURL)))
        self.check(False, publication=True)

    def test_publication_requires_urls_and_final_integrity_fields(self):
        # Synthetic test-only URLs and digest, never publication metadata.
        for distribution in self.graph.objects(LBD.londonBikeSharingDataset, DCAT.distribution):
            self.graph.set((distribution, DCAT.accessURL, URIRef("https://example.org/dataset/")))
            self.graph.set((distribution, DCAT.downloadURL, URIRef("https://example.org/dataset/file")))
        self.check(False, publication=True)
        distribution = LBD.londonBikesRdfDistribution
        checksum = BNode()
        self.graph.add((distribution, DCAT.byteSize, Literal(1)))
        self.graph.add((distribution, SPDX.checksum, checksum))
        self.graph.add((checksum, RDF.type, SPDX.Checksum))
        self.graph.add((checksum, SPDX.algorithm, SPDX.checksumAlgorithm_sha256))
        self.graph.add((checksum, SPDX.checksumValue, Literal("0" * 64, datatype=XSD.hexBinary)))
        self.check(publication=True)
        self.graph.set((distribution, DCAT.downloadURL, URIRef("file:///tmp/london_bikes.ttl")))
        self.check(False, publication=True)


if __name__ == "__main__":
    unittest.main()
