"""Compare the native RNC2 codec with the pinned research process, not gameplay."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile

from rom import ROOT, DEFAULT_ROM, inspect_file, verify_expected
from rnc import approved_directory, atomic_write, parse_block, validate_decoded
from rnc_validate import invoke_decoder, validate_native_metadata, validate_reference_metadata
from native_build import verify_executable as native_executable, PRESETS
from build_rnc_reference import verify_executable as reference_executable


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=PRESETS, default="debug")
    parser.add_argument("--rom", action="store_true", help="Also compare every cataloged ROM block")
    args = parser.parse_args(argv)
    native = native_executable(args.preset)
    reference = reference_executable()
    sys.path.insert(0, str(ROOT / "tests"))
    from rnc2_cases import valid_cases
    cases = valid_cases()
    directory = Path(tempfile.mkdtemp(prefix="run-", dir=approved_directory(ROOT, "local/generated/rnc-comparison")))
    report = {"schema_version": 1, "scope": "RNC2 codec only; no gameplay or CPU execution",
              "native_executable_sha256": hashlib.sha256(native.read_bytes()).hexdigest(),
              "native_build": json.loads((native.parent / "provenance.json").read_text()),
              "reference_executable_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
              "reference_lock": "third_party/rnc_reference.lock.json", "cases": [], "ok": False}
    try:
        expected_rom_hashes = {}
        if args.rom:
            identity = inspect_file()
            verify_expected(identity)
            data = DEFAULT_ROM.read_bytes()
            if hashlib.sha256(data).hexdigest() != identity["sha256"]:
                raise ValueError("ROM changed before comparison")
            report["rom_identity"] = {k: identity[k] for k in ("size_bytes", "sha256")}
            for entry in json.loads((ROOT / "re/rnc_blocks.json").read_text())["blocks"]:
                packed = data[entry["file_offset"]:entry["end_exclusive"]]
                if hashlib.sha256(packed).hexdigest() != entry["block_sha256"]:
                    raise ValueError("ROM block digest differs from catalog")
                if entry["id"] in cases:
                    raise ValueError("duplicate comparison case ID")
                cases[entry["id"]] = packed, None
                expected_rom_hashes[entry["id"]] = entry["decoded_sha256"]
        for name, (packed, expected) in cases.items():
            if not re.fullmatch(r"[a-z0-9]+(?:[._-][a-z0-9]+)*", name):
                raise ValueError("invalid comparison case logical ID")
            source = directory / f"{name}.rnc"
            atomic_write(source, packed)
            header, _ = parse_block(packed)
            item = {"id": name, "input_sha256": hashlib.sha256(packed).hexdigest()}
            report["cases"].append(item)
            outputs = []
            for backend, executable, validator in (
                ("native", native, validate_native_metadata),
                ("reference", reference, validate_reference_metadata),
            ):
                decoded, process = invoke_decoder(executable, source)
                item[backend] = process
                if process["exit_status"] != 0 or process["timed_out"] or process["stderr_truncated"]:
                    raise ValueError(f"{name}: {backend} process failed")
                validator(json.loads(process["stderr"]), header, len(packed))
                validate_decoded(header, decoded)
                outputs.append(decoded)
            if outputs[0] != outputs[1] or (expected is not None and outputs[0] != expected):
                raise ValueError(f"{name}: byte-for-byte disagreement")
            digest = hashlib.sha256(outputs[0]).hexdigest()
            if expected is None and digest != expected_rom_hashes[name]:
                raise ValueError(f"{name}: digest differs from prior reference result")
            item.update(ok=True, output_sha256=digest, output_bytes=len(outputs[0]))
        report["ok"] = True
    except (OSError, ValueError, KeyError) as exc:
        report["error"] = str(exc)
    finally:
        if args.rom:
            try:
                verify_expected(inspect_file())
                report["rom_unchanged"] = True
            except (OSError, ValueError) as exc:
                report.update(ok=False, rom_unchanged=False, identity_error=str(exc))
        atomic_write(directory / "report.json", (json.dumps(report, indent=2) + "\n").encode())
    print(json.dumps({"ok": report["ok"], "cases_passed": sum(item.get("ok", False) for item in report["cases"]),
                      "report": str(directory / "report.json"), "error": report.get("error")}, indent=2))
    return int(not report["ok"])
