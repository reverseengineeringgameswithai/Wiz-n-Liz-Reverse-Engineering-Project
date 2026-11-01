"""Exercise local extent sharing on disposable synthetic files."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from dedupe_local import find_duplicates, process

BLOCK = bytes(range(256)) * 64  # 16 KiB of synthetic data


class DedupeLocalTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def write(self, name: str, data: bytes) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def test_groups_only_identical_regular_files_once_per_inode(self):
        first = self.write("run-a/trace.json", BLOCK)
        self.write("run-b/trace.json", BLOCK)
        self.write("run-c/trace.json", BLOCK[:-1] + b"x")  # Same size, other bytes.
        self.write("run-a/small.txt", b"tiny")
        self.write("run-b/small.txt", b"tiny")
        os.symlink(first, self.root / "link.json")
        os.link(first, self.root / "hardlink.json")
        groups = find_duplicates(self.root)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["size"], len(BLOCK))
        self.assertEqual(len(groups[0]["paths"]), 2)
        self.assertIn(str(self.root / "run-b/trace.json"), groups[0]["paths"])
        self.assertNotIn(str(self.root / "link.json"), groups[0]["paths"])

    def test_apply_keeps_every_path_content_and_mtime(self):
        data = BLOCK * 3 + b"unaligned tail"
        paths = [self.write(f"run-{index}/cases.txt", data) for index in range(3)]
        for index, path in enumerate(paths):
            os.utime(path, ns=(1_000_000_000 * index, 2_000_000_000 * index))
        before = [(path.stat().st_ino, path.stat().st_mtime_ns) for path in paths]
        summary = process(find_duplicates(self.root), apply=True)
        self.assertEqual(summary["duplicate_bytes"], 2 * len(data))
        # Extent-sharing filesystems share both copies; others (tmpfs) report each.
        self.assertEqual(summary["shared_bytes"] + summary["already_shared_bytes"]
                         + len(data) * len(summary["failures"]), 2 * len(data))
        for path, (inode, mtime) in zip(paths, before):
            self.assertEqual(path.read_bytes(), data)
            self.assertEqual((path.stat().st_ino, path.stat().st_mtime_ns), (inode, mtime))

    def test_report_only_changes_nothing(self):
        paths = [self.write(f"run-{index}/state.bin", BLOCK) for index in range(2)]
        summary = process(find_duplicates(self.root), apply=False)
        self.assertEqual(summary["shared_bytes"], 0)
        self.assertEqual(summary["failures"], [])
        self.assertEqual(summary["reclaimable_bytes"] + summary["already_shared_bytes"], len(BLOCK))
        for path in paths:
            self.assertEqual(path.read_bytes(), BLOCK)

    def test_cli_reports_json_and_rejects_missing_root(self):
        self.write("run-a/x.bin", BLOCK)
        self.write("run-b/x.bin", BLOCK)
        tool = [sys.executable, "-B", str(ROOT / "tools/dedupe_local.py")]
        report = subprocess.run([*tool, str(self.root)], capture_output=True, text=True)
        self.assertEqual(report.returncode, 0, report.stderr)
        self.assertIn('"applied": false', report.stdout)
        missing = subprocess.run([*tool, str(self.root / "absent")], capture_output=True, text=True)
        self.assertEqual(missing.returncode, 2)


if __name__ == "__main__":
    unittest.main()
