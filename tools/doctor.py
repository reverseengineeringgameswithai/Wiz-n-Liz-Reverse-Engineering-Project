#!/usr/bin/env python3
"""Read-only local toolchain audit; never installs or downloads dependencies."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys


TIMEOUT_SECONDS = 10
OUTPUT_LIMIT = 8192
TOOL_COMMANDS = {
    "c++": ["c++", "--version"],
    "clang++": ["clang++", "--version"],
    "python3": ["python3", "--version"],
    "go": ["go", "version"],
    "cmake": ["cmake", "--version"],
    "ninja": ["ninja", "--version"],
    "pkg-config": ["pkg-config", "--version"],
    "radare2": ["r2", "-v"],
    "mame": ["mame", "-version"],
    "java": ["java", "-version"],
    "objdump": ["objdump", "--version"],
}
PACKAGES = (
    "gcc", "gcc-c++", "clang", "python3", "golang", "cmake", "ninja-build",
    "SDL3", "SDL3-devel", "mame", "ghidra", "radare2", "binutils",
)


def probe(argv: list[str], root: Path) -> dict:
    """Probe without a shell, with timeout and bounded retained output."""
    executable = shutil.which(argv[0])
    result = {"command": argv, "path": executable, "exit_code": None}
    if executable is None:
        return {**result, "status": "missing", "output": ""}
    try:
        completed = subprocess.run(
            [executable, *argv[1:]], cwd=root, capture_output=True,
            text=True, errors="replace", timeout=TIMEOUT_SECONDS, check=False,
        )
    except subprocess.TimeoutExpired:
        return {**result, "status": "timeout", "output": ""}
    except OSError as exc:
        return {**result, "status": "error", "output": str(exc)}
    output = (completed.stdout + completed.stderr).strip()
    return {
        **result,
        "status": "available" if completed.returncode == 0 else "failed",
        "exit_code": completed.returncode,
        "output": output[:OUTPUT_LIMIT],
        "output_truncated": len(output) > OUTPUT_LIMIT,
    }


def collect_report(root: Path | None = None) -> dict:
    """Return JSON-safe observations, separating availability from validation."""
    root = (root or Path(__file__).resolve().parents[1]).resolve()
    tools = {name: probe(command, root) for name, command in TOOL_COMMANDS.items()}
    sdl3 = probe(["pkg-config", "--modversion", "sdl3"], root)
    try:
        os_release = platform.freedesktop_os_release()
    except OSError:
        os_release = {}
    required_native = ["c++", "cmake", "ninja", "pkg-config"]
    missing_native = [name for name in required_native if tools[name]["status"] != "available"]
    if sdl3["status"] != "available":
        missing_native.append("SDL3 development package (pkg-config sdl3)")
    return {
        "schema_version": 1,
        "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository_root": str(root),
        "host": {
            "os_release": os_release,
            "machine": platform.machine(),
            "kernel": platform.release(),
            "python_running": sys.version,
        },
        "tools": tools,
        "other_paths": {
            name: shutil.which(name)
            for name in ("ghidraRun", "analyzeHeadless", "rizin", "clownassembler", "m68k-linux-gnu-objdump")
        },
        "installed_rpm_packages": probe(["rpm", "-q", *PACKAGES], root),
        "sdl3_pkg_config": sdl3,
        "native_build_prerequisites": {
            "available": not missing_native,
            "missing": missing_native,
            "build_verified": False,
            "note": "Availability probes do not establish that this project builds or runs.",
        },
        "scope": "PATH and installed RPM audit; no installs, downloads, builds, or emulator execution",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-native", action="store_true",
        help="Exit 1 when native C++/CMake/Ninja/SDL3 development prerequisites are unavailable.",
    )
    args = parser.parse_args(argv)
    report = collect_report()
    print(json.dumps(report, indent=2, sort_keys=True))
    return int(args.require_native and not report["native_build_prerequisites"]["available"])


if __name__ == "__main__":
    raise SystemExit(main())
