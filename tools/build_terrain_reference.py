#!/usr/bin/env python3
"""Explicit offline build (or --download bootstrap) of isolated Musashi research.

Normal CMake/native builds do not invoke or link this tool.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from build_rnc_reference import digest, reject_symlinks, safe_directory, ReferenceBuildError
from rom import ROOT

LOCK = ROOT / "third_party/terrain_reference.lock.json"
LOCAL = ROOT / "local/tools/terrain-reference"
EXECUTABLE = LOCAL / "terrain-reference"
REPORT = LOCAL / "build.json"
HARNESS = ROOT / "re/reference_scripts/terrain_reference.c"


def verify_sources(download=False):
    lock = json.loads(LOCK.read_text())
    for item in lock["files"]:
        path = LOCAL / "upstream" / item["path"]
        safe_directory(path.parent)
        reject_symlinks(path)
        if not path.exists() and download:
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
                temporary = Path(f.name)
            try:
                subprocess.run(["curl", "--fail", "--location", "--max-time", "30", "--max-filesize", "1048576",
                                item["url"], "--output", str(temporary)], check=True, capture_output=True, timeout=35)
                if digest(temporary) != item["sha256"]:
                    raise ReferenceBuildError("terrain reference download hash mismatch")
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
        if not path.is_file() or path.stat().st_size != item["size_bytes"] or digest(path) != item["sha256"]:
            raise ReferenceBuildError(f"missing/modified terrain reference source {path}; use explicit --download for absent files")
    return lock


def verify_executable():
    verify_sources()
    reject_symlinks(REPORT); reject_symlinks(EXECUTABLE)
    if REPORT.stat().st_size > 1048576:
        raise ReferenceBuildError("terrain reference report too large")
    report = json.loads(REPORT.read_text())
    for key, path in (("harness", HARNESS), ("builder", Path(__file__).resolve()), ("lock", LOCK), ("executable", EXECUTABLE)):
        if report[key + "_sha256"] != digest(path):
            raise ReferenceBuildError("terrain reference changed; rebuild explicitly")
    return EXECUTABLE


def build(download=False):
    safe_directory(LOCAL)
    lock = verify_sources(download)
    work = Path(tempfile.mkdtemp(prefix="build-", dir=LOCAL))
    # Copy verified upstream into build work; generator outputs never modify pin.
    for item in lock["files"]:
        dst = work / item["path"]; dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(LOCAL / "upstream" / item["path"], dst)
    compiler = shutil.which("clang")
    if not compiler: raise ReferenceBuildError("Clang with compiler-rt required")
    commands = [[compiler, "-O2", "m68kmake.c", "-o", "m68kmake"], [str(work / "m68kmake")],
        [compiler, "-O1", "-g", "-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-fno-omit-frame-pointer",
         "-DM68K_EMULATE_010=0", "-DM68K_EMULATE_EC020=0", "-DM68K_EMULATE_020=0", "-DM68K_EMULATE_030=0",
         "-DM68K_EMULATE_040=0", "-DM68K_EMULATE_PMMU=0", "-DM68K_INSTRUCTION_HOOK=1",
         "-I.", "m68kcpu.c", "m68kops.c", "softfloat/softfloat.c", str(HARNESS), "-lm", "-o", "terrain-reference"]]
    report = {"revision": lock["revision"], "cpu": "68000", "commands": [],
              "compiler": subprocess.check_output([compiler,"--version"], text=True, timeout=5)}
    for command in commands:
        p = subprocess.run(command, cwd=work, capture_output=True, text=True, timeout=120)
        report["commands"].append({"argv":command,"exit_status":p.returncode,"stdout":p.stdout,"stderr":p.stderr})
        (work / "build.json").write_text(json.dumps(report, indent=2) + "\n")
        if p.returncode: raise ReferenceBuildError(f"terrain reference build failed: {work / 'build.json'}")
    reject_symlinks(EXECUTABLE); reject_symlinks(REPORT)
    os.replace(work / "terrain-reference", EXECUTABLE)
    for key, path in (("harness", HARNESS), ("builder", Path(__file__).resolve()), ("lock", LOCK), ("executable", EXECUTABLE)):
        report[key + "_sha256"] = digest(path)
    (work / "complete.json").write_text(json.dumps(report, indent=2) + "\n")
    os.replace(work / "complete.json", REPORT)
    return {"ok": True, "report": str(REPORT)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    try: print(json.dumps(build(args.download), indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as exc: parser.exit(2, f"{exc}\n")
