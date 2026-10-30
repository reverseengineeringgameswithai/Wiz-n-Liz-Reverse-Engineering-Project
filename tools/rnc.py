"""Bounded RNC2 header/CRC validation, independent of the selected decoder.

CRC parameters: width 16, reflected polynomial 0xA001, initial value 0,
no final xor. Implementation is direct bitwise arithmetic, not imported code.
Header observations do not establish the decoded resource's gameplay role.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
import struct
import tempfile

HEADER = struct.Struct(">3sBIIHHBB")
MAX_PACKED_BYTES = 4 * 1024 * 1024
MAX_UNPACKED_BYTES = 4 * 1024 * 1024


class RncError(ValueError):
    """Malformed, unsupported or integrity-invalid RNC data."""


def crc16(data: bytes) -> int:
    crc = 0
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = (crc >> 1) ^ (0xA001 if crc & 1 else 0)
    return crc


@dataclass(frozen=True)
class RncHeader:
    file_offset: int
    method: int
    unpacked_size: int
    packed_size: int
    unpacked_crc16: int
    packed_crc16: int
    leeway_field: int
    chunks_field: int

    @property
    def payload_start(self) -> int:
        return self.file_offset + HEADER.size

    @property
    def end_exclusive(self) -> int:
        return self.payload_start + self.packed_size


def parse_block(data: bytes, offset: int = 0) -> tuple[RncHeader, bytes]:
    """Lengths are checked before slicing; no allocation uses untrusted sizes."""
    if type(offset) is not int or not 0 <= offset <= len(data) - HEADER.size:
        raise RncError("invalid offset or truncated 18-byte RNC header")
    magic, method, unpacked, packed, out_crc, in_crc, leeway, chunks = HEADER.unpack_from(data, offset)
    if magic != b"RNC" or method != 2:
        raise RncError("only RNC method 2 is supported by this validation path")
    if not 2 <= packed <= MAX_PACKED_BYTES:
        raise RncError(f"packed size outside supported [2, {MAX_PACKED_BYTES}] bytes")
    if unpacked > MAX_UNPACKED_BYTES:
        raise RncError(f"unpacked size exceeds {MAX_UNPACKED_BYTES}-byte safety limit")
    header = RncHeader(offset, method, unpacked, packed, out_crc, in_crc, leeway, chunks)
    if header.end_exclusive > len(data):
        raise RncError("declared packed extent exceeds available input")
    return header, data[header.payload_start:header.end_exclusive]


def inspect_block(data: bytes, offset: int = 0) -> dict:
    header, payload = parse_block(data, offset)
    actual_crc = crc16(payload)
    if actual_crc != header.packed_crc16:
        raise RncError(f"packed CRC mismatch: calculated {actual_crc:#06x}, header {header.packed_crc16:#06x}")
    block = data[offset:header.end_exclusive]
    return {
        "schema_version": 1,
        "status": "packed_crc_verified",
        "header": asdict(header),
        "payload_start": header.payload_start,
        "end_exclusive": header.end_exclusive,
        "block_size_bytes": len(block),
        "block_sha256": hashlib.sha256(block).hexdigest(),
        "packed_sha256": hashlib.sha256(payload).hexdigest(),
        "packed_crc16_calculated": actual_crc,
        "packed_crc_matches": True,
        "decoded": None,
        "resource_role": None,
    }


def validate_decoded(header: RncHeader, decoded: bytes) -> dict:
    if len(decoded) != header.unpacked_size:
        raise RncError(f"decoded size {len(decoded)} differs from declared {header.unpacked_size}")
    actual_crc = crc16(decoded)
    if actual_crc != header.unpacked_crc16:
        raise RncError(f"unpacked CRC mismatch: calculated {actual_crc:#06x}, header {header.unpacked_crc16:#06x}")
    return {"size_bytes": len(decoded), "sha256": hashlib.sha256(decoded).hexdigest(),
            "crc16_calculated": actual_crc, "unpacked_crc_matches": True}


def approved_directory(root: Path, relative: str) -> Path:
    """Only known local subtrees, with no symlinked ancestor redirection."""
    root = root.resolve()
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts or relative_path.parts[:1] != ("local",):
        raise RncError("output must stay under repository local/")
    path = root / relative_path
    if path.resolve() != path:
        raise RncError("output directory contains a symlink")
    path.mkdir(parents=True, exist_ok=True)
    return path


def atomic_write(path: Path, content: bytes) -> None:
    """Replace the destination entry, without following existing file symlinks."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".rnc-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
