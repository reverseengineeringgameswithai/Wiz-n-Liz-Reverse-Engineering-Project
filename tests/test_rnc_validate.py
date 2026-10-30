"""Publication must follow independent length/CRC/consumption validation."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import rnc_validate as validation
from rnc import RncError, parse_block
from test_rnc_upstream import LITERAL_A


def reference_metadata():
    return {"status": "ok", "decoder": "wiznliz-rnc2", "schema_version": 1, "decoder_return": 1, "consumed_total_bytes": 21,
            "consumed_payload_bytes": 3, "produced_bytes": 1,
            "packed_crc16": 0x5650, "unpacked_crc16": 0x30C0,
            "address_sanitizer": True, "undefined_behavior_sanitizer": True}


class PublicationCases:
    """Same publication contract exercised independently for each backend."""

    def run_case(self, decoded: bytes, process_overrides=None, metadata=None):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        rom = root / "synthetic.rnc"
        rom.write_bytes(LITERAL_A)
        executable = root / "build/debug/wiznliz-rnc2"
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"synthetic stand-in; never executed")
        (executable.parent / "provenance.json").write_text('{"sources": {}}')
        metadata_dir = root / "re"
        metadata_dir.mkdir()
        header, _ = parse_block(LITERAL_A)
        entry = {"id": "test.literal", "file_offset": 0, "end_exclusive": 21,
                 "block_sha256": hashlib.sha256(LITERAL_A).hexdigest(),
                 "decoded_sha256": hashlib.sha256(b"A").hexdigest()}
        for key in ("method", "packed_size", "unpacked_size", "packed_crc16", "unpacked_crc16"):
            entry[key] = getattr(header, key)
        (metadata_dir / "rnc_blocks.json").write_text(json.dumps({
            "schema_version": 1, "address_space": "rom_file_offset", "blocks": [entry]}))
        destination = root / "local/extracted_assets/rnc/test.literal.bin"
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b"pre-existing validated asset")
        process = {"exit_status": 0, "timed_out": False, "stderr_truncated": False,
                   "stderr": json.dumps(reference_metadata() if metadata is None else metadata)}
        process.update(process_overrides or {})
        identity = {"size_bytes": len(LITERAL_A), "sha256": hashlib.sha256(LITERAL_A).hexdigest()}
        with (patch.object(validation, "ROOT", root), patch.object(validation, "DEFAULT_ROM", rom),
              patch.object(validation, "inspect_file", return_value=identity),
              patch.object(validation, "verify_expected"),
              patch("build_rnc_reference.verify_executable", return_value=executable),
              patch("native_build.verify_executable", return_value=executable),
              patch.object(validation, "invoke_decoder", return_value=(decoded, process))):
            code, summary = validation.run_validation("test.literal", True, backend=self.backend)
        report = json.loads(Path(summary["report"]).read_text())
        return code, report, destination

    def test_valid_decoder_is_published(self):
        code, report, destination = self.run_case(b"A")
        self.assertEqual(code, 0)
        self.assertEqual(report["outcome"], "decoded_integrity_verified")
        self.assertEqual(destination.read_bytes(), b"A")

    def test_same_size_corruption_preserves_existing_asset(self):
        code, report, destination = self.run_case(b"G")
        self.assertEqual(code, 1)
        self.assertIn("CRC mismatch", report["error"])
        self.assertEqual(destination.read_bytes(), b"pre-existing validated asset")

    def test_failed_decoder_preserves_existing_asset(self):
        code, report, destination = self.run_case(b"A", {"exit_status": -6})
        self.assertEqual(code, 1)
        self.assertEqual(report["outcome"], "failed")
        self.assertEqual(report[f"{self.backend}_process"]["exit_status"], -6)
        self.assertEqual(destination.read_bytes(), b"pre-existing validated asset")

    def test_extra_consumed_bytes_prevent_publication(self):
        code, report, destination = self.run_case(b"A", metadata=reference_metadata() | {"consumed_total_bytes": 22})
        self.assertEqual(code, 1)
        self.assertIn("consumed_total_bytes", report["error"])
        self.assertEqual(destination.read_bytes(), b"pre-existing validated asset")


class ReferencePublicationTests(PublicationCases, unittest.TestCase):
    backend = "reference"

    def test_reference_cannot_claim_wrong_consumption_or_sanitizers(self):
        header, _ = parse_block(LITERAL_A)
        for key, value in (("consumed_total_bytes", 20), ("consumed_payload_bytes", 4),
                           ("produced_bytes", 2), ("address_sanitizer", False),
                           ("undefined_behavior_sanitizer", 1), ("decoder_return", True)):
            metadata = reference_metadata() | {key: value}
            with self.subTest(key=key), self.assertRaises(RncError):
                validation.validate_reference_metadata(metadata, header, 21)
        with self.assertRaises(RncError):
            validation.validate_reference_metadata([], header, 21)


class NativePublicationTests(PublicationCases, unittest.TestCase):
    backend = "native"

    def test_native_metadata_rejects_inconsistent_fields(self):
        header, _ = parse_block(LITERAL_A)
        for key, value in (("decoder", "other"), ("schema_version", True),
                           ("consumed_payload_bytes", 4), ("produced_bytes", 2),
                           ("packed_crc16", False), ("unpacked_crc16", 0)):
            with self.subTest(key=key), self.assertRaises(RncError):
                validation.validate_native_metadata(reference_metadata() | {key: value}, header, 21)
        with self.assertRaises(RncError):
            validation.validate_native_metadata([], header, 21)


if __name__ == "__main__":
    unittest.main()
