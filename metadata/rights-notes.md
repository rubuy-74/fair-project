# Rights and Timestamp Evidence

Sources checked directly by HTTP during the local metadata review:

- [Kaggle dataset page](https://www.kaggle.com/datasets/hmavrodiev/london-bike-sharing-dataset). Its embedded `application/ld+json` includes the dataset description, creator Hristo Mavrodiev, and licence name `Other (specified in description)` with an empty licence URL. The description reproduces TfL Transport Data Service licence terms, identifies TfL cycling data, Freemeteo weather and UK bank holidays as the three sources, and says hires are grouped by start time/hour. It describes `timestamp` only as the field used for grouping. It does not specify a timezone, UTC conversion or daylight-saving handling.
- [Kaggle dataset search API](https://www.kaggle.com/api/v1/datasets/list?search=london-bike-sharing-dataset). The exact `hmavrodiev/london-bike-sharing-dataset` entry independently returns `licenseName` = `Other (specified in description)` and creator Hristo Mavrodiev. Licences of other search results or copies do not establish rights for this dataset.
- [TfL Transport Data Service terms](https://tfl.gov.uk/corporate/terms-and-conditions/transport-data-service). These are based on Open Government Licence 2.0 with TfL-specific amendments, not an unmodified OGL grant. They require attribution including `Powered by TfL Open Data`, contain additional requirements/exemptions, and allow revision. The current text is not identical to the copy on Kaggle (for example, the feed request limit differs).

## Conclusions

There is evidence for TfL-specific terms for the TfL source, but not a verified blanket licence for the combined CSV or its RDF derivative. In particular, the checked evidence does not establish permission to redistribute the Freemeteo weather component. The metadata therefore uses `dcterms:rights` with an explicit uncertainty statement instead of asserting a dataset-wide `dcterms:license`. This is not a claim that no rights exist or legal advice. The three upstream sites are recorded as source attributions made by the Kaggle description, not as independently reconstructed acquisition provenance.

No source timezone has been established. The source timestamps use the timezone-free `yyyy-MM-dd HH:mm:ss` representation; no CSV column schema is asserted in the metadata. London location alone is not evidence for UTC, Europe/London, or a particular DST policy. The Kaggle prose coverage (`1/1/2015` to `31/12/2016`) also differs from the local CSV's observed timestamp endpoints; metadata coverage describes the local artifact, not a new claim about Kaggle's prose.

No publication agent, transformation activity, acquisition date or release date has been inferred from this review. Kaggle's modification timestamp is not a local transformation/release date.

## Local Versus Published Validation

`metadata/tests/validate.py` loads `data/london-bike-metadata.ttl` and the semantic variable vocabulary together. Metadata validation checks RDF descriptions and semantic units, not CSV structure or source cells. The CSV is described only as a DCAT source-file distribution with access, format, size and checksum; CSV-to-RDF source-fidelity checks remain in the separate `metadata/validate_fidelity.py` tool. Local validation permits the RDF distribution to be described by its repository-relative identifier without pretending it is publicly downloadable. The optional `--publication` check additionally requires HTTP(S) access/download URL syntax and final size/checksum on every distribution; it does not test HTTP reachability or grant publication approval. The current local metadata intentionally does not pass that publication check.

The main agent must refresh the RDF distribution's `dcat:byteSize` and SHA-256 `spdx:checksum` after all RDF edits finish. Neither has been guessed or computed on an intermediate RDF artifact. Real distribution URLs and combined-source rights clearance remain publication followups.
