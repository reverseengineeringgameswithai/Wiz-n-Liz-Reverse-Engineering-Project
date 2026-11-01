"""Reclaim space in ignored `local/` by sharing the extents of identical files.

Regression reruns write byte-identical captures, traces and corpora into new
`run-*` directories. On a filesystem with extent sharing (btrfs here), the
kernel's FIDEDUPERANGE ioctl makes identical files share storage while each
keeps its own path, inode, permissions and contents; a later write to one copy
is copy-on-write and never reaches the others. The kernel locks and compares
both ranges before sharing, so differing data is never merged. Nothing is
deleted. Without `--apply` the tool only reports. See vault note
`02_Workflow/REPRODUCIBILITY` (local storage).
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import fcntl
import hashlib
import json
import os
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
MIN_BYTES = 4096
CHUNK = 16 << 20
FIDEDUPERANGE = 0xC0189436
FS_IOC_FIEMAP = 0xC020660B
FIEMAP_EXTENT_LAST = 0x1
FIEMAP_UNSHAREABLE = 0x2 | 0x4 | 0x100 | 0x200  # unknown, delalloc, not aligned, inline
FIEMAP_BATCH = 512


def file_digest(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def find_duplicates(root: Path, min_bytes: int = MIN_BYTES) -> list[dict]:
    """Group regular files (no symlinks, one path per inode) by size, then SHA-256."""
    by_size: dict[int, dict[tuple[int, int], str]] = defaultdict(dict)
    for directory, _, names in os.walk(root):
        for name in names:
            path = os.path.join(directory, name)
            info = os.lstat(path)
            if not os.path.isfile(path) or os.path.islink(path) or info.st_size < min_bytes:
                continue
            by_size[info.st_size].setdefault((info.st_dev, info.st_ino), path)
    groups = []
    for size, inodes in by_size.items():
        if len(inodes) < 2:
            continue
        by_digest: dict[str, list[str]] = defaultdict(list)
        for path in inodes.values():
            by_digest[file_digest(path)].append(path)
        for digest, paths in by_digest.items():
            if len(paths) > 1:
                groups.append({"size": size, "sha256": digest, "paths": sorted(paths)})
    return sorted(groups, key=lambda group: group["paths"][0])


def extent_map(fd: int) -> tuple | None:
    """Physical extents of an open file, or None when they cannot be compared."""
    extents, start = [], 0
    while True:
        request = bytearray(struct.pack("=QQIIII", start, 2**64 - 1 - start, 0, 0, FIEMAP_BATCH, 0))
        request += bytes(56 * FIEMAP_BATCH)
        try:
            fcntl.ioctl(fd, FS_IOC_FIEMAP, request)
        except OSError:
            return None
        mapped = struct.unpack_from("=I", request, 20)[0]
        if mapped == 0:
            return tuple(extents)
        for index in range(mapped):
            logical, physical, length = struct.unpack_from("=QQQ", request, 32 + 56 * index)
            flags = struct.unpack_from("=I", request, 32 + 56 * index + 40)[0]
            if flags & FIEMAP_UNSHAREABLE or physical == 0:
                return None
            extents.append((logical, physical, length))
            if flags & FIEMAP_EXTENT_LAST:
                return tuple(extents)
        start = logical + length


def share(src_fd: int, dst_fd: int, size: int) -> str | None:
    """Share dst's data with src's; return an error description or None."""
    done = 0
    while done < size:
        length = min(CHUNK, size - done)
        request = bytearray(struct.pack("=QQHHI", done, length, 1, 0, 0) + struct.pack("=qQQiI", dst_fd, done, 0, 0, 0))
        try:
            fcntl.ioctl(src_fd, FIDEDUPERANGE, request)
        except OSError as error:
            return f"{os.strerror(error.errno)} at offset {done}"
        deduped, status = struct.unpack_from("=Qi", request, 24 + 16)
        if status == 1:
            return f"contents differ at offset {done}"
        if status < 0:
            return f"{os.strerror(-status)} at offset {done}"
        if deduped == 0:
            return f"no bytes shared at offset {done}"
        done += deduped
    return None


def process(groups: list[dict], apply: bool) -> dict:
    summary = {"duplicate_groups": len(groups), "duplicate_bytes": 0, "already_shared_bytes": 0,
               "reclaimable_bytes": 0, "shared_bytes": 0, "mtimes_restored": 0, "failures": []}
    for group in groups:
        size, paths = group["size"], group["paths"]
        before = {path: os.stat(path) for path in paths}
        summary["duplicate_bytes"] += size * (len(paths) - 1)
        if any(info.st_size != size for info in before.values()):
            summary["failures"].append({"path": paths[0], "error": "size changed since scan"})
            continue
        src_fd = os.open(paths[0], os.O_RDONLY)
        try:
            src_map = extent_map(src_fd)
            for path in paths[1:]:
                dst_fd = os.open(path, os.O_RDONLY)  # Owners may share without write access.
                try:
                    if src_map is not None and extent_map(dst_fd) == src_map:
                        summary["already_shared_bytes"] += size
                        continue
                    summary["reclaimable_bytes"] += size
                    if not apply:
                        continue
                    error = share(src_fd, dst_fd, size)
                finally:
                    os.close(dst_fd)
                if error:
                    summary["failures"].append({"path": path, "error": error})
                else:
                    summary["shared_bytes"] += size
        finally:
            os.close(src_fd)
        for path, info in before.items():
            if os.stat(path).st_mtime_ns != info.st_mtime_ns:
                os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns))
                summary["mtimes_restored"] += 1
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", nargs="?", type=Path, default=ROOT / "local", help="directory to scan (default: local/)")
    parser.add_argument("--apply", action="store_true", help="share extents; without it, only report")
    parser.add_argument("--min-bytes", type=int, default=MIN_BYTES, help="skip smaller files")
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"not a directory: {args.root}")
    groups = find_duplicates(args.root, args.min_bytes)
    summary = {"root": str(args.root), "applied": args.apply, **process(groups, args.apply)}
    print(json.dumps(summary, indent=2))
    return 1 if summary["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
