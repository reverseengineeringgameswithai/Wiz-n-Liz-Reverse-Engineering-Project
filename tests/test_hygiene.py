"""Exercise the real Git index using disposable synthetic repositories."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from hygiene import check_hygiene


class HygieneTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.git("init", "-q")
        (self.root / ".gitignore").write_text((ROOT / ".gitignore").read_text())
        (self.root / "re").mkdir()
        self.synthetic = b"original synthetic protected input\x00"
        (self.root / "re/rom_manifest.json").write_text(json.dumps({
            "original": {"sha256": hashlib.sha256(self.synthetic).hexdigest()}
        }))

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def test_clean_index_and_scoped_ignores(self):
        self.git("add", ".gitignore", "re/rom_manifest.json")
        report = check_hygiene(self.root)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["indexed_files_checked"], 2)

    def test_index_content_checked_even_when_worktree_differs(self):
        path = self.root / "disguised.txt"
        path.write_bytes(self.synthetic)
        self.git("add", "disguised.txt")
        path.write_text("innocent working copy")
        self.assertIn("original ROM bytes tracked", str(check_hygiene(self.root)["errors"]))

    def test_tracked_protected_path_is_not_saved_by_ignore(self):
        path = self.root / "Original_Game/fake.txt"
        path.parent.mkdir()
        path.write_text("synthetic")
        self.git("add", "-f", "Original_Game/fake.txt")
        self.assertIn("protected/generated path", str(check_hygiene(self.root)["errors"]))

    def test_blanket_markdown_ignore_fails(self):
        with (self.root / ".gitignore").open("a") as stream:
            stream.write("*.md\n")
        self.assertIn("source unexpectedly ignored", str(check_hygiene(self.root)["errors"]))


if __name__ == "__main__":
    unittest.main()
