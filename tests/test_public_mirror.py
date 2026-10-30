"""Exercise the public mirror export with disposable synthetic repositories."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from public_mirror import check_push, commit, export, install_guards, scrub

FAKE_GH = """#!/bin/sh
case "$1 $2" in
  "auth token") echo "token-for-$4" ;;
  "auth git-credential") cat >/dev/null; printf 'username=x-access-token\\npassword=%s\\n' "$GH_TOKEN" ;;
  *) exit 1 ;;
esac
"""


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
        self.git(self.source, "config", "mirror.forbid", "synthhandle")
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

    def test_scrub_replaces_longer_terms_first(self):
        terms = {"synthuser": "[author]", "synthuser.x@example.invalid": "[redacted]"}
        self.assertEqual(scrub("mail synthuser.x@example.invalid", self.home, terms), "mail [redacted]")

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

    def test_forbidden_handles_from_local_config(self):
        (self.source / "handle.md").write_text("Account SynthHandle.\n")
        self.commit_source("handle.md")
        self.run_export()
        self.assertEqual((self.dest / "handle.md").read_text(), "Account [redacted].\n")

    def mirror_identity(self):
        self.git(self.dest, "config", "user.name", "mirror-account")
        self.git(self.dest, "config", "user.email", "mirror@example.invalid")

    def test_check_push_scans_metadata_and_every_new_commit(self):
        self.mirror_identity()
        self.run_export()
        clean = commit(self.dest, "Mirror", root=self.source, home=self.home)
        update = lambda sha: [f"refs/heads/main {sha} refs/heads/main {'0' * 40}"]
        self.assertEqual(check_push(self.dest, update(clean), self.source, self.home), [])
        self.git(self.dest, "-c", "user.name=Synthuser", "commit", "-q", "--allow-empty", "-m", "x")
        named = self.git(self.dest, "rev-parse", "HEAD").decode().strip()
        self.git(self.dest, "commit", "-q", "--allow-empty", "-m", "later, clean")
        errors = check_push(self.dest, update(self.git(self.dest, "rev-parse", "HEAD").decode().strip()),
                            self.source, self.home)
        self.assertEqual(errors, [f"refs/heads/main: identity in commit {named[:12]}"])
        self.assertEqual(check_push(self.dest, [f"(delete) {'0' * 40} refs/heads/old {clean}"],
                                    self.source, self.home), [])

    def test_installed_hook_blocks_a_real_push(self):
        remote = self.dest.parent / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        self.git(self.dest, "remote", "add", "origin", str(remote))
        self.mirror_identity()
        self.run_export()
        clean = commit(self.dest, "Mirror", root=self.source, home=self.home)
        self.assertTrue(os.access(install_guards(self.dest, "mirror-account", self.source), os.X_OK))
        push = lambda: subprocess.run(["git", "-C", str(self.dest), "push", "-q", "origin", "HEAD:refs/heads/main"],
                                      capture_output=True, env={**os.environ, "HOME": str(self.home)})
        self.assertEqual(push().returncode, 0)
        (self.dest / "added.md").write_text("thanks synthhandle\n")
        self.git(self.dest, "add", "added.md")
        self.git(self.dest, "commit", "-q", "-m", "manual edit")
        result = push()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"public-mirror pre-push: refused", result.stderr)
        self.assertEqual(self.git(remote, "rev-parse", "main").decode().strip(), clean)

    def test_credential_gate_survives_skipped_hooks(self):
        self.mirror_identity()
        self.run_export()
        commit(self.dest, "Mirror", root=self.source, home=self.home)
        install_guards(self.dest, "mirror-account", self.source)
        helpers = self.git(self.dest, "config", "--local", "--get-all",
                           "credential.https://github.com.helper").decode().split("\n")
        self.assertEqual(helpers[0], "")
        bin_dir = self.dest.parent / "bin"
        bin_dir.mkdir()
        (bin_dir / "gh").write_text(FAKE_GH)
        (bin_dir / "gh").chmod(0o755)
        env = {**os.environ, "HOME": str(self.home), "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
               "GIT_TERMINAL_PROMPT": "0"}
        fill = lambda: subprocess.run(["git", "-C", str(self.dest), "credential", "fill"], capture_output=True,
                                      input=b"protocol=https\nhost=github.com\n\n", env=env)
        clean = fill()
        self.assertEqual(clean.returncode, 0, clean.stderr)
        self.assertIn(b"password=token-for-mirror-account", clean.stdout)
        self.git(self.dest, "-c", "user.name=Synthuser", "commit", "-q", "--allow-empty", "-m", "x")
        refused = fill()
        self.assertNotEqual(refused.returncode, 0)
        self.assertNotIn(b"password=", refused.stdout)
        self.assertIn(b"public-mirror credential: refused", refused.stderr)


if __name__ == "__main__":
    unittest.main()
