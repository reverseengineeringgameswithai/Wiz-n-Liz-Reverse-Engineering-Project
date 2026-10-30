"""Exercise the identity guard with disposable synthetic repositories."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from hygiene import check_hygiene
from identity_guard import install, message_clean, scan_index


class IdentityGuardTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name) / "repo"
        self.home = Path(directory.name) / "home/someone"
        self.root.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Test Author")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "mirror.forbid", "synthhandle")
        (self.root / "clean.md").write_text("Nothing personal.\n")
        self.git("add", "clean.md")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, check=True)

    def stage(self, name, text):
        (self.root / name).parent.mkdir(parents=True, exist_ok=True)
        (self.root / name).write_text(text)
        self.git("add", name)

    def test_clean_index(self):
        self.assertEqual(scan_index(self.root, self.home), [])

    def test_terms_in_content_names_and_home_path(self):
        self.stage("a.md", "thanks SYNTHHANDLE\n")
        self.stage("b.json", f'{{"path": "{self.home}/project"}}\n')
        self.stage("notes/synthhandleish.md", "fine\n")
        self.stage("c.md", "someone else entirely\n")
        self.assertEqual(scan_index(self.root, self.home), ["a.md", "b.json", "notes/synthhandleish.md"])

    def test_staged_content_counts_not_the_worktree(self):
        self.stage("a.md", "synthhandle\n")
        (self.root / "a.md").write_text("cleaned but not staged\n")
        self.assertEqual(scan_index(self.root, self.home), ["a.md"])

    def test_messages_ignore_comment_lines(self):
        self.assertTrue(message_clean("Subject\n# synthhandle in a comment\n", self.root, self.home))
        self.assertFalse(message_clean("Thanks Synthhandle\n", self.root, self.home))
        self.assertFalse(message_clean(f"Built in {self.home}/x\n", self.root, self.home))

    def test_hygiene_reports_blocked_terms(self):
        self.stage("re/rom_manifest.json", '{"original": {"sha256": "' + "0" * 64 + '"}}\n')
        self.stage("a.md", "synthhandle\n")
        report = check_hygiene(self.root)
        self.assertFalse(report["ok"])
        self.assertTrue(any(error.endswith(" in a.md") for error in report["errors"]))

    def test_installed_hooks_refuse_content_and_messages(self):
        install(self.root)
        commit = lambda message: subprocess.run(["git", "-C", str(self.root), "commit", "-q", "-m", message],
                                                capture_output=True)
        self.assertEqual(commit("Clean start").returncode, 0)
        self.stage("a.md", "by synthhandle\n")
        refused = commit("Add a note")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn(b"blocked identity term in a.md", refused.stderr)
        self.assertNotIn(b"synthhandle", refused.stderr)
        self.stage("a.md", "by the user\n")
        refused = commit("Thanks synthhandle")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn(b"commit message contains a blocked identity term", refused.stderr)
        self.assertEqual(commit("Add a note").returncode, 0)


if __name__ == "__main__":
    unittest.main()
