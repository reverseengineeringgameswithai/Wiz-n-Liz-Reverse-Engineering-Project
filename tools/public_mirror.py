"""Export the committed project tree into the separate public mirror repository.

The mirror carries the reverse engineering project exactly as committed at a
revision, minus everything Git already excludes (ROM, `local/`, builds) and the
local author's identity: home-directory paths become `~` and the configured Git
name/email become placeholders. Private history is never copied. Pushing is a
separate step after each checkpoint; see vault note `02_Workflow/PUBLIC_MIRROR`.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 2 * 1024 * 1024


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True).stdout


def config(root: Path, key: str) -> str | None:
    result = subprocess.run(["git", "-C", str(root), "config", "--get", key], capture_output=True, text=True)
    return result.stdout.strip() or None


def identity(root: Path, home: Path) -> dict[str, str]:
    """Terms that must not reach the mirror, mapped to their placeholders.

    Besides the configured Git identity and home directory name, the multi-valued
    local setting `mirror.forbid` lists further names and handles. It lives only
    in this repository's untracked `.git/config`, so the list never publishes.
    """
    terms = {}
    if email := config(root, "user.email"):
        terms[email] = "[email]"
    if name := config(root, "user.name"):
        terms[name] = "[author]"
    terms.setdefault(home.name, "[author]")
    forbidden = subprocess.run(["git", "-C", str(root), "config", "--get-all", "mirror.forbid"],
                               capture_output=True, text=True).stdout.split("\n")
    for term in filter(None, map(str.strip, forbidden)):
        terms.setdefault(term, "[redacted]")
    return terms


def scrub(text: str, home: Path, terms: dict[str, str]) -> str:
    text = re.sub(re.escape(str(home)) + r"(?!\w)", "~", text)
    for term, placeholder in sorted(terms.items(), key=lambda item: -len(item[0])):  # Whole email before its name part.
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


def published(repo: Path, revision: str) -> bytes:
    """Everything a commit publishes: raw metadata, every path and every blob."""
    entries = [e for e in git(repo, "ls-tree", "-r", "-z", "--full-tree", revision).split(b"\0") if e]
    blobs = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch"], capture_output=True, check=True,
                           input=b"".join(e.split(b"\t", 1)[0].split()[2] + b"\n" for e in entries)).stdout
    return git(repo, "cat-file", "-p", revision) + b"\0".join(e.split(b"\t", 1)[1] for e in entries) + blobs


def check_push(dest: Path, updates: list[str], root: Path = ROOT, home: Path = Path.home()) -> list[str]:
    """Refuse any pushed ref whose new commits carry an identity term anywhere."""
    terms = identity(root, home)
    errors = []
    for update in filter(None, updates):
        local_ref, local_sha, remote_ref, _ = update.split()
        if set(local_sha) == {"0"}:
            continue
        if leaks(f"{local_ref} {remote_ref}".encode() + git(dest, "cat-file", "-p", local_sha), terms):
            errors.append(f"{remote_ref}: identity in the ref or its object")
        for revision in git(dest, "rev-list", local_sha, "--not", "--remotes").decode().split():
            if leaks(published(dest, revision), terms):
                errors.append(f"{remote_ref}: identity in commit {revision[:12]}")
    return errors


def credential(dest: Path, account: str, action: str, request: str,
               root: Path = ROOT, home: Path = Path.home()) -> str:
    """Git credential helper that releases the account's token only for a clean mirror.

    `git push --no-verify` skips the pre-push hook, but an HTTPS push still needs
    credentials: every unpublished commit and every ref name is scanned first.
    Answering `quit=1` makes Git fail at once instead of prompting.
    """
    if action != "get":
        return ""
    terms = identity(root, home)
    refs = git(dest, "for-each-ref", "--format=%(refname)")
    pending = git(dest, "rev-list", "--all", "--not", "--remotes").decode().split()
    if leaks(refs, terms) or any(leaks(published(dest, revision), terms) for revision in pending):
        print("public-mirror credential: refused: unpublished commits or refs carry an identity term",
              file=sys.stderr)
        return "quit=1\n"
    gh = shutil.which("gh") or str(home / ".local/bin/gh")
    token = subprocess.run([gh, "auth", "token", "--user", account], capture_output=True, text=True,
                           check=True).stdout.strip()
    return subprocess.run([gh, "auth", "git-credential", "get"], input=request, capture_output=True, text=True,
                          check=True, env={**os.environ, "GH_TOKEN": token}).stdout


def install_guards(dest: Path, account: str, root: Path = ROOT) -> Path:
    """Install the mirror's pre-push hook and its credential gate for `account`."""
    tool = f"python3 -B {shlex.quote(str(Path(__file__).resolve()))} --source {shlex.quote(str(root))}"
    hook = Path(git(dest, "rev-parse", "--git-path", "hooks/pre-push").decode().strip())
    hook = hook if hook.is_absolute() else dest / hook
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\n# Installed by tools/public_mirror.py --install-guards.\n"
                    f'exec {tool} --pre-push "$(git rev-parse --show-toplevel)"\n')
    hook.chmod(0o755)
    key = "credential.https://github.com.helper"
    git(dest, "config", "--local", "--replace-all", key, "")  # Drop global helpers for the mirror only.
    git(dest, "config", "--local", "--add", key,
        f"!{tool} --credential {shlex.quote(account)} {shlex.quote(str(dest.resolve()))}")
    return hook


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dest", type=Path, help="the mirror repository's working tree")
    parser.add_argument("--revision", default="HEAD", help="committed revision to export (default HEAD)")
    parser.add_argument("--commit", metavar="MESSAGE", help="commit the exported tree in the mirror")
    parser.add_argument("--source", type=Path, default=ROOT, help=argparse.SUPPRESS)
    parser.add_argument("action", nargs="?", help=argparse.SUPPRESS)  # Appended by Git to credential helpers.
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--install-guards", metavar="ACCOUNT",
                      help="install the pre-push identity check and credential gate for ACCOUNT")
    mode.add_argument("--pre-push", action="store_true", help="pre-push hook mode: check refs read from stdin")
    mode.add_argument("--credential", metavar="ACCOUNT", help=argparse.SUPPRESS)
    options = parser.parse_args()
    try:
        if options.pre_push:
            errors = check_push(options.dest, sys.stdin.read().splitlines(), options.source)
            for error in errors:
                print(f"public-mirror pre-push: refused: {error}", file=sys.stderr)
            return int(bool(errors))
        if options.credential:
            try:
                answer = credential(options.dest, options.credential, options.action or "",
                                    sys.stdin.read(), options.source)
            except (OSError, ValueError, subprocess.CalledProcessError) as exc:  # Fail closed, never prompt.
                print(f"public-mirror credential: {exc}", file=sys.stderr)
                answer = "quit=1\n"
            sys.stdout.write(answer)
            return 0
        if options.install_guards:
            print(f"installed {install_guards(options.dest, options.install_guards, options.source)}")
            return 0
        report = export(options.dest, options.revision, options.source)
        if options.commit:
            report["mirror_commit"] = commit(options.dest, options.commit, options.source)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"public-mirror: {exc}")
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
