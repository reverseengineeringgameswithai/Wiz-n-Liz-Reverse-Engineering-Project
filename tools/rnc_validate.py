"""Verify the recorded RNC2 block and extract using a native or reference codec.

No implicit download/build happens. Only validated output is published locally.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from rom import DEFAULT_ROM, ROOT, inspect_file, verify_expected
from rnc import (RncError, approved_directory, atomic_write, inspect_block,
                 parse_block, validate_decoded)


def validate_reference_metadata(metadata: dict, header, block_size: int) -> None:
    expected = {
        "status": "ok", "decoder_return": header.unpacked_size,
        "consumed_total_bytes": block_size, "consumed_payload_bytes": header.packed_size,
        "produced_bytes": header.unpacked_size, "packed_crc16": header.packed_crc16,
        "unpacked_crc16": header.unpacked_crc16,
        "address_sanitizer": True, "undefined_behavior_sanitizer": True,
    }
    if not isinstance(metadata, dict):
        raise RncError("reference metadata is not an object")
    for key, value in expected.items():
        if type(metadata.get(key)) is not type(value) or metadata.get(key) != value:
            raise RncError(f"reference metadata disagrees on {key}")


def validate_native_metadata(metadata: dict, header, block_size: int) -> None:
    expected = {"status": "ok", "decoder": "wiznliz-rnc2", "schema_version": 1,
                "consumed_total_bytes": block_size, "consumed_payload_bytes": header.packed_size,
                "produced_bytes": header.unpacked_size, "packed_crc16": header.packed_crc16,
                "unpacked_crc16": header.unpacked_crc16}
    if not isinstance(metadata, dict):
        raise RncError("native metadata is not an object")
    for key, value in expected.items():
        if type(metadata.get(key)) is not type(value) or metadata.get(key) != value:
            raise RncError(f"native metadata disagrees on {key}")


def invoke_decoder(executable: Path, source: Path) -> tuple[bytes, dict]:
    command = [str(executable), str(source)]
    overrides = {"ASAN_OPTIONS": "detect_leaks=0:abort_on_error=1",
                 "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=1"}
    try:
        result = subprocess.run(command, cwd=ROOT, env=os.environ | overrides,
                                capture_output=True, timeout=12, check=False)
        stdout, stderr = result.stdout, result.stderr
        code, timed_out = result.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or b"", exc.stderr or b""
        code, timed_out = None, True
    return stdout, {
        "command": command, "cwd": str(ROOT), "environment_overrides": overrides,
        "exit_status": code, "timed_out": timed_out,
        "stdout_size": len(stdout), "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr": stderr.decode("utf-8", errors="replace")[:65536],
        "stderr_truncated": len(stderr) > 65536,
    }


def invoke_reference(executable: Path, source: Path) -> tuple[bytes, dict]:
    return invoke_decoder(executable, source)


def run_validation(block_id: str, decode: bool, backend="native", preset="debug") -> tuple[int, dict]:
    if backend not in ("native", "reference"):
        raise RncError("unknown RNC2 backend")
    metadata = json.loads((ROOT / "re/rnc_blocks.json").read_text())
    if metadata["schema_version"] != 1 or metadata["address_space"] != "rom_file_offset":
        raise RncError("unsupported RNC metadata schema/address space")
    if not re.fullmatch(r"[a-z0-9]+(?:[._-][a-z0-9]+)*", block_id):
        raise RncError("invalid block logical ID")
    selected = [entry for entry in metadata["blocks"] if entry["id"] == block_id]
    if len(selected) != 1:
        raise RncError("block must have exactly one recorded metadata entry")
    entry = selected[0]
    before = inspect_file()
    verify_expected(before)
    data = DEFAULT_ROM.read_bytes()
    if hashlib.sha256(data).hexdigest() != before["sha256"]:
        raise RncError("input changed before validation")
    output = Path(tempfile.mkdtemp(prefix="run-", dir=approved_directory(ROOT, "local/generated/rnc-validation")))
    report = {"schema_version": 1, "block_id": block_id, "outcome": "failed",
              "rom_identity": {k: before[k] for k in ("size_bytes", "sha256")},
              "decode_requested": decode, "backend": backend, "native_game_logic": False}
    try:
        offset = entry["file_offset"]
        header, _ = parse_block(data, offset)
        block = data[offset:header.end_exclusive]
        observed = inspect_block(data, offset)
        report["observation"] = observed
        for field in ("method", "packed_size", "unpacked_size", "packed_crc16", "unpacked_crc16"):
            if getattr(header, field) != entry[field]:
                raise RncError(f"header differs from recorded metadata: {field}")
        if header.end_exclusive != entry["end_exclusive"] or observed["block_sha256"] != entry["block_sha256"]:
            raise RncError("block boundary/hash differs from recorded metadata")
        report["outcome"] = "packed_crc_verified"
        decoded = None
        if decode:
            source = output / "input.rnc"
            atomic_write(source, block)
            if backend == "reference":
                from build_rnc_reference import verify_executable
                executable = verify_executable()
                decoded, process = invoke_reference(executable, source)
                report["reference_lock"] = "third_party/rnc_reference.lock.json"
            else:
                from native_build import verify_executable
                executable = verify_executable(preset)
                decoded, process = invoke_decoder(executable, source)
                report["native_build_provenance"] = str((executable.parent / "provenance.json").relative_to(ROOT))
                report["native_build_sources"] = json.loads((executable.parent / "provenance.json").read_text())["sources"]
            report[f"{backend}_process"] = process
            report[f"{backend}_executable_sha256"] = hashlib.sha256(executable.read_bytes()).hexdigest()
            if process["exit_status"] != 0 or process["timed_out"] or process["stderr_truncated"]:
                raise RncError(f"{backend} failed; see recorded process diagnostics")
            decoder_metadata = json.loads(process["stderr"])
            validator = validate_reference_metadata if backend == "reference" else validate_native_metadata
            validator(decoder_metadata, header, len(block))
            report[f"{backend}_metadata"] = decoder_metadata
            report["decoded"] = validate_decoded(header, decoded)
            if report["decoded"]["sha256"] != entry["decoded_sha256"]:
                raise RncError("decoded digest differs from independently recorded reference")
            report["outcome"] = "decoded_integrity_verified"
        verify_expected(inspect_file())
        report["rom_unchanged"] = True
        if decoded is not None:
            destination = approved_directory(ROOT, "local/extracted_assets/rnc") / f"{block_id}.bin"
            atomic_write(destination, decoded)
            report["decoded"]["path"] = str(destination.relative_to(ROOT))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        report["outcome"] = "failed"
        report["error"] = str(exc)
    finally:
        try:
            verify_expected(inspect_file())
            report["rom_unchanged"] = True
        except (OSError, ValueError) as exc:
            report["rom_unchanged"] = False
            report["outcome"] = "failed"
            report["identity_error"] = str(exc)
        atomic_write(output / "report.json", (json.dumps(report, indent=2) + "\n").encode())
    return int(report["outcome"] == "failed"), {
        "outcome": report["outcome"], "report": str(output / "report.json"),
        "decoded": report.get("decoded"), "error": report.get("error"),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block", default="rnc.unclassified.0001", help="Recorded logical block ID")
    parser.add_argument("--decode", action="store_true", help="Use the explicitly built codec and atomically save validated output")
    parser.add_argument("--backend", choices=("native", "reference"), default="native")
    parser.add_argument("--preset", choices=("debug", "release", "sanitize"), default="debug", help="Native build preset")
    args = parser.parse_args(argv)
    try:
        code, result = run_validation(args.block, args.decode, args.backend, args.preset)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(f"rnc-validate: {exc}")
        return 1
    print(json.dumps(result, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
