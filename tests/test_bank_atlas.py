"""Atlas transport, independent expectations, catalog/path and PNG validation."""
import json
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import bank_atlas
from bank_reference import pattern_indices, check_atlas
from rnc import RncError


class BankAtlasTests(unittest.TestCase):
    def test_bitplane_reference_known_rows(self):
        pattern = bytes.fromhex("0123456789ABCDEFFEDCBA9876543210") + bytes(16)
        self.assertEqual(pattern_indices(pattern), list(range(16)) + list(reversed(range(16))) + [0] * 32)
        with self.assertRaises(RncError):
            pattern_indices(bytes(31))

    def test_reference_rejects_wrong_pixel_or_extent(self):
        data = bytes(74)
        self.assertEqual(check_atlas(data, bytes(256), 8, 8, 1)["pattern_pixels"], 64)
        for rgba in (bytes(255), b"x" + bytes(255)):
            with self.assertRaises(RncError):
                check_atlas(data, rgba, 8, 8, 1)

    def test_pam_transport_bounds(self):
        good = b"P7\nWIDTH 1\nHEIGHT 1\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n" + bytes(4)
        self.assertEqual(bank_atlas.unpack_pam(good), (1, 1, bytes(4)))
        for bad in (good[:-1], good + b"x", good.replace(b"WIDTH 1", b"WIDTH 0"),
                    good.replace(b"WIDTH 1", b"WIDTH 9999999"), good.replace(b"DEPTH 4", b"DEPTH 3")):
            with self.assertRaises(RncError):
                bank_atlas.unpack_pam(bad)

    def test_png_chunks_raster_and_multiple_deflate_blocks(self):
        for width, height in ((2, 1), (256, 112)):
            with self.subTest(width=width, height=height):
                rgba = bytes(range(256)) * (width * height * 4 // 256) + bytes(range(width * height * 4 % 256))
                png = bank_atlas.png_from_rgba(width, height, rgba)
                self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
                cursor = 8
                chunks = {}
                while cursor < len(png):
                    size = struct.unpack_from(">I", png, cursor)[0]
                    kind = png[cursor + 4:cursor + 8]
                    body = png[cursor + 8:cursor + 8 + size]
                    crc = struct.unpack_from(">I", png, cursor + 8 + size)[0]
                    self.assertEqual(crc, zlib.crc32(kind + body))
                    chunks[kind] = body
                    cursor += size + 12
                self.assertEqual(cursor, len(png))
                self.assertEqual(list(chunks), [b"IHDR", b"IDAT", b"IEND"])
                self.assertEqual(struct.unpack(">IIBBBBB", chunks[b"IHDR"]), (width,height,8,6,0,0,0))
                raster = zlib.decompress(chunks[b"IDAT"])
                self.assertEqual(raster, b"".join(b"\0" + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height)))
        with self.assertRaises(RncError):
            bank_atlas.png_from_rgba(1, 1, b"")

    def test_unknown_format_and_path_ids_rejected(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(bank_atlas, "ROOT", Path(directory)):
            root = Path(directory)
            (root / "re").mkdir()
            (root / "re/rnc_blocks.json").write_text(json.dumps({"schema_version": 1, "blocks": [{"id": "unknown"}]}))
            for identifier in ("../escape", "a/b", "x'", "a..b", "x" * 97, "unknown", "absent"):
                with self.subTest(identifier=identifier), self.assertRaises(RncError):
                    bank_atlas.catalog_entry(identifier)

    def test_metadata_requires_exact_values_and_types(self):
        entry = {"id": "test", "unpacked_size": 74, "structure": {"record_count": 1}}
        metadata = dict(status="ok", schema_version=1, renderer="wiznliz-bank-atlas", logical_id="test",
                        patterns=1, columns=1, input_bytes=74, width=8, height=8,
                        palette_policy="normal-rgb3-rounded-v1", transparent_index=0)
        bank_atlas.validate_metadata(metadata, entry, 1, 8, 8)
        for key, value in (("schema_version", True), ("patterns", 2), ("palette_policy", "guessed")):
            with self.assertRaises(RncError):
                bank_atlas.validate_metadata(metadata | {key: value}, entry, 1, 8, 8)

    def test_changed_or_redirected_extraction_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(bank_atlas, "ROOT", Path(directory)):
            root = Path(directory)
            destination = root / "local/extracted_assets/rnc"
            destination.mkdir(parents=True)
            source = destination / "test.bin"
            entry = {"id": "test", "unpacked_size": 74, "decoded_sha256": hashlib.sha256(bytes(74)).hexdigest()}
            with patch.object(bank_atlas, "catalog_entry", return_value=entry), \
                    patch.object(bank_atlas, "verify_executable", return_value=root / "unused"), \
                    patch.object(bank_atlas.subprocess, "run") as process:
                source.write_bytes(b"x" * 74)
                with self.assertRaisesRegex(RncError, "differs"):
                    bank_atlas.run_atlas("test")
                source.unlink()
                target = root / "outside.bin"
                target.write_bytes(bytes(74))
                source.symlink_to(target)
                with self.assertRaisesRegex(RncError, "redirected"):
                    bank_atlas.run_atlas("test")
                process.assert_not_called()


if __name__ == "__main__":
    unittest.main()
