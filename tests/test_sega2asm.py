"""Synthetic safety tests; no proprietary ROM is read."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import sega2asm


class Sega2asmTests(unittest.TestCase):
    def setUp(self):
        self.metadata = {"schema_version": 1, "address_space": "rom_file_offset",
                         "interval_convention": "[start,end)", "segments": [
                             {"name": "header", "type": "header", "start": 0, "end": 512},
                             {"name": "unknown", "type": "bin", "start": 512, "end": 768}]}

    def test_valid_partition(self):
        self.assertEqual(len(sega2asm.validate_segments(self.metadata, 768)), 2)

    def test_invalid_boundaries_handlers_and_names(self):
        for field, value in [("start", 511), ("start", 513), ("end", 900),
                             ("end", 512), ("end", 767), ("end", "768"),
                             ("name", "../escape"), ("name", "header"),
                             ("type", "z80")]:
            with self.subTest(field=field, value=value):
                metadata = copy.deepcopy(self.metadata)
                metadata["segments"][1][field] = value
                with self.assertRaises(ValueError):
                    sega2asm.validate_segments(metadata, 768)

    def test_config_quotes_spaces_and_apostrophes(self):
        source = Path("/tmp/with spaces/Wiz 'N' Liz.md")
        result = json.loads(sega2asm.make_config(source, Path("/tmp/out"),
                                                 Path("/tmp/symbols"), []))
        self.assertEqual(result["options"]["target_path"], str(source))

    def test_symlinked_output_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "elsewhere").mkdir()
            (root / "local").symlink_to(root / "elsewhere", target_is_directory=True)
            with self.assertRaises(ValueError):
                sega2asm.approved_output_base(root)

    def test_partial_extraction_is_not_success(self):
        self.assertEqual(sega2asm.classify_result(0, "[OK]", []), "complete")
        self.assertEqual(sega2asm.classify_result(0, "[WARN] error\n[OK]", []), "partial_extraction")
        self.assertEqual(sega2asm.classify_result(0, "", ["missing"]), "partial_extraction")
        self.assertEqual(sega2asm.classify_result(1, "", []), "tool_failure")
        self.assertEqual(sega2asm.classify_result(None, "", [], timed_out=True), "tool_failure")

    def test_raw_artifact_must_match_input(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            destination = output / "assets/bin/blob.bin"
            destination.parent.mkdir(parents=True)
            destination.write_bytes(b"abcd")
            segments = [{"name": "blob", "type": "bin", "start": 0, "end": 4}]
            _, failures = sega2asm.check_outputs(output, segments, b"abce")
            self.assertEqual(len(failures), 1)
            _, failures = sega2asm.check_outputs(output, segments, b"abcd")
            self.assertEqual(failures, [])

    def test_all_pinned_m68k_output_is_unverified(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            destination = output / "asm/m68k/fragment.asm"
            destination.parent.mkdir(parents=True)
            destination.write_text("\tnot.?\t#$2700\n")
            segments = [{"name": "fragment", "type": "m68k", "start": 0, "end": 4}]
            _, failures = sega2asm.check_outputs(output, segments, bytes(4))
            self.assertEqual(len(failures), 1)
            destination.write_text("\tmovem.l\t(a5)+,d3/d4/d5/d6/d7\n")
            _, failures = sega2asm.check_outputs(output, segments, bytes(4))
            self.assertEqual(len(failures), 1)


class UpstreamProbe(unittest.TestCase):
    @unittest.skipUnless((ROOT / "local/tools/sega2asm").is_file(), "pinned local tool unavailable")
    def test_actual_upstream_movem_and_move_to_sr_decode_errors(self):
        lock = json.loads((ROOT / "third_party/manifest.lock.json").read_text())["sega2asm"]
        binary = ROOT / lock["executable"]
        self.assertEqual(sega2asm.sha256(binary), lock["executable_sha256"])
        with tempfile.TemporaryDirectory(prefix="sega2asm-decode-") as directory:
            root = Path(directory)
            rom = root / "synthetic.md"
            # Original synthetic two-instruction fixture: MOVEM.L postincrement,
            # followed by MOVE.W immediate to SR; no game content required.
            rom.write_bytes(bytes(512) + bytes.fromhex("4cdd1f00 46fc2700"))
            symbols = root / "symbols.txt"
            symbols.write_text("")
            segments = [{"name": "fragment", "type": "m68k", "start": 512, "end": 520}]
            config = root / "probe.yaml"
            config.write_text(sega2asm.make_config(rom, root / "out", symbols, segments))
            result = subprocess.run([str(binary), "-c", str(config), "-v"],
                                    text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0)
            output = (root / "out/asm/m68k/fragment.asm").read_text()
            self.assertIn("movem.l\t(a5)+,d3/d4/d5/d6/d7", output)
            self.assertIn("not.?\t#$2700", output)
            _, failures = sega2asm.check_outputs(root / "out", segments, rom.read_bytes())
            self.assertEqual(len(failures), 1)

    @unittest.skipUnless((ROOT / "local/tools/sega2asm").is_file(), "pinned local tool unavailable")
    def test_actual_upstream_zero_exit_on_segment_failure(self):
        """Minimal failing bin write: upstream says [OK] despite [WARN] error."""
        lock = json.loads((ROOT / "third_party/manifest.lock.json").read_text())["sega2asm"]
        binary = ROOT / lock["executable"]
        self.assertEqual(sega2asm.sha256(binary), lock["executable_sha256"])
        with tempfile.TemporaryDirectory(prefix="sega2asm-synthetic-") as directory:
            root = Path(directory)
            rom = root / "synthetic.md"
            rom.write_bytes(bytes(512))
            symbols = root / "symbols.txt"
            symbols.write_text("")
            blocker = root / "not_a_directory"
            blocker.write_text("synthetic blocker")
            config = json.loads(sega2asm.make_config(rom, root / "out", symbols, []))
            config["segments"] = [{"name": "bad", "type": "bin", "start": 0, "end": 2,
                                   "output": str(blocker / "cannot_write.bin")}]
            path = root / "probe.yaml"
            path.write_text(json.dumps(config))
            result = subprocess.run([str(binary), "-c", str(path), "-v"],
                                    text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0)
            self.assertIn("[WARN]   error:", result.stdout)
            self.assertIn("[OK] sega2asm", result.stdout)
            self.assertEqual(sega2asm.classify_result(result.returncode, result.stdout, []),
                             "partial_extraction")


if __name__ == "__main__":
    unittest.main()
