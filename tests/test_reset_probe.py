"""Synthetic instruction fixtures authored for the narrow static field readers."""

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from reset_probe import (analyze_reset, atomic_json, branch_target, dbf_body_iterations,
                         dbf_target, lea_pc_target, moveq, movem_postincrement,
                         output_directory, word)


class ResetFieldsTests(unittest.TestCase):
    def test_word_bounds(self):
        self.assertEqual(word(bytes.fromhex("1234"), 0), 0x1234)
        for data, offset in ((b"", 0), (b"x", 0), (b"xx", -1), (b"xx", 1)):
            with self.assertRaises(ValueError):
                word(data, offset)

    def test_branch_displacements(self):
        self.assertEqual(branch_target(bytes.fromhex("607e"), 0), 128)
        self.assertEqual(branch_target(bytes.fromhex("60fe"), 0), 0)
        self.assertEqual(branch_target(bytes.fromhex("60000006"), 0), 8)
        self.assertEqual(branch_target(bytes.fromhex("6000fffc"), 0), 0xFFFFFFFE)
        self.assertEqual(branch_target(bytes.fromhex("60ff"), 0), 1)
        with self.assertRaises(ValueError):
            branch_target(bytes.fromhex("6000"), 0)
        with self.assertRaises(ValueError):
            branch_target(bytes.fromhex("4e71"), 0)

    def test_pc_relative_extension_base(self):
        self.assertEqual(lea_pc_target(bytes.fromhex("47fa0008"), 0), (3, 10))
        self.assertEqual(lea_pc_target(bytes.fromhex("43fafffc"), 0), (1, 0xFFFFFFFE))
        with self.assertRaises(ValueError):
            lea_pc_target(bytes.fromhex("43f90000"), 0)

    def test_movem_mask_order_and_width(self):
        self.assertEqual(movem_postincrement(bytes.fromhex("4c9a8103"), 0),
                         (2, 2, ["d0", "d1", "a0", "a7"]))
        self.assertEqual(movem_postincrement(bytes.fromhex("4cdb0404"), 0),
                         (3, 4, ["d2", "a2"]))
        with self.assertRaises(ValueError):
            movem_postincrement(bytes.fromhex("489a8103"), 0)

    def test_moveq_sign_extension(self):
        self.assertEqual(moveq(bytes.fromhex("767f"), 0), (3, 127))
        self.assertEqual(moveq(bytes.fromhex("7880"), 0), (4, -128))
        self.assertEqual(moveq(bytes.fromhex("7eff"), 0), (7, -1))
        with self.assertRaises(ValueError):
            moveq(bytes.fromhex("7180"), 0)

    def test_dbf_low_word_count_and_extension_base(self):
        self.assertEqual(dbf_target(bytes.fromhex("51cdfffe"), 0), (5, 0))
        self.assertEqual(dbf_body_iterations(0), 1)
        self.assertEqual(dbf_body_iterations(0xABCD0001), 2)
        self.assertEqual(dbf_body_iterations(0xFFFF), 65536)
        with self.assertRaises(ValueError):
            dbf_target(bytes.fromhex("50cdfffe"), 0)

    def test_analysis_rejects_truncated_or_unrecognized_input(self):
        for data in (b"", bytes(0x2FF), bytes(0x300)):
            with self.assertRaises(ValueError):
                analyze_reset(data)

    def test_output_rejects_symlinked_ancestors(self):
        for relative in ("local", "local/generated", "local/generated/reset"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "repo"
                root.mkdir()
                outside = Path(temporary) / "outside"
                outside.mkdir()
                link = root / relative
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(outside, target_is_directory=True)
                with self.assertRaises(ValueError):
                    output_directory(root)
                self.assertEqual(list(outside.iterdir()), [])

    def test_atomic_output_does_not_follow_existing_file_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = output_directory(root)
            protected = root / "protected.bin"
            protected.write_bytes(b"do not modify")
            report = output / "report.json"
            report.symlink_to(protected)
            # A historical predictable temporary name must also remain untouched.
            (output / "report.json.tmp").symlink_to(protected)
            atomic_json(report, {"ok": True})
            self.assertEqual(protected.read_bytes(), b"do not modify")
            self.assertFalse(report.is_symlink())
            self.assertEqual(report.read_text(), '{\n  "ok": true\n}\n')


if __name__ == "__main__":
    unittest.main()
