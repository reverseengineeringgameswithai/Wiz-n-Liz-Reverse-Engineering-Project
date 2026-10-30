"""Run the reviewed sega2asm revision on the supported ROM, with audited outputs.

No download occurs here. See vault/03_Reverse_Engineering/SEGA2ASM.md for bootstrap.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate_segments(metadata: dict, size: int) -> list[dict]:
    """Reject silent gaps, overlaps, truncation and output-path injection."""
    if metadata.get("schema_version") != 1:
        raise ValueError("Unsupported segmentation schema")
    if metadata.get("address_space") != "rom_file_offset":
        raise ValueError("Segmentation must use ROM file offsets")
    if metadata.get("interval_convention") != "[start,end)":
        raise ValueError("Segmentation must use half-open intervals")
    segments = metadata.get("segments", [])
    if not segments or len(segments) > 4096:
        raise ValueError("Expected 1..4096 segments")
    offset, names = 0, set()
    for seg in segments:
        name = seg.get("name", "")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) or name in names:
            raise ValueError("Invalid or duplicate segment name")
        names.add(name)
        start, end = seg.get("start"), seg.get("end")
        if type(start) is not int or type(end) is not int:
            raise ValueError("Segment boundaries must be integers")
        if start != offset or not start < end <= size:
            raise ValueError("Segments must exactly partition the ROM")
        if seg.get("type") not in {"header", "m68k", "bin"}:
            raise ValueError("Unreviewed segment handler")
        if seg["type"] == "header" and (start, end) != (0, 512):
            raise ValueError("Header handler requires [0,512)")
        if seg["type"] == "m68k" and (start % 2 or end % 2):
            raise ValueError("68000 fragment must be word aligned")
        offset = end
    if offset != size:
        raise ValueError("Segmentation does not cover the ROM")
    return segments


def approved_output_base(root: Path) -> Path:
    root = root.resolve()
    base = root / "local" / "generated" / "sega2asm"
    # Reject redirecting any existing output ancestor through a symlink.
    if base.resolve() != base:
        raise ValueError("sega2asm output path contains a symlink")
    base.mkdir(parents=True, exist_ok=True)
    return base


def export_symbols(source: Path, destination: Path) -> None:
    lines = ["; Generated from re/symbols.csv; do not edit this export."]
    with source.open(newline="") as stream:
        for row in csv.DictReader(stream):
            if row["address_space"] != "m68000":
                continue
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", row["name"]):
                raise ValueError("Invalid symbol name")
            address = int(row["address"], 0)
            if not 0 <= address <= 0xFFFFFFFF:
                raise ValueError("Invalid symbol address")
            lines.append(f"{row['name']} = ${address:08X}")
    destination.write_text("\n".join(lines) + "\n")


def make_config(rom: Path, output: Path, symbols: Path, segments: list[dict]) -> str:
    """JSON is YAML-compatible and provides safe quoting without PyYAML."""
    return json.dumps({
        "name": "wiznliz_initial_analysis",
        "options": {
            "platform": "genesis", "basename": "wiznliz_initial_analysis",
            "target_path": str(rom), "base_path": str(output),
            "symbols_path": str(symbols), "asm_path": "asm",
            "asset_path": "assets", "build_path": "build",
            "header_output": False, "no_suggestions": True,
        },
        "segments": [{k: s[k] for k in ("name", "type", "start", "end")}
                     for s in segments],
    }, indent=2) + "\n"


def classify_result(returncode: int | None, output: str, missing: list[str],
                    *, timed_out: bool = False) -> str:
    if timed_out or returncode != 0:
        return "tool_failure"
    if "[WARN]" in output or "[ERROR]" in output or missing:
        return "partial_extraction"
    return "complete"


def check_outputs(output: Path, segments: list[dict], rom_data: bytes) -> tuple[list, list]:
    artifacts, failures = [], []
    for seg in segments:
        if seg["type"] == "header":
            paths = [output / "asm/header/header.asm", output / "asm/header/interrupts.asm"]
        elif seg["type"] == "m68k":
            paths = [output / f"asm/m68k/{seg['name']}.asm"]
        else:
            paths = [output / f"assets/bin/{seg['name']}.bin"]
        for path in paths:
            rel = str(path.relative_to(output))
            if not path.is_file() or path.stat().st_size == 0:
                failures.append(f"Missing or empty: {rel}")
                continue
            data = path.read_bytes()
            if seg["type"] == "bin" and data != rom_data[seg["start"]:seg["end"]]:
                failures.append(f"Raw range mismatch: {rel}")
            if seg["type"] == "m68k":
                # Even plausible MOVEM text is silently wrong at this pin.
                failures.append(f"Unverified upstream m68k output: {rel}; see FIND-0002")
            artifacts.append({"path": rel, "size": len(data),
                              "sha256": hashlib.sha256(data).hexdigest()})
    return artifacts, failures


def run_split(*, dry_run: bool = False) -> tuple[int, dict]:
    # Import at call time to keep pure wrapper helpers usable with synthetic fixtures.
    from rom import inspect_file, verify_expected

    lock = json.loads((ROOT / "third_party/manifest.lock.json").read_text())["sega2asm"]
    manifest = json.loads((ROOT / "re/rom_manifest.json").read_text())
    rom = ROOT / manifest["original"]["path"]
    before = inspect_file(rom)
    verify_expected(before)
    binary = ROOT / lock["executable"]
    if sha256(binary) != lock["executable_sha256"]:
        raise ValueError("Pinned sega2asm executable hash mismatch; inspect/rebuild explicitly")
    metadata = json.loads((ROOT / "re/sega2asm/segments.json").read_text())
    segments = validate_segments(metadata, rom.stat().st_size)
    output = Path(tempfile.mkdtemp(prefix="dry-run-" if dry_run else "split-",
                                   dir=approved_output_base(ROOT)))
    symbols = output / "symbols.txt"
    export_symbols(ROOT / "re/symbols.csv", symbols)
    config = output / "config.yaml"
    config.write_text(make_config(rom, output, symbols, segments))
    command = [str(binary)] + (["--dry-run"] if dry_run else []) + ["-c", str(config), "-v"]
    version_command = [str(binary), "--version"]
    version = subprocess.run(version_command, text=True, capture_output=True, timeout=10)
    if version.returncode or version.stdout.strip() != lock["version_output"]:
        raise ValueError("Pinned sega2asm version output mismatch")
    timed_out, returncode, captured = False, None, ""
    try:
        result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=60)
        returncode, captured = result.returncode, result.stdout
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        captured = (exc.stdout or b"").decode(errors="replace")
    (output / "process.log").write_text(captured)
    failures = []
    try:
        verify_expected(inspect_file(rom))
        unchanged = True
    except (ValueError, OSError) as exc:
        unchanged = False
        failures.append(str(exc))
    artifacts = []
    if not dry_run:
        try:
            artifacts, output_failures = check_outputs(output, segments, rom.read_bytes())
            failures.extend(output_failures)
        except OSError as exc:
            # Preserve the invocation/report even if an input or output disappears.
            failures.append(f"Cannot validate outputs: {exc}")
    outcome = classify_result(returncode, captured, failures, timed_out=timed_out)
    report = {
        "schema_version": 1, "outcome": outcome, "dry_run": dry_run,
        "tool_revision": lock["revision"], "tool_sha256": lock["executable_sha256"],
        "command": command, "cwd": str(ROOT), "exit_status": returncode,
        "timed_out": timed_out, "rom_unchanged": unchanged,
        "rom_identity": {"size_bytes": before["size_bytes"], "sha256": before["sha256"]},
        "version_command": version_command, "version_output": version.stdout.strip(),
        "version_exit_status": version.returncode,
        "config_sha256": sha256(config), "artifacts": artifacts, "failures": failures,
    }
    report_path = output / "run.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return (0 if outcome == "complete" else 2), {"outcome": outcome, "report": str(report_path),
                                               "failures": failures}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        code, result = run_split(dry_run=args.dry_run)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(f"sega2asm: {exc}")
        return 2
    print(json.dumps(result, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
