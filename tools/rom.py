"""Bounded, read-only inspection of a linear big-endian Genesis ROM image.

Header ranges follow the Sega header layout. No normalization is implicit.
Header-declared sizes never drive reads or allocations.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROM = ROOT / "Original_Game" / "Wiz 'N' Liz (USA).md"
MAX_ROM_SIZE = 32 * 1024 * 1024
MIN_ROM_SIZE = 0x200


class RomError(ValueError):
    """Unsupported, malformed, changed or unexpectedly identified input."""


def _text(data: bytes) -> str:
    return data.decode("ascii", errors="backslashreplace").rstrip(" ")


def inspect_bytes(data: bytes) -> dict:
    """Return observations; never infer semantic identity from a title/checksum."""
    size = len(data)
    if size < MIN_ROM_SIZE:
        raise RomError(f"truncated input: {size} bytes; need at least 512")
    if size > MAX_ROM_SIZE:
        raise RomError(f"input exceeds inspection limit of {MAX_ROM_SIZE} bytes")
    if data[0x100:0x104] != b"SEGA":
        if data[0x100:0x104] == b"ESAG":
            raise RomError("probable pair-byte-swapped image; normalization is not implemented")
        if data[0x300:0x304] == b"SEGA":
            raise RomError("probable 512-byte-prefixed image; normalization is not implemented")
        raise RomError("unsupported image: no linear SEGA signature at file offset 0x100")
    if size % 2:
        raise RomError("malformed image: odd byte length prevents word checksum")

    word = lambda offset: struct.unpack_from(">H", data, offset)[0]
    longword = lambda offset: struct.unpack_from(">I", data, offset)[0]
    stored_checksum = word(0x18E)
    calculated = sum(value[0] for value in struct.iter_unpack(">H", memoryview(data)[0x200:])) & 0xFFFF
    rom_start, rom_end = longword(0x1A0), longword(0x1A4)
    ram_start, ram_end = longword(0x1A8), longword(0x1AC)
    vectors = []
    for index in range(64):
        raw = longword(index * 4)
        bus = raw & 0xFFFFFF
        vectors.append({
            "index": index,
            "file_offset": index * 4,
            "raw_u32": raw,
            "low24": bus,
            "even_low24": bus % 2 == 0,
            "low24_in_file": bus < size,
        })
    warnings = []
    if rom_start != 0 or rom_end + 1 != size:
        warnings.append("header ROM range does not equal [0, actual file size)")
    if rom_end < rom_start:
        warnings.append("header ROM range is reversed")
    if ram_end < ram_start:
        warnings.append("header RAM range is reversed")
    if calculated != stored_checksum:
        warnings.append("stored checksum differs from word sum over [0x200, EOF)")
    reset = vectors[1]
    if not reset["low24_in_file"] or not reset["even_low24"]:
        warnings.append("reset vector low 24 bits do not identify an even offset inside this image")
    return {
        "schema_version": 1,
        "size_bytes": size,
        "sha256": hashlib.sha256(data).hexdigest(),
        "encoding": "linear_big_endian",
        "normalization": None,
        "header": {
            "console": _text(data[0x100:0x110]),
            "copyright": _text(data[0x110:0x120]),
            "domestic_title": _text(data[0x120:0x150]),
            "overseas_title": _text(data[0x150:0x180]),
            "product_code": _text(data[0x180:0x18E]),
            "supported_io": _text(data[0x190:0x1A0]),
            "rom_start_inclusive": rom_start,
            "rom_end_inclusive": rom_end,
            "ram_start_inclusive": ram_start,
            "ram_end_inclusive": ram_end,
            "extra_memory_hex": data[0x1B0:0x1BC].hex(),
            "modem_hex": data[0x1BC:0x1C8].hex(),
            "memo": _text(data[0x1C8:0x1F0]),
            "region_text": _text(data[0x1F0:0x200]),
        },
        "checksum": {
            "algorithm": "sum big-endian u16 over file [0x200, EOF), modulo 65536",
            "stored": stored_checksum,
            "calculated": calculated,
            "matches": stored_checksum == calculated,
        },
        "vectors": vectors,
        "warnings": warnings,
    }


def inspect_file(path: Path | str = DEFAULT_ROM) -> dict:
    """Read with a fixed bound, and detect size/stat changes during inspection."""
    path = Path(path)
    before = path.stat()
    if not MIN_ROM_SIZE <= before.st_size <= MAX_ROM_SIZE:
        raise RomError(f"file size {before.st_size} outside [{MIN_ROM_SIZE}, {MAX_ROM_SIZE}]")
    with path.open("rb") as stream:
        data = stream.read(MAX_ROM_SIZE + 1)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (
        after.st_size, after.st_mtime_ns, after.st_ino
    ) or len(data) != before.st_size:
        raise RomError("input changed during read")
    return inspect_bytes(data)


def verify_expected(report: dict, manifest_path: Path = ROOT / "re/rom_manifest.json") -> None:
    expected = json.loads(manifest_path.read_text(encoding="utf-8"))["original"]
    for field in ("size_bytes", "sha256"):
        if report[field] != expected[field]:
            raise RomError(f"unsupported ROM: {field} differs from re/rom_manifest.json")
