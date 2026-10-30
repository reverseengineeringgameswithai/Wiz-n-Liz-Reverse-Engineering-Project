---
id: FIND-0001
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: m68000_rom_window
confidence: confirmed
task: TASK-0001
---
# Reset initialization table and bounded control flow

**Confirmed scope:** static instruction fields, references, and table consumption
in this exact ROM. No original-machine execution or timing has been observed.
Task: [[07_Tasks/TASK-0001-foundation]]. Identity:
[[03_Reverse_Engineering/ROM_IDENTITY]], 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
All ranges below are half-open file offsets, numerically matching the initial
unbanked ROM window's 68000 addresses. No normalization was applied.

## Observations

The reset vector at file offset `0x004` contains `0x00000200`. At `0x200`, a long
test reads `0x00A10008`; a conditional branch can reach `0x20E`, otherwise a word
test reads `0x00A1000C`. The branch at `0x20E` can skip initialization to `0x28C`.
The unconditional branch at `0x28C` goes to `0x2FA`.

On the initialization path, `LEA` at `0x210` sets A5 to `0x28E`.
`MOVEM.W` at `0x214` loads D5–D7 and advances A5 by six bytes. `MOVEM.L` at
`0x218` loads A0–A4 and advances it by twenty bytes. The resulting values are:

| Register | Value after load | Source file range |
|---|---:|---|
| D5 | `0xFFFF8000` | `[0x28E,0x290)` |
| D6 | `0x00003FFF` | `[0x290,0x292)` |
| D7 | `0x00000100` | `[0x292,0x294)` |
| A0 | `0x00A00000` | `[0x294,0x298)` |
| A1 | `0x00A11100` | `[0x298,0x29C)` |
| A2 | `0x00A11200` | `[0x29C,0x2A0)` |
| A3 | `0x00C00000` | `[0x2A0,0x2A4)` |
| A4 | `0x00C00004` | `[0x2A4,0x2A8)` |

Later consumers account for every remaining byte before the branch destination:

| Source file range | Consumer | Static use |
|---|---:|---|
| `[0x2A8,0x2C0)` | `0x238`–`0x23E` | 24 bytes, each placed in D5's low byte and written as a word through A4; D7 is added to D5 between writes |
| `[0x2C0,0x2C4)` | `0x242` | One long write through A4 |
| `[0x2C4,0x2EA)` | `0x250`–`0x252` | 38 byte copies to successive addresses starting at A0=`0x00A00000` |
| `[0x2EA,0x2EE)` | `0x262` | One long write through A4 |
| `[0x2EE,0x2F2)` | `0x264` | One long write through A4 |
| `[0x2F2,0x2F6)` | `0x26E` | One long write through A4 |
| `[0x2F6,0x2FA)` | `0x27A`–`0x27E` | Four byte writes to A3+`0x11` |

Thus `[0x28E,0x2FA)` is a **108-byte inline initialization table**, not a sequence
of 68000 instructions along this reset path. Its 38-byte copied payload has
SHA-256 `2eaa830f89e9443f07c1c637df822f83d6a9e17d6a797c32947e20fd2435bb01`.
That digest identifies the copied bytes; it does not identify a sound driver.

At `0x230`–`0x234`, D0 and A6 become zero and USP is set from A6. The clear loop
at `0x25C`–`0x25E` stores D0 as a long through predecrement A6, using D6's low word
as a DBF counter. If that loop completes uninterrupted, it performs 16,384 long
writes, covering the 32-bit effective range `[0xFFFF0000,0x100000000)` downward
and leaving A6=`0xFFFF0000`. On a 24-bit bus that corresponds to
`[0xFF0000,0x1000000)`. This arithmetic is static; RAM contents were not captured.

The reset fragment has no subroutine calls before `0x28E`. External dependencies
include the tested I/O values and the polling loop at `0x24A`–`0x24C`; without a
reference run there is no assertion that the initialization path or its exit
actually occurred. `0x2FA` is an observed branch destination, not a known function
boundary. The whole reset routine's end remains unknown.

## Interpretation and decision

The bytes and consumer arithmetic justify classifying `[0x200,0x28E)` as a
reachable reset-code fragment and `[0x28E,0x2FA)` as referenced inline data.
The device names/roles, copied program behavior, sound system, and initialization
timing require more evidence. Keep `[0x2FA,EOF)` conservatively unclassified in
the first segmentation; an entry label does not classify everything after it.

`re/symbols.csv` is authoritative for labels; `re/functions.csv` records one
partial reset-flow entry with an unknown complete end. This is disassembly and
analysis, not reconstructed native gameplay. There is no native function or
differential test for this routine.

## Verification and reproduction

```sh
python3 -m unittest discover -s tests -p test_reset_probe.py -v
python3 tools/reset_probe.py --disassemble
```

The first command runs nine ROM-independent synthetic tests for bounds,
displacements, widths, masks, loop counts, and protected output handling.
The second validates `re/rom_manifest.json` before processing and rehashes the
original afterward. It reads the original without modifying it and writes:

- `local/generated/reset/report.json`: boundaries, seed values, table-consumer
  ranges and hashes, byte-copy and clearing counts; explicitly `static_only`.
- `local/generated/reset/decoder-evidence.json`: exact local invocations, exit
  codes, stderr, original fragment decoding and ten short-instruction independent
  corroborations. Both files are ignored local evidence, regenerated by the tool.

Tested with Python 3 on this host and installed `rasm2 5.9.8`, Capstone 5 plugin
`m68k` and Binutils 2.36-based plugin `m68k.gnu`. The explicit `68000` selection
rejects the synthetic later-family opcode `49C0`; the same opcode becomes
`EXTB.L D0` under `68020`. This validates CPU selection despite the CLI's
misleading "Ignored -c" warning. Opcode fields for LEA, MOVEM, MOVEQ, DBF and
branches were additionally checked against the Motorola manual.

Important tool limits:

- `m68k.gnu` in radare2 5.9.8 rejects reads beyond four instruction bytes;
  the six-byte instruction at `0x200` reproduces this defect. It also includes
  ColdFire flags internally. Use it only as corroboration for the ten reviewed
  two/four-byte instructions, never as proof of full original-68000 validity.
- System `objdump 2.46-3.fc44` lists no m68k target; it was not an independent
  usable decoder here.
- `rasm2 -B -i 0x200 -l 0x8E -f <ROM>` unexpectedly decoded the file's initial
  vector bytes in the attempted invocation. The probe instead supplies the
  bounded slice as a local hex argument, and records matching bytes/addresses.
- The first sega2asm output disagreed at `0x218` (wrong MOVEM register mask) and
  `0x288` (`not.?`). Correct operands are A0–A4 at `0x218` and
  `MOVE.W #0x2700,SR` at `0x288`, confirmed by both local decoders and instruction
  fields. A tool's zero exit code does not establish semantic correctness.

## Sources and limitations

Primary sources accessed 2026-10-02:

- [Motorola M68000 Programmer's Reference Manual](https://www.nxp.com/docs/en/reference-manual/M68000PM.pdf):
  §§2.2.11 and instruction entries BRA, DBcc, LEA, MOVEM, MOVEQ; instruction
  encodings, PC-relative base, register order, sign extension and loop semantics.
- [Motorola M68000 User's Manual](https://www.nxp.com/docs/en/reference-manual/MC68000UM.pdf):
  §2 introduction, original MC68000's 24-bit external addressing.
- [radare2 5.9.8 Capstone plugin](https://raw.githubusercontent.com/radareorg/radare2/5.9.8/libr/arch/p/m68k_cs/plugin.c):
  `get_capstone_mode` selects `CS_MODE_M68K_000` for `68000`.
- [radare2 5.9.8 GNU plugin](https://raw.githubusercontent.com/radareorg/radare2/5.9.8/libr/arch/p/m68k_gnu/plugin.c):
  four-byte callback limit, extra CPU flags, GPL-3.0-only plugin declaration.

No third-party source was copied into tracked implementation. No emulator ran,
no cycles were measured, and no assets were identified by this probe. The next
useful validation is a reset reference run with a breakpoint at `0x2FA`, logging
which path reached it and observing the copied range and cleared memory. Then
follow the continuation's calls to select a gameplay-relevant native routine.
See [[03_Reverse_Engineering/CONTROL_FLOW]] and
[[03_Reverse_Engineering/MEMORY_MAP]].
