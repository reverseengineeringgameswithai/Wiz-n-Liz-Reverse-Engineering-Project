---
id: FIND-0010
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0007
---
# Native terrain queries, contact probes and one-pixel settling

Task: [[07_Tasks/TASK-0007-terrain-query]]. Confirmed scope: six bounded original
routines executed in isolated, constructed states and compared with native C++
semantic replacements. This is the first original CPU differential in the project.
It does not establish a full player controller or a booted/playable game.

## Identity, boundaries and callers

ROM-LOCAL-0001, 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
No normalization or original-file change. Intervals are half-open, direct ROM
CPU addresses equal file offsets in the established window. RAM addresses below
are effective 68000 addresses, with low 24 bits used externally.

| ID / ROM range | Verified behavior | Native mapping |
| --- | --- | --- |
| FUNC-0010 `[0x99D4,0x9A18)` | Coordinate-to-map-word query, including negative-y sentinel and scratch writes | `query_terrain`, map portion |
| FUNC-0011 `[0x9A18,0x9A5E)` | Eight-byte record column query, horizontal reversal | `query_terrain`, record portion |
| FUNC-0012 `[0x9A80,0x9AAE)` | Compare foot contact; increment position y by one on mismatch | `settle_down` |
| FUNC-0013 `[0x9B34,0x9B5C)` | Contact comparison at position+(12,22) | `probe_contact(upper)` |
| FUNC-0014 `[0x9B5C,0x9B84)` | Contact comparison at position+(12,23) | `probe_contact(foot)` |
| FUNC-0015 `[0x9B84,0x9BAC)` | Contact comparison at position+(12,24) | `probe_contact(lower)` |

`re/terrain_query.json` records hashes, boundaries, instruction counts and ten
validated direct calls. `re/functions.csv` / `re/symbols.csv` are index authorities.
The additional `[0x2908,0x2934)` fragment repeats the foot comparison using long
JSRs at `0x2918/0x291E`; it is statically checked, not counted as a seventh
differential function. Its containing function/entry remains unpromoted.

`terrain-probe --disassemble` checks 97 decoded instructions in seven ranges,
closed intra-routine branch boundaries with reviewed calls, original-68000 CPU
selection sentinel, and 12 selected GNU corroborations. Six executed routines
contain 86 instructions. Exploratory transfer scans beyond these ranges remain
leads, not confirmed whole-program control flow.

## Exact query observations

`0x99D4` receives coordinate words in D0/D1. Both subtract 128 with word wrap.
The negative test examines the resulting y word, not x and not a host signed
integer. If negative, D0.W becomes the base-pattern word at `0xFFFF140E`, and
neither scratch word is updated. Thus a following record/contact query uses
the **previous** scratch x/y; the native API exposes `TerrainScratch` explicitly.

Otherwise it saves untranslated-by-mask local x/y at `0xFFFF4442/4444`, preserves
D2, masks x with `0xFFFF13AE`, and reads the map via pointer `0xFFFF4452`. For
the verified 128x32 resource, the x mask is 1023 and row stride is 256 bytes.
The companion consumer derives these as width*8-1 and width*2 respectively.

The byte displacement is:

```text
2 * ((local_x & 1023) >> 3)
+ sign_extend_16(((local_y >> 3) * 256) & 65535)
```

The second term is **not** an unbounded row product: MULU.W produces a longword,
but ADDA.W consumes its low signed word. Large positive y can alias earlier rows
(e.g. input y2176 maps to row0), or address unrelated RAM. Native code preserves
the verified alias arithmetic and rejects addresses outside this scene's 8192
map bytes. Failures leave native scratch unchanged. Reading arbitrary original
RAM on malformed/out-of-resource inputs is outside the replacement contract.

`0x9A18` selects `(map_word & 0x7FF)*8` through adjusted record pointer
`0xFFFF444E`. Column is `scratch_x & 7`; bit11 reverses it with XOR7. The final
MOVE.B supplies an unsigned byte and N/Z flags, clearing V/C. **Bit12 does not
reverse or otherwise change the record.** Palette and priority also do not alter
this byte lookup. Do not reuse visual vertical-flip logic for terrain records.

Original loader setup `[0x3CB6,0x3CE4)`, already hashed in FIND-0007, stores the
base pattern and adjusts the record pointer by base*8. Native resources use
logical relative indices and concatenate base/additional records. Comparison
uses bases0 and 257 without 11-bit index overflow; those are constructed fixtures,
not claims about the base selected in a real game session. Relocation/index
overflow into attributes remains excluded from logical-index equivalence.

## Record meaning and contact behavior

The three probes read position words at A6+2/+4, add x12 and y22/23/24 with word
wrap, call both queries, then compare `((scratch_y & 7)+1)` with the returned byte
using CMP.B. Native `Contact` exposes the operands, equality and all NZVC flags.
This establishes **per-column one-based contact levels** in these consumers.
It does not establish all collision types, vertical response or solid-volume rules.

The 578 actual records contain only values0–8: counts
`0:4169, 1:25, 2:30, 3:27, 4:20, 5:268, 6:27, 7:31, 8:27`.
Zero cannot equal any of these probes' one-based values; larger authored bytes
are retained and tested as unsigned, including signed-overflow CMP flag cases.
The asset field keeps its existing `opaque_record` name to preserve bytes/API;
its terrain use is now verified, while other consumers remain to be interpreted.

`0x9A80` performs the foot comparison. Equality leaves position unchanged and
the compare flags intact. Mismatch increments y by one (including FFFF->0000),
then MOVEQ #1 leaves D1=1 and NZVC=0. This is one original movement primitive,
not a guessed gravity system. Its outer scheduling, player ownership, velocity,
input and timing remain unverified. Native `SettleResult` exposes moved/contact;
the comparison transport maps that result to observed final D1/flags.

## Independent execution and containment

[Musashi at the inspected pin](https://github.com/kstenerud/Musashi/tree/313ebf1bd9f4d0d93341eb5ce21fd8a119e9dbdd)
is isolated in `local/tools/terrain-reference/`, pinned by
`third_party/terrain_reference.lock.json`. Musashi's MIT notice and bundled
SoftFloat Release2b custom notice remain in the unmodified local source.
`tools/build_terrain_reference.py` builds with Clang22.1.7 ASan/UBSan, all later
CPU variants disabled, explicit M68000 selection and instruction hook enabled.
Source, harness, builder, lock and executable hashes are verified before use.
No upstream CPU implementation is copied into tracked native source or linked
into `wiz_sim`, `wiz_assets` or any normal executable.

The project-owned C harness executes original ROM bytes with a constructed map,
record store, scratch, state, stack and return sentinel. ROM is immutable in the
process. Read/write domains are bounded; code escapes, device/ROM writes,
undeclared reads, unbalanced stack, D2 corruption and instruction-budget overruns
fail. It traces instruction addresses and enforces 256 instructions per call.
Three explicit out-of-map fixtures must fail before producing output. The host
wrapper adds a 60-second subprocess timeout. No Genesis hardware, interrupts,
prefetch/cycle fidelity, full register ABI or reset-to-game path is modeled.

## Reproduce and verification

```sh
python3 tools/build_terrain_reference.py --download
python3 tools/project.py terrain-probe --disassemble
python3 tools/project.py build --preset debug
python3 tools/project.py terrain-compare --rom --preset debug
python3 tools/project.py terrain-compare --rom --preset release
python3 tools/project.py terrain-compare --rom --preset sanitize
```

Configure/build each native preset first; both cataloged resources must already
be extracted. Omit `--download` when sources are present. Normal build/test never
downloads or invokes Musashi. `terrain-compare` always needs original routine
ROM; its `--rom` adds the actual resource corpus to authored-state comparisons.

**614,436 cases per preset:** two relocated authored groups of 110,610 each,
and 393,216 actual-resource cases. Authored cases include all 65536 x words,
all y words whose computed addresses remain in the declared map or sentinel
path, all 256 byte values versus eight comparison positions for all four callers,
and 18 hand-worked golden cases checked against the reference independently.
The real corpus queries all 262,144 pixels and tests all 4096 map cells/eight
columns through each of the three probes and settling step (131,072 cases).
Outputs compare byte, logical map word, scratch, position and exposed final
NZVC/comparison result. Every one of 86 routine instruction addresses is visited
across the authored corpus; this is not whole-game or exhaustive-state coverage.

Evidence and exact runs: [[05_Validation/RESULTS]],
`local/logs/terrain-query/commands.json`, reports and case/output hashes under
`local/generated/terrain-comparison/`. Initial successful debug report:
`run-5hjj3vq8/report.json`. Current handoff:
[[08_Sessions/2026-10-02-007-terrain-query]].

## Remaining work

This meets the first bounded M2 native-behavior/differential milestone. Native
playability remains none. Reconstruct actual surrounding movement, actor ownership
and response through [[07_Tasks/TASK-0008-movement-step]], with independently
executed cases before integrating the controller and SDL3 platform. Record
semantics outside these consumers, scene identity, global terrain-query ordering,
camera, full collision response and audio remain open.
