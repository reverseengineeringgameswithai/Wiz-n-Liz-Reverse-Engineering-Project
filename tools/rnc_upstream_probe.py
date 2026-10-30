"""Bounded, offline experiment against the pinned upstream RNC2 decoder.

Run directly for the one TASK-0002 ROM candidate. Outputs stay under ignored
local/generated/rnc-sega2asm. No package downloads or source modifications occur.
"""
from __future__ import annotations

import hashlib
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from rom import DEFAULT_ROM, inspect_file, verify_expected
from rnc import crc16, inspect_block, parse_block, validate_decoded

ROOT = Path(__file__).resolve().parents[1]
OFFSET = 0x348B2
MAX_BYTES = 1 << 20


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run_command(command: list[str], *, cwd: Path, env=None, timeout=60) -> dict:
    try:
        result = subprocess.run(command, cwd=cwd, env=env, text=True,
                                capture_output=True, timeout=timeout)
        return {"command": command, "cwd": str(cwd), "exit_status": result.returncode,
                "timed_out": False, "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired as exc:
        return {"command": command, "cwd": str(cwd), "exit_status": None,
                "timed_out": True, "stdout": (exc.stdout or b"").decode(errors="replace"),
                "stderr": (exc.stderr or b"").decode(errors="replace")}


def probe_directory(root: Path = ROOT) -> Path:
    base = root.resolve() / "local/generated/rnc-sega2asm"
    if base.resolve() != base:
        raise ValueError("Probe output ancestor must not be a symlink")
    base.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="run-", dir=base))


def build_adapter(output: Path) -> tuple[Path, dict]:
    lock = json.loads((ROOT / "third_party/manifest.lock.json").read_text())
    source = ROOT / lock["sega2asm"]["source_path"]
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"], text=True).strip()
    if revision != lock["sega2asm"]["revision"] or dirty:
        raise ValueError("Upstream source must match its pin and be unmodified")
    go = ROOT / lock["go"]["executable"]
    version = run_command([str(go), "version"], cwd=ROOT, timeout=10)
    expected_version = f"go version {lock['go']['version']} {lock['go']['platform']}"
    if version["exit_status"] != 0 or version["stdout"].strip() != expected_version:
        raise ValueError("Reviewed Go compiler version/platform unavailable")
    adapter = ROOT / "re/reference_scripts/rnc_sega2asm_probe.go"
    executable = output / "rnc-sega2asm-probe"
    overrides = {
        "GOTOOLCHAIN": "local", "GOPROXY": "off", "GOSUMDB": "off",
        "GOCACHE": str(ROOT / "local/tools/go-cache"),
        "GOPATH": str(ROOT / "local/tools/go-work"),
        "GOMODCACHE": str(ROOT / "local/tools/go-modcache"),
    }
    environment = os.environ | overrides
    command = [str(go), "build", "-mod=readonly", "-trimpath", "-o", str(executable), str(adapter)]
    build = run_command(command, cwd=source, env=environment)
    build["environment_overrides"] = overrides
    (output / "build.json").write_text(json.dumps(build, indent=2) + "\n")
    if build["exit_status"] != 0:
        raise ValueError(f"Offline probe build failed; see {output / 'build.json'}")
    record = {"upstream_revision": revision, "upstream_dirty": False,
              "go_version": version, "adapter_source_sha256": digest(adapter),
              "adapter_executable_sha256": digest(executable), "build": build}
    return executable, record


def invoke_adapter(executable: Path, source: Path, destination: Path) -> dict:
    prlimit = shutil.which("prlimit")
    if prlimit is None:
        raise ValueError("prlimit is required to enforce hard subprocess limits")
    command = [prlimit, "--as=2147483648", "--cpu=5", "--fsize=1048576", "--",
               str(executable), str(source), str(destination)]
    overrides = {"GOMEMLIMIT": "64MiB", "GOMAXPROCS": "1"}
    result = run_command(command, cwd=ROOT, env=os.environ | overrides, timeout=5)
    result["environment_overrides"] = overrides
    if result["exit_status"] == 0:
        result["decoder"] = json.loads(result["stdout"])
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path,
                        help="Probe an exact bounded RNC2 block, without accessing the ROM")
    args = parser.parse_args(argv)
    report = {"schema_version": 1, "outcome": "unattempted"}
    output = None
    try:
        if args.input is None:
            before = inspect_file()
            verify_expected(before)
            report["rom_identity"] = {k: before[k] for k in ("size_bytes", "sha256")}
            data = DEFAULT_ROM.read_bytes()
            offset = OFFSET
        else:
            with args.input.open("rb") as stream:
                data = stream.read(MAX_BYTES + 19)
            if len(data) > MAX_BYTES + 18:
                raise ValueError("Input exceeds bounded probe limit")
            report["input_path"] = str(args.input.resolve())
            offset = 0
        header, _ = parse_block(data, offset)
        report["input_validation"] = inspect_block(data, offset)
        end = header.end_exclusive
        if not 0 < header.packed_size <= MAX_BYTES or not 0 < header.unpacked_size <= MAX_BYTES:
            raise ValueError("RNC2 candidate outside bounded probe limits")
        if args.input is not None and end != len(data):
            raise ValueError("Explicit input must contain exactly one declared block")
        output = probe_directory()
        source = output / "input.rnc"
        source.write_bytes(data[offset:end])
        executable, build = build_adapter(output)
        result = invoke_adapter(executable, source, output / "decoded.bin")
        report.update({"source_offset": offset, "source_end_exclusive": end,
                       "input_sha256": digest(source), "build": build, "process": result})
        if result["exit_status"] != 0:
            report["outcome"] = "tool_failure"
        else:
            with (output / "decoded.bin").open("rb") as stream:
                decoded = stream.read(MAX_BYTES + 1)
            if len(decoded) > MAX_BYTES:
                raise ValueError("Decoded file exceeds probe limit")
            actual_crc = crc16(decoded)
            report["decoded_validation"] = {
                "size_bytes": len(decoded), "sha256": hashlib.sha256(decoded).hexdigest(),
                "crc16_calculated": actual_crc,
                "unpacked_crc16_expected": header.unpacked_crc16,
                "size_matches": len(decoded) == header.unpacked_size,
                "crc_matches": actual_crc == header.unpacked_crc16,
            }
            try:
                if result["decoder"]["decoder_error"] is not None:
                    raise ValueError(result["decoder"]["decoder_error"])
                validate_decoded(header, decoded)
                report["outcome"] = "verified_output"
            except ValueError as exc:
                report["outcome"] = "rejected_output"
                report["validation_error"] = str(exc)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report["outcome"] = "probe_failure"
        report["error"] = str(exc)
    finally:
        if args.input is None:
            try:
                verify_expected(inspect_file())
                report["rom_unchanged"] = True
            except (OSError, ValueError) as exc:
                report["rom_unchanged"] = False
                report["outcome"] = "identity_failure"
                report["identity_error"] = str(exc)
        if output is not None:
            path = output / "report.json"
            path.write_text(json.dumps(report, indent=2) + "\n")
            print(json.dumps({"outcome": report["outcome"], "report": str(path)}, indent=2))
        else:
            print(json.dumps(report, indent=2))
    return 0 if report["outcome"] == "verified_output" else 2


if __name__ == "__main__":
    raise SystemExit(main())
