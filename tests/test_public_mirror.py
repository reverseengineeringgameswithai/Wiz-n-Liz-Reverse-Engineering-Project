"""Exercise the public mirror export with disposable synthetic repositories."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from public_mirror import commit, export, scrub


class PublicMirrorTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        base = Path(directory.name)
        self.home = base / "home/synthuser"
        self.source, self.dest = base / "source", base / "mirror"
        self.rom = b"synthetic protected input\x00"
        for repo in (self.source, self.dest):
            repo.mkdir()
            self.git(repo, "init", "-q")
        self.git(self.source, "config", "user.name", "Synthuser")
        self.git(self.source, "config", "user.email", "synthuser@example.invalid")
        (self.source / "re").mkdir()
        (self.source / "re/rom_manifest.json").write_text(json.dumps({
            "original": {"sha256": hashlib.sha256(self.rom).hexdigest()}
        }))
        (self.source / "notes.md").write_text(
            f"Root `{self.home}/Project`, tool {self.home}. Author SYNTHUSER, synthuser@example.invalid.\n")
        self.commit_source("notes.md", "re/rom_manifest.json")

    def git(self, repo, *args):
        return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout

    def commit_source(self, *paths):
        self.git(self.source, "add", *paths)
        self.git(self.source, "commit", "-q", "-m", "synthetic")

    def run_export(self):
        return export(self.dest, root=self.source, home=self.home)

    def test_scrub_paths_name_and_email(self):
        report = self.run_export()
        self.assertEqual(report["files"], 2)
        self.assertEqual((self.dest / "notes.md").read_text(),
                         "Root `~/Project`, tool ~. Author [author], [email].\n")

    def test_scrub_keeps_longer_words(self):
        terms = {"Synthuser": "[author]"}
        self.assertEqual(scrub("Synthusers /homes", self.home, terms), "Synthusers /homes")

    def test_untracked_and_stale_files_do_not_survive(self):
        (self.source / "local").mkdir()
        (self.source / "local/research.bin").write_bytes(b"untracked")
        (self.dest / "stale/old.md").parent.mkdir()
        (self.dest / "stale/old.md").write_text("old")
        report = self.run_export()
        self.assertEqual(report["removed"], ["stale/old.md"])
        self.assertFalse((self.dest / "stale").exists())
        self.assertFalse((self.dest / "local").exists())

    def test_refuses_rom_bytes_and_unscrubbable_identity(self):
        (self.source / "copy.bin").write_bytes(self.rom)
        self.commit_source("copy.bin")
        with self.assertRaisesRegex(ValueError, "original ROM bytes"):
            self.run_export()
        self.assertFalse((self.dest / "notes.md").exists())
        self.git(self.source, "rm", "-q", "copy.bin")
        (self.source / "word.md").write_text("synthuserish\n")
        self.commit_source("word.md")
        with self.assertRaisesRegex(ValueError, "identity remains"):
            self.run_export()

    def test_refuses_source_as_destination(self):
        with self.assertRaisesRegex(ValueError, "separate"):
            export(self.source, root=self.source, home=self.home)

    def test_commit_requires_separate_identity(self):
        self.run_export()
        with self.assertRaisesRegex(ValueError, "mirror identity"):
            self.git(self.dest, "config", "user.name", "Synthuser")
            self.git(self.dest, "config", "user.email", "synthuser@example.invalid")
            commit(self.dest, "Mirror", root=self.source, home=self.home)
        self.git(self.dest, "config", "user.name", "mirror-account")
        self.git(self.dest, "config", "user.email", "mirror@example.invalid")
        self.assertIsNotNone(commit(self.dest, "Mirror", root=self.source, home=self.home))
        self.assertIsNone(commit(self.dest, "Mirror", root=self.source, home=self.home))
        tracked = self.git(self.dest, "ls-files").decode().split()
        self.assertEqual(tracked, ["notes.md", "re/rom_manifest.json"])


if __name__ == "__main__":
    unittest.main()
