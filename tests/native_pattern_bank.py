"""ROM-independent native transport tests, including an independently specified raster."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

EXECUTABLE = sys.argv.pop(1)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from bank_atlas import unpack_pam
from bank_reference import check_atlas


class NativePatternBankTests(unittest.TestCase):
    def run_bank(self, data, logical_id="authored.colors", columns="1"):
        with tempfile.TemporaryDirectory(prefix="bank's fixture ") as directory:
            source = Path(directory) / "input bank.bin"
            source.write_bytes(data)
            return subprocess.run([EXECUTABLE, logical_id, str(source), columns],
                                  capture_output=True, timeout=10, check=False)

    def test_independent_color_row_and_row_order(self):
        # Source palette 0RGB, index0 white but transparent, then pure R/G/B.
        palette = bytes.fromhex("0EEE 0E00 00E0 000E") + bytes(24)
        patterns = bytes.fromhex("01230123") + bytes.fromhex("32103210") + bytes(24)
        data = palette + bytes(2) + patterns + bytes.fromhex("0123456789ABCDEF")
        result = self.run_bank(data)
        self.assertEqual(result.returncode, 0, result.stderr)
        header = b"P7\nWIDTH 8\nHEIGHT 8\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"
        colors = [bytes((255,255,255,0)), bytes((255,0,0,255)),
                  bytes((0,255,0,255)), bytes((0,0,255,255))]
        expected = b"".join(colors) * 2 + b"".join(reversed(colors)) * 2 + colors[0] * 48
        self.assertEqual(result.stdout, header + expected)
        self.assertEqual(json.loads(result.stderr)["patterns"], 1)
        self.assertEqual(result.stdout, self.run_bank(data).stdout)

    def test_errors_never_publish_pixels(self):
        valid = bytes(74)
        for data, identifier, columns in [(bytes(33), "test", "1"), (valid + b"x", "test", "1"),
                                          (valid, "../test", "1"), (valid, "test", "0"),
                                          (valid, "test", "2garbage"), (valid, "test", "-1")]:
            with self.subTest(identifier=identifier, columns=columns, length=len(data)):
                result = self.run_bank(data, identifier, columns)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b"")
                self.assertEqual(json.loads(result.stderr)["status"], "error")

    def test_all_pattern_bits_against_independent_bitplanes(self):
        # 256 one-hot patterns distinguish every pixel/plane, including rows.
        palette = b"".join((index * 0x222).to_bytes(2, "big") for index in range(8)) * 2
        patterns = b"".join((1 << bit).to_bytes(32, "big") for bit in range(256))
        data = palette + bytes.fromhex("00FF") + patterns + bytes(256 * 8)
        result = self.run_bank(data, columns="17")
        self.assertEqual(result.returncode, 0, result.stderr)
        width, height, rgba = unpack_pam(result.stdout)
        self.assertEqual(check_atlas(data, rgba, width, height, 17)["pattern_pixels"], 16384)


if __name__ == "__main__":
    unittest.main()
