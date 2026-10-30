"""ROM-free checks of the optional, explicitly built sanitized ScummVM harness.

The two invalid-stream checks expect upstream's unchecked accesses to terminate
the child process under ASan. They do not establish a hardened decoder.
"""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_rnc_reference as reference
from rnc import crc16
from test_rnc_upstream import LITERAL_A


class RncReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Only an absent binary is optional. Modified sources, stale hashes,
        # missing provenance, and symlink redirects are errors, not skips.
        reference.reject_symlinks(reference.EXECUTABLE)
        if not reference.EXECUTABLE.exists():
            raise unittest.SkipTest(
                "reviewed RNC reference executable absent; explicit bootstrap/build required"
            )
        cls.executable = reference.verify_executable()
        cls.temporary = tempfile.TemporaryDirectory(prefix="synthetic-tests-", dir=reference.LOCAL)
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.directory = Path(cls.temporary.name)

    def invoke(self, name, data):
        source = self.directory / f"{name}.rnc"
        source.write_bytes(data)
        environment = os.environ.copy()
        environment["ASAN_OPTIONS"] = "halt_on_error=1:abort_on_error=0:detect_leaks=0"
        environment["UBSAN_OPTIONS"] = "halt_on_error=1"
        return subprocess.run(
            [str(self.executable), str(source)], cwd=ROOT, env=environment,
            capture_output=True, check=False, timeout=15,
        )

    def test_literal_a_crc_length_and_exact_consumption(self):
        result = self.invoke("literal-a", LITERAL_A)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertEqual(result.stdout, b"A")
        metadata = json.loads(result.stderr)
        self.assertEqual(metadata["status"], "ok")
        self.assertEqual(metadata["decoder_return"], 1)
        self.assertEqual(metadata["produced_bytes"], 1)
        self.assertEqual(metadata["consumed_payload_bytes"], 3)
        self.assertEqual(metadata["consumed_total_bytes"], len(LITERAL_A))
        self.assertEqual(metadata["packed_crc16"], 0x5650)
        self.assertEqual(metadata["unpacked_crc16"], 0x30C0)
        self.assertTrue(metadata["address_sanitizer"])
        self.assertTrue(metadata["undefined_behavior_sanitizer"])

    def test_malformed_extents_fail_before_decode_without_output(self):
        cases = {
            "truncated-header": LITERAL_A[:17],
            "trailing-byte": LITERAL_A + b"X",
            "truncated-payload": LITERAL_A[:-1],
            "wrong-method": LITERAL_A[:3] + b"\x01" + LITERAL_A[4:],
            "excessive-output": LITERAL_A[:4] + b"\xff\xff\xff\xff" + LITERAL_A[8:],
            "zero-output": LITERAL_A[:4] + bytes(4) + LITERAL_A[8:],
            "excessive-packed": LITERAL_A[:8] + b"\xff\xff\xff\xff" + LITERAL_A[12:],
        }
        for name, data in cases.items():
            with self.subTest(case=name):
                result = self.invoke(name, data)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b"")
                self.assertEqual(json.loads(result.stderr)["status"], "error")

    def test_packed_crc_failure_emits_no_output(self):
        data = LITERAL_A[:14] + bytes(2) + LITERAL_A[16:]
        result = self.invoke("packed-crc", data)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(json.loads(result.stderr)["message"], "packed CRC mismatch")

    def test_unpacked_crc_failure_emits_no_output(self):
        data = LITERAL_A[:12] + bytes(2) + LITERAL_A[14:]
        result = self.invoke("unpacked-crc", data)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        metadata = json.loads(result.stderr)
        self.assertEqual(metadata["status"], "decoder_failure")
        self.assertEqual(metadata["decoder_return"], -2)

    def assert_sanitizer_bounds_failure(self, name, data):
        # Valid packed CRC ensures the malformed stream reaches the decoder.
        self.assertEqual(crc16(data[18:]), int.from_bytes(data[14:16], "big"))
        result = self.invoke(name, data)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"AddressSanitizer: heap-buffer-overflow", result.stderr)

    def test_missing_terminator_byte_stops_at_input_boundary(self):
        # Literal A control byte remains, but its required terminator byte is
        # removed; declared length and packed CRC match the shortened input.
        data = bytes.fromhex("524e4302000000010000000230c090c900011e41")
        self.assert_sanitizer_bounds_failure("missing-terminator-byte", data)

    def test_backreference_before_output_stops_at_output_boundary(self):
        # Control 00110 requests a distance-one length-two match before any
        # literal exists. The next raw byte is distance-minus-one = 0.
        data = bytes.fromhex("524e430200000002000000020000001400013000")
        self.assert_sanitizer_bounds_failure("backreference-before-output", data)


if __name__ == "__main__":
    unittest.main()
