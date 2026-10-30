"""Required CTest CLI cases; no ROM, downloads, reference binary or SDL needed."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from rnc2_cases import Wire, block, valid_cases

EXECUTABLE = Path(sys.argv.pop(1)).resolve()


class NativeRnc2Tests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="RNC ' test ")
        self.addCleanup(directory.cleanup)
        self.source = Path(directory.name) / "literal ' data.rnc"

    def invoke(self, data):
        self.source.write_bytes(data)
        return subprocess.run([str(EXECUTABLE), str(self.source)], capture_output=True, timeout=5)

    def rejects(self, data, message):
        result = self.invoke(data)
        self.assertEqual(result.returncode, 2, result.stderr.decode(errors="replace"))
        self.assertEqual(result.stdout, b"")
        metadata = json.loads(result.stderr)
        self.assertEqual(metadata["status"], "error")
        self.assertIn(message, metadata["message"])

    def test_49_authored_reference_validated_cases(self):
        for name, (packed, expected) in valid_cases().items():
            with self.subTest(case=name):
                result = self.invoke(packed)
                self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
                self.assertEqual(result.stdout, expected)
                metadata = json.loads(result.stderr)
                self.assertEqual(metadata["consumed_total_bytes"], len(packed))
                self.assertEqual(metadata["consumed_payload_bytes"], len(packed) - 18)
                self.assertEqual(metadata["produced_bytes"], len(expected))
                self.assertEqual(metadata["packed_crc16"], int.from_bytes(packed[14:16], "big"))
                self.assertEqual(metadata["unpacked_crc16"], int.from_bytes(packed[12:14], "big"))

    def test_container_guards(self):
        packed = valid_cases()["literal-flags-00"][0]
        for data, message in (
            (packed[:17], "size limits"), (packed + b"X", "input extent"),
            (packed[:-1], "input extent"), (b"BAD!" + packed[4:], "signature"),
            (packed[:4] + b"\xff" * 4 + packed[8:], "limits"),
            (packed[:8] + b"\xff" * 4 + packed[12:], "limits"),
            (packed[:4] + bytes(4) + packed[8:], "limits"),
        ):
            with self.subTest(data=data):
                self.rejects(data, message)

    def test_crc_failures(self):
        packed = valid_cases()["literal-flags-00"][0]
        self.rejects(packed[:14] + bytes(2) + packed[16:], "packed CRC")
        self.rejects(packed[:12] + bytes(2) + packed[14:], "unpacked CRC")

    def test_missing_terminator_raw_byte(self):
        self.rejects(bytes.fromhex("524e4302000000010000000230c090c900011e41"), "truncated")

    def test_backreference_before_output(self):
        self.rejects(bytes.fromhex("524e430200000002000000020000001400013000"), "precedes output")

    def test_output_overrun_for_each_token_family(self):
        self.rejects(Wire().literals(b"AB").marker().block(b"A"), "exceeds")
        self.rejects(Wire().literals(b"A").bits("110").raw(b"\0").marker().block(b"AA"), "exceeds")
        self.rejects(Wire().bits("101110000").raw(bytes(12)).marker().block(bytes(11)), "exceeds")
        self.rejects(Wire().literals(b"A").bits("1111").raw(b"\xff").bits("0").raw(b"\0").marker().block(b"A" * 263), "exceeds")

    def test_early_end_and_unconsumed_bytes(self):
        self.rejects(Wire().literals(b"A").marker().block(b"AA"), "extents")
        payload = bytes(Wire().literals(b"A").marker().data) + b"X"
        self.rejects(block(payload, b"A"), "extents")

    def test_continuation_without_end(self):
        self.rejects(Wire().literals(b"A").marker(more=True).block(b"A"), "truncated")

    def test_payload_truncation_reaches_stream_guards(self):
        packed, expected = valid_cases()["literal-run-72"]
        for cut in range(2, len(packed) - 18):
            with self.subTest(cut=cut):
                self.rejects(block(packed[18:18 + cut], expected), "truncated")

    def test_cli_missing_input(self):
        result = subprocess.run([str(EXECUTABLE)], capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        self.assertIn("usage:", json.loads(result.stderr)["message"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
