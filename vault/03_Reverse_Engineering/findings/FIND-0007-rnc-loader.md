---
id: FIND-0007
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset
confidence: confirmed
task: TASK-0004
---
# Original RNC2 decoder, caller chain and first pattern-bank layout

Task: [[07_Tasks/TASK-0004-rnc-loader]]. **Confirmed scope is static code/data
relationships and decoded byte extents.** No original CPU was executed; runtime
selection, rendered appearance and gameplay equivalence remain unobserved.
Symbols below are project-assigned descriptions, not recovered original names.

## Identity and code boundaries

ROM-LOCAL-0001, 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
No normalization. Ranges are half-open file offsets; the direct ROM mapping is
used for the corroborated 68000 code/data addresses within this 1 MiB window.
RAM effective addresses and their 24-bit external forms are kept separate.

| Region | Static role | Boundary evidence |
| --- | --- | --- |
| `[0x19462,0x1959E)` | RNC2 decoder, FUNC-0002 | Prologue, 147 reachable instructions, closed branch graph, one RTS at `0x1959C` |
| `[0x10D8,0x10F8)` | Select resource descriptor, FUNC-0003 | Multiply/index/store followed by RTS |
| `[0x1896,0x18EE)` | Dispatch selected resource banks, FUNC-0004 | Loads descriptor fields, tail JMP `0x3CB6` |
| `[0x3CB6,0x3D46)` | Unpack and consume two resources, FUNC-0005 | PACK checks, calls, final RTS |
| `[0x3D46,0x3E14)` | Consume first pattern bank, FUNC-0006 | Palette call, two counted transfer loops, final RTS |
| `[0x13754,0x137A0)` | Load 16 palette entries, FUNC-0007 | Fixed count loop, nested call, restored pointers and RTS |

Metadata authority: `re/functions.csv` / `re/symbols.csv` for names and
boundaries; `re/rnc_loader.json` for selected analysis ranges/hashes and linkage;
`re/rnc_blocks.json` for resource identity and measured structure. Generated
disassembly remains local and is not the sole record of this finding.

## Decoder semantics and native mapping

Entry `0x19462` saves D0–D2/A0–A2. A0 points to the RNC header and A1 to output.
`LEA 18(A0),A0` at `0x19466` skips the header without inspecting it. D2 contains
an MSB-first control-byte shift register with a sentinel bit; ADD.B/ADDX.B and
refill branches interleave control bits with direct `(A0)+` raw reads. Initial
shifts consume two ignored bits. Literal copies use `(A0)+ -> (A1)+`.

The short/extended match-length branches, `(n+3)*4` literal-run loop, high/low
distance assembly, overlap copies and zero-length continuation/end marker match
the grammar documented in [[03_Reverse_Engineering/findings/FIND-0006-native-rnc2]].
The distance-one path repeats the previous byte; other matches copy forward.
`0x19598` restores the saved registers; RTS follows. The caller therefore keeps
its original A0/A1 values, even though internal cursors advanced.

The decoder's graph covers 147/147 instructions (181 edges) and stays within
the 316-byte routine, with no subroutine or indirect jump. This is static
closure, not executed coverage. The routine has no RNC signature, length or CRC
checks and no input/output safety bounds. Native `wiz::rnc2::decode` is a
**well-formed-format replacement** with additional safety checks and a host API;
it does not reproduce malformed-input memory corruption, register ABI or CCR
side effects. Original-vs-native execution comparison remains unperformed.

## Why the first block had no direct header pointer

`0x10D8` loads table base `0x33400`. It reads a word at offset 4 of the structure
pointed to by RAM `0xFFFF3398`, multiplies it unsigned by `0x22`, then uses the
signed low-word product as an indexed displacement. It stores the descriptor
pointer at RAM `0xFFFF33F0`. Full table length and index meaning are not asserted.

For index **zero**, descriptor `[0x33400,0x33422)` contains a longword at
`+0x1C` (`0x3341C`) equal to **`0x348AE`**, four bytes before the known RNC header.
Bytes `[0x348AE,0x348B2)` are `PACK`; the RNC2 header starts at `0x348B2`.
The earlier raw search for a longword `0x348B2` correctly found nothing: the
consumer points to the wrapper and skips its tag.

`0x1896` loads the descriptor from `0xFFFF33F0`. At `0x18E0` it loads a separately
selected pointer into A1; at `0x18E4` it loads the `+0x1C` bank pointer into A0,
then tail-jumps to `0x3CB6`. The bank-pair routine saves the other pointer,
compares the first resource's tag to `PACK`, advances A0 by four, and calls
`0x19462` at `0x3CFA` with output **`0xFFFF8844`** (external `0xFF8844`).
After return it passes that same buffer to the consumer `0x3D46` via the BSR at
`0x3D06`. A non-PACK input bypasses decompression and is consumed directly.

This establishes the conditional source/destination chain for descriptor zero.
It does not establish when a real play session selects zero or which named
scene/world it represents. A scan logs 16 even-offset direct-transfer byte matches to the decoder,
including one tail JMP and the verified `0x3CFA` call. The other 15 remain
**candidates**, not promoted to verified callers or a full call graph.

## Consumer-derived resource structure

The verified 17,714-byte output retains SHA-256
`048aec81ffb0e5463029b931c2716e5aaa818539b5f72c078f7a19cc195a9ac7`.
Its stable logical ID remains `rnc.unclassified.0001`; changing our understanding
does not rename the asset or break downstream references.

| Decoded range | Meaning established by consumer | Size |
| --- | --- | --- |
| `[0,32)` | 16 two-byte palette inputs passed to `0x13754` with selector D0=2 | 32 |
| `[32,34)` | Big-endian DBF initial count `0x01B9`; body-first loops give 442 iterations | 2 |
| `[34,14178)` | 442 patterns, eight longword writes (32 bytes) per iteration to effective `0xFFC00000` | 14,144 |
| `[14178,17714)` | 442 opaque records, two longword copies (8 bytes) each into RAM | 3,536 |

`0x13754` preserves A0 and converts each input pair `[a,b]` to
`[b & 0x0F, (b & 0xF0) | (a & 0x0F)]` in a RAM palette buffer. The first bank's
selector 2 selects `0xFFFF0D20`. Its nested callee at `0x137CE` is not fully
reconstructed here. Display color scaling and pixel order remain unvalidated.

`0x3D70` skips the 32 palette bytes; `0x3D94` reads count-minus-one. The DBF at
`0x3DCC` controls eight longword writes per iteration. The second DBF at `0x3DF4`
uses the same saved count and copies eight bytes per record, starting from RAM
destination `0xFFFF6D02` on this first-bank path. All regions sum exactly to the
output size: `32 + 2 + 442*32 + 442*8 = 17714`.

Interpretation: a graphics pattern bank with a palette and parallel records.
The port addresses/control words support video transfers; the records' gameplay
meaning (including a possible collision interpretation) is **unknown**. Do not
infer an 8x8 pixel layout, a tile count limit, scene names or collision formulas
from byte size alone. The 442 records are a measured bank count, not a verified
original maximum capacity.

## Reproduce and limitations

```sh
python3 tools/project.py rnc-validate --decode
python3 tools/project.py rnc-loader-probe --disassemble \
  --decoded-bank local/extracted_assets/rnc/rnc.unclassified.0001.bin
python3 tools/project.py test --rom --preset sanitize
```

`tools/rnc_loader_probe.py` verifies exact ROM/range hashes and selected operand,
branch, count and pointer relationships. Optional disassembly refuses fabricated
truncated instructions, invalid mnemonics and inconsistent extents/bytes. The
original-68000/68020 sentinel passes with installed rasm2 5.9.8 (Capstone5), and
16 selected instructions are independently corroborated by its GNU backend.
The GNU plugin remains restricted to <=4-byte instructions; extra CPU flags mean
it is corroboration only. Synthetic `tests/test_rnc_loader.py` has nine tests
covering parsing bounds, counts, word-index semantics, direct transfers, strict
disassembly parsing and control-flow rejection cases.

Evidence: `local/generated/rnc-loader/run-s3737ul_/report.json` and adjacent
`decoder-evidence.json`; `local/logs/rnc-loader/commands.json`. Bulk raw analysis
attempts stay under `local/generated/rnc-loader-research/`. Initial dumps from
arbitrary pre-call offsets were misaligned and produced invalid/padded decodes;
the reproducible probe uses reviewed entry/end boundaries and rejects them.

No native gameplay, emulator run, rendering or audio was added. The native codec
still passes 50 independent comparison cases. Next:
[[07_Tasks/TASK-0005-native-pattern-bank]] implements the now-bounded structured
asset loader and verifies pixel/color representation. Then trace the companion
scene resource and its movement/collision consumers for the playable slice.
See [[03_Reverse_Engineering/ASSET_FORMATS]], [[03_Reverse_Engineering/CONTROL_FLOW]],
[[04_Native_Implementation/PORTING_MAP]], [[05_Validation/RESULTS]].


## Subsequent result

TASK-0005 is complete. The then-unvalidated pixel/color representation now has
source corroboration and native diagnostic rendering; see
[[03_Reverse_Engineering/findings/FIND-0008-native-pattern-bank]]. This does not
retroactively turn this static investigation into original execution evidence.
