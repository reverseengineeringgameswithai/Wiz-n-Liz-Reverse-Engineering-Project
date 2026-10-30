"""Inspect a cataloged extracted bank through native C++; package its RGBA as PNG."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import zlib

from native_build import PRESETS, verify_executable
from bank_reference import check_atlas
from rnc import RncError, approved_directory, atomic_write
from rom import ROOT

MAX_PIXELS = 4 * 1024 * 1024
MAX_BANK_BYTES = 34 + 65536 * 40


def unpack_pam(data):
    """Accept only the bounded canonical transport emitted by the native CLI."""
    match = re.match(rb"P7\nWIDTH ([1-9][0-9]{0,6})\nHEIGHT ([1-9][0-9]{0,6})\n"
                     rb"DEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n", data[:160])
    if not match:
        raise RncError("unsupported native atlas transport")
    width, height = map(int, match.groups())
    if width * height > MAX_PIXELS or len(data) != match.end() + width * height * 4:
        raise RncError("atlas exceeds limits or has inconsistent extent")
    return width, height, data[match.end():]


def png_from_rgba(width, height, rgba):
    """Container encoding only; all pixel values are supplied by native code."""
    if not 0 < width * height <= MAX_PIXELS or width <= 0 or height <= 0 or len(rgba) != width * height * 4:
        raise RncError("invalid PNG raster extent")

    def chunk(kind, content):
        return struct.pack(">I", len(content)) + kind + content + struct.pack(">I", zlib.crc32(kind + content))

    stride = width * 4
    scanlines = b"".join(b"\0" + rgba[start:start + stride] for start in range(0, len(rgba), stride))
    # Stored DEFLATE blocks avoid compression-version-dependent output bytes.
    blocks = bytearray(b"\x78\x01")
    for start in range(0, len(scanlines), 65535):
        piece = scanlines[start:start + 65535]
        blocks.append(int(start + len(piece) == len(scanlines)))
        blocks.extend(struct.pack("<HH", len(piece), len(piece) ^ 0xFFFF))
        blocks.extend(piece)
    blocks.extend(struct.pack(">I", zlib.adler32(scanlines)))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", bytes(blocks)) + chunk(b"IEND", b""))


def catalog_entry(logical_id, expected_format="pattern_bank_v1"):
    if not isinstance(logical_id, str) or len(logical_id) > 96 or not re.fullmatch(r"[a-z0-9]+(?:[._-][a-z0-9]+)*", logical_id):
        raise RncError("invalid logical resource ID")
    catalog = json.loads((ROOT / "re/rnc_blocks.json").read_text())
    if catalog.get("schema_version") != 1:
        raise RncError("unsupported catalog schema")
    entries = [entry for entry in catalog["blocks"] if entry["id"] == logical_id]
    if len(entries) != 1 or entries[0].get("structure", {}).get("format") != expected_format:
        raise RncError(f"resource has no verified {expected_format} catalog entry")
    return entries[0]


def read_extracted(entry, max_bytes):
    source = approved_directory(ROOT, "local/extracted_assets/rnc") / f"{entry['id']}.bin"
    if source.is_symlink() or not 2 <= source.stat().st_size <= max_bytes:
        raise RncError("extracted resource is redirected or outside size limits")
    with source.open("rb") as stream:
        data = stream.read(max_bytes + 1)
    if len(data) != entry["unpacked_size"] or hashlib.sha256(data).hexdigest() != entry["decoded_sha256"]:
        raise RncError("extracted resource differs from verified catalog; run rnc-validate --decode")
    return source, data


def validate_metadata(metadata, entry, columns, width, height):
    expected = {"status": "ok", "schema_version": 1, "renderer": "wiznliz-bank-atlas",
                "logical_id": entry["id"], "patterns": entry["structure"]["record_count"],
                "columns": columns, "input_bytes": entry["unpacked_size"], "width": width,
                "height": height, "palette_policy": "normal-rgb3-rounded-v1", "transparent_index": 0}
    if not isinstance(metadata, dict):
        raise RncError("native metadata is not an object")
    for key, value in expected.items():
        if type(metadata.get(key)) is not type(value) or metadata.get(key) != value:
            raise RncError(f"native atlas metadata disagrees on {key}")
    if width != columns * 8 or height != ((expected["patterns"] - 1) // columns + 1) * 8:
        raise RncError("native atlas dimensions disagree with catalog")


def run_atlas(logical_id, columns=32, preset="debug"):
    if type(columns) is not int or not 1 <= columns <= 256:
        raise RncError("atlas requires 1 to 256 columns")
    entry = catalog_entry(logical_id)
    executable = verify_executable(preset, "wiznliz-bank-atlas")
    source, data = read_extracted(entry, MAX_BANK_BYTES)
    output = Path(tempfile.mkdtemp(prefix="run-", dir=approved_directory(ROOT, "local/generated/bank-atlas")))
    report = {"schema_version": 1, "outcome": "failed", "logical_id": logical_id,
              "input_path": str(source.relative_to(ROOT)), "input_sha256": entry["decoded_sha256"],
              "catalog_sha256": hashlib.sha256((ROOT / "re/rnc_blocks.json").read_bytes()).hexdigest(),
              "wrapper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "reference_model_sha256": hashlib.sha256((ROOT / "tools/bank_reference.py").read_bytes()).hexdigest(),
              "reference_lock_sha256": hashlib.sha256((ROOT / "third_party/vdp_reference.lock.json").read_bytes()).hexdigest(),
              "native_build": json.loads((executable.parent / "provenance.json").read_text()),
              "native_game_logic": False, "rom_cpu_execution": False}
    try:
        # Snapshot avoids racing a concurrent extraction. This is a local asset,
        # not the ROM, and no raw ROM is required by this command or executable.
        snapshot = output / "input.bin"
        atomic_write(snapshot, data)
        command = [str(executable), logical_id, str(snapshot), str(columns)]
        overrides = {"ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1", "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=1"}
        report["process"] = {"command": command, "cwd": str(ROOT), "environment_overrides": overrides,
                             "exit_status": None, "timed_out": False}
        result = subprocess.run(command, cwd=ROOT, env=os.environ | overrides, capture_output=True, timeout=20, check=False)
        report["process"].update(exit_status=result.returncode, stderr=result.stderr.decode(errors="replace")[:65536])
        if result.returncode or len(result.stderr) > 65536:
            raise RncError("native atlas failed; see process diagnostics")
        width, height, rgba = unpack_pam(result.stdout)
        metadata = json.loads(result.stderr)
        validate_metadata(metadata, entry, columns, width, height)
        report["native_metadata"] = metadata
        report["layout_check"] = check_atlas(data, rgba, width, height, columns)
        png = png_from_rgba(width, height, rgba)
        report["artifacts"] = {}
        for name, contents in (("atlas.pam", result.stdout), ("atlas.png", png)):
            atomic_write(output / name, contents)
            report["artifacts"][name] = {"path": str((output / name).relative_to(ROOT)),
                                         "size_bytes": len(contents), "sha256": hashlib.sha256(contents).hexdigest()}
        report["rgba_sha256"] = hashlib.sha256(rgba).hexdigest()
        report["outcome"] = "atlas_generated"
    except subprocess.TimeoutExpired as exc:
        report["process"]["timed_out"] = True
        report["error"] = str(exc)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        report["error"] = str(exc)
    atomic_write(output / "report.json", (json.dumps(report, indent=2) + "\n").encode())
    return int(report["outcome"] == "failed"), {"outcome": report["outcome"],
            "report": str(output / "report.json"), "artifacts": report.get("artifacts"), "error": report.get("error")}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bank", default="rnc.unclassified.0001")
    parser.add_argument("--columns", type=int, default=32)
    parser.add_argument("--preset", choices=PRESETS, default="debug")
    args = parser.parse_args(argv)
    code, report = run_atlas(args.bank, args.columns, args.preset)
    print(json.dumps(report, indent=2))
    return code
