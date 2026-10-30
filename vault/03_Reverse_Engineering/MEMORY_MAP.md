---
id: RE-MEMORY-MAP
type: technical
status: partial
---
# Address spaces and initial observations

All ranges use `[start,end)` with end exclusive. `re/rom_manifest.json` is the
identity authority; see [[03_Reverse_Engineering/ROM_IDENTITY]]. No normalization
was performed. The header declares an initial ROM window `0x000000`–`0x0FFFFF`
inclusive. For the reset fragment and the corroborated resource routines/data in FIND-0007,
direct file offset = CPU address in that window is the working mapping. Banked/aliased views have not been observed.

Keep these spaces separate:

| Space | Representation and evidence |
|---|---|
| ROM file offset | Byte index `[0,0x100000)` into the identified immutable input |
| 68000 effective address | 32-bit value held in registers/instruction operands; never a host pointer |
| 68000 external address | Original MC68000 has a 24-bit external address space; truncation alone does not prove what device responds |
| Main memory | Reset loop statically writes `[0xFFFF0000,0x100000000)` effective addresses, externally `[0xFF0000,0x1000000)`; no captured RAM state yet |
| Z80/program view | Not established; reset copies 38 bytes to 68000 effective address `0x00A00000`, but this finding does not translate it into a validated Z80 execution range |
| Video/audio device spaces | Not established; port-address operands are not video-memory offsets or sample positions |

The raw initial SP is `0xFFFF0100`, whose 24-bit external address is `0xFF0100`.
Keep both representations in evidence. Similarly, raw vector `0x0220800C`
reduces to `0x20800C`, still outside this ROM's directly mapped file range;
that does not justify modulo-ROM wrapping or invented handlers.

[[03_Reverse_Engineering/findings/FIND-0001-reset-path]] establishes only these
specific observed startup references:

- Tests at effective addresses `0x00A10008` and `0x00A1000C` control whether the
  initialization fragment executes.
- Seed address registers contain `0x00A00000`, `0x00A11100`, `0x00A11200`,
  `0x00C00000`, `0x00C00004`. Their exact game-visible device behavior is pending
  reference validation; these are not ROM offsets.
- The byte read at `0x21C` uses A1−`0x10FF`=`0x00A10001`; the conditional long
  write at `0x226` uses A1+`0x2F00`=`0x00A14000`. The literal encodes `SEGA`.
  A probable hardware initialization interpretation is a lead, not proof of
  the game's platform timing or all memory mappings.

Primary architecture source:
[Motorola M68000 User's Manual](https://www.nxp.com/docs/en/reference-manual/MC68000UM.pdf),
§2, accessed 2026-10-02. Task context: [[07_Tasks/TASK-0001-foundation]].
There is no general CPU-to-file conversion API yet; refuse unmapped addresses
instead of assuming every apparent pointer belongs to the ROM.

## Resource-loader references (static, not captured memory)

[[03_Reverse_Engineering/findings/FIND-0007-rnc-loader]] distinguishes these
additional spaces; all RAM values below are instruction operands/dataflow, not
emulator snapshots:

| Effective / file address | Observed role |
| --- | --- |
| ROM `0x33400`, stride `0x22` | Resource descriptor base/stride; only record zero's full structure is classified |
| ROM `0x348AE` / `0x348B2` | PACK tag / RNC2 header, respectively |
| RAM effective `0xFFFF33F0` (external `0xFF33F0`) | Selected descriptor pointer |
| RAM effective `0xFFFF8844` (external `0xFF8844`) | First-bank decompression destination; 17,714 bytes on descriptor-zero path |
| RAM effective `0xFFFF0D20` (external `0xFF0D20`) | Sixteen converted palette inputs for selector 2 |
| RAM effective `0xFFFF6D02` (external `0xFF6D02`) | Initial destination for 442 eight-byte opaque companion records |
| Effective `0xFFC00004` / `0xFFC00000` (external `0xC00004` / `0xC00000`) | Control/data writes in the pattern-transfer path; video-port interpretation, timing unobserved |

The scratch interval ends at effective `0xFFFFCD76` for the known output. These
are observed legacy addresses, not host allocation limits or permanent resource
identifiers. No general address conversion or banked-memory model is introduced.


## Companion resource and map (static dataflow)

[[03_Reverse_Engineering/findings/FIND-0009-companion-scene]] adds:

| Space / address | Role |
| --- | --- |
| ROM `0x48FD4` / `0x48FD8` | Companion PACK tag / RNC2 header |
| RAM `[0xFFFF8844,0xFFFFBDC8)` | Companion decode output, 13,700 bytes; scratch reused after first bank consumed |
| RAM `[0xFFFF4C80,0xFFFF4CB8)` | 13 translated coordinate pairs plus two FFFF word sentinels |
| RAM `0xFFFF0690+0x3C/+0x3E`, `0xFFFF0838+0x3C/+0x3E` | Two translated state-start pairs; gameplay role pending |
| RAM `[0xFFFF4D02,0xFFFF6D02)` | 4096 relocated map words; pointer stored at `0xFFFF4452` |
| RAM `[0xFFFF7AD2,0xFFFF7F12)` | Companion 136 opaque records after the base 442 records |
| RAM `0xFFFF13A4` | Map row stride in bytes, first header word*2 |

External RAM addresses are the low 24 bits; none are ROM offsets or host pointers.
Native resource IDs/indexed arrays replace these layouts. No captured RAM state
or original device timing is claimed by these derived intervals.


## Constructed terrain execution fixtures

[[03_Reverse_Engineering/findings/FIND-0010-terrain-query]] executes six original
routines against explicit fixture RAM, not a captured full-game state. Added
verified operands: scratch x/y `0xFFFF4442/4444`, adjusted record base pointer
`0xFFFF444E`, map pointer `0xFFFF4452`, pixel-x mask `0xFFFF13AE`, base-pattern
sentinel `0xFFFF140E`. Map stride at `0xFFFF13A4` is 256 for the known resource;
x mask is 1023. A6+2/+4 are the position words used by these callers.

The research fixture places map words at `0xFFFF4D02`, records at `0xFFFF8000`,
actor state at `0xFFFF0690` and the return stack at `0xFFFFF000`. Records are
intentionally relocated from the original loader's destination to verify
pointer independence. Bases0 and 257 are constructed inputs, not observed game
setup values. Only declared reads, scratch/state/stack writes and reviewed code
are permitted. Native code uses resources/explicit state, never these addresses.

## Paired actor/control records and movement fixtures

[[03_Reverse_Engineering/findings/FIND-0011-movement-step]] statically identifies
control A5=`0xFFFF0690` -> actor A6=`0xFFFF1AB4`, and control `0xFFFF0838` ->
actor `0xFFFF1B02`. The pointer is stored at control+0 and the backlink at
actor+0x4A; actor stride is 0x4E. Physical pad/player identity is not traced.
Actor+2/+4 are x/y, +0x22 signed horizontal speed, +0x26 vertical motion,
+0x2A delay, +0x16 long handler. The airborne transition assigns mode+0,
presentation words+6/+8/+A, counters+C/+D and handler `0xAAEA`. Controls hold
signed speed limits at +0x5A/+0x5C and damping count-minus-one at +0x66.

Movement execution fixtures now place the actor at the first actual bound
address `0xFFFF1AB4` and controls at `0xFFFF0690`. The older terrain-only fixture
used `0xFFFF0690` as an arbitrary A6 test address; that was not an ownership
claim. Both remain constructed states, not captured game RAM. Native motion
uses explicit state/parameters/events and no legacy address-space interpreter.

## Airborne controls and continuation state

[[03_Reverse_Engineering/findings/FIND-0012-airborne-update]] adds control byte
inputs at A5+0x16 (boost), +0x1C/+0x1D (directional acceleration), words +0x60
(acceleration), +0x6A (contact damping count minus one), +0x6C (gravity), and
gate word at effective `0xFFFF0F16`. Actor flags at +0x12 retain all bits except
verified direction bit 0800 updates. Physical button producers remain untraced.

The constructed reference uses the established first actor/control addresses.
At ordinary RTS the fixture SP is `0xFFFFF004`; at immediate idle continuation
`0xA1BE/0xA246` it is `0xFFFFF000`, with the caller return still pending. Native
code exposes continuation state instead of an original stack or code pointer.
Landing-selected logical handlers do not imply that their future instructions
or a full game scheduler have been implemented.
