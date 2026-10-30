"""Independently validate authored token cases using the isolated GPL reference."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build_rnc_reference as reference
from rnc_validate import invoke_reference
from rnc2_cases import valid_cases
from test_rnc_upstream import LITERAL_A


class Rnc2CorpusTests(unittest.TestCase):
    def test_authored_literal_matches_prior_hand_encoded_fixture(self):
        self.assertEqual(valid_cases()["literal-flags-00"][0], LITERAL_A)

    def test_all_authored_cases_against_independent_reference(self):
        reference.reject_symlinks(reference.EXECUTABLE)
        if not reference.EXECUTABLE.exists():
            self.skipTest("explicitly built pinned reference absent")
        executable = reference.verify_executable()
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "fixture.rnc"
            for name, (packed, expected) in valid_cases().items():
                with self.subTest(case=name):
                    source.write_bytes(packed)
                    decoded, process = invoke_reference(executable, source)
                    self.assertEqual(process["exit_status"], 0, process["stderr"])
                    self.assertEqual(decoded, expected)
                    metadata = json.loads(process["stderr"])
                    self.assertEqual(metadata["consumed_total_bytes"], len(packed))
                    self.assertEqual(metadata["produced_bytes"], len(expected))
