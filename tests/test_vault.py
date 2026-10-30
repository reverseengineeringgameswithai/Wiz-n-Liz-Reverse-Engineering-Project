from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from check_vault import check_vault


class VaultTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)

    def note(self, name, fields="id: N-1\ntype: note\nstatus: active", body=""):
        path = self.root / (name + ".md")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\n{fields}\n---\n{body}\n")

    def test_valid_explicit_links_and_anchors(self):
        self.note("a", body="[[b#Real heading|alias]]\n[[b#^block]]")
        self.note("b", "id: N-2\ntype: note\nstatus: active", "# Real heading\ntext ^block")
        self.assertTrue(check_vault(self.root)["ok"])

    def test_examples_are_ignored(self):
        self.note("a", body="`[[fake]]`\n````md\n[[fake]]\n```\n[[still-fake]]\n````\n~~~\n[[fake]]\n~~~\n")
        self.assertTrue(check_vault(self.root)["ok"])

    def test_missing_and_duplicate_fields(self):
        self.note("a", "id: SAME\ntype: note")
        self.note("b", "id: SAME\ntype: note\nstatus: active")
        errors = "\n".join(check_vault(self.root)["errors"])
        self.assertIn("required field status", errors)
        self.assertIn("duplicate stable ID", errors)

    def test_missing_links_and_anchors(self):
        self.note("a", body="[[missing]] [[a#missing]]")
        self.assertEqual(len(check_vault(self.root)["errors"]), 2)

    def test_task_relationship_must_exist_and_be_linked(self):
        self.note("a", "id: N-1\ntype: note\nstatus: active\ntask: TASK-0001")
        self.assertFalse(check_vault(self.root)["ok"])
        self.note("07_Tasks/TASK-0001-example", 'id: TASK-0001\ntype: task\nstatus: done\ndeliverable: a useful thing\nacceptance: ["verified"]')
        self.assertIn("requires matching explicit task link", str(check_vault(self.root)["errors"]))
        self.note("a", "id: N-1\ntype: note\nstatus: active\ntask: TASK-0001", "[[07_Tasks/TASK-0001-example]]")
        self.assertTrue(check_vault(self.root)["ok"])

    def test_task_acceptance_and_finding_evidence_required(self):
        self.note("07_Tasks/TASK-1-example", "id: TASK-1\ntype: task\nstatus: done")
        self.note("finding", "id: FIND-1\ntype: finding\nstatus: active")
        errors = "\n".join(check_vault(self.root)["errors"])
        self.assertIn("task needs", errors)
        self.assertIn("finding needs rom_id", errors)

    def test_bad_frontmatter_and_empty_vault(self):
        self.assertFalse(check_vault(self.root)["ok"])
        self.note("a", "id: x\nid: y\ntype: note\nstatus: active")
        self.assertIn("duplicate frontmatter key", str(check_vault(self.root)["errors"]))


if __name__ == "__main__":
    unittest.main()
