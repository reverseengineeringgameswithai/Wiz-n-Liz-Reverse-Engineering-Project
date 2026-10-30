"""Synthetic checks for the isolated pinned decoder adapter, without the ROM."""
import json
import contextlib
import io
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import rnc_upstream_probe as probe
from rnc import inspect_block, parse_block, validate_decoded, RncError

# Hand-authored literal A plus termination. Independently accepted by ScummVM
# e60a6799188cc04e6ef0fba34978f8afd4f25d43 under ASan/UBSan; payload consumed 3.
LITERAL_A = bytes.fromhex("524e4302000000010000000330c0565000011e4100")


@unittest.skipUnless((ROOT / "local/tools/go/bin/go").is_file()
                     and (ROOT / "local/tools/sega2asm-src/go.mod").is_file()
                     and shutil.which("prlimit"), "pinned Go/source or prlimit unavailable")
class UpstreamRncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = probe.probe_directory()
        cls.executable, cls.build = probe.build_adapter(cls.directory)

    def invoke(self, name, data):
        source = self.directory / f"{name}.rnc"
        destination = self.directory / f"{name}.bin"
        source.write_bytes(data)
        result = probe.invoke_adapter(self.executable, source, destination)
        (self.directory / f"{name}.json").write_text(json.dumps(result, indent=2) + "\n")
        return result, destination

    def test_malformed_inputs_fail_before_decoder(self):
        header = b"RNC\x02" + (1).to_bytes(4, "big") + (3).to_bytes(4, "big") + bytes(6)
        cases = {
            "short": b"RNC\x02",
            "wrong_magic": b"BAD\x02" + header[4:] + bytes(3),
            "truncated_payload": header + bytes(2),
            "trailing_payload": header + bytes(4),
            "oversize_output": header[:4] + (probe.MAX_BYTES + 1).to_bytes(4, "big") + header[8:] + bytes(3),
            "zero_output": header[:4] + bytes(4) + header[8:] + bytes(3),
        }
        for name, data in cases.items():
            with self.subTest(name=name):
                result, destination = self.invoke(name, data)
                self.assertEqual(result["exit_status"], 2)
                self.assertFalse(result["timed_out"])
                self.assertIn("adapter_error", json.loads(result["stdout"]))
                self.assertFalse(destination.exists())

    def test_valid_literal_reference_is_corrupted_by_pinned_decoder(self):
        header, _ = parse_block(LITERAL_A)
        inspect_block(LITERAL_A)  # The packed CRC is valid independently of Go.
        validate_decoded(header, b"A")  # Reference expected output and CRC agree.
        result, destination = self.invoke("literal_a", LITERAL_A)
        self.assertEqual(result["exit_status"], 0)
        self.assertIsNone(result["decoder"]["decoder_error"])
        self.assertTrue(result["decoder"]["decoded_size_matches"])
        decoded = destination.read_bytes()
        self.assertNotEqual(decoded, b"A")
        with self.assertRaisesRegex(RncError, "CRC mismatch"):
            validate_decoded(header, decoded)

    def test_cli_rejects_crc_failure_without_reading_rom(self):
        source = self.directory / "literal_cli.rnc"
        source.write_bytes(LITERAL_A)
        captured = io.StringIO()
        with patch.object(probe, "inspect_file", side_effect=AssertionError("ROM access forbidden")):
            with contextlib.redirect_stdout(captured):
                status = probe.main(["--input", str(source)])
        self.assertEqual(status, 2)
        summary = json.loads(captured.getvalue())
        report = json.loads(Path(summary["report"]).read_text())
        self.assertEqual(report["outcome"], "rejected_output")
        self.assertTrue(report["decoded_validation"]["size_matches"])
        self.assertFalse(report["decoded_validation"]["crc_matches"])


if __name__ == "__main__":
    unittest.main()
