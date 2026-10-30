"""Exercise the identity guard with disposable synthetic repositories."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from hygiene import check_hygiene
from identity_guard import agent_decision, install, message_clean, scan_index


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

    def decide(self, tool, tool_input):
        return agent_decision({"tool_name": tool, "tool_input": tool_input}, self.root, self.home)

    def test_agent_shell_commands(self):
        self.git("config", "--add", "mirror.forbid", "someone")  # The home folder name is a blocked term.
        encoded = str(self.home).replace("/", "-")
        self.assertIsNone(self.decide("Bash", {"command": f"cd {self.home}/WizNLizPC && ls"}))
        self.assertIsNone(self.decide("Bash", {"command": f"ls /tmp/x{encoded}-WizNLizPC/"}))
        self.assertIsNotNone(self.decide("Bash", {"command": "echo someone > a.md"}))
        self.assertIsNone(self.decide("Bash", {"command": "git config --get-all mirror.forbid"}))
        self.assertIsNotNone(self.decide("Bash", {"command": "git commit -m 'thanks SynthHandle'"}))
        self.assertIsNotNone(self.decide("Bash", {"command": ["bash", "-lc", "echo synthhandle > a.md"]}))

    def test_agent_patches_check_added_lines_and_headers(self):
        patch = lambda body: {"command": f"*** Begin Patch\n{body}\n*** End Patch\n"}
        self.assertIsNone(self.decide("apply_patch", patch(
            f"*** Update File: {self.home}/WizNLizPC/a.md\n@@\n-by synthhandle\n+by the user")))
        self.assertIsNotNone(self.decide("apply_patch", patch("*** Add File: a.md\n+thanks Synthhandle")))
        self.assertIsNotNone(self.decide("apply_patch", patch(f"*** Add File: a.md\n+path {self.home}/x")))
        self.assertIsNotNone(self.decide("apply_patch", patch("*** Add File: notes/synthhandle.md\n+fine")))

    def test_agent_file_tools_and_other_tools(self):
        self.assertIsNone(self.decide("Write", {"file_path": f"{self.home}/WizNLizPC/a.md", "content": "fine"}))
        self.assertIsNotNone(self.decide("Write", {"file_path": "a.md", "content": f"see {self.home}/x"}))
        self.assertIsNone(self.decide("Edit", {"file_path": "a.md", "old_string": "synthhandle",
                                               "new_string": "the user"}))
        self.assertIsNotNone(self.decide("MultiEdit", {"file_path": "a.md",
                                                       "edits": [{"new_string": "x"}, {"new_string": "SYNTHHANDLE"}]}))
        self.assertIsNotNone(self.decide("mcp__github__create_issue", {"body": "by synthhandle"}))
        self.assertIsNone(self.decide("update_plan", {"plan": [{"step": "fix the notes"}]}))

    def test_agent_hook_command_denies_as_json(self):
        import json, os
        event = {"tool_name": "Bash", "tool_input": {"command": "echo synthhandle"}, "cwd": str(self.root)}
        run = lambda payload: subprocess.run([sys.executable, "-B", str(ROOT / "tools/identity_guard.py"),
                                              "--agent-hook"], input=json.dumps(payload).encode(),
                                             capture_output=True, env={**os.environ, "HOME": str(self.home)})
        denied = run(event)
        self.assertEqual(denied.returncode, 0)
        output = json.loads(denied.stdout)["hookSpecificOutput"]
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertNotIn("synthhandle", output["permissionDecisionReason"].lower())
        allowed = run({**event, "tool_input": {"command": "echo hello"}})
        self.assertEqual((allowed.returncode, allowed.stdout), (0, b""))

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
