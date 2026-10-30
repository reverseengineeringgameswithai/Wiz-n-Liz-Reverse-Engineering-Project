#!/usr/bin/env python3
"""Explicit bootstrap/build of a pinned GPL research decoder, not native gameplay.

By default uses existing verified downloads only. --download fetches the four
pinned source/license files; no normal project build performs these downloads.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "third_party/rnc_reference.lock.json"
LOCAL = ROOT / "local/tools/rnc-reference"
EXECUTABLE = LOCAL / "rnc-reference"
REPORT = LOCAL / "build.json"

# Original minimal compatibility glue. No ScummVM implementation is copied here.
ENDIAN_SHIM = """#pragma once
#include <cstdint>
#include <cstring>
using uint = unsigned int;
using byte = std::uint8_t;
using uint8 = std::uint8_t;
using uint16 = std::uint16_t;
using uint32 = std::uint32_t;
using int16 = std::int16_t;
using int32 = std::int32_t;
inline uint16 READ_BE_UINT16(const void *p) {
    const auto *b = static_cast<const uint8 *>(p);
    return static_cast<uint16>((uint16{b[0]} << 8) | b[1]);
}
inline uint16 READ_LE_UINT16(const void *p) {
    const auto *b = static_cast<const uint8 *>(p);
    return static_cast<uint16>((uint16{b[1]} << 8) | b[0]);
}
inline uint32 READ_BE_UINT32(const void *p) {
    const auto *b = static_cast<const uint8 *>(p);
    return (uint32{b[0]} << 24) | (uint32{b[1]} << 16) | (uint32{b[2]} << 8) | b[3];
}
"""


class ReferenceBuildError(ValueError):
    pass


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_directory(path: Path) -> None:
    path.relative_to(ROOT / "local")
    relative = path.relative_to(ROOT)
    if ".." in relative.parts:
        raise ReferenceBuildError("parent traversal is not permitted for local outputs")
    current = ROOT
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ReferenceBuildError(f"refusing symlink directory: {current}")
        current.mkdir(exist_ok=True)


def reject_symlinks(path: Path) -> None:
    relative = path.relative_to(ROOT)
    if ".." in relative.parts:
        raise ReferenceBuildError("parent traversal is not permitted")
    current = ROOT
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ReferenceBuildError(f"refusing symlink path: {current}")


def verify_sources() -> dict:
    lock = json.loads(LOCK.read_text())
    for item in lock["files"]:
        path = LOCAL / "upstream" / item["path"]
        reject_symlinks(path)
        if not path.is_file() or path.is_symlink():
            raise ReferenceBuildError(f"missing regular source file: {path}; use explicit --download")
        if path.stat().st_size != item["size_bytes"] or digest(path) != item["sha256"]:
            raise ReferenceBuildError(f"source differs from pin; preserve/review it: {path}")
    return lock


def download_sources() -> None:
    lock = json.loads(LOCK.read_text())
    for item in lock["files"]:
        destination = LOCAL / "upstream" / item["path"]
        safe_directory(destination.parent)
        if destination.exists() or destination.is_symlink():
            if destination.is_symlink() or not destination.is_file() or digest(destination) != item["sha256"]:
                raise ReferenceBuildError(f"refusing to replace existing modified path: {destination}")
            continue
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
            temporary = Path(stream.name)
        try:
            subprocess.run(
                ["curl", "--fail", "--location", "--max-time", "30", "--max-filesize",
                 "1048576", item["url"], "--output", str(temporary)],
                check=True, capture_output=True, timeout=35,
            )
            if temporary.stat().st_size != item["size_bytes"] or digest(temporary) != item["sha256"]:
                raise ReferenceBuildError(f"download digest/length mismatch: {item['path']}")
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)


def verify_executable() -> Path:
    """Check the local build's hashes; do not download or build implicitly."""
    verify_sources()
    reject_symlinks(REPORT)
    reject_symlinks(EXECUTABLE)
    if REPORT.stat().st_size > 1024 * 1024:
        raise ReferenceBuildError("reference build report exceeds 1 MiB")
    report = json.loads(REPORT.read_text())
    harness = ROOT / "re/reference_scripts/rnc_reference_main.cpp"
    if report["harness_sha256"] != digest(harness):
        raise ReferenceBuildError("reference harness changed; rebuild it explicitly")
    if report["builder_sha256"] != digest(Path(__file__).resolve()):
        raise ReferenceBuildError("reference builder changed; rebuild it explicitly")
    if EXECUTABLE.is_symlink() or digest(EXECUTABLE) != report["executable_sha256"]:
        raise ReferenceBuildError("reference executable differs from its build report")
    return EXECUTABLE


def build(download: bool = False) -> dict:
    safe_directory(LOCAL)
    if download:
        download_sources()
    lock = verify_sources()
    compiler = shutil.which("clang++")
    if compiler is None:
        raise ReferenceBuildError("clang++ with compiler-rt is required for this verified ASan harness")
    # Keep build work/logs for reproducibility; never modify the pinned sources.
    work = Path(tempfile.mkdtemp(prefix="build-", dir=LOCAL))
    shim = work / "compat/common/endian.h"
    shim.parent.mkdir(parents=True)
    shim.write_text(ENDIAN_SHIM)
    harness = ROOT / "re/reference_scripts/rnc_reference_main.cpp"
    output = work / "rnc-reference"
    command = [
        compiler, "-std=c++20", "-O1", "-g", "-fno-omit-frame-pointer",
        "-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-Wall", "-Wextra",
        "-I", str(work / "compat"), "-I", str(LOCAL / "upstream"),
        str(LOCAL / "upstream/common/compression/rnc_deco.cpp"), str(harness), "-o", str(output),
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60, check=False)
    report = {
        "schema_version": 1,
        "role": "independent research reference only, not native gameplay",
        "source_revision": lock["revision"],
        "license": lock["license"],
        "command": command,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "compiler_version": subprocess.check_output([compiler, "--version"], text=True, timeout=5),
        "harness_sha256": digest(harness),
        "builder_sha256": digest(Path(__file__).resolve()),
        "shim_sha256": digest(shim),
    }
    (work / "build.json").write_text(json.dumps(report, indent=2) + "\n")
    if result.returncode:
        raise ReferenceBuildError(f"reference compilation failed; see {work / 'build.json'}")
    if EXECUTABLE.is_symlink() or REPORT.is_symlink():
        raise ReferenceBuildError("refusing symlink executable/report destination")
    os.replace(output, EXECUTABLE)
    report["executable_sha256"] = digest(EXECUTABLE)
    report["executable"] = str(EXECUTABLE.relative_to(ROOT))
    (work / "complete.json").write_text(json.dumps(report, indent=2) + "\n")
    os.replace(work / "complete.json", REPORT)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Explicitly fetch absent pinned source/license files.")
    args = parser.parse_args()
    try:
        report = build(download=args.download)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(2, f"RNC reference build failed: {exc}\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
