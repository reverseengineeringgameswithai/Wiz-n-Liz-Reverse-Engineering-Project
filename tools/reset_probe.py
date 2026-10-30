"""Bounded static evidence for FIND-0001, never an execution engine.

The handful of instruction-field readers below reject other encodings. They
support independently checked table boundaries, not arbitrary 68000 analysis.
Bulk decoder output is written only beneath local/generated/reset/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def word(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 2 > len(data):
        raise ValueError(f"truncated word at {offset:#x}")
    return struct.unpack_from(">H", data, offset)[0]


def signed(value: int, bits: int) -> int:
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def branch_target(data: bytes, offset: int) -> int:
    opcode = word(data, offset)
    if opcode & 0xF000 != 0x6000:
        raise ValueError(f"not a Bcc/BRA/BSR at {offset:#x}")
    displacement = opcode & 0xFF
    displacement = signed(displacement, 8) if displacement else signed(word(data, offset + 2), 16)
    # Original 68000: low byte FF means -1, never the 68020 long form.
    return (offset + 2 + displacement) & 0xFFFFFFFF


def lea_pc_target(data: bytes, offset: int) -> tuple[int, int]:
    opcode = word(data, offset)
    if opcode & 0xF1FF != 0x41FA:
        raise ValueError(f"not LEA d16(PC),An at {offset:#x}")
    return (opcode >> 9) & 7, (offset + 2 + signed(word(data, offset + 2), 16)) & 0xFFFFFFFF


def movem_postincrement(data: bytes, offset: int) -> tuple[int, int, list[str]]:
    opcode = word(data, offset)
    if opcode & 0xFFB8 != 0x4C98:
        raise ValueError(f"not MOVEM (An)+,registers at {offset:#x}")
    mask = word(data, offset + 2)
    registers = [f"{'d' if n < 8 else 'a'}{n % 8}" for n in range(16) if mask & (1 << n)]
    return opcode & 7, 4 if opcode & 0x40 else 2, registers


def moveq(data: bytes, offset: int) -> tuple[int, int]:
    opcode = word(data, offset)
    if opcode & 0xF100 != 0x7000:
        raise ValueError(f"not MOVEQ at {offset:#x}")
    return (opcode >> 9) & 7, signed(opcode & 0xFF, 8)


def dbf_target(data: bytes, offset: int) -> tuple[int, int]:
    opcode = word(data, offset)
    if opcode & 0xFFF8 != 0x51C8:
        raise ValueError(f"not DBF at {offset:#x}")
    return opcode & 7, (offset + 2 + signed(word(data, offset + 2), 16)) & 0xFFFFFFFF


def dbf_body_iterations(initial_counter: int) -> int:
    """Body-first loop with DBF, no early exit; counts the initial body visit."""
    return (initial_counter & 0xFFFF) + 1


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def analyze_reset(data: bytes) -> dict:
    require(len(data) >= 0x300, "reset fragment truncated")
    table_reg, start = lea_pc_target(data, 0x210)
    end = branch_target(data, 0x28C)
    require((table_reg, start, end) == (5, 0x28E, 0x2FA), "unsupported reset table boundaries")
    cursor = start
    seeds = {}
    groups = []
    for instruction in (0x214, 0x218):
        reg, width, registers = movem_postincrement(data, instruction)
        require(reg == table_reg, "MOVEM source differs from table register")
        group_start = cursor
        for register in registers:
            require(cursor + width <= end, "MOVEM exceeds table")
            value = int.from_bytes(data[cursor:cursor + width], "big")
            seeds[register] = (signed(value, 16) if width == 2 else value) & 0xFFFFFFFF
            cursor += width
        groups.append({"start": group_start, "end_exclusive": cursor,
                       "consumer": instruction, "role": "register_seed"})
    require(set(seeds) == {"d5", "d6", "d7", "a0", "a1", "a2", "a3", "a4"},
            "unsupported reset register set")
    for instruction, dbf, body in ((0x236, 0x23E, 0x238), (0x24E, 0x252, 0x250),
                                   (0x266, 0x26A, 0x268), (0x270, 0x274, 0x272),
                                   (0x278, 0x27E, 0x27A)):
        register, _ = moveq(data, instruction)
        require(dbf_target(data, dbf) == (register, body), "unsupported reset loop")
    require(dbf_target(data, 0x25E) == (6, 0x25C), "unsupported clear loop")
    # Consumer widths come from the reviewed instruction forms, checked here.
    for offset, opcode in ((0x238, 0x1A1D), (0x242, 0x289D), (0x250, 0x10DD),
                           (0x25C, 0x2D00), (0x262, 0x289D), (0x264, 0x289D),
                           (0x26E, 0x289D), (0x27A, 0x175D)):
        require(word(data, offset) == opcode, f"unsupported table consumer at {offset:#x}")
    require(word(data, 0x230) == 0x7000 and word(data, 0x232) == 0x2C40,
            "unsupported zero/clear-address setup")
    for consumer, count, role in (
        (0x238, dbf_body_iterations(moveq(data, 0x236)[1]), "byte_to_word_device_writes"),
        (0x242, 4, "long_device_write"),
        (0x250, dbf_body_iterations(moveq(data, 0x24E)[1]), "byte_copy_to_a0"),
        (0x262, 4, "long_device_write"),
        (0x264, 4, "long_device_write"),
        (0x26E, 4, "long_device_write"),
        (0x27A, dbf_body_iterations(moveq(data, 0x278)[1]), "byte_device_writes"),
    ):
        require(cursor + count <= end, "consumer exceeds table")
        groups.append({"start": cursor, "end_exclusive": cursor + count,
                       "consumer": consumer, "role": role,
                       "sha256": hashlib.sha256(data[cursor:cursor + count]).hexdigest()})
        cursor += count
    require(cursor == end, "table consumers do not cover skipped range")
    clear_count = dbf_body_iterations(seeds["d6"])
    return {
        "finding_id": "FIND-0001", "method": "static_only", "intervals": "half_open",
        "reset_fragment": [0x200, 0x28E], "table": [start, end],
        "continuation": end, "register_seeds_u32": seeds, "table_groups": groups,
        "copy": {"source": [0x2C4, 0x2EA], "destination_m68000": seeds["a0"],
                 "size_bytes": dbf_body_iterations(moveq(data, 0x24E)[1])},
        "clear_loop": {"instruction": 0x25C, "longword_writes": clear_count,
                       "size_bytes": 4 * clear_count, "initial_a6": 0,
                       "final_a6": (-4 * clear_count) & 0xFFFFFFFF},
        "runtime_observed": False,
    }


def capture_decoders(data: bytes, output: Path) -> dict:
    require(shutil.which("rasm2") is not None, "rasm2 is required for --disassemble")
    records = []

    def run(name: str, arch: str, cpu: str, offset: int, fragment: bytes) -> str:
        command = ["rasm2", "-a", arch, "-b", "32", "-e", "-c", cpu,
                   "-s", hex(offset), "-D", fragment.hex()]
        result = subprocess.run(command, capture_output=True, text=True, timeout=20, check=False)
        records.append({"name": name, "argv": command, "returncode": result.returncode,
                        "stdout": result.stdout, "stderr": result.stderr})
        require(result.returncode == 0, f"decoder command failed: {name}")
        return result.stdout

    sentinel_000 = run("cpu_sentinel_68000", "m68k", "68000", 0, bytes.fromhex("49c0"))
    sentinel_020 = run("cpu_sentinel_68020", "m68k", "68020", 0, bytes.fromhex("49c0"))
    require("invalid" in sentinel_000 and "extb.l" in sentinel_020,
            "decoder did not distinguish original 68000 from 68020")
    run("reset_capstone", "m68k", "68000", 0x200, data[0x200:0x28E])
    # The GNU plugin's four-byte read limit excludes longer instructions. It
    # also enables ColdFire flags internally; this is corroboration only.
    for offset, size in ((0x210, 4), (0x214, 4), (0x218, 4), (0x23E, 4),
                         (0x250, 2), (0x252, 4), (0x25C, 2), (0x25E, 4),
                         (0x288, 4), (0x28C, 2)):
        decoded = run(f"gnu_{offset:04x}", "m68k.gnu", "m68000", offset, data[offset:offset + size])
        require("invalid" not in decoded and ".short" not in decoded,
                f"GNU crosscheck rejected instruction at {offset:#x}")
    run("gnu_known_six_byte_failure", "m68k.gnu", "m68000", 0x200, data[0x200:0x206])
    version = subprocess.run(["rasm2", "-v"], capture_output=True, text=True, timeout=10, check=True)
    artifact = {"rasm2_version": version.stdout.strip(), "commands": records,
                "limitations": "GNU corroborates selected short instructions only; review mnemonics manually."}
    atomic_json(output / "decoder-evidence.json", artifact)
    return {"artifact": str((output / "decoder-evidence.json").relative_to(ROOT)),
            "rasm2_version": version.stdout.strip(), "cpu_sentinel_passed": True}


def output_directory(root: Path = ROOT) -> Path:
    root = root.resolve()
    output = root / "local/generated/reset"
    for ancestor in (root / "local", root / "local/generated", output):
        require(not ancestor.is_symlink(), f"refusing symlinked output directory: {ancestor}")
    require(output.resolve().is_relative_to(root / "local"), "output escapes local research directory")
    output.mkdir(parents=True, exist_ok=True)
    return output


def atomic_json(path: Path, value: dict) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".reset-probe-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(value, indent=2) + "\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disassemble", action="store_true", help="capture optional local rasm2 crosschecks")
    args = parser.parse_args(argv)
    try:
        manifest = json.loads((ROOT / "re/rom_manifest.json").read_text())
        identity = manifest["original"]
        path = ROOT / identity["path"]
        require(path.stat().st_size == identity["size_bytes"], "unsupported ROM size")
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        require(digest == identity["sha256"], "unsupported ROM SHA-256")
        report = analyze_reset(data)
        report["rom_sha256"] = digest
        output = output_directory()
        if args.disassemble:
            report["decoder_evidence"] = capture_decoders(data, output)
        require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, "ROM changed during probe")
        atomic_json(output / "report.json", report)
        print(f"FIND-0001: static table [0x28E,0x2FA),108 bytes; report: {output / 'report.json'}")
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"reset-probe: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
