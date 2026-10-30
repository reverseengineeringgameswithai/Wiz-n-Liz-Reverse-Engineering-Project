"""Keep the user's name, handles and home path out of everything agents commit.

Blocked terms are the multi-valued local setting `mirror.forbid` (untracked
`.git/config`, so the list itself is never committed) plus the absolute home
directory path. Matching is case-insensitive and also inside longer words.
`check-hygiene` runs this over the index; the installed pre-commit and
commit-msg hooks refuse such a commit before it is made. Messages never echo
a term. See vault note `02_Workflow/PUBLIC_MIRROR`.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def forbidden(root: Path) -> list[str]:
    result = subprocess.run(["git", "-C", str(root), "config", "--get-all", "mirror.forbid"],
                            capture_output=True, text=True)
    return [term for term in map(str.strip, result.stdout.split("\n")) if term]


def blocked(root: Path, home: Path) -> list[str]:
    return [*forbidden(root), str(home)]


def found(data: bytes, terms: list[str]) -> bool:
    lowered = data.lower()
    return any(term.lower().encode() in lowered for term in terms)


def scan_index(root: Path, home: Path = Path.home()) -> list[str]:
    """Indexed paths whose name or staged content contains a blocked term."""
    terms = blocked(root, home)
    names = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True,
                           check=True).stdout.decode().split("\0")
    hits = {name for name in names if name and found(name.encode(), terms)}
    patterns = [arg for term in terms for arg in ("-e", term)]
    grep = subprocess.run(["git", "-C", str(root), "grep", "--cached", "-a", "-l", "-z", "-i", "-F", *patterns],
                          capture_output=True)
    if grep.returncode > 1:
        raise subprocess.CalledProcessError(grep.returncode, grep.args, grep.stdout, grep.stderr)
    hits.update(name for name in grep.stdout.decode().split("\0") if name)
    return sorted(hits)


def message_clean(text: str, root: Path, home: Path = Path.home()) -> bool:
    body = "\n".join(line for line in text.splitlines() if not line.startswith("#"))
    return not found(body.encode(), blocked(root, home))


def install(root: Path = ROOT) -> list[Path]:
    tool = f"python3 -B {shlex.quote(str(Path(__file__).resolve()))} --root \"$(git rev-parse --show-toplevel)\""
    hooks = []
    for name, mode in (("pre-commit", "--pre-commit"), ("commit-msg", '--commit-msg "$1"')):
        hook = Path(subprocess.run(["git", "-C", str(root), "rev-parse", "--git-path", f"hooks/{name}"],
                                   capture_output=True, text=True, check=True).stdout.strip())
        hook = hook if hook.is_absolute() else root / hook
        hook.parent.mkdir(parents=True, exist_ok=True)
        hook.write_text(f"#!/bin/sh\n# Installed by tools/identity_guard.py --install.\nexec {tool} {mode}\n")
        hook.chmod(0o755)
        hooks.append(hook)
    return hooks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT, help="repository to guard (default: this one)")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--install", action="store_true", help="install the pre-commit and commit-msg hooks")
    mode.add_argument("--check", action="store_true", help="list indexed files that contain a blocked term")
    mode.add_argument("--pre-commit", action="store_true", help=argparse.SUPPRESS)
    mode.add_argument("--commit-msg", type=Path, help=argparse.SUPPRESS)
    options = parser.parse_args()
    try:
        if options.install:
            for hook in install(options.root):
                print(f"installed {hook}")
            return 0
        if options.commit_msg:
            if message_clean(options.commit_msg.read_text(encoding="utf-8", errors="replace"), options.root):
                return 0
            print("identity guard: refused: the commit message contains a blocked identity term", file=sys.stderr)
            return 1
        hits = scan_index(options.root)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"identity guard: {exc}", file=sys.stderr)
        return 1
    for name in hits:
        print(f"identity guard: blocked identity term in {name}", file=sys.stderr)
    if options.check and not hits:
        print("identity guard: no blocked identity terms in the index")
    return int(bool(hits))


if __name__ == "__main__":
    raise SystemExit(main())
