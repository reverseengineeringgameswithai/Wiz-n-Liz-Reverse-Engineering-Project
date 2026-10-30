"""Original synthetic bytes only; no proprietary fixtures are needed."""

from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from rom import MAX_ROM_SIZE, RomError, inspect_bytes, inspect_file, verify_expected


def synthetic_rom() -> bytearray:
    data = bytearray(0x208)
    data[0x100:0x110] = b"SEGA GENESIS    "
    data[0x120:0x150] = b"SYNTHETIC TEST".ljust(48, b" ")
    struct.pack_into(">II", data, 0, 0x00FFFF00, 0x200)
    struct.pack_into(">IIII", data, 0x1A0, 0, len(data) - 1, 0xFF0000, 0xFFFFFF)
    struct.pack_into(">4H", data, 0x200, 0xFFFF, 2, 0x1234, 0x8000)
    # Hand-computed 0xFFFF + 2 + 0x1234 + 0x8000 = 0x19235.
    struct.pack_into(">H", data, 0x18E, 0x9235)
    return data


class RomTests(unittest.TestCase):
    def test_header_checksum_and_vectors(self):
        report = inspect_bytes(synthetic_rom())
        self.assertEqual(report["size_bytes"], 520)
        self.assertEqual(report["header"]["domestic_title"], "SYNTHETIC TEST")
        self.assertEqual(report["checksum"]["calculated"], 0x9235)
        self.assertTrue(report["checksum"]["matches"])
        self.assertEqual(len(report["vectors"]), 64)
        self.assertEqual(report["vectors"][0]["raw_u32"], 0x00FFFF00)
        self.assertEqual(report["vectors"][1]["low24"], 0x200)
        self.assertEqual(report["warnings"], [])

    def test_truncated_and_unexpected(self):
        for data in (b"", b"x" * 511, b"x" * 1024):
            with self.subTest(size=len(data)), self.assertRaises(RomError):
                inspect_bytes(data)

    def test_odd_length(self):
        with self.assertRaisesRegex(RomError, "odd byte"):
            inspect_bytes(synthetic_rom() + b"x")

    def test_header_lengths_do_not_drive_allocations(self):
        data = synthetic_rom()
        struct.pack_into(">IIII", data, 0x1A0, 0xFFFFFFFF, 0, 9, 1)
        report = inspect_bytes(data)
        self.assertEqual(report["size_bytes"], 520)
        self.assertEqual(len(report["warnings"]), 3)

    def test_bad_checksum_is_observation_not_rejection(self):
        data = synthetic_rom()
        data[-1] ^= 1
        report = inspect_bytes(data)
        self.assertFalse(report["checksum"]["matches"])
        self.assertIn("stored checksum differs", report["warnings"][0])

    def test_address_spaces_not_raw_offsets(self):
        data = synthetic_rom()
        struct.pack_into(">I", data, 4, 0xFF000200)
        report = inspect_bytes(data)
        self.assertEqual(report["vectors"][1]["raw_u32"], 0xFF000200)
        self.assertEqual(report["vectors"][1]["low24"], 0x200)
        self.assertTrue(report["vectors"][1]["low24_in_file"])
        struct.pack_into(">I", data, 4, 0x00FFFFFF)
        self.assertIn("reset vector", inspect_bytes(data)["warnings"][0])

    def test_packaging_hints_are_rejected_not_transformed(self):
        original = synthetic_rom()
        swapped = bytearray(original)
        swapped[0::2], swapped[1::2] = original[1::2], original[0::2]
        for data, hint in ((swapped, "byte-swapped"), (bytes(512) + original, "prefixed")):
            with self.subTest(hint=hint), self.assertRaisesRegex(RomError, hint):
                inspect_bytes(data)

    def test_non_ascii_header_and_input_unchanged(self):
        data = synthetic_rom()
        data[0x120] = 0xFF
        before = bytes(data)
        report = inspect_bytes(data)
        self.assertTrue(report["header"]["domestic_title"].startswith("\\xff"))
        self.assertEqual(bytes(data), before)

    def test_file_is_read_only_and_manifest_rejects_synthetic(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "space and 'quote.md"
            data = synthetic_rom()
            path.write_bytes(data)
            before = path.stat()
            report = inspect_file(path)
            self.assertEqual(path.read_bytes(), data)
            self.assertEqual(path.stat().st_mtime_ns, before.st_mtime_ns)
            with self.assertRaisesRegex(RomError, "unsupported ROM"):
                verify_expected(report)

    def test_oversized_file_rejected_without_reading(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "large.bin"
            with path.open("wb") as stream:
                stream.truncate(MAX_ROM_SIZE + 1)
            with self.assertRaisesRegex(RomError, "file size"):
                inspect_file(path)


if __name__ == "__main__":
    unittest.main()
