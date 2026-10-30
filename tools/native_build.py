"""Explicit offline CMake builds and provenance for native asset executables."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from rom import ROOT
from rnc import RncError, atomic_write

PRESETS = ("debug", "release", "sanitize")
EXECUTABLES = ("wiznliz-rnc2", "wiznliz-bank-atlas", "wiznliz-scene-preview", "wiznliz-terrain", "wiznliz-movement", "wiznliz-airborne", "wiznliz-actor", "wiznliz-session", "wiznliz-trail", "wiznliz-private", "wiznliz-table-motion", "wiznliz-collision", "wiznliz-return-only")


def build_directory(preset):
    if preset not in PRESETS:
        raise RncError("unknown native build preset")
    directory = ROOT / "build" / preset
    if directory.resolve() != directory:
        raise RncError("native build directory contains a symlink")
    return directory


def source_hashes():
    paths = [ROOT / "CMakeLists.txt", ROOT / "CMakePresets.json", Path(__file__).resolve()]
    for relative in ("src", "tools/native", "tests/unit"):
        paths.extend(p for p in (ROOT / relative).rglob("*") if p.suffix in (".cpp", ".hpp"))
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def verify_executable(preset="debug", name="wiznliz-rnc2"):
    if name not in EXECUTABLES:
        raise RncError("unknown native executable")
    directory = build_directory(preset)
    executable = directory / name
    if executable.is_symlink():
        raise RncError("native executable may not be a symlink")
    try:
        report = json.loads((directory / "provenance.json").read_text())
        if (type(report["schema_version"]) is not int or report["schema_version"] != 2
                or report["preset"] != preset or report["sources"] != source_hashes()
                or report["executables"][name] != hashlib.sha256(executable.read_bytes()).hexdigest()):
            raise RncError("native source/executable changed since recorded build")
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise RncError(f"build native assets first: project.py build --preset {preset}: {exc}") from exc
    return executable


def run(command, preset):
    directory = build_directory(preset)
    if command == "configure":
        invocation = ["cmake", "--preset", preset, f"-DPython3_EXECUTABLE={sys.executable}"]
    elif command == "build":
        invocation = ["cmake", "--build", "--preset", preset]
    elif command == "test":
        for name in EXECUTABLES:
            verify_executable(preset, name)
        invocation = ["ctest", "--preset", preset]
    else:
        raise RncError("unknown native build command")
    before = source_hashes()
    process = subprocess.run(invocation, cwd=ROOT, check=False)
    if process.returncode == 0 and command == "build":
        after = source_hashes()
        if before != after:
            raise RncError("native sources changed during build; repeat build before extraction")
        if any((directory / name).is_symlink() for name in EXECUTABLES):
            raise RncError("native executable may not be a symlink")
        report = {"schema_version": 2, "preset": preset, "command": invocation,
                  "exit_status": process.returncode, "sources": after,
                  "executables": {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                                  for name in EXECUTABLES}}
        atomic_write(directory / "provenance.json", (json.dumps(report, indent=2) + "\n").encode())
    return process.returncode


def main(command, argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=PRESETS, default="debug")
    args = parser.parse_args(argv)
    return run(command, args.preset)
