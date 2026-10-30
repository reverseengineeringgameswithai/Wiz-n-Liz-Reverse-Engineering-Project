"""Authored synthetic RNC headers and independent CRC check vectors."""

from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from rnc import (HEADER, MAX_PACKED_BYTES, MAX_UNPACKED_BYTES, RncError,
                 approved_directory, atomic_write, crc16, inspect_block,
                 parse_block, validate_decoded)


def fixture(payload=b"123456789", unpacked=9, out_crc=0xBB3D):
    # Known CRC16/ARC check vector: ASCII 123456789 -> BB3D.
    return HEADER.pack(b"RNC", 2, unpacked, len(payload), out_crc, 0xBB3D, 4, 2) + payload


class RncTests(unittest.TestCase):
    def test_crc_known_vectors(self):
        self.assertEqual(crc16(b""), 0)
        self.assertEqual(crc16(bytes(32)), 0)
        self.assertEqual(crc16(b"123456789"), 0xBB3D)
        self.assertEqual(crc16(b"\x01"), 0xC0C1)

    def test_header_and_half_open_extents(self):
        data = b"prefix" + fixture() + b"ignored tail"
        header, payload = parse_block(data, 6)
        self.assertEqual(header.payload_start, 24)
        self.assertEqual(header.end_exclusive, 33)
        self.assertEqual(payload, b"123456789")
        self.assertEqual((header.leeway_field, header.chunks_field), (4, 2))
        report = inspect_block(data, 6)
        self.assertEqual(report["block_size_bytes"], 27)
        self.assertTrue(report["packed_crc_matches"])
        self.assertIsNone(report["decoded"])
        self.assertIsNone(report["resource_role"])

    def test_truncated_headers_and_invalid_offsets(self):
        for size in range(18):
            with self.subTest(size=size), self.assertRaises(RncError):
                parse_block(bytes(size))
        for offset in (-1, True, 999, 0.0):
            with self.subTest(offset=offset), self.assertRaises(RncError):
                parse_block(fixture(), offset)

    def test_unknown_magic_and_methods(self):
        for signature in (b"ABC\x02", b"RNC\x01", b"RNC\x00", b"RNC\xff"):
            with self.subTest(signature=signature), self.assertRaises(RncError):
                parse_block(signature + fixture()[4:])

    def test_declared_extent_rejected_before_slice(self):
        for length in (0, 1, 10, 0xFFFFFFFF, MAX_PACKED_BYTES + 1):
            data = bytearray(fixture())
            struct.pack_into(">I", data, 8, length)
            with self.subTest(length=length), self.assertRaises(RncError):
                parse_block(data)

    def test_unpacked_size_capped_before_decode(self):
        for size in (MAX_UNPACKED_BYTES + 1, 0xFFFFFFFF):
            with self.subTest(size=size), self.assertRaisesRegex(RncError, "safety limit"):
                parse_block(fixture(unpacked=size))

    def test_packed_corruption_and_truncation(self):
        data = bytearray(fixture())
        data[-1] ^= 1
        with self.assertRaisesRegex(RncError, "packed CRC mismatch"):
            inspect_block(data)
        with self.assertRaisesRegex(RncError, "extent"):
            inspect_block(fixture()[:-1])

    def test_output_length_and_crc_required(self):
        header, _ = parse_block(fixture())
        result = validate_decoded(header, b"123456789")
        self.assertTrue(result["unpacked_crc_matches"])
        with self.assertRaisesRegex(RncError, "size"):
            validate_decoded(header, b"12345678")
        with self.assertRaisesRegex(RncError, "unpacked CRC"):
            validate_decoded(header, b"123456788")

    def test_output_directory_rejects_escape_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in ("../escape", "/tmp/escape", "local/../escape", "Original_Game"):
                with self.subTest(relative=relative), self.assertRaises(RncError):
                    approved_directory(root, relative)
            (root / "elsewhere").mkdir()
            (root / "local").symlink_to(root / "elsewhere", target_is_directory=True)
            with self.assertRaises(RncError):
                approved_directory(root, "local/generated/rnc")

    def test_atomic_output_replaces_symlink_not_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "protected"
            target.write_bytes(b"unchanged")
            output = approved_directory(root, "local/generated/rnc") / "result.bin"
            output.symlink_to(target)
            atomic_write(output, b"validated synthetic content")
            self.assertFalse(output.is_symlink())
            self.assertEqual(target.read_bytes(), b"unchanged")
            self.assertEqual(output.read_bytes(), b"validated synthetic content")


if __name__ == "__main__":
    unittest.main()
