"""Check Git boundaries, protected ignore rules and actual indexed file paths."""

from pathlib import Path
import hashlib
import json
import subprocess

from identity_guard import scan_index

ROOT = Path(__file__).resolve().parents[1]
PROTECTED = ("Original_Game/", "local/", "build/", "dist/", ".venv/",
             "vault/.obsidian/plugins/", "vault/.obsidian/cache/", "vault/.trash/")


def check_hygiene(root: Path = ROOT) -> dict:
    def git(*args):
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True).stdout

    errors = []
    actual = Path(git("rev-parse", "--show-toplevel").decode().strip()).resolve()
    if actual != root.resolve():
        errors.append(f"wrong repository root: {actual}")
    indexed = [p.decode() for p in git("ls-files", "-z").split(b"\0") if p]
    digest = json.loads((root / "re/rom_manifest.json").read_text())["original"]["sha256"]
    for name in indexed:
        if name.startswith(PROTECTED) or name.startswith("vault/.obsidian/workspace") or "__pycache__/" in name:
            errors.append(f"protected/generated path is tracked: {name}")
        # Inspect the index version, not just the working copy: staged content matters.
        content = git("show", f":{name}")
        if hashlib.sha256(content).hexdigest() == digest:
            errors.append(f"original ROM bytes tracked under {name}")
        if len(content) > 2 * 1024 * 1024:
            errors.append(f"large indexed file requires explicit hygiene review: {name}")
    for name in ("Original_Game/Wiz 'N' Liz (USA).md", "local/generated/test.bin", "build/test",
                 "dist/test", "vault/.obsidian/workspace.json", "vault/.obsidian/plugins/test"):
        result = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", "--no-index", name])
        if result.returncode != 0:
            errors.append(f"protective ignore missing: {name}")
    for name in ("START_HERE.md", "vault/00_START_HERE.md", "tools/project.py"):
        result = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", "--no-index", name])
        if result.returncode != 1:
            errors.append(f"source unexpectedly ignored or ignore check failed: {name}")
    for name in scan_index(root):
        errors.append(f"blocked identity term (the user's name, a handle or the home path) in {name}")
    return {"indexed_files_checked": len(indexed), "ok": not errors, "errors": errors}
