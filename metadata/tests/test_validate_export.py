import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ExportValidationTests(unittest.TestCase):
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
