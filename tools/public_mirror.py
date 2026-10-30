"""Export the committed project tree into the separate public mirror repository.

The mirror carries the reverse engineering project exactly as committed at a
revision, minus everything Git already excludes (ROM, `local/`, builds) and the
local author's identity: home-directory paths become `~` and the configured Git
name/email become placeholders. Private history is never copied. Pushing stays
a separate, explicit step; see vault note `02_Workflow/PUBLIC_MIRROR`.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 2 * 1024 * 1024


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True).stdout


def config(root: Path, key: str) -> str | None:
    result = subprocess.run(["git", "-C", str(root), "config", "--get", key], capture_output=True, text=True)
    return result.stdout.strip() or None


def identity(root: Path, home: Path) -> dict[str, str]:
    """Terms that must not reach the mirror, mapped to their placeholders."""
    terms = {}
    if email := config(root, "user.email"):
        terms[email] = "[email]"
    if name := config(root, "user.name"):
        terms[name] = "[author]"
    terms.setdefault(home.name, "[author]")
    return terms


def scrub(text: str, home: Path, terms: dict[str, str]) -> str:
    text = re.sub(re.escape(str(home)) + r"(?!\w)", "~", text)
    for term, placeholder in terms.items():
        text = re.sub(rf"(?<!\w){re.escape(term)}(?!\w)", placeholder, text, flags=re.IGNORECASE)
    return text


def leaks(data: bytes, terms: dict[str, str]) -> list[str]:
    lowered = data.lower()
    return [term for term in terms if term.lower().encode() in lowered]


def export(dest: Path, revision: str = "HEAD", root: Path = ROOT, home: Path = Path.home()) -> dict:
    dest = dest.resolve()
    if dest == root.resolve() or not (dest / ".git").is_dir():
        raise ValueError(f"destination must be a separate, initialized Git repository: {dest}")
    if Path(git(dest, "rev-parse", "--show-toplevel").decode().strip()).resolve() != dest:
        raise ValueError(f"destination is not a repository root: {dest}")
    terms = identity(root, home)
    rom_digest = json.loads(git(root, "show", f"{revision}:re/rom_manifest.json"))["original"]["sha256"]
    archive = tarfile.open(fileobj=io.BytesIO(git(root, "archive", "--format=tar", revision)))
    files = {}
    for member in archive.getmembers():
        if member.isdir():
            continue
        if not member.isfile():
            raise ValueError(f"unsupported tracked entry: {member.name}")
        data = archive.extractfile(member).read()
        try:
            data = scrub(data.decode("utf-8"), home, terms).encode("utf-8")
        except UnicodeDecodeError:
            pass
        files[member.name] = data

    errors = []
    for name, data in files.items():
        if found := leaks(name.encode() + b"\0" + data, terms):
            errors.append(f"{name}: identity remains ({len(found)} term(s))")
        if hashlib.sha256(data).hexdigest() == rom_digest:
            errors.append(f"{name}: original ROM bytes")
        if len(data) > MAX_BYTES:
            errors.append(f"{name}: larger than {MAX_BYTES} bytes")
    if errors:
        raise ValueError("export refused:\n" + "\n".join(errors))

    removed = []
    for path in sorted(dest.rglob("*"), reverse=True):
        rel = path.relative_to(dest)
        if rel.parts[0] == ".git":
            continue
        if path.is_file() or path.is_symlink():
            if rel.as_posix() not in files:
                path.unlink()
                removed.append(rel.as_posix())
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    changed = 0
    for name, data in files.items():
        target = dest / name
        if target.is_file() and target.read_bytes() == data:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        changed += 1
    return {"revision": git(root, "rev-parse", revision).decode().strip(), "files": len(files),
            "written": changed, "removed": removed}


def commit(dest: Path, message: str, root: Path = ROOT, home: Path = Path.home()) -> str | None:
    """Commit the mirror's whole tree, which this tool alone produces."""
    terms = identity(root, home)
    author = f"{config(dest, 'user.name')} <{config(dest, 'user.email')}>"
    if None in (config(dest, "user.name"), config(dest, "user.email")) or leaks(author.encode(), terms):
        raise ValueError("configure a separate mirror identity in the destination repository first")
    if leaks(message.encode(), terms):
        raise ValueError("commit message contains the local identity")
    git(dest, "add", "--all")
    if not git(dest, "status", "--porcelain"):
        return None
    git(dest, "commit", "-q", "-m", message)
    return git(dest, "rev-parse", "HEAD").decode().strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dest", type=Path, help="the mirror repository's working tree")
    parser.add_argument("--revision", default="HEAD", help="committed revision to export (default HEAD)")
    parser.add_argument("--commit", metavar="MESSAGE", help="commit the exported tree in the mirror")
    options = parser.parse_args()
    try:
        report = export(options.dest, options.revision)
        if options.commit:
            report["mirror_commit"] = commit(options.dest, options.commit)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"public-mirror: {exc}")
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
