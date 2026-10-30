"""Load cataloged native scene resources and generate a checked local map plane."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

from bank_atlas import catalog_entry, read_extracted, unpack_pam, png_from_rgba, MAX_BANK_BYTES
from native_build import PRESETS, verify_executable
from rnc import RncError, approved_directory, atomic_write
from rom import ROOT
from scene_probe import inspect_scene
from scene_reference import check_scene_image

MAX_SCENE_BYTES = 2 + 65536 * 4 + 10 + 65536 * 40 + 4 + 8192


def validate_metadata(metadata, scene_entry, base_entry, width, height):
    expected = {"status": "ok", "schema_version": 1, "renderer": "wiznliz-scene-preview",
                "logical_id": scene_entry["id"], "base_bank_id": base_entry["id"],
                "coordinates": scene_entry["structure"]["coordinate_count"],
                "additional_patterns": scene_entry["structure"]["additional_pattern_count"],
                "base_patterns": base_entry["structure"]["record_count"], "map_cells": 4096,
                "width": 1024, "height": 256, "single_plane": True, "palette_policy": "normal-rgb3-rounded-v1"}
    if not isinstance(metadata, dict) or (width, height) != (1024, 256):
        raise RncError("invalid scene metadata or dimensions")
    for key, value in expected.items():
        if type(metadata.get(key)) is not type(value) or metadata.get(key) != value:
            raise RncError(f"native scene metadata disagrees on {key}")


def run_preview(logical_id, preset="debug"):
    entry = catalog_entry(logical_id, "companion_scene_v1")
    base_entry = catalog_entry(entry["structure"]["base_bank_id"])
    executable = verify_executable(preset, "wiznliz-scene-preview")
    source, scene = read_extracted(entry, MAX_SCENE_BYTES)
    base_source, base = read_extracted(base_entry, MAX_BANK_BYTES)
    out = Path(tempfile.mkdtemp(prefix="run-", dir=approved_directory(ROOT, "local/generated/scene-preview")))
    report = {"schema_version": 1, "outcome": "failed", "logical_id": logical_id,
              "input_path": str(source.relative_to(ROOT)), "input_sha256": entry["decoded_sha256"],
              "base_path": str(base_source.relative_to(ROOT)), "base_sha256": base_entry["decoded_sha256"],
              "native_build": json.loads((executable.parent / "provenance.json").read_text()),
              "research_sources": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in
                   ("tools/scene_preview.py", "tools/scene_probe.py", "tools/scene_reference.py", "tools/bank_atlas.py",
                    "tools/bank_reference.py", "third_party/vdp_reference.lock.json", "re/rnc_blocks.json")},
              "rom_cpu_execution": False, "native_game_logic": False}
    try:
        atomic_write(out / "scene.bin", scene)
        atomic_write(out / "bank.bin", base)
        command = [str(executable), logical_id, str(out / "scene.bin"), base_entry["id"], str(out / "bank.bin")]
        overrides = {"ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1", "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=1"}
        report["process"] = {"command": command, "cwd": str(ROOT), "environment_overrides": overrides,
                             "exit_status": None, "timed_out": False}
        result = subprocess.run(command, cwd=ROOT, env=os.environ | overrides, capture_output=True, timeout=20, check=False)
        report["process"].update(exit_status=result.returncode, stderr=result.stderr.decode(errors="replace")[:65536])
        if result.returncode or len(result.stderr) > 65536:
            raise RncError("native scene failed; see process diagnostics")
        width, height, rgba = unpack_pam(result.stdout)
        metadata = json.loads(result.stderr)
        validate_metadata(metadata, entry, base_entry, width, height)
        report["native_metadata"] = metadata
        report["layout"] = inspect_scene(scene)
        report["pixel_check"] = check_scene_image(scene, base, rgba, width, height)
        report["rgba_sha256"] = hashlib.sha256(rgba).hexdigest()
        report["artifacts"] = {}
        for name, content in (("scene.pam", result.stdout), ("scene.png", png_from_rgba(width, height, rgba))):
            atomic_write(out / name, content)
            report["artifacts"][name] = {"path": str((out / name).relative_to(ROOT)), "size_bytes": len(content),
                                         "sha256": hashlib.sha256(content).hexdigest()}
        report["outcome"] = "scene_plane_generated"
    except subprocess.TimeoutExpired as exc:
        report["process"]["timed_out"] = True
        report["error"] = str(exc)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        report["error"] = str(exc)
    atomic_write(out / "report.json", (json.dumps(report, indent=2) + "\n").encode())
    return int(report["outcome"] == "failed"), {"outcome": report["outcome"], "report": str(out / "report.json"),
            "artifacts": report.get("artifacts"), "error": report.get("error")}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", default="scene.companion.0001")
    parser.add_argument("--preset", choices=PRESETS, default="debug")
    args = parser.parse_args(argv)
    code, report = run_preview(args.scene, args.preset)
    print(json.dumps(report, indent=2))
    return code
