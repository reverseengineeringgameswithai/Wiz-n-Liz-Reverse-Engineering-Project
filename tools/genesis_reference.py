"""Thin research client for the independent BizHawk Genesis routine comparator."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from rom import ROOT, inspect_file, verify_expected


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--bizhawk-root", type=Path, default=ROOT.parent / "BizHawkOpenSource")
    parser.add_argument("--preset", choices=("debug", "release", "sanitize"), default="debug")
    args = parser.parse_args(argv)
    try:
        script = args.bizhawk_root.resolve() / "Tools/GenesisDebug/wiz/compare.py"
        if not script.is_file():
            raise ValueError("BizHawk Genesis comparator unavailable: " + str(script))
        verify_expected(inspect_file())
        process = subprocess.run([sys.executable, "-B", str(script), str(args.fixture.resolve()), "--wiznliz-root", str(ROOT), "--preset", args.preset],
                                 capture_output=True, text=True, timeout=90)
        result = json.loads(process.stdout)
        if not isinstance(result, dict) or type(result.get("ok")) is not bool or process.returncode != (0 if result["ok"] else 1):
            raise ValueError("Genesis comparator returned an inconsistent result")
        result["consumer_script_sha256"] = hashlib.sha256(script.read_bytes()).hexdigest()
        verify_expected(inspect_file())
        result["rom_unchanged"] = True
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        result = {"schema_version": 1, "ok": False, "error": {"code": "genesis_comparison_failed", "message": str(error)}}
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
