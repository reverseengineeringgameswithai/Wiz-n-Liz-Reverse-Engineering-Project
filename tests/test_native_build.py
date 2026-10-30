"""Reject stale/redirected codec artifacts before executing extraction."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import native_build
from rnc import RncError


class NativeBuildTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.directory = self.root / "build/debug"
        self.directory.mkdir(parents=True)
        self.executable = self.directory / "wiznliz-rnc2"
        self.executable.write_bytes(b"fixture, never executed")
        self.report = {"schema_version": 2, "preset": "debug", "sources": {"codec.cpp": "old"},
                       "executables": {"wiznliz-rnc2": hashlib.sha256(self.executable.read_bytes()).hexdigest()}}
        self.save_report()
        patcher = patch.object(native_build, "ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(native_build, "source_hashes", return_value={"codec.cpp": "old"})
        self.sources = patcher.start()
        self.addCleanup(patcher.stop)

    def save_report(self):
        (self.directory / "provenance.json").write_text(json.dumps(self.report))

    def test_matching_build_accepted(self):
        self.assertEqual(native_build.verify_executable(), self.executable)

    def test_selected_executable_requires_own_hash(self):
        atlas = self.directory / "wiznliz-bank-atlas"
        atlas.write_bytes(b"atlas fixture")
        with self.assertRaises(RncError):
            native_build.verify_executable(name=atlas.name)
        self.report["executables"][atlas.name] = hashlib.sha256(atlas.read_bytes()).hexdigest()
        self.save_report()
        self.assertEqual(native_build.verify_executable(name=atlas.name), atlas)
        with self.assertRaises(RncError):
            native_build.verify_executable(name="../unknown")

    def test_changed_source_or_executable_rejected(self):
        self.sources.return_value = {"codec.cpp": "new"}
        with self.assertRaises(RncError):
            native_build.verify_executable()
        self.sources.return_value = self.report["sources"]
        self.executable.write_bytes(b"different")
        with self.assertRaises(RncError):
            native_build.verify_executable()

    def test_missing_or_wrong_provenance_rejected(self):
        for field, value in (("schema_version", True), ("preset", "release")):
            before = self.report[field]
            self.report[field] = value
            self.save_report()
            with self.assertRaises(RncError):
                native_build.verify_executable()
            self.report[field] = before
        (self.directory / "provenance.json").unlink()
        with self.assertRaises(RncError):
            native_build.verify_executable()

    def test_symlinked_executable_or_build_rejected(self):
        target = self.root / "outside"
        target.write_bytes(self.executable.read_bytes())
        self.executable.unlink()
        self.executable.symlink_to(target)
        with self.assertRaises(RncError):
            native_build.verify_executable()
        (self.root / "build/release").symlink_to(self.directory, target_is_directory=True)
        with self.assertRaises(RncError):
            native_build.build_directory("release")
