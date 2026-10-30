---
id: RE-CONTROL-FLOW
type: technical
status: partial
---
# Control flow

The initial vector names one confirmed static entry: file/68000 address `0x200`.
[[03_Reverse_Engineering/findings/FIND-0001-reset-path]] documents the bounded
fragment `[0x200,0x28E)`, branches, inline table and reproduction commands.
Reset-to-game reachability is still unobserved. Isolated terrain routines now
have original execution evidence; see the scoped terrain section below.

| Address | Evidence | Current interpretation |
|---|---|---|
| `0x200` | Initial PC vector | Reset entry |
| `0x20E` | Conditional branch target | Tests flags from one of two I/O reads |
| `0x210` | Fallthrough after conditional skip | Initializes table pointer A5 |
| `0x24A` | Backward conditional branch | Polls an external value; exit timing unknown |
| `0x28C` | Conditional skip destination | Unconditional branch over inline data |
| `0x28E` | LEA target plus bounded consumers | Data, not reset fallthrough code |
| `0x2FA` | BRA target | Reset continuation; later flow not classified |

The code fragment contains 50 decoded instructions, but this is neither a
function count nor a gameplay coverage measure. The partial reset entry remains
in `re/functions.csv` with an unknown full end; eight resource routines and six
terrain/contact routines plus eight movement mappings now have reviewed entries. Labels in
`re/symbols.csv` are authoritative and can be exported into tool formats.
Do not edit generated disassembly as the only record of discoveries.

The vector values `0x0220800C` through `0x0920800C` and `0x00208008` do not
directly index this 1 MiB ROM. Their address interpretation and handler behavior
remain unknown. Never seek those raw values in the input or infer executable
RAM solely because they are outside the ROM window.

Original execution from reset through the selected resource/gameplay paths is
still needed for dynamic validation. Do not turn the remaining ROM into code
through a linear sweep. Reset task: [[07_Tasks/TASK-0001-foundation]].

## Statically verified resource path

[[03_Reverse_Engineering/findings/FIND-0007-rnc-loader]] establishes:

| Address | Role and transfer |
| --- | --- |
| `0x10D8` | Descriptor selector: table `0x33400` plus signed low word of unsigned index*34, stored to effective RAM `0xFFFF33F0` |
| `0x1896` | Loads that descriptor; A0 gets its `+0x1C` bank pointer; tail JMP at `0x18E8` to `0x3CB6` |
| `0x3CB6` | PACK-aware pair loader; verified JSR at `0x3CFA` to decoder with A0 past wrapper and A1=`0xFFFF8844` |
| `0x19462` | RNC2 decoder; closed 147-instruction graph, sole RTS at `0x1959C`; skips rather than checks the 18-byte header |
| `0x3D46` | First-bank consumer after return; palette/count/pattern/opaque-record layout |
| `0x13754` | Fixed 16-entry palette conversion, with nested callee `0x137CE` still incompletely traced |

Descriptor zero points to `PACK` at `0x348AE`, four bytes before the cataloged RNC
header. The A1-selected resource consumed by `0x3E14` is resolved in the companion
section below. Runtime index selection and reachability
from reset are unobserved. Sixteen direct-transfer byte matches to the decoder
are discovery candidates; only the documented chain is promoted here.

`rnc-loader-probe --disassemble` validates exact region bytes, control targets,
closed decoder reachability, selected field relationships and 16 short independent
GNU instruction crosschecks. This is static analysis, not CPU interpretation.


## Companion selection and map consumer

[[03_Reverse_Engineering/findings/FIND-0009-companion-scene]] resolves the saved
A1 path: for descriptor 0 with the smaller signed state+0x26 word in 0–2, dispatcher
selects slot 0 -> PACK `0x48FD4` -> RNC2 `0x48FD8`. The pair loader restores that
pointer at `0x3D0A`, optionally decompresses at `0x3D20`, and calls `0x3E14`.
Actual runtime selection remains unobserved.

`ConsumeCompanionScene [0x3E14,0x3F34)` copies counted coordinates, two state
starts, 136 additional patterns, map header and opaque records on the known input.
`InitializeSceneMapWords [0x3F34,0x3F60)` performs 4096 full-word relocations and
palette selection. The internal column-reader fragment `[0x406C,0x40F8)`
corroborates row-major indexing/stride and 32-row bounds; it is not a complete
function. FUNC-0008/0009 were added in that pass; current total is 31 entries.

`scene-probe --disassemble` checks exact bytes, 56 reviewed fields and 16 GNU
corroborations across 67 consumer, 11 map-helper and 36 fragment instructions.
Those instruction counts are disassembly scope, not executed coverage.
The former terrain-query leads are now resolved as described below.


## Executed terrain/contact routines

[[03_Reverse_Engineering/findings/FIND-0010-terrain-query]] promotes six entries
FUNC-0010–0015: map query `0x99D4`, record query `0x9A18`, settling `0x9A80` and
contact probes `0x9B34/0x9B5C/0x9B84`. `terrain-probe --disassemble` validates 97
instructions in seven exact hashed ranges, ten direct calls, closed branches
and 12 GNU corroborations. The seventh range `[0x2908,0x2934)` is a duplicate
contact fragment, not another promoted function entry.

Pinned isolated M68000 execution visits 86/86 instruction addresses in the six
routines across 614,436 comparison cases per preset. All semantic outputs/state
and exposed NZVC agree with native C++. These are constructed state/function
runs, not evidence of full-game reachability or timing. The horizontal chain at `0x9AAE` is now resolved below.
The `0x9BAC` airborne horizontal helper is now resolved below.

## Executed horizontal movement and state transition

[[03_Reverse_Engineering/findings/FIND-0011-movement-step]] adds FUNC-0016–0023.
`0x9A5E` loops over damping at `0x9A6C`. `0x9AAE` either tail-calls settling
or chooses the `0x9AC8`/`0x9B04` left/right step, using a body-first DBF loop.
The positive dispatcher fragment is at `0x9AF8`; it is not another function.
Each single step calls foot/upper/foot probes in order as needed, then the
signed clamp `0xACE8`/`0xACD6` and tail transition `0xAA50` on loss of contact.
That transition assigns handler `0xAAEA` and returns; the horizontal loop
continues. The handler itself is not executed by these calls.

Nine executed fragments add 260 bytes / 74 instructions. Six hashed static
context fragments add 390 bytes / 84 instructions and establish the paired
A5/A6 bindings and initializer/caller relationships. The combined executable
graph closes across 160 instructions; all are visited across terrain and
movement corpora. This does not prove reset reachability or frame scheduling.
The next airborne/landing handler has since been resolved as described below.

## Airborne execution with explicit idle continuation exits

[[03_Reverse_Engineering/findings/FIND-0012-airborne-update]] adds eight mappings
FUNC-0024–0031. Delay/boost prefix `0xAAEA` falls into `0xAB04`, which applies
damping/controls/gravity, calls the airborne horizontal chain at `0x9BAC`, then
uses downward settling or upward subtraction. Horizontal left/right pixels at
`0x9BCA/0x9C18` probe upper contact and damp on equality; their dispatcher forces
non-equality on nonzero-speed return. Landing at `0xAB8A` selects presentation
and grounded handler, calling reload helpers `0xA658/0xA690` as needed.

Zero-speed normal landing branches into initializer `0xA1A4/0xA22C` and falls
immediately into idle `0xA1BE/0xA246`. These are declared same-call boundaries,
not RTS or a new frame. Reference execution pauses before the idle instruction;
native returns an explicit pending continuation. The 706-byte new scope has
172 instructions; combined graph contains 332 with exactly those two external
fallthrough edges. Full idle/grounded handlers are
[[07_Tasks/TASK-0010-grounded-controller]].

## The top-level loop between scenes

Observed in the preserved recording (sessions 053..056) and read statically;
see [[03_Reverse_Engineering/findings/FIND-0051-hub-doors]],
[[03_Reverse_Engineering/findings/FIND-0052-scene-change]] and
[[03_Reverse_Engineering/findings/FIND-0053-second-level-entry]]. FF33E0 is the
scene's mode word.

| Address | Evidence | Current interpretation |
|---|---|---|
| `0x418..0x424` | Recording 634, 1532 | 108A (FF33F8/FF33F4/FF33FC descriptors), 103A, then JSR 6664: the first level (its loop runs while FF33E0 = 000E) |
| `0x42A..0x46E` | Static | FF33E0 = 8, 9, 12/11 dispatch to other scenes, back to 0x424 |
| `0x470..0x49E` | Recording 1532 | 17400, FF33E0 = 0A's FF31C8 call, 0x488 (FF4446/48 into FF0690's +A2/+A4), JSR 5D30: the hub (loops while 6024 does not end it) |
| `0x4A4..0x4CA` | Recording 1758 | 10D8 (FF33F0), 10F8; unless FF13E2 = 3, FF32BE = FF33F4's +0E and JSR 1959E, the hint screen (none when FF32BE is FFFFFFFF) |
| `0x4CA..0x4EA` | Recording 2067..2106 | E2A (16EA4, P1's +A2/+A4 cleared, 9880, resources); FF0690's +80..+88 cleared |
| `0x4EA` | Recording 2106 onward | BSR 754: 118C, FF33E0 = 0013, 14A4 (music), then its own loop at 0x792 while FF33E0 = 0013: the second level |
| `0x4EE..0x73E` | Static | After 754 returns: FF33E0 dispatch (3: 5736 and repeat; 1: next stage via 1B1AA/1D134, FF33C4 + 1; 0B; 0C; else 73E, 139E0/13830 and 0x33A) |
