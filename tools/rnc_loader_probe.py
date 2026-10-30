"""Bounded static RNC2 caller/consumer evidence; never a CPU execution engine."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from rom import ROOT, DEFAULT_ROM, inspect_file, verify_expected
from rnc import approved_directory, atomic_write, parse_block, validate_decoded
from reset_probe import branch_target, dbf_target, signed, word


def u32(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise ValueError(f"truncated longword at {offset:#x}")
    return int.from_bytes(data[offset:offset + 4], "big")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def descriptor_address(base: int, index: int, stride: int) -> int:
    """MULU.W followed by d16-width indexed LEA; no invented table bounds."""
    offset_word = ((index & 0xFFFF) * (stride & 0xFFFF)) & 0xFFFF
    return (base + signed(offset_word, 16)) & 0xFFFFFFFF


def inspect_pattern_bank(data: bytes, max_records: int = 65536) -> dict:
    """Layout from the two DBF consumers, not inferred from an image preview."""
    require(len(data) >= 34, "pattern bank header truncated")
    count = word(data, 32) + 1  # body-first DBF consumes zero as one record
    require(1 <= count <= max_records, "pattern count exceeds configured limit")
    pattern_end = 34 + 32 * count
    end = pattern_end + 8 * count
    require(end == len(data), "pattern bank extent differs from consumer loops")
    regions = {}
    for name, lo, hi in (("palette", 0, 32), ("count_minus_one", 32, 34),
                         ("patterns", 34, pattern_end), ("opaque_records", pattern_end, end)):
        regions[name] = {"range": [lo, hi], "size_bytes": hi - lo,
                         "sha256": hashlib.sha256(memoryview(data)[lo:hi]).hexdigest()}
    return {"format": "pattern_bank_v1", "record_count": count, "regions": regions,
            "pixel_interpretation_checked": False, "opaque_record_meaning": None}


def direct_target(data: bytes, pc: int) -> int | None:
    """Selected original-68000 direct transfers; scans remain candidates."""
    opcode = word(data, pc)
    if opcode in (0x4EB9, 0x4EF9):
        return u32(data, pc + 2)
    if opcode in (0x4EBA, 0x4EFA):
        return (pc + 2 + signed(word(data, pc + 2), 16)) & 0xFFFFFFFF
    if opcode & 0xFF00 == 0x6100:
        return branch_target(data, pc)
    return None


def analyze_fields(data: bytes, metadata: dict) -> dict:
    for region in metadata["regions"]:
        lo, hi = region["start"], region["end_exclusive"]
        require(0 <= lo < hi <= len(data), "invalid analysis region")
        require(hashlib.sha256(data[lo:hi]).hexdigest() == region["sha256"],
                f"changed analysis region: {region['id']}")
    # Check the reviewed forms before using their operands as dataflow evidence.
    for pc, opcode in ((0x10D8, 0x43F9), (0x10E8, 0xC2FC), (0x10EC, 0x43F1),
                       (0x10F0, 0x23C9), (0x1896, 0x2079), (0x18E4, 0x2068),
                       (0x3CE8, 0x0C80), (0x3CF0, 0x41E8), (0x3CF4, 0x43F9),
                       (0x3D00, 0x41F9), (0x19466, 0x41E8), (0x3D70, 0x41E8),
                       (0x3D94, 0x3E18), (0x3DEA, 0x3E39)):
        require(word(data, pc) == opcode, f"unsupported instruction form at {pc:#x}")
    base = u32(data, 0x10DA)
    stride = word(data, 0x10EA)
    field = word(data, 0x18E6)
    require((base, stride, field) == (metadata["descriptor_table"], metadata["descriptor_stride"],
                                    metadata["bank_pointer_field"]), "descriptor metadata mismatch")
    require(word(data, 0x10EE) == 0x1000, "unexpected descriptor index extension")
    require(u32(data, 0x10F2) == u32(data, 0x1898) == 0xFFFF33F0,
            "selector/dispatch do not share descriptor pointer")
    require(direct_target(data, 0x18E8) == 0x3CB6, "dispatch tail call differs")
    require(u32(data, 0x3CEA) == int.from_bytes(b"PACK", "big"), "unexpected wrapper tag")
    wrapper_size = word(data, 0x3CF2)
    require(wrapper_size == metadata["wrapper_size"] == 4, "wrapper skip differs")
    require(branch_target(data, 0x3CEE) == 0x3D06, "wrapper bypass differs")
    require(direct_target(data, 0x3CFA) == metadata["decoder_entry"], "decoder call differs")
    scratch = u32(data, 0x3CF6)
    require(scratch == u32(data, 0x3D02) == metadata["scratch_effective_address"],
            "decode destination/consumer source mismatch")
    require(word(data, 0x19468) == 18, "RNC header skip differs")
    require(direct_target(data, 0x3D06) == 0x3D46, "bank consumer call differs")
    require(direct_target(data, 0x3D4A) == 0x13754, "palette consumer call differs")
    require(word(data, 0x3D72) == 32, "palette skip differs")
    require(dbf_target(data, 0x3DCC) == (7, 0x3D9C), "pattern loop differs")
    require(dbf_target(data, 0x3DF4) == (7, 0x3DF0), "opaque-record loop differs")
    require(word(data, 0x1376E) == 0x7E0F and dbf_target(data, 0x13788) == (7, 0x13770),
            "palette count loop differs")
    for pc in range(0x3D9C, 0x3DCC, 6):
        require(word(data, pc) == 0x23D8 and u32(data, pc + 2) == 0xFFC00000,
                "pattern transfer differs")
    require(word(data, 0x3DF0) == word(data, 0x3DF2) == 0x22D8, "opaque record width differs")
    descriptor = descriptor_address(base, metadata["validated_descriptor_index"], stride)
    wrapper = u32(data, descriptor + field)
    require(wrapper == metadata["wrapper_offset"], "descriptor no longer selects known wrapper")
    require(data[wrapper:wrapper + 4] == b"PACK", "selected resource lacks PACK tag")
    header, _ = parse_block(data, wrapper + wrapper_size)
    # Byte-pattern searches are discovery leads, not additional confirmed callers.
    candidates = []
    for pc in range(0, len(data) - 6, 2):
        if direct_target(data, pc) == metadata["decoder_entry"]:
            candidates.append(pc)
    return {"method": "static_only", "runtime_observed": False,
            "descriptor": descriptor, "pointer_field": descriptor + field,
            "wrapper": wrapper, "block_offset": header.file_offset,
            "block_end_exclusive": header.end_exclusive, "scratch_effective_address": scratch,
            "scratch_external_address": scratch & 0xFFFFFF,
            "decoder_range": [0x19462, 0x1959E], "header_bytes_skipped": 18,
            "confirmed_chain": [0x10D8, 0x1896, 0x3CB6, 0x19462, 0x3D46],
            "chain_condition": "descriptor index zero; selected at runtime not observed",
            "transfer_candidate_offsets": candidates,
            "candidate_warning": "other byte matches are not a verified call graph"}


def parse_disassembly(text: str, data: bytes, start: int, end: int) -> list[dict]:
    instructions = []
    cursor = start
    for line in text.splitlines():
        match = re.fullmatch(r"(0x[0-9a-f]+)\s+(\d+)\s+([0-9a-f]+)\s+(.+)", line.strip())
        require(match is not None, "unrecognized disassembler output")
        address, size = int(match[1], 16), int(match[2])
        require(address == cursor and size in (2, 4, 6, 8, 10), "invalid instruction extent")
        require(address + size <= end, "disassembler fabricated a truncated instruction")
        require(bytes.fromhex(match[3]) == data[address:address + size], "decoder byte mismatch")
        require("invalid" not in match[4] and "dc.w" not in match[4], "unsupported instruction")
        instructions.append({"address": address, "size": size, "assembly": match[4]})
        cursor += size
    require(cursor == end, "disassembly does not cover requested region")
    return instructions


def decoder_cfg(data: bytes, instructions: list[dict]) -> dict:
    """Reachability for the small closed decoder: branch/DBcc/RTS, no CPU state."""
    require(bool(instructions), "empty decoder instruction list")
    by_address = {row["address"]: row for row in instructions}
    work = [instructions[0]["address"]]
    seen, edges, returns = set(), [], []
    while work:
        pc = work.pop()
        if pc in seen:
            continue
        require(pc in by_address, f"branch leaves decoder/instruction boundary: {pc:#x}")
        row = by_address[pc]
        seen.add(pc)
        op = word(data, pc)
        if op == 0x4E75:
            returns.append(pc)
            continue
        successors = [pc + row["size"]]
        if op & 0xF000 == 0x6000:
            condition = (op >> 8) & 15
            require(condition != 1, "unexpected subroutine call inside closed decoder")
            if condition == 0:
                successors = []
            successors.append(branch_target(data, pc))
        elif op & 0xF0F8 == 0x50C8:
            successors.append((pc + 2 + signed(word(data, pc + 2), 16)) & 0xFFFFFFFF)
        else:
            require(not (0x4E80 <= op <= 0x4EFF), "unexpected indirect control flow")
        for target in successors:
            edges.append([pc, target])
            work.append(target)
    require(len(seen) == len(instructions) and len(returns) == 1, "decoder has unexplained code/returns")
    return {"reachable_instructions": len(seen), "return_addresses": returns, "edges": edges,
            "scope": "static closure; not execution or semantic equivalence"}


def capture_decoders(data, metadata, directory):
    records = []

    def run(arch, cpu, start, fragment):
        command = ["rasm2", "-a", arch, "-b", "32", "-e", "-c", cpu,
                   "-s", hex(start), "-D", fragment.hex()]
        process = subprocess.run(command, capture_output=True, text=True, timeout=15)
        records.append({"argv": command, "exit_status": process.returncode,
                        "stdout": process.stdout, "stderr": process.stderr})
        require(process.returncode == 0, "decoder process failed")
        return process.stdout

    sentinel = bytes.fromhex("49c0")
    require("invalid" in run("m68k", "68000", 0, sentinel), "68000 sentinel failed")
    require("extb.l" in run("m68k", "68020", 0, sentinel), "68020 sentinel failed")
    rows = {}
    for region in metadata["regions"]:
        lo, hi = region["start"], region["end_exclusive"]
        output = run("m68k", "68000", lo, data[lo:hi])
        rows[region["id"]] = parse_disassembly(output, data, lo, hi)
    corroborated = []
    # GNU plugin cannot decode >4-byte instructions and exposes extra CPU flags.
    # Expected mnemonics here are independently reviewed, not auto-consensus.
    for pc, size, mnemonic in ((0x19462,4,"moveml"),(0x19466,4,"lea"),
                              (0x19470,2,"addxb"),(0x194AE,2,"addxw"),
                              (0x194B0,4,"dbf"),(0x194FC,2,"rolw"),
                              (0x19502,2,"subaw"),(0x19504,2,"subqw"),
                              (0x19522,4,"dbf"),(0x19598,4,"moveml"),
                              (0x18E4,4,"moveal"),(0x10E8,4,"muluw"),
                              (0x3D94,2,"movew"),(0x3DCC,4,"dbf"),
                              (0x3DF4,4,"dbf"),(0x13788,4,"dbf")):
        text = run("m68k.gnu", "m68000", pc, data[pc:pc + size])
        row, = parse_disassembly(text, data, pc, pc + size)
        require(row["assembly"].split()[0] == mnemonic, "GNU corroboration differs")
        corroborated.append(pc)
    version = subprocess.run(["rasm2", "-v"], capture_output=True, text=True, timeout=10, check=True)
    artifact = {"version": version.stdout.strip(), "commands": records, "instructions": rows,
                "gnu_corroborated_addresses": corroborated,
                "decoder_cfg": decoder_cfg(data, rows["rnc2_decoder"])}
    atomic_write(directory / "decoder-evidence.json", (json.dumps(artifact, indent=2) + "\n").encode())
    return {"artifact": str((directory / "decoder-evidence.json").relative_to(ROOT)),
            "version": artifact["version"], "decoder_instruction_count": artifact["decoder_cfg"]["reachable_instructions"],
            "gnu_corroborations": len(corroborated)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disassemble", action="store_true", help="Require rasm2 and capture bounded CFG/crosschecks")
    parser.add_argument("--decoded-bank", type=Path, help="Validate layout of the known native-extracted blob")
    args = parser.parse_args(argv)
    before = inspect_file()
    verify_expected(before)
    data = DEFAULT_ROM.read_bytes()
    require(hashlib.sha256(data).hexdigest() == before["sha256"], "ROM changed before analysis")
    metadata = json.loads((ROOT / "re/rnc_loader.json").read_text())
    require(metadata["schema_version"] == 1 and metadata["address_space"] == "rom_file_offset", "unsupported metadata")
    directory = Path(tempfile.mkdtemp(prefix="run-", dir=approved_directory(ROOT, "local/generated/rnc-loader")))
    report = {"finding_id": "FIND-0007", "rom_sha256": before["sha256"], "ok": False}
    try:
        report["static"] = analyze_fields(data, metadata)
        if args.disassemble:
            report["decoders"] = capture_decoders(data, metadata, directory)
        else:
            report["decoders"] = {"status": "not_requested"}
        if args.decoded_bank:
            entry, = [e for e in json.loads((ROOT / "re/rnc_blocks.json").read_text())["blocks"]
                      if e["id"] == metadata["block_id"]]
            header, _ = parse_block(data, report["static"]["block_offset"])
            require(args.decoded_bank.stat().st_size == header.unpacked_size, "decoded blob size differs")
            decoded = args.decoded_bank.read_bytes()
            identity = validate_decoded(header, decoded)
            require(identity["sha256"] == entry["decoded_sha256"], "unsupported decoded blob")
            structure = inspect_pattern_bank(decoded)
            recorded = entry["structure"]
            require((structure["format"], structure["record_count"]) ==
                    (recorded["format"], recorded["record_count"]), "catalog structure differs")
            for region, key in (("palette", "palette_range"), ("patterns", "pattern_range"),
                                ("count_minus_one", "count_minus_one_range"),
                                ("opaque_records", "opaque_records_range")):
                require(structure["regions"][region]["range"] == recorded[key],
                        f"catalog range differs: {region}")
            report["decoded"] = identity | structure
        report["ok"] = True
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        report["error"] = str(exc)
    finally:
        try:
            verify_expected(inspect_file())
            report["rom_unchanged"] = True
        except (OSError, ValueError) as exc:
            report.update(ok=False, rom_unchanged=False, identity_error=str(exc))
        atomic_write(directory / "report.json", (json.dumps(report, indent=2) + "\n").encode())
    print(json.dumps({"ok": report["ok"], "report": str(directory / "report.json"),
                      "error": report.get("error"), "decoded": report.get("decoded")}, indent=2))
    return int(not report["ok"])
